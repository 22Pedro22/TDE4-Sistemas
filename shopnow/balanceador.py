#!/usr/bin/env python3

"""

Algoritmos implementados:

    Round Robin (rodízio)
    Least Connections (menor número de conexões ativas)

"""

import socket
import threading
import time
import sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

import config


class EstadoServidor:

    # guarda o estado do servidor backend

    def __init__(self, host: str, porta: int, identificador: str):
        self.host = host
        self.porta = porta
        self.identificador = identificador
        self.ativo = True
        self.conexoes_ativas = 0
        self.falhas_consecutivas = 0

    def endereco(self) -> str:
        return f"{self.host}:{self.porta}"

    def __repr__(self):
        status = "ATIVO" if self.ativo else "OFFLINE"
        return f"{self.identificador} ({self.endereco()}) [{status}] conexões={self.conexoes_ativas}"


class Balanceador:

    def __init__(self, servidores: list, algoritmo: str = "round_robin"):
        self.servidores = [
            EstadoServidor(host, porta, ident)
            for host, porta, ident in servidores
        ]
        self.algoritmo = algoritmo
        self.indice_round_robin = 0
        self.indice_desempate = 0  # desempate do least_connections
        self.lock = threading.Lock()
        self.rodando = True

        # inicia o health check em background

        thread_health = threading.Thread(target=self._loop_health_check, daemon=True)
        thread_health.start()

        print(f"⚖️  Balanceador iniciado com algoritmo: {self.algoritmo.upper()}")
        print(f"   Servidores configurados: {len(self.servidores)}")
        for s in self.servidores:
            print(f"   - {s}")
        print()

    def servidores_ativos(self) -> list:

        # só retorna os servidores ativos

        return [s for s in self.servidores if s.ativo]

    def escolher_servidor(self) -> EstadoServidor | None:

        # scolhe o próximo servidor de acordo com o algoritmo configurado

        with self.lock:
            ativos = self.servidores_ativos()
            if not ativos:
                return None

            if self.algoritmo == "round_robin":
                return self._round_robin(ativos)
            elif self.algoritmo == "least_connections":
                return self._least_connections(ativos)
            else:

                # fallback seguro

                return ativos[0]

    def _round_robin(self, ativos: list) -> EstadoServidor:

        # algoritmo do round robin

        servidor = ativos[self.indice_round_robin % len(ativos)]
        self.indice_round_robin = (self.indice_round_robin + 1) % len(ativos)
        return servidor

    def _least_connections(self, ativos: list) -> EstadoServidor:

        # algoritmo do least connections

        menor = min(s.conexoes_ativas for s in ativos)
        empatados = [s for s in ativos if s.conexoes_ativas == menor]
        servidor = empatados[self.indice_desempate % len(empatados)]
        self.indice_desempate += 1
        return servidor

    def _loop_health_check(self):

        # vai verificando se os servidores respondem

        while self.rodando:
            for servidor in self.servidores:
                self._verificar_saude(servidor)
            time.sleep(config.INTERVALO_HEALTH_CHECK)

    def _verificar_saude(self, servidor: EstadoServidor):

        # faz requisição simples para verificar o estaudo do servidor

        url = f"http://{servidor.host}:{servidor.porta}/"
        try:
            requisicao = Request(url, method="GET")
            with urlopen(requisicao, timeout=config.TIMEOUT_HEALTH_CHECK) as resposta:
                if resposta.status == 200:
                    if not servidor.ativo:
                        print(f"✅ {servidor.identificador} voltou a ficar ONLINE")
                    servidor.ativo = True
                    servidor.falhas_consecutivas = 0
                else:
                    self._marcar_falha(servidor)
        except (URLError, HTTPError, TimeoutError, ConnectionError, OSError):
            self._marcar_falha(servidor)

    def _marcar_falha(self, servidor: EstadoServidor):

        servidor.falhas_consecutivas += 1
        if servidor.falhas_consecutivas >= 2 and servidor.ativo:
            servidor.ativo = False
            print(f"❌ {servidor.identificador} marcado como OFFLINE (falha de health check)")

    def registrar_falha_encaminhamento(self, servidor: EstadoServidor):

        with self.lock:
            servidor.falhas_consecutivas += 1
            if servidor.ativo:
                servidor.ativo = False
                print(f"❌ {servidor.identificador} marcado como OFFLINE (erro de encaminhamento)")

    def escolher_e_reservar(self, excluidos):

        with self.lock:
            ativos = [s for s in self.servidores_ativos() if s.identificador not in excluidos]
            if not ativos:
                return None
            if self.algoritmo == "least_connections":
                servidor = self._least_connections(ativos)
            else:
                servidor = self._round_robin(ativos)
            servidor.conexoes_ativas += 1
            return servidor

    def incrementar_conexao(self, servidor: EstadoServidor):
        with self.lock:
            servidor.conexoes_ativas += 1

    def decrementar_conexao(self, servidor: EstadoServidor):
        with self.lock:
            servidor.conexoes_ativas = max(0, servidor.conexoes_ativas - 1)

    def status(self) -> str:

        # resumo do estado atual dos servidores

        linhas = [f"Algoritmo atual: {self.algoritmo}", "Servidores:"]
        for s in self.servidores:
            linhas.append(f"  - {s}")
        return "\n".join(linhas)


# instância global do balanceador (será criada no main)
balanceador_global: Balanceador | None = None


class ServidorBalanceador(ThreadingHTTPServer):

    # atende cada cliente em uma thread

    request_queue_size = 256
    daemon_threads = True


class ManipuladorBalanceador(BaseHTTPRequestHandler):

    # recebe as requisições dos clientes e repassa para um servidor backend

    def do_GET(self):
        self._processar_requisicao()

    def do_POST(self):
        self._processar_requisicao()

    def do_HEAD(self):
        self._processar_requisicao()

    def _processar_requisicao(self):
        global balanceador_global

        caminho = urlparse(self.path).path

        if caminho == "/status":
            self._responder_status()
            return

        if caminho == "/algoritmo":
            self._trocar_algoritmo()
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho) if tamanho > 0 else None

        excluidos = set()
        for _ in range(len(balanceador_global.servidores)):
            servidor = balanceador_global.escolher_e_reservar(excluidos)
            if servidor is None:
                break
            try:
                if self._encaminhar_requisicao(servidor, corpo):
                    return
            finally:
                balanceador_global.decrementar_conexao(servidor)
            excluidos.add(servidor.identificador)  # falhou: tenta outro servidor

        self.send_error(503, "Nenhum servidor disponível no momento")

    def _encaminhar_requisicao(self, servidor: EstadoServidor, corpo) -> bool:

        # devolve o status da conexão

        url = f"http://{servidor.host}:{servidor.porta}{self.path}"
        try:
            requisicao = Request(url, data=corpo, method=self.command)
            for chave, valor in self.headers.items():
                if chave.lower() not in ("host", "content-length"):
                    requisicao.add_header(chave, valor)

            with urlopen(requisicao, timeout=5) as resposta_backend:
                conteudo = resposta_backend.read()
                status = resposta_backend.status
                cabecalhos = resposta_backend.getheaders()
        except HTTPError as e:
            if e.code >= 500:
                print(f"⚠️  {servidor.identificador} respondeu {e.code}")
                balanceador_global.registrar_falha_encaminhamento(servidor)
                return False
            status, conteudo, cabecalhos = e.code, e.read(), e.headers.items()
        except Exception as e:
            print(f"⚠️  Erro ao encaminhar para {servidor.identificador}: {e}")
            balanceador_global.registrar_falha_encaminhamento(servidor)
            return False

        self.send_response(status)
        for chave, valor in cabecalhos:
            if chave.lower() not in ("transfer-encoding", "server", "date"):
                self.send_header(chave, valor)
        self.send_header("X-Balanceador-Servidor", servidor.identificador)
        self.send_header("X-Balanceador-Algoritmo", balanceador_global.algoritmo)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(conteudo)
        print(f"→ {self.command} {self.path}  →  {servidor.identificador}")
        return True

    def _responder_status(self):

        # endpoint de status do balanceador

        global balanceador_global
        texto = balanceador_global.status()
        conteudo = texto.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def _trocar_algoritmo(self):

        # permite trocar o algoritmo em tempo de execução

        global balanceador_global
        parametros = parse_qs(urlparse(self.path).query)
        novo = parametros.get("nome", [None])[0]

        if novo in ("round_robin", "least_connections"):
            balanceador_global.algoritmo = novo
            mensagem = f"Algoritmo alterado para: {novo}"
            print(f"🔄 {mensagem}")
        else:
            mensagem = "Algoritmo inválido. Use: round_robin ou least_connections"

        conteudo = mensagem.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def log_message(self, formato, *args):
        pass


def iniciar_balanceador(algoritmo: str = None):

    # inicia e sobe o balanceador

    global balanceador_global

    if algoritmo is None:
        algoritmo = config.ALGORITMO_PADRAO

    balanceador_global = Balanceador(config.SERVIDORES, algoritmo=algoritmo)

    endereco = ("0.0.0.0", config.PORTA_BALANCEADOR)
    servidor_http = ServidorBalanceador(endereco, ManipuladorBalanceador)

    print(f"🌐 Balanceador escutando em http://127.0.0.1:{config.PORTA_BALANCEADOR}")
    print("   Endpoints úteis:")
    print(f"   - http://127.0.0.1:{config.PORTA_BALANCEADOR}/          → site")
    print(f"   - http://127.0.0.1:{config.PORTA_BALANCEADOR}/status    → status dos servidores")
    print(f"   - http://127.0.0.1:{config.PORTA_BALANCEADOR}/algoritmo?nome=round_robin")
    print(f"   - http://127.0.0.1:{config.PORTA_BALANCEADOR}/algoritmo?nome=least_connections")
    print("\n   Pressione Ctrl+C para parar.\n")

    try:
        servidor_http.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Balanceador encerrado.")
        balanceador_global.rodando = False
        servidor_http.server_close()


if __name__ == "__main__":
    algoritmo_escolhido = None
    if len(sys.argv) > 1:
        algoritmo_escolhido = sys.argv[1]
        if algoritmo_escolhido not in ("round_robin", "least_connections"):
            print("Algoritmo inválido. Use: round_robin ou least_connections")
            sys.exit(1)

    iniciar_balanceador(algoritmo_escolhido)

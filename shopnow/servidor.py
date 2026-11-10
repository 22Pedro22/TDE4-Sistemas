#!/usr/bin/env python3
"""
Instância do site ShopNow.
Rode várias vezes em portas diferentes para simular múltiplos servidores.
Exemplo:
    python servidor.py 8001
    python servidor.py 8002
    python servidor.py 8003
"""

import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


class ManipuladorShopNow(BaseHTTPRequestHandler):
    """Manipula as requisições HTTP de cada instância do site."""

    identificador_servidor = "Servidor-Desconhecido"
    porta_servidor = 0

    def do_GET(self):
        """Responde a requisições GET com uma página HTML simples."""
        self._responder_pagina()

    def do_HEAD(self):
        """Responde a requisições HEAD (usado por ferramentas de teste)."""
        self._responder_pagina(apenas_cabecalhos=True)

    def _responder_pagina(self, apenas_cabecalhos=False):
        """Gera e envia a página HTML do ShopNow."""
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopNow - {self.identificador_servidor}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #333;
        }}
        .container {{
            background: white;
            padding: 40px 50px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
        }}
        h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.2em;
        }}
        .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 1.1em;
            margin: 15px 0;
            font-weight: bold;
        }}
        .info {{
            margin-top: 20px;
            color: #666;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        .porta {{
            color: #764ba2;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛒 ShopNow</h1>
        <div class="badge">{self.identificador_servidor}</div>
        <div class="info">
            <p>Você está sendo atendido por este servidor.</p>
            <p>Porta: <span class="porta">{self.porta_servidor}</span></p>
            <p>Horário: {horario}</p>
        </div>
    </div>
</body>
</html>"""

        conteudo = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.send_header("X-Servidor", self.identificador_servidor)
        self.end_headers()

        if not apenas_cabecalhos:
            self.wfile.write(conteudo)

    def log_message(self, formato, *args):
        """Log personalizado em português."""
        print(f"[{self.identificador_servidor}] {args[0]}", flush=True)


def iniciar_servidor(porta: int):
    """Inicia uma instância do servidor ShopNow na porta informada."""
    # Mapeia a porta para um nome amigável (8001 → Servidor-1, etc.)
    mapa_nomes = {
        8001: "Servidor-1",
        8002: "Servidor-2",
        8003: "Servidor-3",
    }
    identificador = mapa_nomes.get(porta, f"Servidor-{porta}")

    ManipuladorShopNow.identificador_servidor = identificador
    ManipuladorShopNow.porta_servidor = porta

    endereco = ("0.0.0.0", porta)
    servidor = HTTPServer(endereco, ManipuladorShopNow)

    print(f"🚀 {identificador} rodando em http://127.0.0.1:{porta}")
    print("   Pressione Ctrl+C para parar.\n")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 {identificador} encerrado.")
        servidor.server_close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python servidor.py <porta>")
        print("Exemplo: python servidor.py 8001")
        sys.exit(1)

    try:
        porta = int(sys.argv[1])
    except ValueError:
        print("Erro: a porta deve ser um número inteiro.")
        sys.exit(1)

    iniciar_servidor(porta)

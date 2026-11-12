# ShopNow - Balanceador de Carga

Projeto de **Sistemas Distribuídos**: implementação de um balanceador de carga com múltiplas instâncias de um site de e-commerce (ShopNow).

## Objetivo

Simular um ambiente de alta concorrência (ex: Black Friday) com:

- Múltiplas instâncias do site ShopNow (mínimo 3)
- Um balanceador de carga na frente das instâncias
- Dois algoritmos de balanceamento diferentes
- Simulação de falha de servidores
- Testes de carga com Apache Benchmark (`ab`)

## Estrutura do Projeto

```
shopnow/
├── config.py           # Configurações (portas, servidores, algoritmo)
├── servidor.py         # Instância do site ShopNow
├── balanceador.py      # Balanceador de carga (Round Robin + Least Connections)
├── iniciar.sh          # Script para subir tudo de uma vez (opcional)
├── teste_carga.sh      # Script de teste de carga com Apache Benchmark
├── requirements.txt
├── .gitignore
└── README.md
```

## Algoritmos Implementados

| Algoritmo              | Descrição                                                        |
|------------------------|------------------------------------------------------------------|
| **Round Robin**        | Distribui as requisições de forma cíclica entre os servidores ativos |
| **Least Connections**  | Encaminha a requisição para o servidor com menos conexões ativas     |

## Como Executar

### Opção 1 – Manual (recomendado para entender melhor)

Abra **4 terminais**:

```bash
# Terminal 1
python servidor.py 8001

# Terminal 2
python servidor.py 8002

# Terminal 3
python servidor.py 8003

# Terminal 4
python balanceador.py                  # Round Robin (padrão)
# ou
python balanceador.py least_connections
```

### Opção 2 – Script único (mais prático)

```bash
chmod +x iniciar.sh
./iniciar.sh                           # Round Robin
./iniciar.sh least_connections         # Least Connections
```

O balanceador fica disponível em: **http://127.0.0.1:8080**

### Endpoints úteis

| URL | Descrição |
|-----|-----------|
| `http://127.0.0.1:8080/` | Página do ShopNow (requisição balanceada) |
| `http://127.0.0.1:8080/status` | Status dos servidores e algoritmo atual |
| `http://127.0.0.1:8080/algoritmo?nome=round_robin` | Troca para Round Robin |
| `http://127.0.0.1:8080/algoritmo?nome=least_connections` | Troca para Least Connections |

## Simulação de Falha

1. Pare um dos servidores com `Ctrl+C` no terminal dele.
2. Aguarde alguns segundos (health check roda a cada 5s).
3. Acesse `/status` → o servidor aparecerá como **OFFLINE**.
4. O balanceador deixa de enviar tráfego para ele automaticamente.
5. Para simular recuperação, suba o servidor novamente. O health check detecta e volta a utilizá-lo.

## Teste de Carga

```bash
# Dê permissão de execução (apenas uma vez)
chmod +x teste_carga.sh

# Execute o teste (balanceador precisa estar rodando)
./teste_carga.sh
```

O script utiliza o **Apache Benchmark (`ab`)** com:
- 10000 requisições
- 100 conexões concorrentes

### Instalação do Apache Benchmark

```bash
# Ubuntu / Debian / WSL
sudo apt install apache2-utils

# Fedora
sudo dnf install httpd-tools

# macOS
# Já vem instalado na maioria das vezes, ou:
brew install apache2
```

## Requisitos

- Python 3.10 ou superior
- Apenas biblioteca padrão do Python (não precisa instalar nada com pip)
- Apache Benchmark (`ab`) apenas para os testes de carga

## Dicas para a Apresentação

1. Mostre os 3 servidores rodando em terminais separados.
2. Acesse o balanceador várias vezes e observe o servidor mudando (header `X-Balanceador-Servidor` ou o nome na página).
3. Pare um servidor e mostre no `/status` que ele ficou OFFLINE.
4. Continue fazendo requisições → só os servidores ativos respondem.
5. Troque o algoritmo em tempo real via `/algoritmo`.
6. Execute o teste de carga e mostre os resultados do `ab`.

## Observações Técnicas

- O balanceador realiza **health check** periódico nos servidores.
- Contador de conexões ativas é usado pelo algoritmo Least Connections.
- Em caso de erro ao encaminhar uma requisição, o servidor pode ser marcado como offline.
- Todo o código utiliza apenas a biblioteca padrão do Python (`http.server`, `urllib`, `threading`, etc.).

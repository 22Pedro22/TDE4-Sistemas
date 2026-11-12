# Configurações do projeto

# Porta onde o balanceador vai escutar

PORTA_BALANCEADOR = 8080

# Lista de servidores backend (instâncias do site)
# Formato: (host, porta, identificador)

SERVIDORES = [
    ("127.0.0.1", 8001, "Servidor-1"),
    ("127.0.0.1", 8002, "Servidor-2"),
    ("127.0.0.1", 8003, "Servidor-3"),
]

# Intervalo de health check

INTERVALO_HEALTH_CHECK = 5

# Timeout para considerar um servidor como offline

TIMEOUT_HEALTH_CHECK = 2

# Algoritmo padrão: round_robin ou least_connections

ALGORITMO_PADRAO = "round_robin"

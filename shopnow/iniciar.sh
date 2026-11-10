#!/bin/bash
# Script auxiliar para subir os 3 servidores + balanceador de uma vez
# Uso: ./iniciar.sh [algoritmo]
# Exemplos:
#   ./iniciar.sh
#   ./iniciar.sh round_robin
#   ./iniciar.sh least_connections

ALGORITMO=${1:-round_robin}
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================="
echo "  ShopNow - Iniciando ambiente completo"
echo "=============================================="
echo "Algoritmo: $ALGORITMO"
echo ""

# Sobe os 3 servidores em background
python3 "$DIR/servidor.py" 8001 &
PID1=$!
python3 "$DIR/servidor.py" 8002 &
PID2=$!
python3 "$DIR/servidor.py" 8003 &
PID3=$!

sleep 1

echo "Servidores iniciados (PIDs: $PID1, $PID2, $PID3)"
echo ""

# Função de limpeza ao sair (Ctrl+C)
limpar() {
    echo ""
    echo "Encerrando todos os processos..."
    kill $PID1 $PID2 $PID3 2>/dev/null
    exit 0
}
trap limpar SIGINT SIGTERM

# Sobe o balanceador em primeiro plano
python3 "$DIR/balanceador.py" "$ALGORITMO"

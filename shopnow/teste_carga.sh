#!/bin/bash
# Script de teste de carga para o Balanceador do ShopNow
# Requer: Apache Benchmark (ab)
# Instalação:
#   Ubuntu/Debian: sudo apt install apache2-utils
#   macOS:         já vem instalado ou brew install apache2

URL="http://127.0.0.1:8080/"
TOTAL_REQUISICOES=1000
CONCORRENCIA=50

echo "=============================================="
echo "  Teste de Carga - ShopNow Balanceador"
echo "=============================================="
echo "URL:            $URL"
echo "Requisições:    $TOTAL_REQUISICOES"
echo "Concorrência:   $CONCORRENCIA"
echo "=============================================="
echo ""

# Verifica se o ab está instalado
if ! command -v ab &> /dev/null; then
    echo "Erro: Apache Benchmark (ab) não encontrado."
    echo "Instale com: sudo apt install apache2-utils"
    exit 1
fi

# Verifica se o balanceador está respondendo
if ! curl -s --max-time 2 "$URL" > /dev/null; then
    echo "Erro: Balanceador não está respondendo em $URL"
    echo "Certifique-se de que o balanceador e os servidores estão rodando."
    exit 1
fi

echo "Iniciando teste..."
echo ""

ab -n $TOTAL_REQUISICOES -c $CONCORRENCIA -g resultados.tsv "$URL"

echo ""
echo "=============================================="
echo "Teste finalizado!"
echo "Arquivo de resultados: resultados.tsv"
echo "=============================================="
echo ""
echo "Dica: Acesse http://127.0.0.1:8080/status para ver o estado dos servidores."

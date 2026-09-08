#!/bin/bash
# Script para executar a aplicação em desenvolvimento com recarregamento automático

echo "Iniciando Sistema de Descoberta de Rede..."
echo "Acesse: http://localhost:5000/rede"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Executar com recarregamento automático
export FLASK_APP=app.py
export FLASK_ENV=development
python3 app.py

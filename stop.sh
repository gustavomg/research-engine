#!/bin/bash

echo "🛑 Parando Research Engine..."

# Parar sesión tmux
tmux kill-session -t research-engine 2>/dev/null && echo "✅ tmux parado" || echo "⚪ tmux no estaba activo"

# Parar agentes Python
pkill -f "python3.*research-engine" 2>/dev/null && echo "✅ Agentes parados" || echo "⚪ No había agentes activos"

# Parar monitor Flask
pkill -f "monitor/server.py" 2>/dev/null && echo "✅ Monitor parado" || echo "⚪ Monitor no estaba activo"

# Parar Ollama
pkill ollama 2>/dev/null && echo "✅ Ollama parado" || echo "⚪ Ollama no estaba activo"

# Parar Dolt (siempre el último)
cd ~/research-engine && /home/oracle/go/bin/bd dolt stop 2>/dev/null && echo "✅ Dolt parado" || echo "⚪ Dolt no estaba activo"

echo ""
echo "🏁 Research Engine detenido completamente."

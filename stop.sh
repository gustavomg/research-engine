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

# Opcional: limpiar todas las tareas de Beads
if [ "$1" == "--clean" ]; then
    echo "🧹 Limpiando tareas de Beads..."
    pkill dolt 2>/dev/null
    sleep 1
    rm -rf /home/oracle/research-engine/.beads
    cd /home/oracle/research-engine && /home/oracle/go/bin/bd dolt start && sleep 2 && /home/oracle/go/bin/bd init
    echo "✅ Beads reiniciado limpio"
fi

# Opcional: limpiar todas las tareas de Beads
if [ "$1" == "--clean" ]; then
    echo "🧹 Limpiando tareas de Beads..."
    pkill dolt 2>/dev/null
    sleep 1
    rm -rf /home/oracle/research-engine/.beads
    cd /home/oracle/research-engine && /home/oracle/go/bin/bd dolt start && sleep 2 && /home/oracle/go/bin/bd init
    echo "✅ Beads reiniciado limpio"
fi

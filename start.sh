#!/bin/bash
SESSION="research-engine"

tmux kill-session -t $SESSION 2>/dev/null
pkill -f "python3.*research-engine" 2>/dev/null
pkill ollama 2>/dev/null
sleep 1

# Limpiar outputs anteriores
rm -f /home/oracle/research-engine/findings/*.md
rm -f /home/oracle/research-engine/informe-final.md
rm -f /home/oracle/research-engine/informe-critico.md

# Arrancar Ollama
echo "🚀 Arrancando Ollama..."
ollama serve > /tmp/ollama.log 2>&1 &
sleep 3
echo "✅ Ollama listo"

# Arrancar monitor web
echo "📊 Arrancando monitor web..."
python3 /home/oracle/research-engine/monitor/server.py > /tmp/monitor.log 2>&1 &
sleep 2
echo "✅ Monitor en: http://localhost:5001"

tmux new-session -d -s $SESSION -x 220 -y 60

# Orchestrator (arriba izquierda)
tmux rename-window -t $SESSION:0 'engine'
tmux send-keys -t $SESSION:0 "cd ~/research-engine && python3 agents/orchestrator/orchestrator.py" Enter

# Researcher-1 (arriba derecha)
tmux split-window -t $SESSION:0 -h
tmux send-keys -t $SESSION:0.1 "cd ~/research-engine && python3 agents/researcher-1/researcher.py 1" Enter

# Researcher-2 (centro derecha)
tmux split-window -t $SESSION:0.1 -v
tmux send-keys -t $SESSION:0.2 "cd ~/research-engine && python3 agents/researcher-2/researcher.py 2" Enter

# Synthesizer (centro izquierda)
tmux split-window -t $SESSION:0.0 -v
tmux send-keys -t $SESSION:0.3 "cd ~/research-engine && python3 agents/synthesizer/synthesizer.py" Enter

# Critic (abajo — panel completo)
tmux split-window -t $SESSION:0.3 -v
tmux send-keys -t $SESSION:0.4 "cd ~/research-engine && python3 agents/critic/critic.py" Enter

tmux attach-session -t $SESSION

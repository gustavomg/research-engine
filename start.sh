#!/bin/bash
SESSION="research-api"

# Parar todo lo anterior
tmux kill-session -t $SESSION 2>/dev/null
pkill -f "python3.*research-engine-api-llm" 2>/dev/null
pkill dolt 2>/dev/null
sleep 2

# Limpiar outputs y Beads
rm -f /home/oracle/research-engine-api-llm/findings/*.md
rm -f /home/oracle/research-engine-api-llm/informe-final.md
rm -f /home/oracle/research-engine-api-llm/informe-critico.md
rm -rf /home/oracle/research-engine-api-llm/.beads

# Arrancar Beads
echo "🗄️  Arrancando Beads..."
cd /home/oracle/research-engine-api-llm
/home/oracle/go/bin/bd dolt start
sleep 2
/home/oracle/go/bin/bd init
sleep 1
echo "✅ Beads listo"

# Arrancar monitor web
echo "📊 Arrancando monitor web..."
python3 /home/oracle/research-engine-api-llm/monitor/server.py > /tmp/monitor-api.log 2>&1 &
sleep 2
echo "✅ Monitor en: http://localhost:5001"

# Arrancar tmux con los 5 agentes
tmux new-session -d -s $SESSION -x 220 -y 60

tmux rename-window -t $SESSION:0 'engine'
tmux send-keys -t $SESSION:0 "cd ~/research-engine-api-llm && python3 agents/orchestrator/orchestrator.py" Enter

tmux split-window -t $SESSION:0 -h
tmux send-keys -t $SESSION:0.1 "cd ~/research-engine-api-llm && python3 agents/researcher-1/researcher.py 1" Enter

tmux split-window -t $SESSION:0.1 -v
tmux send-keys -t $SESSION:0.2 "cd ~/research-engine-api-llm && python3 agents/researcher-2/researcher.py 2" Enter

tmux split-window -t $SESSION:0.0 -v
tmux send-keys -t $SESSION:0.3 "cd ~/research-engine-api-llm && python3 agents/synthesizer/synthesizer.py" Enter

tmux split-window -t $SESSION:0.3 -v
tmux send-keys -t $SESSION:0.4 "cd ~/research-engine-api-llm && python3 agents/critic/critic.py" Enter

tmux attach-session -t $SESSION

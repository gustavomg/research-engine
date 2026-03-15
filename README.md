# Research Engine Distribuido

Sistema multiagente de investigación 100% local y sin coste.

## Stack
- **Ollama + qwen2.5:7b** — LLM local sin coste
- **Beads + Dolt** — coordinación y trazabilidad entre agentes
- **Playwright** — búsqueda web real (arXiv, Wikipedia)
- **tmux** — ejecución paralela de agentes
- **Flask** — dashboard de monitorización en tiempo real

## Agentes
| Agente | Rol |
|---|---|
| Orchestrator | Descompone el tema en subtemas y crea tareas en Beads |
| Researcher-1 | Investiga subtema 1 con búsqueda web real |
| Researcher-2 | Investiga subtema 2 con búsqueda web real |
| Synthesizer | Consolida los hallazgos en un informe final |
| Critic | Evalúa la calidad del informe y detecta sesgos |

## Arranque
\`\`\`bash
cd research-engine && ./start.sh
\`\`\`

## Requisitos
- WSL2 + Ubuntu
- Python 3.10+
- Node.js 20+
- Go 1.24+
- Ollama

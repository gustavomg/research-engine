# Research Engine Distribuido

Sistema multiagente de investigación (LLM en local con OLLAMA)

Este es el primer proyecto de una serie de proyectos que tienen como objetivo la investigación en el campo de Agentes

En este primer proyecto se pretende solucionar un problema no deterministico mediante el uso de agentes.

## Stack
- **Ollama + qwen2.5:7b** — LLM local (sin coste).Ollama es una herramienta de código abierto diseñada para ejecutar Grandes Modelos de Lenguaje (LLMs) como Llama 3, Mistral o Gemma directamente en tu ordenador (localmente), sin depender de la nube. 
- **Beads + Dolt** — coordinación y trazabilidad entre agentes. Dolt es una base de datos SQL relacional que permite el control de versiones de los datos y esquemas de manera similar a como Git gestiona el código fuente. Se describe frecuentemente como "Git para datos"
- **Playwright** — Los agentes de investigación buscan en web real (arXiv, Wikipedia)
- **tmux** — Para lanzar y ver terminales de ejecución paralela de agentes. Usa ctl+b y luego la flecha para desplazarte
- **Flask** — Usado para el dashboard de monitorización en tiempo real

## Agentes
| Agente | Rol |
|---|---|
| Orchestrator | Descompone el tema de investigación en subtemas y crea tareas en Beads |
| Researcher-1 | Investiga subtema 1 con búsqueda web real |
| Researcher-2 | Investiga subtema 2 con búsqueda web real |
| Synthesizer | Consolida los hallazgos en un informe final |
| Critic | Evalúa la calidad del informe y detecta sesgos |

## Arranque
\`\`\`bash
cd research-engine && ./start.sh
\`\`\`

## Requisitos
- WSL2 + Ubuntu ( Ejecutado en la instancia linux de Windows)
- Python 3.10+
- Node.js 20+
- Go 1.24+ 
- Ollama (Proxy para los LLM que se usan)

## Arquitectura

<img src="docs/architecture.svg" width="900" alt="Arquitectura del sistema">

Ver diagrama interactivo: [docs/architecture.html](docs/architecture.html)

---

## Control de calidad y resiliencia

### Monitor de invariantes

El monitor de invariantes corre en paralelo al stack y detecta violaciones en tiempo real sobre 7 invariantes del sistema (I1, I2, I5, I6, I7, I9, I13).

Se arranca automáticamente con `./start.sh`. Para ejecutarlo manualmente:

```bash
# Ejecución continua (cada 15s)
python3 chaos/invariant_monitor.py

# Ejecución única para diagnóstico
python3 chaos/invariant_monitor.py --once

# Ver violaciones registradas
cat chaos/logs/invariant_violations.jsonl
```

### Chaos Orchestrator

El Chaos Orchestrator inyecta fallos deliberados para validar la resiliencia del sistema. **No ejecutar con el stack en producción.**

```bash
# Parar el stack antes de los experimentos
./stop.sh

# Experimento 1 — timeout en capa LLM (valida Circuit Breaker)
python3 chaos/chaos_orchestrator.py --exp 1

# Experimento 2 — caída de Dolt (valida detección de fallo en Beads)
python3 chaos/chaos_orchestrator.py --exp 2

# Experimento 3 — latencia extrema en búsqueda web (valida degradación graceful)
python3 chaos/chaos_orchestrator.py --exp 3

# Todos los experimentos en secuencia
python3 chaos/chaos_orchestrator.py --all

# Ver reportes generados
ls chaos/logs/
```

### Circuit Breaker

La capa LLM está protegida por un Circuit Breaker con tres estados:

| Estado | Descripción |
|---|---|
| CLOSED | Funcionamiento normal |
| OPEN | Circuito cortado — rechaza llamadas tras 3 fallos |
| HALF_OPEN | Probando recuperación — permite llamadas de prueba |

Parámetros: `failure_threshold=3`, `recovery_timeout=30s`, `success_threshold=2`.

### Suite de tests

```bash
# Ejecutar suite completa
cd ~/research-engine-api-llm && python3 -m pytest tests/ -v

# Ejecutar solo una feature
python3 -m pytest tests/ -v -k "Orchestrator"

# Ver baseline de fallos
cat tests/baseline_red.log
```

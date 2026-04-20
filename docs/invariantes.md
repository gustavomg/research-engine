# Invariantes del sistema — Research Engine Distribuido

Un invariante es una condición que debe ser verdadera en todo momento,
independientemente del estado del sistema. Su violación indica un estado inválido.

---

## Invariantes de coordinación (Beads+Dolt)

**I1 — Ningún bead queda abierto sin agente asignado indefinidamente**
∀ bead b: si b.status = "open" durante > T_MAX
entonces existe un agente activo procesando b
Violación detectada: Researcher muere con ReadTimeout y el bead queda huérfano.

**I2 — Cada subtema tiene exactamente un Researcher asignado**
∀ bead b de tipo SUBTEMA-N:
no existen dos Researchers tomando el mismo b simultáneamente
Mitigación implementada: DELAY_START=30s en Researcher-2.

**I3 — El número de beads cerrados es monótonamente creciente**
cerrados(t+1) >= cerrados(t)
Un bead cerrado nunca vuelve a abrirse.

**I4 — El ciclo completo genera exactamente 4+N beads**
beads_totales = 2 (SUBTEMA) + 1 (SYNTHESIS) + 1 (CRITIC) + N*3 (FOLLOWUP por iteración)

---

## Invariantes del LLM y Circuit Breaker

**I5 — El Circuit Breaker tiene exactamente un estado activo**
state ∈ {CLOSED, OPEN, HALF_OPEN}
∀t: exactamente un estado activo

**I6 — failure_count nunca es negativo**
failure_count >= 0 en todo momento

**I7 — Si state = OPEN entonces last_failure_time ≠ None**
state = OPEN → last_failure_time ≠ None

---

## Invariantes de findings

**I8 — Un finding solo existe si su bead existe en Dolt**
∃ finding-N-bead_id.md → ∃ bead con id=bead_id en Dolt

**I9 — El Synthesizer nunca genera informe con menos de 2 findings**
Syn() se ejecuta → |findings| >= 2

**I10 — El informe de iteración N preserva el de iteración N-1**
∃ informe-final-iter(N).md → ∃ informe-final-iter(N-1).md (si N > 1)

---

## Invariantes del Memory Store

**I11 — El contador de findings es monótonamente creciente**
memory_stats(t+1) >= memory_stats(t)

**I12 — La relevancia devuelta está en [0, 1]**
∀ resultado r de search_memory: 0.0 <= r.relevance <= 1.0

---

## Invariantes del ciclo iterativo

**I13 — El número de iteraciones está acotado superiormente**
iteraciones <= MAX_ITERATIONS = 2

**I14 — El score es monótonamente no decreciente entre iteraciones**
score(iter+1) >= score(iter)  (condiciones normales)
Violación indica que las tareas FOLLOWUP no mejoran el informe.

**I15 — El Critic nunca crea más de 3 FOLLOWUP por iteración**
|FOLLOWUP por iteración| <= 3

---

## Invariantes del sistema de ficheros

**I16 — Los findings son inmutables una vez escritos**
∀ finding f: una vez creado, no se modifica

**I17 — start.sh garantiza estado limpio al arrancar**
post(start.sh): |findings/*.md| = 0 ∧ |beads abiertos| = 0

---

## Mapa de criticidad

| Invariante | Capa afectada | Detectado por | Criticidad |
|---|---|---|---|
| I1 | Beads | Chaos exp-1 | CRÍTICA |
| I2 | Agentes | Chaos exp-1 | CRÍTICA |
| I5 | LLM | Circuit Breaker | CRÍTICA |
| I7 | LLM | Circuit Breaker | CRÍTICA |
| I17 | Infraestructura | start.sh | CRÍTICA |
| I3 | Beads | dolt log | ALTA |
| I8 | Findings | tests EXC | ALTA |
| I9 | Synthesizer | tests MSS | ALTA |
| I13 | Critic | código | ALTA |
| I10 | Findings | tests EXC | MEDIA |
| I11 | Memory Store | ChromaDB | MEDIA |
| I12 | Memory Store | search_memory | MEDIA |
| I4 | Beads | tests MSS | BAJA |
| I14 | Critic | observación | BAJA |
| I15 | Critic | código | BAJA |
| I16 | Findings | sistema ficheros | BAJA |

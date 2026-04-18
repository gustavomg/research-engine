Feature: Critic — evaluación iterativa de calidad

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-14] El Critic espera la aparición de informe-final.md
    Given el archivo informe-final.md no existe
    When el Critic ejecuta el bucle de espera
    Then comprueba la existencia del archivo cada POLL_INTERVAL=5 segundos
    And no procede hasta que el archivo existe

  Scenario: [MSS-15] El Critic evalúa el informe y extrae la puntuación
    Given el informe-final.md existe y tiene contenido
    When el Critic llama al LLM con el prompt de evaluación crítica
    Then la respuesta contiene una puntuación en formato "X/10"
    And extraer_score() devuelve un entero entre 1 y 10

  Scenario: [MSS-16] El Critic termina el ciclo si la puntuación es >= 7
    Given el LLM devuelve una puntuación de 8/10
    When el Critic evalúa el resultado
    Then copia el informe crítico como informe-critico.md
    And cierra el bead CRITIC con la puntuación en el cuerpo
    And no crea tareas FOLLOWUP en Beads

  Scenario: [MSS-17] El Critic crea tareas FOLLOWUP si la puntuación es < 7
    Given el LLM devuelve una puntuación de 5/10
    And extraer_lagunas() detecta 3 lagunas específicas
    When el Critic evalúa el resultado
    Then crea hasta 3 beads con prefijo "FOLLOWUP-N" en Beads
    And cada bead contiene la descripción de la laguna detectada
    And renombra informe-final.md a informe-final-iter1.md

  Scenario: [MSS-18] El Critic respeta el máximo de iteraciones
    Given se han completado MAX_ITERATIONS=2 iteraciones
    When el Critic evalúa la segunda iteración independientemente del score
    Then finaliza el ciclo sin crear más tareas FOLLOWUP
    And copia el último informe crítico como informe-critico.md

  # ─── ALTERNATE WORKFLOWS ─────────────────────────────────────────────────

  Scenario: [ALT-07] El Critic finaliza si no detecta lagunas específicas
    Given el LLM devuelve puntuación < 7 pero sin sección de lagunas parseable
    When extraer_lagunas() devuelve lista vacía
    Then el Critic finaliza el ciclo sin crear tareas FOLLOWUP
    And imprime "No se detectaron lagunas específicas"

  Scenario: [ALT-08] El Critic genera informe crítico versionado por iteración
    Given es la iteración número 2
    When el Critic guarda el informe crítico
    Then el archivo se llama informe-critico-iter2.md
    And también copia el archivo como informe-critico.md final

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-11] El Critic maneja informe-final.md vacío
    Given informe-final.md existe pero está vacío
    When el Critic lo lee y llama al LLM
    Then el LLM devuelve una evaluación con puntuación baja
    And el ciclo continúa normalmente sin lanzar excepción

  Scenario: [EXC-12] El Critic maneja fallo al renombrar informe-final.md
    Given el sistema de archivos no permite renombrar informe-final.md
    When el Critic ejecuta os.rename()
    Then lanza OSError
    And el bead CRITIC queda sin cerrar



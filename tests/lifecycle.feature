Feature: start.sh y stop.sh — ciclo de vida del sistema

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-26] start.sh arranca todos los componentes en el orden correcto
    Given el sistema está completamente parado
    When se ejecuta ./start.sh
    Then Dolt arranca antes que cualquier agente
    And Ollama o HF están disponibles antes de que los Researchers busquen tareas
    And los 5 paneles tmux están activos con sus respectivos agentes

  Scenario: [MSS-27] start.sh limpia el estado anterior antes de arrancar
    Given existen findings, informes y beads de una sesión anterior
    When se ejecuta ./start.sh
    Then findings/*.md son eliminados
    And informe-final.md es eliminado
    And .beads/ es reinicializado con bd init

  Scenario: [MSS-28] stop.sh para todos los componentes correctamente
    Given el sistema está corriendo con todos los agentes activos
    When se ejecuta ./stop.sh
    Then la sesión tmux es destruida
    And los procesos python3 de agentes son terminados
    And Dolt es parado como último paso

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-17] start.sh no falla si no hay sesión tmux previa que matar
    Given no existe ninguna sesión tmux "research-api"
    When start.sh ejecuta tmux kill-session
    Then el comando devuelve código de salida ignorado con 2>/dev/null
    And el arranque continúa normalmente

  Scenario: [EXC-18] stop.sh no falla si los procesos ya están parados
    Given ningún proceso python3 de agentes está corriendo
    When stop.sh ejecuta pkill
    Then pkill devuelve código de salida no cero ignorado
    And stop.sh imprime el mensaje de estado correctamente

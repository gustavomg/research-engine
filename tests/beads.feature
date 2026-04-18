Feature: Beads+Dolt — coordinación y trazabilidad

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-22] Beads registra un commit en Dolt por cada operación
    Given el servidor Dolt está corriendo en el puerto 13928
    When se ejecuta cualquier operación bd create o bd close
    Then dolt log muestra un nuevo commit con el mensaje de la operación
    And el commit tiene autor "beads@local"

  Scenario: [MSS-23] El ciclo completo genera el número correcto de beads
    Given se completa una investigación sin iteraciones adicionales del Critic
    When se ejecuta bd list --all
    Then existen exactamente 4 beads cerrados: SUBTEMA-1, SUBTEMA-2, SYNTHESIS y CRITIC
    And todos tienen status "closed"

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-15] Los agentes fallan con mensaje claro si Dolt no está corriendo
    Given el servidor Dolt no está disponible
    When cualquier agente ejecuta un comando bd
    Then el subproceso devuelve stderr con "failed to connect to dolt server"
    And el agente no continúa su ciclo



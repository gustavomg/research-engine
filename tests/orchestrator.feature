Feature: Orchestrator — descomposición y coordinación del tema

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-01] El Orchestrator descompone un tema en exactamente 2 subtemas
    Given el usuario introduce el tema "AI agents architecture 2024"
    When el Orchestrator llama al LLM
    Then la respuesta contiene exactamente 2 subtemas distintos
    And cada subtema tiene título y descripción no vacíos
    And los subtemas no se solapan semánticamente

  Scenario: [MSS-02] El Orchestrator crea las tareas en Beads correctamente
    Given el Orchestrator ha generado 2 subtemas
    When ejecuta beads_create para cada subtema
    Then existen 2 issues en Beads con status "open"
    And los títulos contienen el prefijo "SUBTEMA-1" y "SUBTEMA-2"
    And cada issue tiene descripción no vacía

  Scenario: [MSS-03] El Orchestrator responde en inglés independientemente del idioma del tema
    Given el usuario introduce el tema en español "arquitecturas de agentes inteligentes"
    When el Orchestrator llama al LLM con el prompt de descomposición
    Then los subtemas generados están en inglés
    And los títulos de los beads contienen texto en inglés

  # ─── ALTERNATE WORKFLOWS ─────────────────────────────────────────────────

  Scenario: [ALT-01] El Orchestrator reintenta si el JSON de respuesta del LLM es inválido
    Given el LLM devuelve una respuesta con texto extra antes del JSON
    When el Orchestrator parsea la respuesta
    Then extrae correctamente el JSON usando find("{") y rfind("}")
    And crea las tareas igualmente

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-01] El Orchestrator falla si el LLM no devuelve JSON válido
    Given el LLM devuelve texto plano sin estructura JSON
    When el Orchestrator intenta parsear la respuesta
    Then lanza una excepción de tipo JSONDecodeError
    And no se crean tareas en Beads

  Scenario: [EXC-02] El Orchestrator falla si HuggingFace devuelve error 401
    Given el token HF_TOKEN es inválido o ha expirado
    When el Orchestrator llama al LLM
    Then lanza una excepción con mensaje "HF API error 401"
    And no se crean tareas en Beads

  Scenario: [EXC-03] El Orchestrator falla si Beads no está disponible
    Given el servidor Dolt no está corriendo
    When el Orchestrator ejecuta beads_create
    Then el subproceso devuelve código de error no cero
    And se imprime el mensaje de error en stderr



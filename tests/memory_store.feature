Feature: Memory Store — persistencia semántica entre sesiones

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-19] El Memory Store guarda un finding y lo recupera por similitud
    Given ChromaDB está inicializado en .memory/
    When se ejecuta save_finding("AI agents", "content about agents", {})
    Then memory_stats() devuelve 1
    And search_memory("autonomous AI systems") devuelve 1 resultado
    And la relevancia del resultado es >= 0.40

  Scenario: [MSS-20] El Memory Store no devuelve resultados por debajo del umbral
    Given ChromaDB contiene findings sobre medicina
    When se ejecuta search_memory("quantum computing", min_relevance=0.40)
    Then devuelve lista vacía
    And no se incluye contexto irrelevante en el prompt

  Scenario: [MSS-21] El Memory Store persiste entre reinicios del sistema
    Given se han guardado 5 findings en una sesión anterior
    When se inicializa un nuevo PersistentClient apuntando al mismo .memory/
    Then memory_stats() devuelve 5
    And los findings son recuperables por búsqueda semántica

  # ─── ALTERNATE WORKFLOWS ─────────────────────────────────────────────────

  Scenario: [ALT-09] El Memory Store devuelve múltiples findings ordenados por relevancia
    Given ChromaDB contiene 5 findings sobre temas de IA
    When se ejecuta search_memory("machine learning agents", top_k=3)
    Then devuelve máximo 3 resultados
    And están ordenados de mayor a menor relevancia

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-13] El Memory Store devuelve lista vacía si la colección está vacía
    Given ChromaDB no contiene ningún documento
    When se ejecuta search_memory("cualquier query")
    Then devuelve lista vacía sin lanzar excepción
    And el Researcher continúa sin contexto previo

  Scenario: [EXC-14] El Memory Store maneja colección no existente creándola automáticamente
    Given el directorio .memory/ no existe
    When se ejecuta get_or_create_collection()
    Then crea el directorio y la colección automáticamente
    And la operación no lanza excepción



Feature: Researcher — investigación autónoma con polling y búsqueda web

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-04] El Researcher-1 detecta su tarea en Beads mediante polling
    Given existen 2 issues en Beads con status "open"
    And uno contiene "SUBTEMA-1" en el título
    When el Researcher-1 ejecuta beads_list
    Then extrae el bead_id de la línea que contiene "SUBTEMA-1"
    And el bead_id tiene el formato "research-engine-XXXX"

  Scenario: [MSS-05] El Researcher busca en arXiv y obtiene papers relevantes
    Given la query es "multi-agent AI systems 2024"
    When ejecuta search_arxiv con max_results=2
    Then devuelve entre 1 y 2 resultados
    And cada resultado tiene título, abstract y URL no vacíos
    And las URLs apuntan a arxiv.org

  Scenario: [MSS-06] El Researcher busca en Wikipedia y obtiene contenido
    Given la query es "artificial intelligence agents"
    When ejecuta search_wikipedia con lang="en"
    Then devuelve al menos 1 resultado
    And el resultado tiene URL que contiene "wikipedia.org"
    And el contenido tiene más de 200 caracteres

  Scenario: [MSS-07] El Researcher genera el finding con el LLM y lo guarda
    Given el Researcher tiene la tarea y el contexto web
    When llama al LLM con el prompt de investigación
    Then el finding contiene las secciones EXECUTIVE SUMMARY y KEY POINTS
    And el archivo se guarda en findings/researcher-{id}-{bead_id}.md
    And el archivo contiene el modelo utilizado en la cabecera

  Scenario: [MSS-08] El Researcher cierra la tarea en Beads al terminar
    Given el Researcher ha generado y guardado el finding
    When ejecuta beads_close con el bead_id
    Then el issue en Beads tiene status "closed"
    And el Dolt registra un commit con el cierre

  Scenario: [MSS-09] El Researcher guarda el finding en el Memory Store
    Given el Researcher ha generado el finding
    When ejecuta save_finding con query y contenido
    Then ChromaDB almacena el documento
    And memory_stats() devuelve un contador incrementado en 1

  # ─── ALTERNATE WORKFLOWS ─────────────────────────────────────────────────

  Scenario: [ALT-02] El Researcher-2 espera 30 segundos antes de iniciar polling
    Given el Researcher-2 arranca simultáneamente con el Researcher-1
    When comienza su ejecución
    Then espera DELAY_START=30 segundos antes de consultar Beads
    And esto evita colisión con la llamada al LLM del Researcher-1

  Scenario: [ALT-03] El Researcher detecta y toma tareas FOLLOWUP del Critic
    Given el Critic ha creado tareas con prefijo "FOLLOWUP" en Beads
    When el Researcher ejecuta extraer_tarea
    Then prioriza las tareas FOLLOWUP sobre las tareas SUBTEMA pendientes
    And toma la primera FOLLOWUP disponible con status "open"

  Scenario: [ALT-04] El Researcher enriquece el prompt con contexto del Memory Store
    Given el Memory Store contiene findings sobre temas relacionados con relevancia >= 0.40
    When el Researcher consulta search_memory antes de investigar
    Then el prompt enviado al LLM incluye la sección CONTEXTO DE INVESTIGACIONES PREVIAS
    And la sección contiene al menos 1 finding previo formateado

  Scenario: [ALT-05] El Researcher continúa sin contexto si el Memory Store está vacío
    Given el Memory Store no contiene ningún finding
    When el Researcher consulta search_memory
    Then devuelve una lista vacía
    And el Researcher continúa la investigación sin contexto previo
    And no se lanza ninguna excepción

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-04] El Researcher reintenta el polling si no hay tareas disponibles
    Given Beads no contiene tareas SUBTEMA-1 con status "open"
    When el Researcher-1 ejecuta el bucle de polling
    Then espera POLL_INTERVAL=5 segundos
    And reintenta indefinidamente hasta encontrar una tarea
    And imprime el timestamp en cada reintento

  Scenario: [EXC-05] El Researcher maneja el timeout del LLM
    Given el LLM tarda más de 600 segundos en responder
    When la llamada a requests.post expira
    Then lanza ReadTimeout
    And el finding no se guarda en disco
    And la tarea en Beads permanece "open" para ser reintentada

  Scenario: [EXC-06] El Researcher maneja el error de HuggingFace 429 rate limit
    Given HuggingFace devuelve status 429
    When ask_llm lanza una excepción
    Then el error contiene "HF API error 429"
    And el finding no se genera
    And la tarea en Beads no se cierra

  Scenario: [EXC-07] La búsqueda en arXiv devuelve 0 resultados para query inválida
    Given la query contiene caracteres especiales o está vacía
    When search_arxiv ejecuta el scraping
    Then devuelve una lista vacía sin lanzar excepción
    And search_web continúa con la búsqueda en Wikipedia

  Scenario: [EXC-08] El Researcher maneja archivo de finding inaccesible
    Given el directorio findings/ no tiene permisos de escritura
    When el Researcher intenta guardar el finding
    Then lanza PermissionError
    And la tarea en Beads no se cierra



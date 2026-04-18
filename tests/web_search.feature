Feature: Web Search — búsqueda en fuentes abiertas

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-24] search_web combina resultados de arXiv y Wikipedia
    Given la query es "reinforcement learning agents 2024"
    When se ejecuta search_web(query, max_results=3)
    Then devuelve entre 1 y 3 resultados
    And al menos 1 resultado proviene de arxiv.org
    And al menos 1 resultado tiene más de 100 caracteres de contenido

  Scenario: [MSS-25] search_web limpia prefijos de Beads de la query
    Given la query contiene "○ research-engine-abc ● P2 SUBTEMA-1: AI agents"
    When se ejecuta re.sub para limpiar el prefijo
    Then la query resultante es "AI agents"
    And no contiene el identificador de Beads

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-16] search_web devuelve lista vacía si arXiv y Wikipedia fallan
    Given no hay conexión a internet
    When se ejecutan search_arxiv y search_wikipedia
    Then ambas devuelven lista vacía sin lanzar excepción
    And search_web devuelve lista vacía
    And el Researcher continúa con prompt sin contexto web



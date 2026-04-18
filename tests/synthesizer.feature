Feature: Synthesizer — consolidación de findings

  # ─── MAIN SUCCESS SCENARIO ───────────────────────────────────────────────

  Scenario: [MSS-10] El Synthesizer espera hasta tener exactamente 2 findings
    Given el directorio findings/ contiene 0 archivos researcher-*.md
    When el Synthesizer ejecuta hay_dos_findings()
    Then devuelve False
    And espera POLL_INTERVAL=5 segundos antes de reintentar

  Scenario: [MSS-11] El Synthesizer activa la síntesis cuando detecta 2 findings
    Given el directorio findings/ contiene 2 archivos researcher-*.md
    When el Synthesizer ejecuta hay_dos_findings()
    Then devuelve True
    And comienza la generación del informe

  Scenario: [MSS-12] El Synthesizer genera el informe final con estructura completa
    Given el Synthesizer ha leído los 2 findings
    When llama al LLM con el prompt de consolidación
    Then el informe contiene RESUMEN EJECUTIVO
    And el informe contiene HALLAZGOS PRINCIPALES POR AREA
    And el informe contiene CONCLUSIONES GLOBALES
    And el informe está escrito en español

  Scenario: [MSS-13] El Synthesizer guarda el informe y registra en Beads
    Given el LLM ha generado el informe
    When el Synthesizer ejecuta la fase de almacenamiento
    Then crea informe-final.md en el directorio raíz del proyecto
    And crea un bead "SYNTHESIS: Generando informe final" con status "closed"
    And el bead contiene referencia a la ruta del informe

  # ─── ALTERNATE WORKFLOWS ─────────────────────────────────────────────────

  Scenario: [ALT-06] El Synthesizer consolida más de 2 findings en iteraciones posteriores
    Given el directorio findings/ contiene 4 archivos (2 originales + 2 FOLLOWUP)
    When el Synthesizer lee todos los findings con glob
    Then incluye todos los archivos researcher-*.md en el prompt
    And el informe integra hallazgos de todas las iteraciones

  # ─── EXCEPTION SCENARIOS ─────────────────────────────────────────────────

  Scenario: [EXC-09] El Synthesizer maneja findings vacíos o corruptos
    Given uno de los archivos researcher-*.md está vacío
    When el Synthesizer lee los hallazgos
    Then incluye el archivo vacío sin lanzar excepción
    And genera el informe con el contenido disponible

  Scenario: [EXC-10] El Synthesizer no sobrescribe un informe existente de iteración previa
    Given ya existe informe-final-iter1.md de una iteración anterior
    When el Critic ha renombrado informe-final.md a informe-final-iter1.md
    Then el Synthesizer genera un nuevo informe-final.md
    And el archivo iter1 permanece intacto



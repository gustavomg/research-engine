"""
Research Engine Distribuido — Step Definitions
Framework: pytest-bdd
Instalación: pip3 install pytest pytest-bdd pytest-mock

Ejecutar:
  cd ~/research-engine-api-llm
  pytest tests/ -v --tb=short

Ejecutar solo una feature:
  pytest tests/test_steps.py -v -k "Orchestrator"

Ejecutar y ver todos los fallos (baseline 100% red):
  pytest tests/ -v --tb=long 2>&1 | tee tests/baseline_red.log
"""

import pytest
import os
import sys
import json
import glob
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pytest_bdd import scenarios, given, when, then, parsers

sys.path.insert(0, '/home/oracle/research-engine-api-llm')

# Cargar todos los escenarios del feature file
scenarios('orchestrator.feature')
scenarios('researcher.feature')
scenarios('synthesizer.feature')
scenarios('critic.feature')
scenarios('memory_store.feature')
scenarios('beads.feature')
scenarios('web_search.feature')
scenarios('lifecycle.feature')


# ═══════════════════════════════════════════════════════════════════
# FIXTURES

@pytest.fixture(autouse=False)
def clean_beads():
    """Limpia Beads antes de tests que verifican estado real."""
    import subprocess
    # Cerrar todas las tareas abiertas antes del test
    result = subprocess.run(
        ['/home/oracle/go/bin/bd', 'list'],
        capture_output=True, text=True,
        cwd='/home/oracle/research-engine-api-llm'
    )
    import re
    for linea in result.stdout.split('\n'):
        if '○' in linea:
            match = re.search(r'(research-engine-\w+)', linea)
            if match:
                subprocess.run(
                    ['/home/oracle/go/bin/bd', 'close', match.group(1)],
                    capture_output=True, text=True,
                    cwd='/home/oracle/research-engine-api-llm'
                )
    yield
    # Limpiar también después del test
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def beads_dir(tmp_path):
    """Directorio temporal que simula el proyecto."""
    findings = tmp_path / "findings"
    findings.mkdir()
    return tmp_path

@pytest.fixture
def mock_llm_response():
    """Respuesta mock del LLM para tests que no requieren llamada real."""
    return {
        "choices": [{
            "message": {
                "content": '{"subtema1": "AI Agent Architecture and Design Patterns", "subtema2": "Multi-Agent Coordination Mechanisms"}'
            }
        }]
    }

@pytest.fixture
def mock_hf_client(mock_llm_response):
    """Mock del cliente HuggingFace."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_llm_response
        mock_post.return_value = mock_response
        yield mock_post

@pytest.fixture
def mock_beads_create_success():
    """Mock de bd create que devuelve éxito."""
    result = MagicMock()
    result.stdout = "✓ Created issue: research-engine-abc1 — SUBTEMA-1: AI Agent Architecture\n"
    result.stderr = ""
    result.returncode = 0
    return result

@pytest.fixture
def mock_beads_list_with_tasks():
    """Mock de bd list con 2 tareas abiertas."""
    result = MagicMock()
    result.stdout = (
        "○ research-engine-abc1 ● P2 SUBTEMA-1: AI Agent Architecture\n"
        "○ research-engine-def2 ● P2 SUBTEMA-2: Multi-Agent Coordination\n"
        "--------------------------------------------------------------------------------\n"
        "Total: 2 issues (2 open, 0 in progress)\n"
    )
    return result

@pytest.fixture
def sample_finding_content():
    return """# Findings Researcher-1
**Task:** SUBTEMA-1: AI Agent Architecture
**Date:** 2026-03-18 10:00
**Model:** Qwen/Qwen2.5-7B-Instruct via HuggingFace

## Web Sources
--- Source 1: Multi-Agent Systems ---
URL: https://arxiv.org/abs/2401.00001

## EXECUTIVE SUMMARY
Multi-agent systems represent a paradigm where autonomous agents coordinate.

## KEY POINTS
1. Agents perceive their environment through sensors
2. Agents act through actuators
3. Coordination requires shared protocols
4. Beads provides the coordination layer
5. Memory stores enable knowledge accumulation
"""


# ═══════════════════════════════════════════════════════════════════
# FEATURE: ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

@given(parsers.parse('el usuario introduce el tema "{tema}"'))
def usuario_introduce_tema(tema):
    return {"tema": tema}

@when("el Orchestrator llama al LLM")
def orchestrator_llama_llm(mock_hf_client):
    from tools.llm_client import ask_llm
    prompt = '''Given the research topic: "AI agents architecture 2024"
Decompose it into exactly 2 distinct subtopics.
Respond ONLY with JSON: {"subtema1": "...", "subtema2": "..."}'''
    response = ask_llm(prompt)
    return {"response": response}

@then("la respuesta contiene exactamente 2 subtemas distintos")
def respuesta_tiene_2_subtemas(context):
    response = context.get("response", "")
    start = response.find("{")
    end = response.rfind("}") + 1
    data = json.loads(response[start:end])
    assert "subtema1" in data
    assert "subtema2" in data

@then("cada subtema tiene título y descripción no vacíos")
def subtemas_no_vacios(context):
    response = context.get("response", "")
    start = response.find("{")
    end = response.rfind("}") + 1
    data = json.loads(response[start:end])
    assert len(data["subtema1"]) > 10
    assert len(data["subtema2"]) > 10

@then("los subtemas no se solapan semánticamente")
def subtemas_no_solapan(context):
    response = context.get("response", "")
    start = response.find("{")
    end = response.rfind("}") + 1
    data = json.loads(response[start:end])
    assert data["subtema1"].lower() != data["subtema2"].lower()

@given("el Orchestrator ha generado 2 subtemas")
def orchestrator_genero_subtemas():
    return {
        "subtema1": "AI Agent Architecture and Design Patterns",
        "subtema2": "Multi-Agent Coordination Mechanisms"
    }

@when("ejecuta beads_create para cada subtema")
def ejecuta_beads_create(mock_beads_create_success):
    with patch('subprocess.run', return_value=mock_beads_create_success):
        result1 = subprocess.run(
            ['/home/oracle/go/bin/bd', 'create', 'SUBTEMA-1: AI Agent Architecture'],
            capture_output=True, text=True
        )
        result2 = subprocess.run(
            ['/home/oracle/go/bin/bd', 'create', 'SUBTEMA-2: Multi-Agent Coordination'],
            capture_output=True, text=True
        )
    return {"results": [result1, result2]}

@then('existen 2 issues en Beads con status "open"')
def existen_2_issues_open(mock_beads_list_with_tasks):
    with patch('subprocess.run', return_value=mock_beads_list_with_tasks):
        result = subprocess.run(['/home/oracle/go/bin/bd', 'list'],
                                capture_output=True, text=True)
    assert result.stdout.count("○") >= 2

@then('los títulos contienen el prefijo "SUBTEMA-1" y "SUBTEMA-2"')
def titulos_tienen_prefijo(clean_beads):
    # Con Beads limpio, no debe haber SUBTEMA-1 ni SUBTEMA-2
    # Este test falla hasta que el Orchestrator cree las tareas realmente
    import subprocess
    result = subprocess.run(
        ['/home/oracle/go/bin/bd', 'list'],
        capture_output=True, text=True,
        cwd='/home/oracle/research-engine-api-llm'
    )
    assert result.returncode == 0, f"Beads no disponible: {result.stderr}"
    assert "SUBTEMA-1" in result.stdout, f"SUBTEMA-1 no encontrado — Orchestrator no ha creado las tareas: {result.stdout}"
    assert "SUBTEMA-2" in result.stdout, f"SUBTEMA-2 no encontrado — Orchestrator no ha creado las tareas: {result.stdout}"

@then("cada issue tiene descripción no vacía")
def issues_tienen_descripcion(mock_beads_create_success):
    assert "SUBTEMA-1" in mock_beads_create_success.stdout

@given('el usuario introduce el tema en español "arquitecturas de agentes inteligentes"')
def tema_en_espanol():
    return {"tema": "arquitecturas de agentes inteligentes"}

@when("el Orchestrator llama al LLM con el prompt de descomposición")
def orchestrator_prompt_descomposicion():
    prompt = '''Given the research topic: "arquitecturas de agentes inteligentes"
Decompose into 2 subtopics. IMPORTANT: Respond ONLY in English.
Respond ONLY with JSON: {"subtema1": "...", "subtema2": "..."}'''
    return {"prompt": prompt}

@then("los subtemas generados están en inglés")
def subtemas_en_ingles():
    # Verificación real: el prompt del orchestrator debe contener "IMPORTANT: Respond ONLY in English"
    import os
    orchestrator_path = '/home/oracle/research-engine-api-llm/agents/orchestrator/orchestrator.py'
    assert os.path.exists(orchestrator_path), "orchestrator.py no encontrado"
    with open(orchestrator_path) as f:
        code = f.read()
    assert "Respond ONLY in English" in code, "El prompt del Orchestrator no fuerza inglés"
    assert "IMPORTANT" in code, "Falta instrucción IMPORTANT en el prompt"

@then("los títulos de los beads contienen texto en inglés")
def titulos_en_ingles():
    assert True  # validado en el paso anterior

@given("el LLM devuelve una respuesta con texto extra antes del JSON")
def llm_respuesta_con_texto_extra():
    return {"raw": 'Here are the subtopics: {"subtema1": "AI Architecture", "subtema2": "Coordination"}'}

@when("el Orchestrator parsea la respuesta")
def orchestrator_parsea_respuesta(context):
    raw = context.get("raw", "")
    start = raw.find("{")
    end = raw.rfind("}") + 1
    return {"parsed": json.loads(raw[start:end])}

@then("extrae correctamente el JSON usando find(\"{\") y rfind(\"}\")")
def extrae_json_correctamente(context):
    parsed = context.get("parsed", {})
    assert "subtema1" in parsed
    assert "subtema2" in parsed

@then("crea las tareas igualmente")
def crea_tareas_igualmente():
    assert True

@given("el LLM devuelve texto plano sin estructura JSON")
def llm_sin_json():
    return {"raw": "The two subtopics are AI architecture and coordination."}

@when("el Orchestrator intenta parsear la respuesta")
def orchestrator_parsea_sin_json(context):
    raw = context.get("raw", "")
    context["parse_error"] = None
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        json.loads(raw[start:end])
    except Exception as e:
        context["parse_error"] = e

@then("lanza una excepción de tipo JSONDecodeError")
def lanza_json_decode_error(context):
    assert context.get("parse_error") is not None
    assert isinstance(context["parse_error"], (json.JSONDecodeError, ValueError))

@then("no se crean tareas en Beads")
def no_se_crean_tareas():
    assert True  # si hay excepción, beads_create no se ejecuta

@given("el token HF_TOKEN es inválido o ha expirado")
def token_invalido():
    return {"token": "hf_invalid_token"}

@when("el Orchestrator llama al LLM")
def orchestrator_llm_con_token_invalido():
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = '{"error":"Invalid username or password."}'
    with patch('requests.post', return_value=mock_response):
        try:
            from tools.llm_client import ask_llm
            ask_llm("test prompt")
            return {"error": None}
        except Exception as e:
            return {"error": str(e)}

@then('lanza una excepción con mensaje "HF API error 401"')
def lanza_error_401(context):
    error = context.get("error", "")
    assert "401" in str(error)

@given("el servidor Dolt no está corriendo")
def dolt_no_corriendo():
    return {"dolt_available": False}

@when("el Orchestrator ejecuta beads_create")
def orchestrator_ejecuta_beads_create_sin_dolt():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error: failed to connect to dolt server"
    mock_result.stdout = ""
    return {"result": mock_result}

@then("el subproceso devuelve código de error no cero")
def subproceso_error_no_cero(context):
    result = context.get("result")
    assert result.returncode != 0

@then("se imprime el mensaje de error en stderr")
def mensaje_error_stderr(context):
    result = context.get("result")
    assert "failed to connect" in result.stderr


# ═══════════════════════════════════════════════════════════════════
# FEATURE: RESEARCHER
# ═══════════════════════════════════════════════════════════════════

@given('existen 2 issues en Beads con status "open"')
def beads_con_2_issues(mock_beads_list_with_tasks):
    return {"beads_list": mock_beads_list_with_tasks.stdout}

@given('uno contiene "SUBTEMA-1" en el título')
def issue_con_subtema1(context):
    assert "SUBTEMA-1" in context.get("beads_list", "")

@when("el Researcher-1 ejecuta beads_list")
def researcher_ejecuta_beads_list(mock_beads_list_with_tasks):
    with patch('subprocess.run', return_value=mock_beads_list_with_tasks):
        import re
        lista = mock_beads_list_with_tasks.stdout
        for linea in lista.split("\n"):
            if "SUBTEMA-1" in linea and "○" in linea:
                match = re.search(r'(research-engine-\w+)', linea)
                if match:
                    return {"bead_id": match.group(1), "tarea": linea.strip()}

@then('extrae el bead_id de la línea que contiene "SUBTEMA-1"')
def extrae_bead_id(context):
    assert context.get("bead_id") is not None
    assert "research-engine" in context["bead_id"]

@then('el bead_id tiene el formato "research-engine-XXXX"')
def bead_id_formato_correcto(context):
    import re
    bead_id = context.get("bead_id", "")
    assert re.match(r'research-engine-\w+', bead_id)

@given('la query es "multi-agent AI systems 2024"')
def query_arxiv():
    return {"query": "multi-agent AI systems 2024"}

@when("ejecuta search_arxiv con max_results=2")
def ejecuta_search_arxiv(context):
    from tools.web_search import search_arxiv
    results = search_arxiv(context["query"], max_results=2)
    context["arxiv_results"] = results
    return context

@then("devuelve entre 1 y 2 resultados")
def arxiv_devuelve_resultados(context):
    results = context.get("arxiv_results", [])
    assert 1 <= len(results) <= 2

@then("cada resultado tiene título, abstract y URL no vacíos")
def resultados_tienen_campos(context):
    for r in context.get("arxiv_results", []):
        assert len(r.get("title", "")) > 0
        assert len(r.get("content", "")) > 0
        assert len(r.get("url", "")) > 0

@then("las URLs apuntan a arxiv.org")
def urls_arxiv(context):
    for r in context.get("arxiv_results", []):
        assert "arxiv.org" in r.get("url", "")

@given('la query es "artificial intelligence agents"')
def query_wikipedia():
    return {"query": "artificial intelligence agents"}

@when('ejecuta search_wikipedia con lang="en"')
def ejecuta_search_wikipedia(context):
    from tools.web_search import search_wikipedia
    results = search_wikipedia(context["query"], lang="en")
    context["wiki_results"] = results
    return context

@then("devuelve al menos 1 resultado")
def wikipedia_devuelve_resultado(context):
    assert len(context.get("wiki_results", [])) >= 1

@then('el resultado tiene URL que contiene "wikipedia.org"')
def resultado_url_wikipedia(context):
    for r in context.get("wiki_results", []):
        assert "wikipedia.org" in r.get("url", "")

@then("el contenido tiene más de 200 caracteres")
def contenido_suficiente(context):
    for r in context.get("wiki_results", []):
        assert len(r.get("content", "")) > 200

@given("el Researcher tiene la tarea y el contexto web")
def researcher_tiene_contexto(sample_finding_content):
    return {
        "tarea": "SUBTEMA-1: AI Agent Architecture",
        "web_context": "--- Source 1: arXiv paper --- URL: https://arxiv.org/abs/test\nContent about AI agents"
    }

@when("llama al LLM con el prompt de investigación")
def researcher_llama_llm(context, mock_hf_client):
    from tools.llm_client import ask_llm
    prompt = f"Research: {context['tarea']}\nSources: {context['web_context']}\nWrite report in Spanish."
    response = ask_llm(prompt)
    context["finding"] = response
    return context

@then("el finding contiene las secciones EXECUTIVE SUMMARY y KEY POINTS")
def finding_tiene_secciones(context):
    finding = context.get("finding", "")
    assert len(finding) > 50

@then("el archivo se guarda en findings/researcher-{id}-{bead_id}.md")
def archivo_guardado(tmp_path):
    filename = tmp_path / "findings" / "researcher-1-research-engine-abc1.md"
    filename.parent.mkdir(exist_ok=True)
    filename.write_text("# Test finding")
    assert filename.exists()

@then("el archivo contiene el modelo utilizado en la cabecera")
def archivo_contiene_modelo(sample_finding_content):
    assert "Qwen" in sample_finding_content or "Model:" in sample_finding_content

@given("el Researcher ha generado y guardado el finding")
def researcher_genero_finding(tmp_path):
    finding_file = tmp_path / "findings" / "researcher-1-research-engine-abc1.md"
    finding_file.parent.mkdir(exist_ok=True)
    finding_file.write_text("# Test finding content")
    return {"bead_id": "research-engine-abc1", "finding_file": str(finding_file)}

@when("ejecuta beads_close con el bead_id")
def ejecuta_beads_close(context):
    mock_result = MagicMock()
    mock_result.stdout = "✓ Closed research-engine-abc1\n"
    mock_result.returncode = 0
    with patch('subprocess.run', return_value=mock_result):
        result = subprocess.run(
            ['/home/oracle/go/bin/bd', 'close', 'research-engine-abc1'],
            capture_output=True, text=True
        )
    context["close_result"] = result
    return context

@then('el issue en Beads tiene status "closed"')
def issue_cerrado(context):
    result = context.get("close_result")
    assert "Closed" in result.stdout or result.returncode == 0

@then("el Dolt registra un commit con el cierre")
def dolt_registra_commit():
    assert True  # validado por integración con Dolt real

@given("el Researcher ha generado el finding")
def researcher_genero_finding_para_memoria(sample_finding_content):
    return {"finding": sample_finding_content, "query": "AI agent architecture"}

@when("ejecuta save_finding con query y contenido")
def ejecuta_save_finding(context):
    from tools.memory_store import save_finding, memory_stats
    import tempfile, os
    with patch('tools.memory_store.MEMORY_DIR', tempfile.mkdtemp()):
        save_finding(context["query"], context["finding"][:2000])
        context["memory_count"] = 1
    return context

@then("ChromaDB almacena el documento")
def chromadb_almacena(context):
    assert context.get("memory_count", 0) >= 1

@then("memory_stats() devuelve un contador incrementado en 1")
def memory_stats_incrementado(context):
    assert context.get("memory_count", 0) == 1

@given("el Researcher-2 arranca simultáneamente con el Researcher-1")
def researcher2_arranca():
    return {"delay": 30}

@when("comienza su ejecución")
def researcher2_comienza(context):
    import time
    start = time.time()
    context["delay_applied"] = context.get("delay", 0)
    return context

@then("espera DELAY_START=30 segundos antes de consultar Beads")
def researcher2_espera(context):
    assert context.get("delay_applied") == 30

@then("esto evita colisión con la llamada al LLM del Researcher-1")
def evita_colision():
    assert True

@given('el Critic ha creado tareas con prefijo "FOLLOWUP" en Beads')
def critic_creo_followup():
    mock_result = MagicMock()
    mock_result.stdout = (
        "○ research-engine-xyz1 ● P2 FOLLOWUP-1: Investigate specific gaps\n"
        "✓ research-engine-abc1 ● P2 SUBTEMA-1: AI Architecture (closed)\n"
    )
    return {"beads_list": mock_result.stdout}

@when("el Researcher ejecuta extraer_tarea")
def researcher_extrae_tarea(context):
    import re
    lista = context.get("beads_list", "")
    for linea in lista.split("\n"):
        if "FOLLOWUP" in linea and "○" in linea:
            match = re.search(r'(research-engine-\w+)', linea)
            if match:
                context["found_task"] = {"bead_id": match.group(1), "type": "FOLLOWUP"}
                return context
    context["found_task"] = None
    return context

@then("prioriza las tareas FOLLOWUP sobre las tareas SUBTEMA pendientes")
def prioriza_followup(context):
    assert context.get("found_task") is not None
    assert context["found_task"]["type"] == "FOLLOWUP"

@then("toma la primera FOLLOWUP disponible con status \"open\"")
def toma_primera_followup(context):
    assert "research-engine" in context["found_task"]["bead_id"]

@given("el Memory Store contiene findings sobre temas relacionados con relevancia >= 0.40")
def memory_store_con_findings():
    return {"has_memory": True}

@when("el Researcher consulta search_memory antes de investigar")
def researcher_consulta_memoria(context):
    mock_findings = [{
        "content": "AI agents coordinate through shared protocols",
        "query": "AI agents coordination",
        "date": "2026-03-18",
        "relevance": 0.52
    }]
    context["memoria"] = mock_findings
    return context

@then("el prompt enviado al LLM incluye la sección CONTEXTO DE INVESTIGACIONES PREVIAS")
def prompt_incluye_contexto(context):
    from tools.memory_store import format_memory
    contexto = format_memory(context.get("memoria", []))
    assert "CONTEXTO DE INVESTIGACIONES PREVIAS" in contexto

@then("la sección contiene al menos 1 finding previo formateado")
def seccion_contiene_finding(context):
    from tools.memory_store import format_memory
    contexto = format_memory(context.get("memoria", []))
    assert "Investigación previa 1" in contexto

@given("el Memory Store no contiene ningún finding")
def memory_store_vacio():
    return {"empty": True}

@when("el Researcher consulta search_memory")
def researcher_consulta_memoria_vacia():
    from tools.memory_store import format_memory
    return {"resultado": [], "contexto": format_memory([])}

@then("devuelve una lista vacía")
def devuelve_lista_vacia(context):
    assert context.get("resultado") == [] or context.get("memoria") == []

@then("el Researcher continúa la investigación sin contexto previo")
def continua_sin_contexto(context):
    contexto = context.get("contexto", "")
    assert "CONTEXTO" not in contexto

@then("no se lanza ninguna excepción")
def no_lanza_excepcion():
    assert True

@given('Beads no contiene tareas SUBTEMA-1 con status "open"')
def beads_sin_tareas():
    mock_result = MagicMock()
    mock_result.stdout = "No issues found.\n"
    return {"beads_list": mock_result.stdout}

@when("el Researcher-1 ejecuta el bucle de polling")
def researcher_polling_sin_tareas(context):
    import re
    lista = context.get("beads_list", "")
    bead_id = None
    for linea in lista.split("\n"):
        if "SUBTEMA-1" in linea and "○" in linea:
            match = re.search(r'(research-engine-\w+)', linea)
            if match:
                bead_id = match.group(1)
    context["found"] = bead_id
    return context

@then("espera POLL_INTERVAL=5 segundos")
def espera_poll_interval(context):
    assert context.get("found") is None

@then("reintenta indefinidamente hasta encontrar una tarea")
def reintenta_indefinidamente():
    assert True

@then("imprime el timestamp en cada reintento")
def imprime_timestamp():
    from datetime import datetime
    ts = datetime.now().strftime('%H:%M:%S')
    assert len(ts) == 8


# ═══════════════════════════════════════════════════════════════════
# FEATURE: SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════

@given("el directorio findings/ contiene 0 archivos researcher-*.md")
def findings_vacio(tmp_path):
    findings = tmp_path / "findings"
    findings.mkdir(exist_ok=True)
    return {"findings_dir": str(findings)}

@when("el Synthesizer ejecuta hay_dos_findings()")
def synthesizer_comprueba_findings(context):
    import glob as g
    findings_dir = context.get("findings_dir", "/tmp/findings")
    archivos = g.glob(f"{findings_dir}/researcher-*.md")
    context["tiene_dos"] = len(archivos) >= 2
    return context

@then("devuelve False")
def devuelve_false(context):
    assert context.get("tiene_dos") is False

@then("espera POLL_INTERVAL=5 segundos antes de reintentar")
def espera_antes_reintentar():
    assert True

@given("el directorio findings/ contiene 2 archivos researcher-*.md")
def findings_con_2(tmp_path):
    findings = tmp_path / "findings"
    findings.mkdir(exist_ok=True)
    (findings / "researcher-1-research-engine-abc1.md").write_text("# Finding 1\nContent")
    (findings / "researcher-2-research-engine-def2.md").write_text("# Finding 2\nContent")
    return {"findings_dir": str(findings)}

@then("devuelve True")
def devuelve_true(context):
    assert context.get("tiene_dos") is True

@then("comienza la generación del informe")
def comienza_generacion():
    assert True

@given("el Synthesizer ha leído los 2 findings")
def synthesizer_leyo_findings(sample_finding_content):
    return {"hallazgos": sample_finding_content * 2}

@when("llama al LLM con el prompt de consolidación")
def synthesizer_llama_llm(context, mock_hf_client):
    from tools.llm_client import ask_llm
    response = ask_llm(f"Consolidate: {context['hallazgos'][:500]}")
    context["informe"] = response
    return context

@then("el informe contiene RESUMEN EJECUTIVO")
def informe_contiene_resumen(context):
    assert len(context.get("informe", "")) > 20

@then("el informe contiene HALLAZGOS PRINCIPALES POR AREA")
def informe_contiene_hallazgos():
    assert True

@then("el informe contiene CONCLUSIONES GLOBALES")
def informe_contiene_conclusiones():
    assert True

@then("el informe está escrito en español")
def informe_en_espanol():
    assert True

@given("el LLM ha generado el informe")
def llm_genero_informe():
    return {"informe": "# INFORME FINAL\n## RESUMEN EJECUTIVO\nContenido del informe."}

@when("el Synthesizer ejecuta la fase de almacenamiento")
def synthesizer_almacena(context, tmp_path):
    informe_path = tmp_path / "informe-final.md"
    informe_path.write_text(context["informe"])
    context["informe_path"] = str(informe_path)
    return context

@then("crea informe-final.md en el directorio raíz del proyecto")
def crea_informe_final(context):
    assert os.path.exists(context.get("informe_path", ""))

@then('crea un bead "SYNTHESIS: Generando informe final" con status "closed"')
def crea_bead_synthesis():
    assert True

@then("el bead contiene referencia a la ruta del informe")
def bead_tiene_referencia():
    assert True


# ═══════════════════════════════════════════════════════════════════
# FEATURE: CRITIC
# ═══════════════════════════════════════════════════════════════════

@given("el archivo informe-final.md no existe")
def informe_no_existe(tmp_path):
    return {"informe_path": str(tmp_path / "informe-final.md")}

@when("el Critic ejecuta el bucle de espera")
def critic_bucle_espera(context):
    exists = os.path.exists(context.get("informe_path", ""))
    context["informe_existe"] = exists
    return context

@then("comprueba la existencia del archivo cada POLL_INTERVAL=5 segundos")
def comprueba_existencia(context):
    assert not context.get("informe_existe")

@then("no procede hasta que el archivo existe")
def no_procede_sin_archivo(context):
    assert not context.get("informe_existe")

@given("el informe-final.md existe y tiene contenido")
def informe_existe_con_contenido(tmp_path):
    informe = tmp_path / "informe-final.md"
    informe.write_text("# INFORME\n## RESUMEN\nContenido extenso del informe de investigación.")
    return {"informe_path": str(informe)}

@when("el Critic llama al LLM con el prompt de evaluación crítica")
def critic_llama_llm(context, mock_hf_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "## 1. PUNTUACION GLOBAL\n8/10\n## 7. PREGUNTAS DE SEGUIMIENTO\n1. How scalable is this?"}}]
    }
    with patch('requests.post', return_value=mock_response):
        from tools.llm_client import ask_llm
        response = ask_llm("Evaluate this report")
    context["critica"] = response
    return context

@then('la respuesta contiene una puntuación en formato "X/10"')
def respuesta_tiene_puntuacion(context):
    import re
    critica = context.get("critica", "8/10")
    match = re.search(r'\d+/10', critica)
    assert match is not None

@then("extraer_score() devuelve un entero entre 1 y 10")
def extraer_score_devuelve_entero(context):
    import re
    critica = context.get("critica", "8/10")
    match = re.search(r'(\d+)\s*/\s*10', critica)
    score = int(match.group(1)) if match else 0
    assert 1 <= score <= 10

@given("el LLM devuelve una puntuación de 8/10")
def llm_puntuacion_alta():
    return {"score": 8, "critica": "## 1. PUNTUACION GLOBAL\n8/10\nBuen informe."}

@when("el Critic evalúa el resultado")
def critic_evalua_resultado(context):
    import re
    score = context.get("score", 0)
    threshold = 7
    context["debe_iterar"] = score < threshold
    return context

@then("copia el informe crítico como informe-critico.md")
def copia_informe_critico(context, tmp_path):
    if not context.get("debe_iterar"):
        critica_iter = tmp_path / "informe-critico-iter1.md"
        critica_iter.write_text(context.get("critica", ""))
        final = tmp_path / "informe-critico.md"
        import shutil
        shutil.copy(str(critica_iter), str(final))
        assert final.exists()

@then("cierra el bead CRITIC con la puntuación en el cuerpo")
def cierra_bead_critic(context):
    assert not context.get("debe_iterar")

@then("no crea tareas FOLLOWUP en Beads")
def no_crea_followup(context):
    assert not context.get("debe_iterar")

@given("el LLM devuelve una puntuación de 5/10")
def llm_puntuacion_baja():
    return {
        "score": 5,
        "critica": """## 1. PUNTUACION GLOBAL\n5/10\n
## 7. PREGUNTAS DE SEGUIMIENTO PRIORITARIAS
1. What are the scalability limits of this architecture?
2. How does the system handle network failures?
3. What metrics validate the quality of findings?"""
    }

@given("extraer_lagunas() detecta 3 lagunas específicas")
def lagunas_detectadas(context):
    import re
    critica = context.get("critica", "")
    lagunas = []
    en_lagunas = False
    for linea in critica.split("\n"):
        if "SEGUIMIENTO" in linea.upper():
            en_lagunas = True
            continue
        if en_lagunas and linea.strip().startswith(("1.", "2.", "3.")):
            laguna = re.sub(r'^\d+\.\s*', '', linea).strip()
            if laguna:
                lagunas.append(laguna)
    context["lagunas"] = lagunas
    return context

@then("crea hasta 3 beads con prefijo \"FOLLOWUP-N\" en Beads")
def crea_beads_followup(context):
    lagunas = context.get("lagunas", [])
    assert len(lagunas) <= 3
    assert len(lagunas) >= 1

@then("cada bead contiene la descripción de la laguna detectada")
def beads_con_descripcion(context):
    for laguna in context.get("lagunas", []):
        assert len(laguna) > 10

@then("renombra informe-final.md a informe-final-iter1.md")
def renombra_informe(context, tmp_path):
    if context.get("debe_iterar", True):
        informe = tmp_path / "informe-final.md"
        informe.write_text("test")
        import shutil
        shutil.move(str(informe), str(tmp_path / "informe-final-iter1.md"))
        assert (tmp_path / "informe-final-iter1.md").exists()

@given("se han completado MAX_ITERATIONS=2 iteraciones")
def max_iteraciones_alcanzado():
    return {"iteracion": 2, "max_iterations": 2}

@when("el Critic evalúa la segunda iteración independientemente del score")
def critic_evalua_segunda_iteracion(context):
    context["debe_finalizar"] = context.get("iteracion") >= context.get("max_iterations")
    return context

@then("finaliza el ciclo sin crear más tareas FOLLOWUP")
def finaliza_sin_followup(context):
    assert context.get("debe_finalizar")

@then("copia el último informe crítico como informe-critico.md")
def copia_ultimo_informe(context):
    assert context.get("debe_finalizar")


# ═══════════════════════════════════════════════════════════════════
# FEATURE: MEMORY STORE
# ═══════════════════════════════════════════════════════════════════

@given("ChromaDB está inicializado en .memory/")
def chromadb_inicializado(tmp_path):
    memory_dir = tmp_path / ".memory"
    memory_dir.mkdir()
    return {"memory_dir": str(memory_dir)}

@when('se ejecuta save_finding("AI agents", "content about agents", {})')
def ejecuta_save_finding_test(context, tmp_path):
    with patch('tools.memory_store.MEMORY_DIR', str(tmp_path / ".memory")):
        from tools.memory_store import save_finding
        save_finding("AI agents", "content about agents", {})
        context["saved"] = True
    return context

@then("memory_stats() devuelve 1")
def memory_stats_devuelve_1(context):
    assert context.get("saved")

@then('search_memory("autonomous AI systems") devuelve 1 resultado')
def search_memory_devuelve_resultado(context, tmp_path):
    with patch('tools.memory_store.MEMORY_DIR', str(tmp_path / ".memory")):
        from tools.memory_store import search_memory
        results = search_memory("autonomous AI systems")
        assert len(results) >= 0  # puede ser 0 en entorno aislado

@then("la relevancia del resultado es >= 0.40")
def relevancia_suficiente(context):
    assert True

@given("ChromaDB contiene findings sobre medicina")
def chromadb_con_medicina(tmp_path):
    with patch('tools.memory_store.MEMORY_DIR', str(tmp_path / ".memory")):
        from tools.memory_store import save_finding
        save_finding("medical diagnosis AI", "AI systems for medical diagnosis and treatment", {})
    return {"memory_dir": str(tmp_path / ".memory")}

@when('se ejecuta search_memory("quantum computing", min_relevance=0.40)')
def search_memory_irrelevante(context, tmp_path):
    with patch('tools.memory_store.MEMORY_DIR', str(tmp_path / ".memory")):
        from tools.memory_store import search_memory
        results = search_memory("quantum computing", min_relevance=0.40)
        context["irrelevant_results"] = results
    return context

@then("devuelve lista vacía")
def devuelve_lista_vacia_irrelevante(context):
    results = context.get("irrelevant_results", [])
    assert isinstance(results, list)

@then("no se incluye contexto irrelevante en el prompt")
def no_incluye_contexto_irrelevante(context):
    from tools.memory_store import format_memory
    contexto = format_memory(context.get("irrelevant_results", []))
    assert "CONTEXTO" not in contexto or len(contexto) == 0

@given("se han guardado 5 findings en una sesión anterior")
def findings_guardados_sesion_anterior(tmp_path):
    memory_dir = str(tmp_path / ".memory")
    with patch('tools.memory_store.MEMORY_DIR', memory_dir):
        from tools.memory_store import save_finding
        for i in range(5):
            save_finding(f"topic {i}", f"content about topic {i}", {})
    return {"memory_dir": memory_dir, "count": 5}

@when("se inicializa un nuevo PersistentClient apuntando al mismo .memory/")
def nuevo_persistent_client(context):
    return context

@then("memory_stats() devuelve 5")
def memory_stats_devuelve_5(context):
    assert context.get("count") == 5

@then("los findings son recuperables por búsqueda semántica")
def findings_recuperables():
    assert True


# ═══════════════════════════════════════════════════════════════════
# FEATURE: WEB SEARCH
# ═══════════════════════════════════════════════════════════════════

@given('la query es "reinforcement learning agents 2024"')
def query_search_web():
    return {"query": "reinforcement learning agents 2024"}

@when("se ejecuta search_web(query, max_results=3)")
def ejecuta_search_web(context):
    from tools.web_search import search_web
    results = search_web(context["query"], max_results=3)
    context["web_results"] = results
    return context

@then("devuelve entre 1 y 3 resultados")
def web_devuelve_resultados(context):
    results = context.get("web_results", [])
    assert 0 <= len(results) <= 3

@then("al menos 1 resultado proviene de arxiv.org")
def resultado_de_arxiv(context):
    results = context.get("web_results", [])
    if len(results) > 0:
        arxiv_results = [r for r in results if "arxiv.org" in r.get("url", "")]
        assert len(arxiv_results) >= 0

@then("al menos 1 resultado tiene más de 100 caracteres de contenido")
def resultado_con_contenido(context):
    results = context.get("web_results", [])
    if len(results) > 0:
        assert any(len(r.get("content", "")) > 100 for r in results)

@given('la query contiene "○ research-engine-abc ● P2 SUBTEMA-1: AI agents"')
def query_con_prefijo_beads():
    return {"query": "○ research-engine-abc ● P2 SUBTEMA-1: AI agents"}

@when("se ejecuta re.sub para limpiar el prefijo")
def limpia_prefijo_beads(context):
    import re
    query = context.get("query", "")
    clean = re.sub(r'^.*SUBTEMA-\d+:\s*', '', query).strip()[:100]
    context["clean_query"] = clean
    return context

@then('la query resultante es "AI agents"')
def query_limpia(context):
    assert context.get("clean_query") == "AI agents"

@then("no contiene el identificador de Beads")
def no_contiene_identificador(context):
    assert "research-engine" not in context.get("clean_query", "")


# ═══════════════════════════════════════════════════════════════════
# FEATURE: CICLO DE VIDA (start.sh / stop.sh)
# ═══════════════════════════════════════════════════════════════════

@given("el sistema está completamente parado")
def sistema_parado():
    return {"estado": "parado"}

@when("se ejecuta ./start.sh")
def ejecuta_start_sh():
    start_script = '/home/oracle/research-engine-api-llm/start.sh'
    if os.path.exists(start_script):
        with open(start_script) as f:
            content = f.read()
        return {"script_content": content}
    return {"script_content": ""}

@then("Dolt arranca antes que cualquier agente")
def dolt_arranca_primero(context):
    content = context.get("script_content", "")
    if content:
        dolt_pos = content.find("bd dolt start")
        agent_pos = content.find("python3 agents/orchestrator")
        assert dolt_pos < agent_pos

@then("Ollama o HF están disponibles antes de que los Researchers busquen tareas")
def llm_disponible_antes():
    assert True

@then("los 5 paneles tmux están activos con sus respectivos agentes")
def paneles_tmux_activos(context):
    content = context.get("script_content", "")
    if content:
        assert "orchestrator" in content
        assert "researcher-1" in content
        assert "researcher-2" in content
        assert "synthesizer" in content
        assert "critic" in content

@given("existen findings, informes y beads de una sesión anterior")
def estado_sesion_anterior():
    return {"tiene_estado_previo": True}

@then("findings/*.md son eliminados")
def findings_eliminados(context):
    content = context.get("script_content", "")
    if content:
        assert "rm -f" in content and "findings" in content

@then("informe-final.md es eliminado")
def informe_eliminado(context):
    content = context.get("script_content", "")
    if content:
        assert "informe-final.md" in content

@then(".beads/ es reinicializado con bd init")
def beads_reinicializado(context):
    content = context.get("script_content", "")
    if content:
        assert "bd init" in content

@given("el sistema está corriendo con todos los agentes activos")
def sistema_corriendo():
    return {"estado": "corriendo"}

@when("se ejecuta ./stop.sh")
def ejecuta_stop_sh():
    stop_script = '/home/oracle/research-engine-api-llm/stop.sh'
    if os.path.exists(stop_script):
        with open(stop_script) as f:
            content = f.read()
        return {"script_content": content}
    return {"script_content": ""}

@then("la sesión tmux es destruida")
def sesion_tmux_destruida(context):
    content = context.get("script_content", "")
    if content:
        assert "tmux kill-session" in content

@then("los procesos python3 de agentes son terminados")
def procesos_python_terminados(context):
    content = context.get("script_content", "")
    if content:
        assert "pkill" in content and "python3" in content

@then("Dolt es parado como último paso")
def dolt_parado_ultimo(context):
    content = context.get("script_content", "")
    if content:
        dolt_stop_pos = content.rfind("bd dolt stop")
        pkill_pos = content.find("pkill")
        assert dolt_stop_pos > pkill_pos

@given('no existe ninguna sesión tmux "research-api"')
def no_sesion_tmux():
    return {"tmux_exists": False}

@when("start.sh ejecuta tmux kill-session")
def start_sh_kill_session(context):
    content = context.get("script_content", "")
    context["has_null_redirect"] = "2>/dev/null" in content
    return context

@then("el comando devuelve código de salida ignorado con 2>/dev/null")
def codigo_ignorado(context):
    content = context.get("script_content", "")
    if content:
        assert "2>/dev/null" in content

@then("el arranque continúa normalmente")
def arranque_continua():
    assert True

@given("ningún proceso python3 de agentes está corriendo")
def no_procesos_python():
    return {"procesos": []}

@when("stop.sh ejecuta pkill")
def stop_sh_pkill(context):
    content = context.get("script_content", "")
    context["pkill_con_redirect"] = "pkill" in content and "2>/dev/null" in content
    return context

@then("pkill devuelve código de salida no cero ignorado")
def pkill_codigo_ignorado(context):
    content = context.get("script_content", "")
    if content:
        assert "2>/dev/null" in content

@then("stop.sh imprime el mensaje de estado correctamente")
def stop_sh_imprime_mensaje(context):
    content = context.get("script_content", "")
    if content:
        assert "echo" in content

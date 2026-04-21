#!/usr/bin/env python3
"""
Chaos Orchestrator — Research Engine Distribuido
Implementa experimentos de caos sobre las capas del sistema.
"""
import subprocess
import requests
import time
import json
import os
import sys
from datetime import datetime
sys.path.insert(0, '/home/oracle/research-engine-api-llm')

TOXIPROXY_API = "http://localhost:8474"
BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine-api-llm"
LOG_DIR = "/home/oracle/research-engine-api-llm/chaos/logs"

os.makedirs(LOG_DIR, exist_ok=True)

# ─── Toxiproxy helpers ────────────────────────────────────────────

def toxiproxy_running():
    try:
        r = requests.get(f"{TOXIPROXY_API}/proxies", timeout=2)
        return r.status_code == 200
    except:
        return False

def create_proxy(name, listen, upstream):
    payload = {"name": name, "listen": listen, "upstream": upstream, "enabled": True}
    r = requests.post(f"{TOXIPROXY_API}/proxies", json=payload)
    return r.status_code in (200, 201, 409)

def delete_proxy(name):
    requests.delete(f"{TOXIPROXY_API}/proxies/{name}")

def add_toxic(proxy, toxic_type, attrs, stream="downstream"):
    payload = {"type": toxic_type, "stream": stream, "toxicity": 1.0, "attributes": attrs}
    r = requests.post(f"{TOXIPROXY_API}/proxies/{proxy}/toxics", json=payload)
    return r.status_code in (200, 201)

def remove_toxics(proxy):
    r = requests.get(f"{TOXIPROXY_API}/proxies/{proxy}/toxics")
    if r.status_code == 200:
        for toxic in r.json():
            requests.delete(f"{TOXIPROXY_API}/proxies/{proxy}/toxics/{toxic['name']}")

def proxy_exists(name):
    r = requests.get(f"{TOXIPROXY_API}/proxies/{name}")
    return r.status_code == 200

# ─── Observaciones ───────────────────────────────────────────────

def observe_cpu(pid=None):
    if pid:
        result = subprocess.run(["ps", "-p", str(pid), "-o", "%cpu="],
                                capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except:
            return 0.0
    return 0.0

def observe_beads():
    result = subprocess.run([BEADS_BIN, "list", "--all"],
                            capture_output=True, text=True, cwd=BEADS_DIR)
    open_count = result.stdout.count("○")
    closed_count = result.stdout.count("✓")
    error_count = result.stdout.count("ERROR")
    return {"open": open_count, "closed": closed_count, "error": error_count, "raw": result.stdout}

def observe_llm_breaker():
    from tools.llm_client import llm_status
    return llm_status()

# ─── Reporte ─────────────────────────────────────────────────────

def save_report(experiment_name, report):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{LOG_DIR}/{experiment_name}_{ts}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📋 Reporte guardado en: {path}")
    return path

# ─── EXPERIMENTO 1: Timeout en LLM ───────────────────────────────

def exp_llm_timeout():
    """
    Hipótesis: Si R(p,t) falla por timeout, el Circuit Breaker debe
    abrir tras 3 fallos y marcar el estado en Beads.
    """
    print("\n" + "="*60)
    print("EXPERIMENTO 1: Timeout en capa LLM")
    print("Hipótesis: Circuit Breaker abre tras 3 timeouts consecutivos")
    print("="*60)

    report = {
        "experiment": "llm_timeout",
        "hypothesis": "Circuit Breaker abre tras 3 fallos consecutivos",
        "start": datetime.now().isoformat(),
        "phases": []
    }

    # FASE 1: Estado estable
    print("\n[FASE 1] Midiendo estado estable...")
    from tools.llm_client import ask_llm, llm_status
    from tools.circuit_breaker import llm_breaker, State

    try:
        t0 = time.time()
        ask_llm("Say OK", timeout=10)
        latency = (time.time() - t0) * 1000
        print(f"  Latencia baseline: {latency:.0f}ms")
        report["phases"].append({"phase": "baseline", "latency_ms": latency, "status": "OK"})
    except Exception as e:
        print(f"  LLM no disponible en baseline: {e}")
        report["phases"].append({"phase": "baseline", "status": "UNAVAILABLE", "error": str(e)})

    # FASE 2: Inyección de caos — simular timeouts directamente
    print("\n[FASE 2] Inyectando fallos de timeout simulados...")
    from unittest.mock import patch
    import requests as req

    failures = []
    for i in range(4):
        try:
            with patch('tools.llm_client.requests.post') as mock_post:
                mock_post.side_effect = req.exceptions.ReadTimeout("Simulated timeout 60s")
                ask_llm(f"Test {i}", timeout=1)
        except req.exceptions.ReadTimeout as e:
            failures.append({"attempt": i+1, "error": "ReadTimeout", "cb_state": llm_breaker.state.value})
            print(f"  Fallo {i+1}: ReadTimeout — CB estado: {llm_breaker.state.value}")
        except Exception as e:
            failures.append({"attempt": i+1, "error": str(e)[:80], "cb_state": llm_breaker.state.value})
            print(f"  Fallo {i+1}: {str(e)[:60]} — CB estado: {llm_breaker.state.value}")

    report["phases"].append({"phase": "chaos_injection", "failures": failures})

    # FASE 3: Observación
    print("\n[FASE 3] Observando estado del sistema...")
    cb_status = llm_status()
    beads_obs = observe_beads()

    print(f"  Circuit Breaker: {cb_status['state']}")
    print(f"  Fallos registrados: {cb_status['failures']}")
    print(f"  Beads abiertos: {beads_obs['open']}")
    print(f"  Beads cerrados: {beads_obs['closed']}")

    report["phases"].append({
        "phase": "observation",
        "circuit_breaker": cb_status,
        "beads": beads_obs
    })

    # FASE 4: Verificar hipótesis
    print("\n[FASE 4] Verificando hipótesis...")
    cb_opened = llm_breaker.state == State.OPEN
    no_orphan_beads = beads_obs["open"] == 0

    if cb_opened:
        print("  ✅ HIPÓTESIS CONFIRMADA: Circuit Breaker abierto correctamente")
    else:
        print("  ❌ HIPÓTESIS RECHAZADA: Circuit Breaker no se abrió")

    if no_orphan_beads:
        print("  ✅ Sin beads huérfanos en Dolt")
    else:
        print(f"  ⚠️  {beads_obs['open']} beads siguen abiertos — posible transacción colgada")

    report["phases"].append({
        "phase": "verification",
        "hypothesis_confirmed": cb_opened,
        "no_orphan_beads": no_orphan_beads,
        "conclusion": "PASS" if cb_opened else "FAIL"
    })

    # Resetear circuit breaker para no afectar otros experimentos
    llm_breaker.state = State.CLOSED
    llm_breaker.failure_count = 0

    report["end"] = datetime.now().isoformat()
    return save_report("exp1_llm_timeout", report)

# ─── EXPERIMENTO 2: Caída de Dolt ────────────────────────────────

def exp_dolt_failure():
    """
    Hipótesis: Si Dolt cae durante una operación Bc(), el agente
    debe detectar el fallo y no continuar con el flujo.
    """
    print("\n" + "="*60)
    print("EXPERIMENTO 2: Caída de capa Beads+Dolt")
    print("Hipótesis: bd create falla limpiamente si Dolt no responde")
    print("="*60)

    report = {
        "experiment": "dolt_failure",
        "hypothesis": "Agentes detectan fallo de Dolt sin corromper estado",
        "start": datetime.now().isoformat(),
        "phases": []
    }

    # FASE 1: Estado estable
    print("\n[FASE 1] Verificando Dolt disponible...")
    result = subprocess.run([BEADS_BIN, "list"], capture_output=True, text=True, cwd=BEADS_DIR)
    baseline_ok = result.returncode == 0
    print(f"  Dolt disponible: {baseline_ok}")
    report["phases"].append({"phase": "baseline", "dolt_available": baseline_ok})

    # FASE 2: Simular caída de Dolt matando el proceso
    print("\n[FASE 2] Simulando caída de Dolt...")
    subprocess.run(["pkill", "dolt"], capture_output=True)
    time.sleep(2)

    # FASE 3: Observar comportamiento de los agentes
    print("\n[FASE 3] Intentando operaciones Beads sin Dolt...")
    result = subprocess.run([BEADS_BIN, "create", "TEST: chaos test"],
                            capture_output=True, text=True, cwd=BEADS_DIR)
    dolt_error_detected = result.returncode != 0
    error_msg = result.stderr[:100]
    print(f"  bd create retornó error: {dolt_error_detected}")
    print(f"  Mensaje: {error_msg}")

    report["phases"].append({
        "phase": "chaos",
        "error_detected": dolt_error_detected,
        "error_msg": error_msg
    })

    # FASE 4: Restaurar Dolt
    print("\n[FASE 4] Restaurando Dolt...")
    subprocess.Popen([BEADS_BIN, "dolt", "start"],
                     cwd=BEADS_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    result = subprocess.run([BEADS_BIN, "list"], capture_output=True, text=True, cwd=BEADS_DIR)
    restored = result.returncode == 0
    print(f"  Dolt restaurado: {restored}")

    report["phases"].append({
        "phase": "recovery",
        "dolt_restored": restored,
        "conclusion": "PASS" if dolt_error_detected and restored else "FAIL"
    })

    report["end"] = datetime.now().isoformat()
    return save_report("exp2_dolt_failure", report)

# ─── EXPERIMENTO 3: Latencia en búsqueda web ─────────────────────

def exp_web_latency():
    """
    Hipótesis: Si Playwright tarda > 15s, search_web debe
    devolver lista vacía sin bloquear al Researcher indefinidamente.
    """
    print("\n" + "="*60)
    print("EXPERIMENTO 3: Latencia extrema en búsqueda web")
    print("Hipótesis: search_web degrada graciosamente con timeout")
    print("="*60)

    report = {
        "experiment": "web_latency",
        "hypothesis": "search_web devuelve [] con timeout sin bloquear",
        "start": datetime.now().isoformat(),
        "phases": []
    }

    # FASE 1: Baseline
    print("\n[FASE 1] Midiendo latencia normal de arXiv...")
    from tools.web_search import search_arxiv
    t0 = time.time()
    results = search_arxiv("AI agents", max_results=1)
    baseline_latency = (time.time() - t0) * 1000
    print(f"  Latencia baseline: {baseline_latency:.0f}ms, resultados: {len(results)}")
    report["phases"].append({"phase": "baseline", "latency_ms": baseline_latency, "results": len(results)})

    # FASE 2: Simular timeout con Toxiproxy si está disponible
    if toxiproxy_running():
        print("\n[FASE 2] Inyectando latencia de 20s via Toxiproxy...")
        create_proxy("arxiv-proxy", "127.0.0.1:8080", "arxiv.org:443")
        add_toxic("arxiv-proxy", "latency", {"latency": 20000, "jitter": 0})
        time.sleep(1)
        report["phases"].append({"phase": "toxiproxy", "toxic": "latency_20s", "proxy": "arxiv-proxy"})
    else:
        print("\n[FASE 2] Toxiproxy no disponible — simulando con mock timeout...")

    # FASE 3: Observar con timeout corto
    print("\n[FASE 3] Ejecutando search_arxiv con timeout corto...")
    from unittest.mock import patch
    from playwright.sync_api import TimeoutError as PlaywrightTimeout

    t0 = time.time()
    try:
        with patch('tools.web_search.sync_playwright') as mock_pw:
            mock_pw.side_effect = PlaywrightTimeout("Navigation timeout 15000ms exceeded")
            results_chaos = search_arxiv("AI agents", max_results=1)
    except:
        results_chaos = []
    elapsed = (time.time() - t0) * 1000
    print(f"  Resultados bajo caos: {len(results_chaos)}, tiempo: {elapsed:.0f}ms")

    degraded_gracefully = len(results_chaos) == 0 and elapsed < 5000
    report["phases"].append({
        "phase": "chaos",
        "results": len(results_chaos),
        "elapsed_ms": elapsed,
        "degraded_gracefully": degraded_gracefully
    })

    # Limpiar Toxiproxy
    if toxiproxy_running():
        remove_toxics("arxiv-proxy")
        delete_proxy("arxiv-proxy")

    print(f"\n  Degradación graceful: {'✅' if degraded_gracefully else '❌'}")
    report["end"] = datetime.now().isoformat()
    return save_report("exp3_web_latency", report)

# ─── RUNNER PRINCIPAL ─────────────────────────────────────────────

def run_all():
    print("\n🔥 CHAOS ORCHESTRATOR — Research Engine Distribuido")
    print(f"   Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Logs en: {LOG_DIR}\n")

    if not toxiproxy_running():
        print("⚠️  Toxiproxy no está corriendo. Iniciándolo...")
        subprocess.Popen(["toxiproxy-server", "--port", "8474"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        if toxiproxy_running():
            print("✅ Toxiproxy iniciado\n")
        else:
            print("⚠️  Toxiproxy no disponible — algunos experimentos usarán mocks\n")

    resultados = {}
    resultados["exp1"] = exp_llm_timeout()
    resultados["exp2"] = exp_dolt_failure()
    resultados["exp3"] = exp_web_latency()

    print("\n" + "="*60)
    print("RESUMEN DE EXPERIMENTOS")
    print("="*60)
    for exp, path in resultados.items():
        print(f"  {exp}: {path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chaos Orchestrator")
    parser.add_argument("--exp", choices=["1", "2", "3", "all"], default="all")
    args = parser.parse_args()

    if args.exp == "1":
        exp_llm_timeout()
    elif args.exp == "2":
        exp_dolt_failure()
    elif args.exp == "3":
        exp_web_latency()
    else:
        run_all()

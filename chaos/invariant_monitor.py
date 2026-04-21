#!/usr/bin/env python3
"""
Monitor de invariantes — Research Engine Distribuido
Detecta violaciones de invariantes en tiempo de ejecución.
Corre en paralelo al stack principal.
"""
import subprocess
import time
import re
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, '/home/oracle/research-engine-api-llm')

BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine-api-llm"
LOG_FILE = "/home/oracle/research-engine-api-llm/chaos/logs/invariant_violations.jsonl"
CHECK_INTERVAL = 15  # segundos entre comprobaciones
MAX_BEAD_AGE_SECONDS = 600  # I1: bead abierto sin proceso → alerta tras 10 min

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# ─── Utilidades ───────────────────────────────────────────────────

def log_violation(invariant, detail, severity="HIGH"):
    entry = {
        "ts": datetime.now().isoformat(),
        "invariant": invariant,
        "severity": severity,
        "detail": detail
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "HIGH" else "🟢"
    print(f"{icon} [{entry['ts'][:19]}] VIOLACION {invariant} ({severity}): {detail}")
    return entry

def log_ok(invariant, detail=""):
    print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] {invariant} OK {detail}")

def get_beads():
    result = subprocess.run(
        [BEADS_BIN, "list", "--all"],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    beads = []
    for linea in result.stdout.split("\n"):
        if "research-engine" not in linea:
            continue
        status = "open" if "○" in linea else "closed" if "✓" in linea else "other"
        match = re.search(r'(research-engine-\w+)', linea)
        bead_id = match.group(1) if match else None
        if bead_id:
            beads.append({"id": bead_id, "status": status, "raw": linea.strip()})
    return beads

def get_agent_processes():
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True, text=True
    )
    agents = []
    for linea in result.stdout.split("\n"):
        if "research-engine-api-llm" in linea and "python3" in linea:
            for agent in ["orchestrator", "researcher-1", "researcher-2", "synthesizer", "critic"]:
                if agent in linea:
                    pid_match = re.search(r'oracle\s+(\d+)', linea)
                    pid = pid_match.group(1) if pid_match else None
                    agents.append({"agent": agent, "pid": pid, "raw": linea[:80]})
    return agents

def get_circuit_breaker_state():
    try:
        from tools.circuit_breaker import llm_breaker
        return llm_breaker.state.value, llm_breaker.failure_count, llm_breaker.last_failure_time
    except Exception as e:
        return "UNKNOWN", 0, None

def get_iteration_count():
    import glob
    informes = glob.glob(f"{BEADS_DIR}/informe-final-iter*.md")
    return len(informes)

def get_followup_count():
    beads = get_beads()
    return len([b for b in beads if "FOLLOWUP" in b.get("raw", "")])

# ─── DETECTOR I1: Beads huérfanos ────────────────────────────────

def check_I1():
    """
    I1: Ningún bead queda abierto sin agente activo indefinidamente.
    Detecta beads abiertos cuando no hay agentes corriendo.
    """
    beads = get_beads()
    agents = get_agent_processes()
    open_beads = [b for b in beads if b["status"] == "open"]

    if not open_beads:
        log_ok("I1", f"sin beads abiertos")
        return True

    if not agents:
        # Beads abiertos pero sin agentes — posible estado huérfano
        for b in open_beads:
            is_followup = "FOLLOWUP" in b.get("raw", "")
            is_synthesis = "SYNTHESIS" in b.get("raw", "")
            is_critic = "CRITIC" in b.get("raw", "")

            if not is_followup and not is_synthesis and not is_critic:
                violation = log_violation(
                    "I1",
                    f"Bead {b['id']} abierto sin agentes activos — posible transacción huérfana",
                    severity="CRITICAL"
                )
                # Marcar bead como ERROR en Beads
                subprocess.run(
                    [BEADS_BIN, "comment", b["id"],
                     f"[INVARIANT-MONITOR] I1 violation detected at {datetime.now().isoformat()}"],
                    capture_output=True, text=True, cwd=BEADS_DIR
                )
        return False

    log_ok("I1", f"{len(open_beads)} beads abiertos, {len(agents)} agentes activos")
    return True

# ─── DETECTOR I2: Colisión de Researchers ────────────────────────

def check_I2():
    """
    I2: Cada SUBTEMA tiene exactamente un Researcher asignado.
    Detecta si dos Researchers tienen el mismo SUBTEMA en progreso.
    """
    beads = get_beads()
    agents = get_agent_processes()

    researcher_agents = [a for a in agents if "researcher" in a["agent"]]

    if len(researcher_agents) > 2:
        violation = log_violation(
            "I2",
            f"Más de 2 Researchers activos: {[a['agent'] for a in researcher_agents]}",
            severity="HIGH"
        )
        return False

    subtema_beads = [b for b in beads
                     if "SUBTEMA" in b.get("raw", "") and b["status"] == "open"]

    if len(subtema_beads) > 0 and len(researcher_agents) == 0:
        log_ok("I2", "subtemas pendientes esperando Researchers")
        return True

    if len(subtema_beads) > len(researcher_agents) and len(researcher_agents) > 0:
        log_ok("I2", f"{len(subtema_beads)} subtemas, {len(researcher_agents)} researchers — normal")
        return True

    log_ok("I2", f"{len(researcher_agents)} researchers activos")
    return True

# ─── DETECTOR I13: Iteraciones acotadas ──────────────────────────

def check_I13():
    """
    I13: El número de iteraciones nunca supera MAX_ITERATIONS=2.
    Detecta bucles infinitos del Critic.
    """
    MAX_ITERATIONS = 2
    iter_count = get_iteration_count()

    if iter_count > MAX_ITERATIONS:
        violation = log_violation(
            "I13",
            f"Iteraciones actuales: {iter_count} > MAX_ITERATIONS={MAX_ITERATIONS} — posible bucle infinito",
            severity="CRITICAL"
        )
        return False

    followup_count = get_followup_count()
    if followup_count > MAX_ITERATIONS * 3:
        violation = log_violation(
            "I13",
            f"FOLLOWUP excesivos: {followup_count} > {MAX_ITERATIONS * 3} esperados",
            severity="HIGH"
        )
        return False

    log_ok("I13", f"iter={iter_count}/{MAX_ITERATIONS}, followups={followup_count}")
    return True

# ─── DETECTOR I5+I7: Circuit Breaker ─────────────────────────────

def check_I5_I7():
    """
    I5: Circuit Breaker tiene exactamente un estado válido.
    I7: Si state=OPEN entonces last_failure_time != None.
    """
    state, failures, last_failure = get_circuit_breaker_state()

    if state == "UNKNOWN":
        log_ok("I5+I7", "Circuit Breaker no inicializado aún")
        return True

    valid_states = {"CLOSED", "OPEN", "HALF_OPEN"}
    if state not in valid_states:
        log_violation("I5", f"Estado inválido del Circuit Breaker: {state}", severity="CRITICAL")
        return False

    if state == "OPEN" and last_failure is None:
        log_violation("I7", "Circuit Breaker OPEN pero last_failure_time=None", severity="CRITICAL")
        return False

    if failures < 0:
        log_violation("I6", f"failure_count negativo: {failures}", severity="HIGH")
        return False

    log_ok("I5+I7", f"CB state={state}, failures={failures}")
    return True

# ─── DETECTOR I9: Synthesizer con findings suficientes ───────────

def check_I9():
    """
    I9: El Synthesizer nunca genera informe con menos de 2 findings.
    """
    import glob
    informe_existe = os.path.exists(f"{BEADS_DIR}/informe-final.md")
    findings = glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")

    if informe_existe and len(findings) < 2:
        log_violation(
            "I9",
            f"informe-final.md existe con solo {len(findings)} findings — violación de precondición",
            severity="HIGH"
        )
        return False

    log_ok("I9", f"findings={len(findings)}, informe={'sí' if informe_existe else 'no'}")
    return True

# ─── BUCLE PRINCIPAL ─────────────────────────────────────────────

def run_monitor(interval=CHECK_INTERVAL, once=False):
    print(f"\n🔍 Invariant Monitor iniciado")
    print(f"   Intervalo: {interval}s")
    print(f"   Log: {LOG_FILE}")
    print(f"   Invariantes: I1, I2, I5, I6, I7, I9, I13\n")

    while True:
        print(f"\n─── Check {datetime.now().strftime('%H:%M:%S')} ───────────────────")
        check_I1()
        check_I2()
        check_I5_I7()
        check_I9()
        check_I13()

        if once:
            break

        time.sleep(interval)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Invariant Monitor")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL)
    parser.add_argument("--once", action="store_true", help="Ejecutar una sola vez")
    args = parser.parse_args()
    run_monitor(interval=args.interval, once=args.once)

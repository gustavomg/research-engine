import subprocess
import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.insert(0, '/home/oracle/research-engine-api-llm')
from tools.llm_client import ask_llm

BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine-api-llm"
POLL_INTERVAL = 5

def beads_create(title, body):
    result = subprocess.run(
        [BEADS_BIN, "create", title, "--body", body],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    match = re.search(r'(research-engine-\w+)', result.stdout)
    return match.group(1) if match else None

def beads_close(bead_id, nota):
    subprocess.run(
        [BEADS_BIN, "close", bead_id, "--body", nota],
        capture_output=True, text=True, cwd=BEADS_DIR
    )

def beads_comment(bead_id, comentario):
    subprocess.run(
        [BEADS_BIN, "comment", bead_id, comentario],
        capture_output=True, text=True, cwd=BEADS_DIR
    )

def main():
    print(f"\n🔍 Critic en espera. Monitorizando informe-final.md cada {POLL_INTERVAL}s...")

    while True:
        if os.path.exists(f"{BEADS_DIR}/informe-final.md"):
            print("\n✅ Informe final detectado. Iniciando análisis crítico...")
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Esperando al Synthesizer...")
        time.sleep(POLL_INTERVAL)

    bead_id = beads_create(
        "CRITIC: Quality evaluation",
        f"Critic started. Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    with open(f"{BEADS_DIR}/informe-final.md", "r") as f:
        informe = f.read()

    if bead_id:
        beads_comment(bead_id, "Report read. Analyzing quality with Qwen2.5-7B.")

    print("\n⚙️  Analizando calidad con Qwen2.5-7B...")

    prompt = f"""You are a rigorous academic critic. Evaluate this research report:

{informe[:3000]}

Produce a CRITICAL REPORT with:
## 1. GLOBAL SCORE (1-10 with justification)
## 2. DETECTED BIASES
## 3. UNSUPPORTED CLAIMS
## 4. CRITICAL GAPS
## 5. INTERNAL CONTRADICTIONS
## 6. REPORT STRENGTHS
## 7. PRIORITY FOLLOW-UP QUESTIONS (top 5)
## 8. IMPROVEMENT RECOMMENDATIONS

Be brutally honest. IMPORTANT: Write the entire report in Spanish."""

    critica = ask_llm(prompt)

    filename = f"{BEADS_DIR}/informe-critico.md"
    with open(filename, "w") as f:
        f.write(f"# CRITICAL QUALITY REPORT\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** Qwen/Qwen2.5-7B-Instruct via HuggingFace\n\n")
        f.write(critica)

    score_match = re.search(r'(\d+)/10', critica)
    score = score_match.group(0) if score_match else "ver informe"

    print(f"\n💾 Informe crítico guardado en: {filename}")

    if bead_id:
        beads_close(bead_id, f"Evaluation complete. Score: {score}. File: {filename}")

    print(f"\n🏁 Ciclo de calidad cerrado. Puntuación: {score}")

if __name__ == "__main__":
    main()

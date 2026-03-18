import subprocess
import os
import glob
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

def hay_dos_findings():
    return len(glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")) >= 2

def leer_hallazgos():
    contenido = ""
    for archivo in glob.glob(f"{BEADS_DIR}/findings/researcher-*.md"):
        print(f"📄 Leyendo: {archivo}")
        with open(archivo, "r") as f:
            contenido += f"\n\n---\n{f.read()}"
    return contenido

def main():
    print(f"\n🧠 Synthesizer en espera. Monitorizando cada {POLL_INTERVAL}s...")

    while True:
        if hay_dos_findings():
            print("\n✅ Dos findings detectados. Iniciando síntesis...")
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Esperando Researchers...")
        time.sleep(POLL_INTERVAL)

    bead_id = beads_create(
        "SYNTHESIS: Generating final report",
        f"Synthesizer started. Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    hallazgos = leer_hallazgos()

    if bead_id:
        beads_comment(bead_id, "Findings read. Generating report with Qwen2.5-7B.")

    print("\n⚙️  Generando informe final con Qwen2.5-7B...")

    prompt = f"""You are an expert analyst. Consolidate these findings from two researchers:

{hallazgos[:3000]}

Produce a FINAL CONSOLIDATED REPORT with:
1. EXECUTIVE SUMMARY (5-7 lines)
2. MAIN FINDINGS BY AREA
3. PATTERNS AND CONNECTIONS
4. CONTRADICTIONS OR TENSIONS
5. GLOBAL CONCLUSIONS
6. GAPS AND NEXT STEPS

Be rigorous and useful for decision making. IMPORTANT: Write the entire report in Spanish."""

    informe = ask_llm(prompt)

    filename = f"{BEADS_DIR}/informe-final.md"
    with open(filename, "w") as f:
        f.write(f"# FINAL RESEARCH REPORT\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** Qwen/Qwen2.5-7B-Instruct via HuggingFace\n\n")
        f.write(informe)

    print(f"\n💾 Informe guardado en: {filename}")

    if bead_id:
        beads_close(bead_id, f"Report generated: {filename}")

    print("\n🏁 Synthesis complete.")

if __name__ == "__main__":
    main()

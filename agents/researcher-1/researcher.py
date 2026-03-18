import subprocess
import sys
import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, '/home/oracle/research-engine-api-llm')
from tools.llm_client import ask_llm
from tools.web_search import search_web, format_results
from tools.memory_store import search_memory, save_finding, format_memory

BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine-api-llm"
POLL_INTERVAL = 5
DELAY_START = 0

def beads_list():
    result = subprocess.run(
        [BEADS_BIN, "list"],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    return result.stdout

def beads_close(bead_id):
    subprocess.run(
        [BEADS_BIN, "close", bead_id],
        capture_output=True, text=True, cwd=BEADS_DIR
    )

def extraer_tarea(researcher_id, lista):
    lineas = lista.strip().split("\n")
    for linea in lineas:
        if f"SUBTEMA-{researcher_id}" in linea and "○" in linea:
            match = re.search(r'(research-engine-\w+)', linea)
            if match:
                return match.group(1), linea.strip()
    return None, None

def main():
    researcher_id = sys.argv[1] if len(sys.argv) > 1 else "1"

    if DELAY_START > 0:
        print(f"\n⏱️  Desfase de {DELAY_START}s...")
        time.sleep(DELAY_START)

    print(f"\n🔬 Researcher-{researcher_id} monitorizando Beads cada {POLL_INTERVAL}s...")

    while True:
        lista = beads_list()
        bead_id, tarea = extraer_tarea(researcher_id, lista)
        if bead_id:
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Sin tareas. Reintentando...")
        time.sleep(POLL_INTERVAL)

    print(f"\n📌 Tarea detectada {bead_id}: {tarea}")

    print("\n🌐 Buscando fuentes web...")
    query = re.sub(r'^.*SUBTEMA-\d+:\s*', '', tarea).strip()[:100]

    # Consultar memoria semántica
    print("\n🧠 Consultando memoria de investigaciones previas...")
    memoria = search_memory(query, top_k=3)
    contexto_previo = format_memory(memoria)
    if memoria:
        print(f"   Encontrados {len(memoria)} findings relevantes en memoria")
    else:
        print("   Sin contexto previo relevante")

    web_results = search_web(query, max_results=3)
    web_context = format_results(web_results)

    print(f"\n⚙️  Investigando con Qwen2.5-7B via HuggingFace...")

    prompt = f"""You are an expert researcher. Research this topic thoroughly:

TOPIC: {tarea}

{contexto_previo}
WEB SOURCES:
{web_context[:1500]}

Write a structured report with:
1. EXECUTIVE SUMMARY (3-5 lines)
2. KEY POINTS (minimum 5)
3. CONTEXT AND BACKGROUND
4. CURRENT TRENDS
5. CONCLUSIONS
6. SOURCES USED
7. GAPS DETECTED

Be exhaustive. Cite sources when using their information. IMPORTANT: Write the entire report in Spanish."""

    hallazgos = ask_llm(prompt)

    os.makedirs(f"{BEADS_DIR}/findings", exist_ok=True)
    filename = f"{BEADS_DIR}/findings/researcher-{researcher_id}-{bead_id}.md"
    with open(filename, "w") as f:
        f.write(f"# Findings Researcher-{researcher_id}\n")
        f.write(f"**Task:** {tarea}\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** Qwen/Qwen2.5-7B-Instruct via HuggingFace\n\n")
        f.write(f"## Web Sources\n{web_context[:500]}\n\n")
        f.write(hallazgos)

    print(f"\n💾 Hallazgos guardados en: {filename}")
    save_finding(query, hallazgos[:2000], {"researcher": researcher_id, "bead_id": bead_id})
    print("🧠 Finding guardado en memoria semántica")
    beads_close(bead_id)
    print(f"✅ Tarea {bead_id} cerrada.")

if __name__ == "__main__":
    main()

import requests
import subprocess
import sys
import os
import re
import time
from datetime import datetime
sys.path.insert(0, '/home/oracle/research-engine')
from tools.web_search import search_web, format_results

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine"
POLL_INTERVAL = 5

def ask_ollama(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=300)
    return response.json()["response"]

def beads_list():
    result = subprocess.run(
        [BEADS_BIN, "list"],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    return result.stdout

def beads_close(bead_id):
    result = subprocess.run(
        [BEADS_BIN, "close", bead_id],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    return result.stdout

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
    print(f"\n🔬 Researcher-{researcher_id} en espera. Monitorizando Beads cada {POLL_INTERVAL}s...")

    while True:
        lista = beads_list()
        bead_id, tarea = extraer_tarea(researcher_id, lista)
        if bead_id:
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Sin tareas. Reintentando...")
        time.sleep(POLL_INTERVAL)

    print(f"\n📌 Tarea detectada {bead_id}: {tarea}")

    # Búsqueda web real
    print("\n🌐 Buscando fuentes web...")
    query = re.sub(r'^.*SUBTEMA-\d+:\s*', '', tarea).strip()[:100]
    web_results = search_web(query, max_results=3)
    web_context = format_results(web_results)

    print(f"\n⚙️  Investigando con {MODEL}...")

    prompt = f"""Eres un investigador experto. Investiga exhaustivamente el siguiente tema:

TEMA: {tarea}

FUENTES WEB REALES ENCONTRADAS:
{web_context}

Basándote en las fuentes anteriores y tu conocimiento, produce un informe con:
1. RESUMEN EJECUTIVO (3-5 líneas)
2. PUNTOS CLAVE (mínimo 5 puntos detallados)
3. CONTEXTO Y ANTECEDENTES
4. TENDENCIAS ACTUALES (basadas en las fuentes)
5. IMPLICACIONES Y CONCLUSIONES
6. FUENTES UTILIZADAS (lista las URLs)
7. LAGUNAS DETECTADAS

Sé exhaustivo. Cita las fuentes cuando uses información de ellas."""

    hallazgos = ask_ollama(prompt)

    os.makedirs(f"{BEADS_DIR}/findings", exist_ok=True)
    filename = f"{BEADS_DIR}/findings/researcher-{researcher_id}-{bead_id}.md"
    with open(filename, "w") as f:
        f.write(f"# Hallazgos Researcher-{researcher_id}\n")
        f.write(f"**Tarea:** {tarea}\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Modelo:** {MODEL}\n\n")
        f.write(f"## Fuentes web consultadas\n{web_context[:500]}\n\n")
        f.write(hallazgos)

    print(f"\n💾 Hallazgos guardados en: {filename}")
    beads_close(bead_id)
    print(f"✅ Tarea {bead_id} cerrada.")

if __name__ == "__main__":
    main()

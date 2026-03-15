import requests
import subprocess
import os
import glob
import time
import re
from datetime import datetime

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
    }, timeout=300
    })
    return response.json()["response"]

def beads_create(title, body):
    result = subprocess.run(
        [BEADS_BIN, "create", title, "--body", body],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    match = re.search(r'(research-engine-\w+)', result.stdout)
    bead_id = match.group(1) if match else None
    print(f"📌 Bead creado en Beads: {bead_id}")
    return bead_id

def beads_close(bead_id, nota):
    subprocess.run(
        [BEADS_BIN, "close", bead_id, "--body", nota],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    print(f"✅ Bead {bead_id} cerrado en Beads.")

def beads_comment(bead_id, comentario):
    subprocess.run(
        [BEADS_BIN, "comment", bead_id, comentario],
        capture_output=True, text=True, cwd=BEADS_DIR
    )

def hay_dos_findings():
    archivos = glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")
    return len(archivos) >= 2

def leer_hallazgos():
    archivos = glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")
    contenido = ""
    for archivo in archivos:
        print(f"📄 Leyendo: {archivo}")
        with open(archivo, "r") as f:
            contenido += f"\n\n---\n{f.read()}"
    return contenido

def main():
    print(f"\n🧠 Synthesizer en espera. Monitorizando findings cada {POLL_INTERVAL}s...")

    while True:
        if hay_dos_findings():
            print("\n✅ Los dos Researchers han terminado. Iniciando síntesis...")
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Esperando a los Researchers...")
        time.sleep(POLL_INTERVAL)

    # Registrar inicio en Beads
    bead_id = beads_create(
        "SYNTHESIS: Generando informe final",
        f"El Synthesizer ha iniciado la consolidación de findings. Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    hallazgos = leer_hallazgos()

    if bead_id:
        beads_comment(bead_id, f"Findings leídos correctamente. Iniciando generación del informe con Ollama.")

    print("\n⚙️  Generando informe final con Ollama...")

    prompt = f"""Eres un analista experto. Tienes los siguientes hallazgos de dos investigadores:

{hallazgos}

Produce un INFORME FINAL CONSOLIDADO con esta estructura:

# INFORME FINAL DE INVESTIGACIÓN

## 1. RESUMEN EJECUTIVO
(síntesis global en 5-7 líneas)

## 2. HALLAZGOS PRINCIPALES POR ÁREA
(organiza los hallazgos más importantes de ambos researchers)

## 3. PATRONES Y CONEXIONES
(elementos comunes o complementarios entre ambas investigaciones)

## 4. CONTRADICCIONES O TENSIONES
(puntos donde los hallazgos difieren)

## 5. CONCLUSIONES GLOBALES

## 6. LAGUNAS Y PRÓXIMOS PASOS

Sé riguroso, claro y útil para la toma de decisiones."""

    informe = ask_ollama(prompt)

    filename = f"{BEADS_DIR}/informe-final.md"
    with open(filename, "w") as f:
        f.write(f"# INFORME FINAL DE INVESTIGACIÓN\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(informe)

    print(f"\n💾 Informe guardado en: {filename}")

    # Cerrar bead con referencia al informe
    if bead_id:
        beads_close(
            bead_id,
            f"Informe generado correctamente en: {filename}\nFecha de cierre: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    print("\n🏁 Ciclo completo. Trazabilidad registrada en Beads+Dolt.")

if __name__ == "__main__":
    main()
EOFcat > ~/research-engine/agents/synthesizer/synthesizer.py << 'EOF'
import requests
import subprocess
import os
import glob
import time
import re
from datetime import datetime

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
    }, timeout=300
    })
    return response.json()["response"]

def beads_create(title, body):
    result = subprocess.run(
        [BEADS_BIN, "create", title, "--body", body],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    match = re.search(r'(research-engine-\w+)', result.stdout)
    bead_id = match.group(1) if match else None
    print(f"📌 Bead creado en Beads: {bead_id}")
    return bead_id

def beads_close(bead_id, nota):
    subprocess.run(
        [BEADS_BIN, "close", bead_id, "--body", nota],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    print(f"✅ Bead {bead_id} cerrado en Beads.")

def beads_comment(bead_id, comentario):
    subprocess.run(
        [BEADS_BIN, "comment", bead_id, comentario],
        capture_output=True, text=True, cwd=BEADS_DIR
    )

def hay_dos_findings():
    archivos = glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")
    return len(archivos) >= 2

def leer_hallazgos():
    archivos = glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")
    contenido = ""
    for archivo in archivos:
        print(f"📄 Leyendo: {archivo}")
        with open(archivo, "r") as f:
            contenido += f"\n\n---\n{f.read()}"
    return contenido

def main():
    print(f"\n🧠 Synthesizer en espera. Monitorizando findings cada {POLL_INTERVAL}s...")

    while True:
        if hay_dos_findings():
            print("\n✅ Los dos Researchers han terminado. Iniciando síntesis...")
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Esperando a los Researchers...")
        time.sleep(POLL_INTERVAL)

    # Registrar inicio en Beads
    bead_id = beads_create(
        "SYNTHESIS: Generando informe final",
        f"El Synthesizer ha iniciado la consolidación de findings. Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    hallazgos = leer_hallazgos()

    if bead_id:
        beads_comment(bead_id, f"Findings leídos correctamente. Iniciando generación del informe con Ollama.")

    print("\n⚙️  Generando informe final con Ollama...")

    prompt = f"""Eres un analista experto. Tienes los siguientes hallazgos de dos investigadores:

{hallazgos}

Produce un INFORME FINAL CONSOLIDADO con esta estructura:

# INFORME FINAL DE INVESTIGACIÓN

## 1. RESUMEN EJECUTIVO
(síntesis global en 5-7 líneas)

## 2. HALLAZGOS PRINCIPALES POR ÁREA
(organiza los hallazgos más importantes de ambos researchers)

## 3. PATRONES Y CONEXIONES
(elementos comunes o complementarios entre ambas investigaciones)

## 4. CONTRADICCIONES O TENSIONES
(puntos donde los hallazgos difieren)

## 5. CONCLUSIONES GLOBALES

## 6. LAGUNAS Y PRÓXIMOS PASOS

Sé riguroso, claro y útil para la toma de decisiones."""

    informe = ask_ollama(prompt)

    filename = f"{BEADS_DIR}/informe-final.md"
    with open(filename, "w") as f:
        f.write(f"# INFORME FINAL DE INVESTIGACIÓN\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(informe)

    print(f"\n💾 Informe guardado en: {filename}")

    # Cerrar bead con referencia al informe
    if bead_id:
        beads_close(
            bead_id,
            f"Informe generado correctamente en: {filename}\nFecha de cierre: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    print("\n🏁 Ciclo completo. Trazabilidad registrada en Beads+Dolt.")

if __name__ == "__main__":
    main()

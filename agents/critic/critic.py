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
    })
    return response.json()["response"]

def beads_create(title, body):
    result = subprocess.run(
        [BEADS_BIN, "create", title, "--body", body],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    match = re.search(r'(research-engine-\w+)', result.stdout)
    bead_id = match.group(1) if match else None
    print(f"📌 Bead creado: {bead_id}")
    return bead_id

def beads_close(bead_id, nota):
    subprocess.run(
        [BEADS_BIN, "close", bead_id, "--body", nota],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    print(f"✅ Bead {bead_id} cerrado.")

def beads_comment(bead_id, comentario):
    subprocess.run(
        [BEADS_BIN, "comment", bead_id, comentario],
        capture_output=True, text=True, cwd=BEADS_DIR
    )

def informe_listo():
    return os.path.exists(f"{BEADS_DIR}/informe-final.md")

def leer_informe():
    with open(f"{BEADS_DIR}/informe-final.md", "r") as f:
        return f.read()

def main():
    print(f"\n🔍 Critic en espera. Monitorizando informe-final.md cada {POLL_INTERVAL}s...")

    while True:
        if informe_listo():
            print("\n✅ Informe final detectado. Iniciando análisis crítico...")
            break
        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Esperando al Synthesizer...")
        time.sleep(POLL_INTERVAL)

    # Registrar inicio en Beads
    bead_id = beads_create(
        "CRITIC: Evaluación de calidad del informe",
        f"El Critic ha iniciado la evaluación crítica del informe final. Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    informe = leer_informe()

    if bead_id:
        beads_comment(bead_id, "Informe leído. Analizando sesgos, lagunas y afirmaciones sin soporte.")

    print("\n⚙️  Analizando calidad del informe con Ollama...")

    prompt = f"""Eres un crítico académico riguroso e imparcial. Tu misión es evaluar la calidad 
de este informe de investigación con máximo rigor intelectual.

INFORME A EVALUAR:
{informe}

Produce un INFORME CRÍTICO con esta estructura exacta:

## 1. PUNTUACIÓN GLOBAL
Asigna una puntuación del 1 al 10 y justifícala en 2-3 líneas.

## 2. SESGOS DETECTADOS
Lista cada sesgo identificado con:
- Tipo de sesgo (confirmación, selección, cultural, temporal...)
- Dónde aparece en el informe
- Impacto en las conclusiones

## 3. AFIRMACIONES SIN SOPORTE
Lista afirmaciones que necesitan evidencia o fuentes que no están respaldadas.
Para cada una indica qué tipo de evidencia faltaría.

## 4. LAGUNAS CRÍTICAS
Aspectos importantes del tema que el informe ignora completamente.
Ordénalos de mayor a menor impacto en la validez del informe.

## 5. CONTRADICCIONES INTERNAS
Puntos donde el informe se contradice a sí mismo o es inconsistente.

## 6. FORTALEZAS DEL INFORME
Qué hace bien el informe. Sé específico y justo.

## 7. PREGUNTAS DE SEGUIMIENTO PRIORITARIAS
Lista las 5 preguntas más importantes que quedan sin responder.
Ordénalas por prioridad de investigación.

## 8. RECOMENDACIONES DE MEJORA
Acciones concretas para mejorar el informe, ordenadas por impacto.

Sé brutalmente honesto. La utilidad del informe final depende de tu rigor."""

    critica = ask_ollama(prompt)

    # Guardar informe crítico
    filename = f"{BEADS_DIR}/informe-critico.md"
    with open(filename, "w") as f:
        f.write(f"# INFORME CRÍTICO DE CALIDAD\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Evaluado por:** Critic Agent\n\n")
        f.write(critica)

    print(f"\n💾 Informe crítico guardado en: {filename}")

    # Extraer puntuación para el bead
    score_match = re.search(r'(\d+)/10|(\d+)\s*/\s*10', critica)
    score = score_match.group(0) if score_match else "ver informe"

    if bead_id:
        beads_comment(bead_id, f"Análisis completado. Puntuación detectada: {score}")
        beads_close(
            bead_id,
            f"Evaluación crítica completada.\nPuntuación: {score}\nInforme en: {filename}\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    print(f"\n🏁 Ciclo de calidad cerrado. Puntuación: {score}")
    print(f"   Lee el análisis en: {filename}")

if __name__ == "__main__":
    main()

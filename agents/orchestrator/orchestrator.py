import requests
import subprocess
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine"

def ask_ollama(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=300)
    return response.json()["response"]

def beads_create(title, description):
    result = subprocess.run(
        [BEADS_BIN, "create", title, "--body", description],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    print(result.stdout)
    if result.stderr:
        print("ERR:", result.stderr)
    return result.stdout

def main():
    tema = input("\n🔍 Introduce el tema de investigación: ")

    print("\n⚙️  Descomponiendo el tema en subtemas...")
    prompt = f"""Dado el tema de investigación: "{tema}"

Descompónlo en exactamente 2 subtemas distintos y complementarios.
Responde SOLO con este formato JSON, sin explicaciones:
{{"subtema1": "titulo y descripcion del subtema 1", "subtema2": "titulo y descripcion del subtema 2"}}"""

    respuesta = ask_ollama(prompt)
    respuesta = respuesta.strip()
    start = respuesta.find("{")
    end = respuesta.rfind("}") + 1
    subtemas = json.loads(respuesta[start:end])

    print(f"\n📋 Subtema 1: {subtemas['subtema1']}")
    print(f"📋 Subtema 2: {subtemas['subtema2']}")

    print("\n📌 Creando tareas en Beads...")
    beads_create(f"SUBTEMA-1: {subtemas['subtema1'][:50]}", subtemas['subtema1'])
    beads_create(f"SUBTEMA-2: {subtemas['subtema2'][:50]}", subtemas['subtema2'])

    print("\n✅ Tareas creadas en Beads.")
    print("   Panel Researcher-1: python3 ~/research-engine/agents/researcher-1/researcher.py 1")
    print("   Panel Researcher-2: python3 ~/research-engine/agents/researcher-2/researcher.py 2")

if __name__ == "__main__":
    main()

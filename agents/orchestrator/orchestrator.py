import subprocess
import sys
sys.path.insert(0, "/home/oracle/research-engine-api-llm")
import sys
sys.path.insert(0, "/home/oracle/research-engine-api-llm")
import json
import os
from dotenv import load_dotenv
load_dotenv()
from tools.llm_client import ask_llm

BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine-api-llm"

def beads_create(title, description):
    result = subprocess.run(
        [BEADS_BIN, "create", title, "--body", description],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    print(result.stdout)
    return result.stdout

def main():
    tema = input("\n🔍 Introduce el tema de investigación: ")

    print("\n⚙️  Descomponiendo el tema en subtemas...")
    prompt = f"""Given the research topic: "{tema}"

Decompose it into exactly 2 distinct and complementary subtopics.
IMPORTANT: Respond ONLY in English.
Respond ONLY with this JSON format, no explanations:
{{"subtema1": "title and description of subtopic 1", "subtema2": "title and description of subtopic 2"}}"""

    respuesta = ask_llm(prompt)
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

if __name__ == "__main__":
    main()

from flask import Flask, jsonify, render_template
import subprocess
import os
import glob
import re
from datetime import datetime

app = Flask(__name__)

BEADS_BIN = "/home/oracle/go/bin/bd"
BEADS_DIR = "/home/oracle/research-engine"

def get_beads():
    result = subprocess.run(
        [BEADS_BIN, "list", "--all"],
        capture_output=True, text=True, cwd=BEADS_DIR
    )
    tareas = []
    for linea in result.stdout.strip().split("\n"):
        if "SUBTEMA" not in linea:
            continue
        status = "open"
        if "✓" in linea:
            status = "closed"
        elif "◐" in linea:
            status = "in_progress"
        match = re.search(r'(research-engine-\w+)', linea)
        bead_id = match.group(1) if match else "?"
        titulo = re.sub(r'^.*SUBTEMA-\d+:\s*', '', linea).strip()[:80]
        tareas.append({"id": bead_id, "status": status, "titulo": titulo})
    return tareas

def get_findings():
    archivos = glob.glob(f"{BEADS_DIR}/findings/researcher-*.md")
    findings = []
    for archivo in archivos:
        nombre = os.path.basename(archivo)
        size = os.path.getsize(archivo)
        mtime = datetime.fromtimestamp(os.path.getmtime(archivo)).strftime("%H:%M:%S")
        with open(archivo, "r") as f:
            preview = f.read(300).replace("\n", " ")
        findings.append({"nombre": nombre, "size": f"{size} bytes", "modificado": mtime, "preview": preview})
    return findings

def get_informe():
    path = f"{BEADS_DIR}/informe-final.md"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/status")
def status():
    return jsonify({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "beads": get_beads(),
        "findings": get_findings(),
        "informe": get_informe()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

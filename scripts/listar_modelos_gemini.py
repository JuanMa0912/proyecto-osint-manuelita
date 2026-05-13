"""
listar_modelos_gemini.py
------------------------
Lista todos los modelos disponibles en tu API key de Gemini
y filtra los que soportan embedContent (embeddings).

Uso:
    uv run python scripts/listar_modelos_gemini.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

import requests

API_KEY = os.getenv("GEMINI_API_KEY", "")
if not API_KEY:
    print("ERROR: Falta GEMINI_API_KEY en .env")
    sys.exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
resp = requests.get(url, timeout=15)

if resp.status_code != 200:
    print(f"ERROR {resp.status_code}: {resp.text}")
    sys.exit(1)

data = resp.json()
models = data.get("models", [])

print("\n" + "=" * 60)
print("  MODELOS GEMINI — SOPORTAN embedContent")
print("=" * 60)

embed_models = []
for m in models:
    methods = m.get("supportedGenerationMethods", [])
    if "embedContent" in methods:
        embed_models.append(m["name"])
        print(f"  ✓  {m['name']}")

if not embed_models:
    print("  (ninguno disponible)")

print(f"\n  Total con embedContent : {len(embed_models)}")
print("=" * 60)

print("\n  TODOS LOS MODELOS DISPONIBLES:")
print("-" * 60)
for m in models:
    methods = m.get("supportedGenerationMethods", [])
    print(f"  {m['name']}  →  {', '.join(methods)}")

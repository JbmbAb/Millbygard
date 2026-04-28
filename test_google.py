import os
import unittest
import urllib.request
from pathlib import Path

def load_env():
    env_path = Path(".env")
    if not env_path.exists(): return
    for line in env_path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("'").strip('"')

load_env()
key = os.environ.get("GOOGLE_API_KEY")
url = f"https://maps.googleapis.com/maps/api/staticmap?center=61.13,14.66&zoom=15&size=400x400&key={key}"

if not key:
    raise unittest.SkipTest("GOOGLE_API_KEY saknas (forvantad i .env eller miljo).")

print(f"Testar nyckel: {key[:10]}...")
try:
    with urllib.request.urlopen(url) as r:
        print("Status: OK!")
except Exception as e:
    print(f"Fel: {e}")
    if hasattr(e, 'read'):
        print(f"Detaljer: {e.read().decode()}")

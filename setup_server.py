import os
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVER_DIR = ROOT / "MinecraftServer"
PLUGINS_DIR = SERVER_DIR / "plugins"

def download_file(url, dest):
    print(f"Laddar ner {dest.name}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response, open(dest, 'wb') as out_file:
            out_file.write(response.read())
        print(f"  ✅ {dest.name} nedladdad!")
    except Exception as e:
        print(f"  ❌ Misslyckades att ladda ner {dest.name}: {e}")

def main():
    print("Sätter upp Minecraft-servern för Millbygård...")
    SERVER_DIR.mkdir(exist_ok=True)
    PLUGINS_DIR.mkdir(exist_ok=True)

    # 1. Godkänn EULA automatiskt
    (SERVER_DIR / "eula.txt").write_text("eula=true\n")

    # 2. Ladda ner Paper Server (Java 1.20.4)
    paper_url = "https://api.papermc.io/v2/projects/paper/versions/1.20.4/builds/496/downloads/paper-1.20.4-496.jar"
    download_file(paper_url, SERVER_DIR / "paper.jar")

    # 3. Ladda ner Plugins (RaspberryJuice, Geyser & Floodgate)
    rj_url = "https://github.com/zhuowei/RaspberryJuice/raw/master/jars/raspberryjuice-1.12.1.jar"
    download_file(rj_url, PLUGINS_DIR / "raspberryjuice.jar")
    
    geyser_url = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot"
    download_file(geyser_url, PLUGINS_DIR / "Geyser-Spigot.jar")
    
    floodgate_url = "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot"
    download_file(floodgate_url, PLUGINS_DIR / "floodgate-spigot.jar")

    print("Hämtar senaste versionen av ViaVersion från GitHub...")
    try:
        req = urllib.request.Request("https://api.github.com/repos/ViaVersion/ViaVersion/releases/latest", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
            for asset in data.get("assets", []):
                if asset["name"].startswith("ViaVersion-") and asset["name"].endswith(".jar"):
                    download_file(asset["browser_download_url"], PLUGINS_DIR / "ViaVersion.jar")
                    break
    except Exception as e:
        print(f"  ❌ Kunde inte slå upp ViaVersion: {e}")

    # 4. Skapa startfil för Windows
    bat_path = SERVER_DIR / "start.bat"
    bat_path.write_text("@echo off\ntitle Millbygard Server\njava -Xmx2G -Xms2G -jar paper.jar nogui\npause\n")
    
    print("\n" + "="*60)
    print("✅ SERVER-SETUP KLAR!")
    print("👉 Gå in i mappen 'MinecraftServer' och dubbelklicka på 'start.bat' för att starta servern.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
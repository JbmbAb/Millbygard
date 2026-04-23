import json
import sys
from pathlib import Path
from mcpi.minecraft import Minecraft
from mcpi import block

ROOT = Path(__file__).resolve().parent
EXPORTS_DIR = ROOT / "exports"
PARCELS_JSON = EXPORTS_DIR / "millbygard_local_parcels.json"

def draw_line(mc, x1, z1, x2, z2, y, block_type):
    """Bresenhams linjealgoritm för att rita raka linjer i Minecraft."""
    dx = abs(x2 - x1)
    dz = abs(z2 - z1)
    sx = 1 if x1 < x2 else -1
    sz = 1 if z1 < z2 else -1
    err = dx - dz

    while True:
        mc.setBlock(x1, y, z1, block_type)
        if x1 == x2 and z1 == z2:
            break
        e2 = 2 * err
        if e2 > -dz:
            err -= dz
            x1 += sx
        if e2 < dx:
            err += dx
            z1 += sz

def main():
    if not PARCELS_JSON.exists():
        print(f"Fel: Hittade inte filen {PARCELS_JSON}")
        print("Kör konverteringsskriptet först för att generera koordinaterna.")
        sys.exit(1)

    print("Läser in lokal fastighetsdata...")
    with open(PARCELS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        mc = Minecraft.create()
        mc.postToChat("Ritar ut fastighetsgranser for Millbygard...")
    except ConnectionRefusedError:
        print("Kunde inte ansluta till Minecraft. Kontrollera servern och RaspberryJuice.")
        sys.exit(1)

    # Vi lägger linjerna på höjd 63 (ofta standard gräsnivå)
    Y_LEVEL = 63 

    for parcel in data.get("parcels", []):
        designation = parcel.get("designation", "Okänd")
        print(f"Ritar ut gränser för: {designation}")
        
        for ring in parcel.get("all_rings_local", []):
            if len(ring) < 2:
                continue
            
            # Rita linjer mellan varje nod i polygonen
            for i in range(len(ring) - 1):
                x1 = ring[i]["x_block"]
                z1 = -ring[i]["z_block"]  # Invertera Z för Minecraft (-Z är norrut)
                
                x2 = ring[i+1]["x_block"]
                z2 = -ring[i+1]["z_block"]
                
                draw_line(mc, x1, z1, x2, z2, Y_LEVEL, block.GOLD_BLOCK.id)

    mc.postToChat("Fastighetsgranserna ar fardigritade!")
    print("Klart! Gå in i spelet och leta efter guldlinjerna.")

if __name__ == "__main__":
    main()
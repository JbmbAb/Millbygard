# Minecraft snabbkarta

Mål: få upp en första visuell karta i Minecraft innan den fulla kartkedjan är klar.

## Skapad nu

- Datapack-funktion: `millbygard:topografi_2km`
- Källa: Lantmäteriet Topografiska kartor, lokalt 2 km-uttag runt Millbygård
- Skala: 1 Minecraft-block = 20 meter
- Placering i världen: ungefär `x=-105..105`, `y=90..94`, `z=211..429`
- Teleporttips: `/tp @s 0 98 320`

## Kör i Minecraft

1. Starta servern med `MinecraftServer/start.bat` om den inte redan är igång.
2. I Minecraft eller serverkonsolen, kör `/reload`.
3. Kör `/function millbygard:topografi_2km`.
4. Gå till kartan med `/tp @s 0 98 320`.

## Teckenförklaring

- Röd linje: fastighetens arbetsyta.
- Grå/gul/brun linjer: vägar, stigar och traktorvägar.
- Gul yta: åker.
- Grön yta: skog.
- Blå yta: vatten.
- Brun/mörk yta: sankmark eller annan marktyp.

Det här är en snabb grovmodell för orientering. Den riktiga terrängen kommer fortfarande från markhöjd/heightmap och kan justeras senare med bättre lager.

# Balloon-Popper

Jednoduchá hra vytvořená v Python pyGame pro ukázku možností OOP.
2D arkádová hra napsaná v Pythonu pomocí knihovny **pygame**. Cílem hry je co nejrychleji klikat na balonky dříve, než prasknou samy.

## 🚀 Spuštění

1. Nainstaluj závislosti:
   ```bash
   pip install requirements.txt
   ```
2. Spusť hru:

   ```bash
   python3 src/main.py
   ```

## ⚙️ Funkce

- Dynamické měřítko pro různá rozlišení obrazovky (HD, FullHD, 2K, 4K)
- Plynulá animace balónků a částic
- High score chráněné hash klíčem
- Možnost zapnout:
   - Fullscreen
   - Antialiasing
   - Dark mode
- Uložení nastavení do `settings.json`

## 💾 Ukládané soubory

- `config/.highscore` – zakódované skóre
- `config/settings.json` – uživatelské nastavení

## 🛠️ Vyžaduje

- Python 3.8+
- pygame 2.0+

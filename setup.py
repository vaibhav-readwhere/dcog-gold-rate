#!/usr/bin/env python3
"""
One-time setup: downloads Outfit font files into assets/fonts/
Run: python3 setup.py
"""
import os
import urllib.request

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')

FONTS = {
    'Outfit-Regular.ttf':   'https://raw.githubusercontent.com/google/fonts/main/ofl/outfit/static/Outfit-Regular.ttf',
    'Outfit-SemiBold.ttf':  'https://raw.githubusercontent.com/google/fonts/main/ofl/outfit/static/Outfit-SemiBold.ttf',
    'Outfit-Bold.ttf':      'https://raw.githubusercontent.com/google/fonts/main/ofl/outfit/static/Outfit-Bold.ttf',
    'Outfit-ExtraBold.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/outfit/static/Outfit-ExtraBold.ttf',
}

def main():
    os.makedirs(FONTS_DIR, exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0'}

    print("Downloading Outfit fonts …")
    for name, url in FONTS.items():
        path = os.path.join(FONTS_DIR, name)
        if os.path.exists(path):
            print(f"  ✓ {name} already present")
            continue
        print(f"  ↓ {name} …", end=' ', flush=True)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as r:
                with open(path, 'wb') as f:
                    f.write(r.read())
            print("done")
        except Exception as e:
            print(f"FAILED ({e})")

    assets = os.path.dirname(FONTS_DIR)
    print(f"\nAll done.")
    print(f"\nNext step → save your logo as:  {assets}/logo.png")
    print("Then run:  python3 main.py --mock")

if __name__ == '__main__':
    main()

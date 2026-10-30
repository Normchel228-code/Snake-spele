# Snake: Light & Dark Zones

## Failu struktūra

```text
game/
├── __init__.py
└── logic.py
client/
├── __init__.py
└── main.py
```

## Nepieciešams

Python 3 un virtuālā vide (.venv)

## Debian instalēšana

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pygame
```

## Palaišana no projekta mapes

```bash
source .venv/bin/activate
python -m client.main
```

## Vadība

- **Bultiņas vai WASD** - kustība
- **Space** - gaismas efekts (3 punkti, 4 sekundes)
- **R** - sākt spēli no jauna
- **Esc** - iziet no spēles

## Spēles noteikumi

- Sākumā čūskai ir 2 posmi un 0 punktu.
- Par ābolu saņem 10 punktus un vienu posmu.
- Ja kaut viens čūskas posms atrodas tumsā, tiek zaudēti 2 punkti sekundē.
- Par katriem zaudētiem punktiem tiek nogriezti astes posmi.
- Punktu skaits nevar būt mazāks par 0, bet čūskai vienmēr paliek vismaz 2 posmi.
- Gaismas efekts maksā 3 punktus un uz 4 sekundēm izgaismo apkārtni.
- Tumšās zonas mainās ik pēc 7 sekundēm.

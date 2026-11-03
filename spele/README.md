# Snake: Light & Dark

Čūskas spēle ar mainīgām tumšajām zonām, līmeņiem un rezultātu nosūtīšanu uz savu API serveri.

## Projekta struktūra

```text
spele/
├── game/               # spēles noteikumi, BEZ pygame
├── client/             # pygame: ievade, zīmēšana, api_client.py
│   └── main.py
├── api/                # FastAPI serveris
│   ├── main.py
│   ├── db.py
│   ├── templates/      # Jinja HTML veidnes
│   └── static/         # CSS
├── Dizains.docx        # spēles apraksts (Word)
├── README.md
├── requirements.txt
└── .gitignore          # .venv/, __pycache__/, *.db
```

## Instalēšana

Nepieciešams Python 3.10 vai jaunāks.

```bash
cd ~/Snake-spele/spele
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Visas komandas zemāk jāpalaiž **no mapes `spele/`** ar ieslēgtu virtuālo vidi (`source .venv/bin/activate`).
Ja sistēmā nav komandas `python`, izmanto `python3`.

## 1. Servera (API + mājaslapa) palaišana

```bash
python -m api.main
```

Terminālis pēc tam "nepabeidzas" — tas ir normāli, serveris strādā, kamēr terminālis ir atvērts. Apturēt: `Ctrl+C`.
Kad terminālī parādījies `Uvicorn running on http://127.0.0.1:8000`, atver:

- [http://127.0.0.1:8000/](http://127.0.0.1:8000/) — līderu tabula
- [http://127.0.0.1:8000/rules](http://127.0.0.1:8000/rules) — spēles noteikumi
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — API dokumentācija (Swagger)
- `http://127.0.0.1:8000/players/<vards>` — spēlētāja profils (parādās pēc pirmā saglabātā rezultāta)

Ja vajag automātisku pārlādi izstrādes laikā:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir api
```

Lapas darbojas tikai caur serveri. Failus `api/templates/*.html` nevar atvērt ar dubultklikšķi — tās ir Jinja veidnes, un pārlūks rādīs tikai tukšu karkasu.

## 2. Spēles palaišana

Citā terminālī (serveris var darboties paralēli):

```bash
python -m client.main
```

Sākuma izvēlnē ieraksti spēlētāja vārdu (līdz 12 burtiem vai cipariem, `_` un `-`) un nospied `Enter`.
Spēle strādā arī bez servera, bet tad rezultāts netiek saglabāts.

## Vadība

- Bultiņas vai `WASD` — kustība
- `Space` — gaismas impulss: līdz 3 punktiem un 3 astes posmiem par 4 sekundēm gaismas; nepieciešams čūskas garums vismaz 4 posmi
- `P` — pauze vai turpināšana
- `R` — sākt kārtu no jauna
- `Esc` — atgriezties izvēlnē; izvēlnē `Esc` iziet no spēles

## Spēles noteikumi

- Sākumā čūskai ir 2 posmi un 0 punktu.
- Katrs apēstais ābols dod 1 punktu un 1 posmu.
- Tumsa noņem punktus un tikpat astes posmu, ja čūskas posms atrodas tumsā ārpus gaismas impulsa zonas. Čūska nevar kļūt īsāka par 1 posmu, un punktu skaits nevar būt mazāks par 0.
- Līmenis paaugstinās pēc 6 un 14 apēstiem āboliem. Augstākos līmeņos čūska kustas ātrāk, tumsa noņem punktus straujāk, un zonas mainās biežāk.
- Tumšo zonu maiņas intervāli ir 7, 6 un 5 sekundes. Punktu zudums līmeņos ir attiecīgi 1,5, 2 un 2,5 punkti sekundē.
- Sadursme ar sienu vai čūskas ķermeni beidz kārtu.

## Rezultātu API

- `POST /scores` — saglabā rezultātu (`name`, `score`)
- `GET /scores/top` — top-10
- `GET /players/{name}/stats` — spēlētāja statistika

API adresi klientā var nomainīt ar vides mainīgo `SNAKE_API_URL` (noklusējums `http://127.0.0.1:8000`), datubāzes failu — ar `SNAKE_DB` (noklusējums `api/scores.db`).

## Problēmas

- `ERR_CONNECTION_REFUSED` — serveris nav palaists vai ir apstājies; pārbaudi terminālī, vai `python -m api.main` joprojām darbojas.
- Lapa ielādējas bezgalīgi — pārlūkā izslēdz proxy lokālajām adresēm (`127.0.0.1`, `localhost`) vai pamēģini citu pārlūku.
- Ports 8000 aizņemts — pārbaudi ar `ss -ltnp | grep 8000` un aptur veco procesu.
- `ModuleNotFoundError: api` — komanda palaista nevis no `spele/`, vai nav `-m` (jābūt `python -m api.main`, nevis `python api/main.py`).

## Papildu materiāli

Mapē `../Exercise/` glabājas tikai uzdevumu nosacījumi. Tā ir personīgs papildinājums ērtībai un nav daļa no šī projekta struktūras.
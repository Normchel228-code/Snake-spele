# Snake: Light & Dark

Čūskas spēle ar mainīgām tumšajām zonām, līmeņiem un rezultātu nosūtīšanu uz API.

## Prasības un instalēšana

Nepieciešams Python 3.10 vai jaunāks.

```bash
cd ~/Snake-spele/spele
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ja sistēmā nav komandas `python`, izmanto `python3`.

`requirements.txt` ietver spēles un API atkarības, kā arī izstrādes rīkus (`pylint`, `pytest`).

## Projekta struktūra

- [api/main.py](api/main.py) — FastAPI serveris un HTML atskaite
- [api/db.py](api/db.py) — SQLite datubāzes savienojums un rezultātu glabāšana
- [client/main.py](client/main.py) — spēles klients un ievades apstrāde
- [game/logic.py](game/logic.py) — spēles loģika un noteikumi
- [static/style.css](static/style.css) — API mājaslapu stils
- [local-demo/index.html](local-demo/index.html) — lokālās demonstrācijas līderu tabula
- [local-demo/rules.html](local-demo/rules.html) — lokālās demonstrācijas noteikumi
- [local-demo/player.html](local-demo/player.html) — lokālās demonstrācijas spēlētāja profils

## Papildu materiāli

- [Dizains.docx](Dizains.docx) — dizaina dokuments
- [requirements.txt](requirements.txt) — nepieciešamās Python bibliotēkas

## Spēles palaišana

Palaižot no projekta saknes ar ieslēgtu virtuālo vidi:

```bash
cd ~/Snake-spele/spele
source .venv/bin/activate
python -m client.main
# vai, ja python komanda nav pieejama:
# python3 -m client.main
```

Sākuma izvēlnē ieraksti spēlētāja vārdu (līdz 12 burtiem vai cipariem, `_` un `-`) un nospied `Enter`.

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

Klients spēli var turpināt arī bez servera, taču bez pieejama API rezultāts netiek saglabāts. API adresi var mainīt ar `SNAKE_API_URL` (noklusējums ir [http://127.0.0.1:8000](http://127.0.0.1:8000)), bet datubāzes failu — ar `SNAKE_DB`.

Serveris tiek palaists no projekta saknes:

```bash
uvicorn api.main:app --reload
```

Pārbaude pārlūkā: [http://localhost:8000/docs](http://localhost:8000/docs).

Ja HTML lapas tiek pārbaudītas lokāli, tās jāatver tieši pārlūkā, piemēram:

- [http://127.0.0.1:8008/rules.html](http://127.0.0.1:8008/rules.html) — spēles noteikumi
- [http://127.0.0.1:8008/index.html](http://127.0.0.1:8008/index.html) — līderu tabula
- [http://127.0.0.1:8008/player.html](http://127.0.0.1:8008/player.html) — spēlētāja profils

Tas ir piemērots testiem un lokālai validācijai, kad lapas tiek palaistas kā statiskās HTML failu versijas.


"""Klients: sūta rezultātus serverim (requests), nesasaldējot spēli."""

import os
# `threading` ļauj palaist fonā darbu atsevišķā pavedienā,
# tāpēc spēles galvenais cikls neapstājas, kamēr notiek API pieprasījums.
# Bez tā servera saziņa bloķētu lietotāja interfeisu un spēli būtu "saldēta".
import threading

# `requests` ir obligāts API klienta darbināšanai, bet reizēm vide ir minimāla
# un bibliotēka nav instalēta. Tāpēc ielādējam to droši ar fallback, lai
# programma nedarbojas ar sintakses kļūdu un var turpināt darboties ar
# vienkāršu kļūdas simulāciju.
try:
    import requests  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    class _RequestsFallback:
        class RequestException(Exception):
            """Simulē `requests` kļūdu, kad bibliotēka nav instalēta."""

        @staticmethod
        def post(*args, **kwargs):
            raise _RequestsFallback.RequestException("requests package is not installed")

    requests = _RequestsFallback()

# `os.environ.get()` nolasa vides mainīgo `SNAKE_API_URL`.
# Ja tas nav iestatīts, tiek izmantots lokālais defaults:
# `http://127.0.0.1:8000`.
# Šādi konfigurācija ir elastīga: to var mainīt operētājsistēmā vai deploy vidē,
# bez koda rediģēšanas.
BASE_URL = os.environ.get("SNAKE_API_URL", "http://127.0.0.1:8000")
TIMEOUT = 2.0  # Sekundes, cik ilgi gaidām serveri.


def submit_score(name: str, score: int) -> tuple[str, bool]:
    # `tuple[str, bool]` = atgriežam divus elementus: pirmo — tekstu spēlētājam,
    # otro — booleanu, kas norāda, vai sūtīšana neizdevās.
    # Piemērs: ("SCORE SAVED", False) vai ("SERVER OFFLINE", True)
    # Tas ir ērti, jo vienā funkcijā atgriežam gan ziņojumu, gan statusu.
    """Nosūta rezultātu serverim.

    Atgriež pāri (teksts spēlētājam, vai neizdevās). Nekad nemet
    izņēmumu: ja serveris nav pieejams, spēle turpina strādāt.
    """
    try:
        response = requests.post(
            f"{BASE_URL}/scores",
            json={"name": name, "score": score},
            timeout=TIMEOUT,
        )
    except requests.RequestException:
        return "SERVER OFFLINE - SCORE NOT SAVED", True
    if response.status_code == 201:
        return "SCORE SAVED", False
    if response.status_code in (400, 422):
        return "SERVER REJECTED THE SCORE", True
    return f"SERVER ERROR {response.status_code}", True


class ScoreUploader:
    """Sūta rezultātu fonā un glabā statusu, ko zīmē spēle."""

    def __init__(self) -> None:
        self.status = ""
        self.failed = False
        self.started = False
        self._token = 0  # Lai vecs pavediens nepārrakstītu jauno statusu.

    def reset(self) -> None:
        """Aizmirst iepriekšējo sūtīšanu (jauna spēle)."""
        self._token += 1
        self.status = ""
        self.failed = False
        self.started = False

    def start(self, name: str, score: int) -> None:
        """Sāk sūtīšanu atsevišķā pavedienā."""
        self.started = True
        self.failed = False
        self.status = "SAVING SCORE..."
        # `daemon=True` nozīmē, ka šis pavediens ir "fona" process.
        # Tas automātiski tiek pārtraukts, kad programma beidz darboties,
        # negaidot, kamēr tas pabeidz pēdējo API pieprasījumu.
        # Šeit tas ir nepieciešams, lai spēle neaizķertos uz izslēgšanas brīdi,
        # ja rezultāta sūtīšana vēl nav pabeigta, bet lietotājs jau ir aizvēris logu.
        thread = threading.Thread(
            target=self._send, args=(self._token, name, score), daemon=True
        )
        thread.start()

    def _send(self, token: int, name: str, score: int) -> None:
        """Pavediena darbs: nosūta un ieraksta rezultātu."""
        status, failed = submit_score(name, score)
        if token == self._token:
            self.status, self.failed = status, failed

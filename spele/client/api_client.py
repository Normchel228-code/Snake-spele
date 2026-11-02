"""Klients: sūta rezultātus serverim (requests), nesasaldējot spēli."""

import os
import threading

import requests

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
        thread = threading.Thread(
            target=self._send, args=(self._token, name, score), daemon=True
        )
        thread.start()

    def _send(self, token: int, name: str, score: int) -> None:
        """Pavediena darbs: nosūta un ieraksta rezultātu."""
        status, failed = submit_score(name, score)
        if token == self._token:
            self.status, self.failed = status, failed

"""Snake: Light & Dark — zīmēšana, ievade un galvenā cilpa (Pygame)."""
# pylint: disable=no-member

import math
from functools import cache
from typing import Any

import pygame  # type: ignore[import-not-found]

from client import api_client
from game.logic import DOWN, LEFT, RIGHT, UP, Cell, Game

Color = tuple[int, int, int]
Point = tuple[float, float]

# ---------- Iestatījumi ----------

CELL = 20  # Vienas šūnas izmērs pikseļos.
GRID_W, GRID_H = 40, 24  # Laukuma izmērs šūnās.
BOARD_W, BOARD_H = GRID_W * CELL, GRID_H * CELL
WINDOW_W, WINDOW_H = 1000, 720
# Laukuma stūris logā.
BOARD_X, BOARD_Y = (WINDOW_W - BOARD_W) // 2, 166
BOARD = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)

# Krāsas: RGB, komentārā — tas pats hex, kas static/style.css.
BG = (12, 17, 23)  # #0c1117
PANEL = (20, 27, 36)  # #141b24
PANEL_EDGE = (39, 49, 62)  # #27313e
FIELD = (17, 24, 32)  # #111820
GRID_LINE = (25, 34, 44)  # #19222c
TEXT = (235, 241, 245)  # #ebf1f5
MUTED = (133, 148, 164)  # #8594a4
MINT = (99, 225, 178)  # #63e1b2
MINT_DARK = (43, 146, 117)  # #2b9275
TAIL = (34, 103, 91)  # #22675b
CORAL = (255, 105, 112)  # #ff6970
AMBER = (246, 193, 104)  # #f6c168
DARK = (43, 52, 66)  # #2b3442
DARK_EDGE = (55, 68, 84)  # #374454


# ---------- Palīgfunkcijas ----------

@cache
def font(size: int, bold: bool = True) -> pygame.font.Font:
    """Fonts (saglabā, lai neveidotu to katru kadru)."""
    return pygame.font.SysFont("dejavusans", size, bold=bold)


def draw_text(screen: pygame.Surface, string: str, size: int, color: Color,
              bold: bool = True, **position: Any) -> None:
    """Uzzīmē tekstu. Pozīciju norāda ar, piemēram, topleft=(x, y)."""
    surface = font(size, bold).render(string, True, color)
    # **position izplata vārdnīcu kā atslēgas un vērtības:
    # top_left=(x, y) kļūst par surface.get_rect(topleft=(x, y)).
    screen.blit(surface, surface.get_rect(**position))


def mix(a: Color, b: Color, t: float) -> Color:
    """Sajauc divas krāsas: t=0 ir a, t=1 ir b."""
    t = max(0.0, min(1.0, t))
    # zip ņem pa pāriem katru krāsas kanālu: R ar R, G ar G, B ar B.
    # Tādējādi mēs varam vienlaikus apstrādāt abas krāsas bez indeksa.
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def cell_to_pixel(x: float, y: float) -> tuple[int, int]:
    """Šūnas centrs logā (pikseļos)."""
    return (round(BOARD_X + (x + 0.5) * CELL),
            round(BOARD_Y + (y + 0.5) * CELL))


def has_moved(previous: list[Cell], snake: list[Cell]) -> bool:
    """Vai galva kopš pēdējā soļa pārvietojās par vienu šūnu."""
    if not previous:
        return False
    (px, py), (hx, hy) = previous[0], snake[0]
    # abs() atgriež skaitļa absolūto vērtību, tas ir, bez zīmes.
    # Šeit mēs pārbaudām, vai galva ir pārvietojusies tieši par 1 šūnu:
    # horizontāli vai vertikāli, ne pa diagonāli.
    return abs(px - hx) + abs(py - hy) == 1


# ---------- Statiskais fons (zīmē vienu reizi) ----------

def make_background() -> pygame.Surface:
    """Uzzīmē fonu: virsrakstus, laukuma rāmi un režģi."""
    surface = pygame.Surface((WINDOW_W, WINDOW_H))
    surface.fill(BG)
    draw_text(surface, "SNAKE", 27, TEXT, topleft=(BOARD_X, 22))
    draw_text(surface, "LIGHT  /  DARK", 10, MUTED,
              topleft=(BOARD_X + 2, 55))
    controls = ("ARROWS / WASD  MOVE     SPACE  LIGHT PULSE (-3)     "
                "P  PAUSE     R  RESTART     ESC  MENU")
    draw_text(surface, controls, 10, MUTED, center=(WINDOW_W // 2, 690))

    frame = BOARD.inflate(14, 14)
    pygame.draw.rect(surface, PANEL, frame, border_radius=16)
    pygame.draw.rect(surface, PANEL_EDGE, frame, 1, border_radius=16)
    pygame.draw.rect(surface, FIELD, BOARD, border_radius=10)
    for i in range(1, GRID_W):
        x = BOARD_X + i * CELL
        pygame.draw.line(surface, GRID_LINE,
                         (x, BOARD_Y + 1), (x, BOARD.bottom - 1))
    for i in range(1, GRID_H):
        y = BOARD_Y + i * CELL
        pygame.draw.line(surface, GRID_LINE,
                         (BOARD_X + 1, y), (BOARD.right - 1, y))
    return surface


# ---------- Informācijas kartītes (HUD) ----------

def draw_card(screen: pygame.Surface, rect: pygame.Rect, label: str,
              value: str, detail: str, accent: Color,
              progress: float | None = None) -> None:
    """Viena informācijas kartīte ar virsrakstu, vērtību un apakšteksu."""
    pygame.draw.rect(screen, PANEL, rect, border_radius=11)
    pygame.draw.rect(screen, PANEL_EDGE, rect, 1, border_radius=11)
    draw_text(screen, label, 9, MUTED, topleft=(rect.x + 13, rect.y + 9))
    draw_text(screen, value, 22, accent, topleft=(rect.x + 12, rect.y + 23))
    draw_text(screen, detail, 9, MUTED, bold=False,
              topright=(rect.right - 12, rect.y + 37))
    if progress is not None:  # Plāna progresa josla apakšā.
        track = pygame.Rect(rect.x + 13, rect.bottom - 9, rect.width - 26, 3)
        pygame.draw.rect(screen, PANEL_EDGE, track, border_radius=2)
        fill = pygame.Rect(track.x, track.y, round(track.width * progress),
                           track.height)
        if fill.width > 0:
            pygame.draw.rect(screen, accent, fill, border_radius=2)


def draw_hud(screen: pygame.Surface, game: Game) -> None:
    """Trīs kartītes virs laukuma: punkti, garums un tumsas taimeris."""
    score_card = pygame.Rect(BOARD_X, 78, 190, 68)
    length_card = score_card.move(198, 0)
    timer_card = pygame.Rect(length_card.right + 8, 78, BOARD_W - 396, 68)

    draw_card(screen, score_card, "SCORE", f"{game.score:03d}",
              "1 APPLE = 1 POINT", MINT)
    draw_card(screen, length_card, "LENGTH", f"{len(game.snake):02d}",
              "MINIMUM  01 CELL", TEXT)

    if game.light_on:
        label, accent = f"LIGHT ACTIVE  {game.light_timer:0.1f}s", MINT
    else:
        label, accent = "DARK AREAS SHIFT IN", AMBER
    interval = game.config.zone_interval
    left = interval - game.zone_timer
    draw_card(screen, timer_card, label, f"{left:0.1f}s",
              "ANY BODY SEGMENT IN DARKNESS = DRAIN", accent,
              game.zone_timer / interval)
    draw_level(screen, game)


def draw_level(screen: pygame.Surface, game: Game) -> None:
    """Līmenis un cik ābolu līdz nākamajam (augšējā labajā stūrī)."""
    right = BOARD_X + BOARD_W
    draw_text(screen, f"LEVEL {game.level}", 16, AMBER, topright=(right, 22))
    left = game.apples_to_next()
    detail = "FINAL LEVEL" if left is None else f"NEXT LEVEL IN {left} APPLES"
    draw_text(screen, detail, 10, MUTED, topright=(right, 46))


def draw_level_banner(screen: pygame.Surface, game: Game) -> None:
    """Īss uzraksts "LEVEL n", kad sākas jauns līmenis (izdziest)."""
    if game.banner_timer <= 0 or game.is_finished():
        return
    fade = min(1.0, game.banner_timer / 0.6)
    draw_text(screen, f"LEVEL {game.level}", 40, mix(FIELD, AMBER, fade),
              center=(BOARD.centerx, BOARD.y + 70))


# ---------- Laukums ----------

def draw_dark_zones(screen: pygame.Surface, game: Game) -> None:
    """Tumšās zonas. Vecās un jaunās zonas pārklājas pārejas laikā."""
    t = game.fade_progress()
    for cell in game.dark_zones | game.old_dark_zones:
        new = cell in game.dark_zones
        old = cell in game.old_dark_zones
        amount = 1.0 if (new and old) else (t if new else 1.0 - t)
        if amount <= 0.01:
            continue
        rect = pygame.Rect(BOARD_X + cell[0] * CELL,
                           BOARD_Y + cell[1] * CELL,
                           CELL, CELL).inflate(-6, -6)
        pygame.draw.rect(screen, mix(FIELD, DARK, amount), rect,
                         border_radius=6)
        if amount > 0.35:
            pygame.draw.rect(screen, mix(FIELD, DARK_EDGE, amount), rect, 1,
                             border_radius=6)


def draw_apple(screen: pygame.Surface, cell: Cell) -> None:
    """Ābols ar kātiņu un lapiņu."""
    if cell[0] < 0:
        return
    # *cell izplata (x, y) kā divus argumentus funkcijai:
    # cell_to_pixel(x, y)
    cx, cy = cell_to_pixel(*cell)
    pygame.draw.circle(screen, (75, 36, 47), (cx, cy + 1), 9)
    pygame.draw.circle(screen, CORAL, (cx, cy), 7)
    pygame.draw.circle(screen, (255, 169, 164), (cx - 2, cy - 2), 2)
    pygame.draw.line(screen, (112, 157, 111), (cx + 1, cy - 6),
                     (cx + 3, cy - 10), 2)
    pygame.draw.ellipse(screen, (118, 211, 145), (cx + 2, cy - 10, 6, 4))


def draw_cut_tails(screen: pygame.Surface, game: Game) -> None:
    """Nogrieztās astes šūnas, kas pakāpeniski izzūd."""
    for effect in game.effects:
        p = effect.progress()
        if p < 1.0:
            color = mix((75, 183, 145), FIELD, p)
            radius = max(1, round(7 * (1 - p)))
            # *effect.cell izplata (x, y) kā divus argumentus, tāpat kā iepriekš.
            pygame.draw.circle(screen, color, cell_to_pixel(*effect.cell),
                               radius)


# ---------- Čūskas ģeometrija ----------

def segment_length(a: Point, b: Point) -> float:
    """Attālums starp diviem punktiem."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a: Point, b: Point, t: float) -> Point:
    """Punkts starp a un b: t=0 ir a, t=1 ir b."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def snake_line(game: Game, previous: list[Cell],
               progress: float) -> tuple[list[Point], int, bool]:
    """Taisna līnija no astes līdz galvai (šūnu centri).

    Atgriež līniju, galvas indeksu pirms gaidošajiem pagriezieniem un to,
    vai čūska šobrīd kustas starp šūnām.
    """
    line: list[Point] = list(reversed(game.snake))
    if previous:
        old_tail = previous[-1]
        # Ja aste pēdējā solī nobīdījās, sākumā pievienojam punktu.
        moved = (abs(old_tail[0] - line[0][0])
                 + abs(old_tail[1] - line[0][1]) == 1)
        if moved and progress < 0.999:
            # abs() šeit pārbauda, vai aste ir nobīdījusies par vienu šūnu.
            # Ja tā, tad pievienojam starpposma punktu, lai animācija būtu gluda.
            line.insert(0, lerp(line[0], old_tail, 1.0 - progress))

    head_index = len(line) - 1
    moving = has_moved(previous, game.snake) and head_index > 0
    if moving:
        # Gaidošie pagriezieni tiek pievienoti līnijas beigās.
        for dx, dy in game.queue:
            x, y = line[-1]
            line.append((x + dx, y + dy))
    return line, head_index, moving


def path_distances(line: list[Point]) -> list[float]:
    """Attālumi pa līniju no astes līdz katram punktam."""
    dist = [0.0]
    # zip ņem blakus esošos punktus pa pāriem: (p0, p1), (p1, p2), (p2, p3)...
    # Tā mēs viegli aprēķinām katra segmenta garumu un uzkrājam kopējo attālumu.
    for a, b in zip(line, line[1:]):
        dist.append(dist[-1] + segment_length(a, b))
    return dist


def unit(a: Point, b: Point, length: float) -> Point:
    """Vienības vektors no a uz b."""
    return ((b[0] - a[0]) / length, (b[1] - a[1]) / length)


def arc_points(corner: Point, dir_in: Point, dir_out: Point, radius: float,
               at: float) -> list[tuple[float, Point]]:
    """Noapaļots stūris: līkne ar kontrolpunktu stūrī."""
    start = (corner[0] - dir_in[0] * radius, corner[1] - dir_in[1] * radius)
    end = (corner[0] + dir_out[0] * radius, corner[1] + dir_out[1] * radius)
    result = []
    for k in range(9):
        t = k / 8
        px = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * corner[0] \
            + t * t * end[0]
        py = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * corner[1] \
            + t * t * end[1]
        result.append((at - radius + 2 * radius * t, (px, py)))
    return result


def round_corners(line: list[Point], dist: list[float],
                  corners: dict[Cell, float]) -> list[tuple[float, Point]]:
    """Stūri kļūst par lokiem. Atgriež pārus (attālums, punkts)."""
    points = [(0.0, line[0])]
    used = 0.0  # Cik no iepriekšējā segmenta jau izmantots loka vajadzībām.
    for i in range(1, len(line) - 1):
        a, v, b = line[i - 1], line[i], line[i + 1]
        len_in = dist[i] - dist[i - 1]
        len_out = dist[i + 1] - dist[i]
        dir_in = unit(a, v, len_in)
        dir_out = unit(v, b, len_out)
        if dir_in == dir_out:  # Taisnā līnijā nav stūra.
            used = 0.0
            continue

        wanted = corners.get((round(v[0]), round(v[1])), 0.5)
        radius = used = max(0.0, min(wanted, len_in - used, len_out))
        if radius < 1e-3:
            points.append((dist[i], v))
            continue
        points.extend(arc_points(v, dir_in, dir_out, radius, dist[i]))
    points.append((dist[-1], line[-1]))
    return points


def cut_at(points: list[tuple[float, Point]], head_at: float) -> list[Point]:
    """Nogriež līniju galvas vietā."""
    cut: list[Point] = []
    for index, (at, point) in enumerate(points):
        if at <= head_at:
            cut.append(point)
            continue
        prev_at, prev_point = points[index - 1]
        t = (head_at - prev_at) / (at - prev_at) if at > prev_at else 0.0
        cut.append(lerp(prev_point, point, t))
        break
    return cut


def snake_points(game: Game, previous: list[Cell], progress: float,
                 corners: dict[Cell, float]) -> list[Point]:
    """Čūskas punkti no galvas līdz astei, ar noapaļotiem stūriem.

    Punkti ir ar daļskaitļiem, jo čūska pārvietojas starp šūnām.
    """
    progress = max(0.0, min(1.0, progress))
    line, head_index, moving = snake_line(game, previous, progress)
    dist = path_distances(line)

    head_at = dist[head_index]
    if moving:
        before = dist[head_index - 1]
        head_at = before + (dist[head_index] - before) * progress

    points = round_corners(line, dist, corners)
    return cut_at(points, head_at)[::-1]


# ---------- Čūska ----------

def draw_snake(screen: pygame.Surface, game: Game, previous: list[Cell],
               progress: float, corners: dict[Cell, float]) -> None:
    """Uzzīmē čūskas ķermeni un galvu."""
    points = snake_points(game, previous, progress, corners)
    centers = [cell_to_pixel(x, y) for x, y in points]

    # Ķermenis: līnijas starp punktiem, tumšāks uz astes pusi.
    for i in range(len(centers) - 1, 0, -1):
        t = i / max(1, len(centers) - 1) * 0.72
        color = mix(MINT_DARK, TAIL, t)
        pygame.draw.line(screen, color, centers[i], centers[i - 1], 15)
        pygame.draw.circle(screen, color, centers[i], 7)
    pygame.draw.circle(screen, TAIL, centers[-1], 6)

    # Galva.
    head = centers[0]
    pygame.draw.circle(screen, MINT, head, 10)
    pygame.draw.circle(screen, (157, 255, 216), (head[0] - 3, head[1] - 4), 2)
    draw_eyes(screen, head, points, game.direction)


def draw_eyes(screen: pygame.Surface, head: tuple[int, int],
              points: list[Point], fallback_dir: Cell) -> None:
    """Acis: skatās virzienā, kurā čūska pārvietojas."""
    # Virziens no galvas uz nākamo punktu, kas ir pietiekami tālu.
    dx, dy = fallback_dir
    for x, y in points[1:]:
        gap = segment_length(points[0], (x, y))
        if gap >= 0.12:
            dx = (points[0][0] - x) / gap
            dy = (points[0][1] - y) / gap
            break
    # Perpendikuls — no tā atkarīgs, kur atrodas abas acis.
    px, py = -dy, dx
    for side in (1, -1):
        eye = (round(head[0] + dx * 2 + px * 4 * side),
               round(head[1] + dy * 2 + py * 4 * side))
        pygame.draw.circle(screen, (245, 255, 250), eye, 2)
        pupil = (round(eye[0] + dx), round(eye[1] + dy))
        pygame.draw.circle(screen, (24, 57, 49), pupil, 1)


def draw_light(screen: pygame.Surface, game: Game,
               overlay: pygame.Surface) -> None:
    """Gaismas aura ap galvu (mirgo)."""
    if not game.light_on:
        return
    overlay.fill((0, 0, 0, 0))
    # *game.snake[0] izplata (x, y) kā divus argumentus funkcijai.
    cx, cy = cell_to_pixel(*game.snake[0])
    center = (cx - BOARD_X, cy - BOARD_Y)
    pulse = 58 + 10 * math.sin(pygame.time.get_ticks() / 260.0)
    # *AMBER izplata RGB tripletu: (R, G, B) -> R, G, B, pēc tam pievieno alfa kanālu.
    # Tādējādi iegūstam RGBA formātu: (R, G, B, alpha).
    pygame.draw.circle(overlay, (*AMBER, 18), center, CELL * 3)
    pygame.draw.circle(overlay, (*AMBER, round(pulse)), center, CELL * 2, 2)
    screen.blit(overlay, BOARD)


# ---------- Izvēlne, pauze, beigu ekrāns ----------

def draw_menu(screen: pygame.Surface, name: str, difficulty: str | None,
              overlay: pygame.Surface) -> None:
    """Galvenā izvēlne ar atsevišķu grūtības izvēli un vārda ievadi."""
    overlay.fill((8, 12, 18, 215))
    screen.blit(overlay, BOARD)

    card = pygame.Rect(0, 0, 420, 255)
    card.center = BOARD.center
    pygame.draw.rect(screen, PANEL, card, border_radius=16)
    pygame.draw.rect(screen, PANEL_EDGE, card, 1, border_radius=16)
    draw_text(screen, "SNAKE  LIGHT / DARK", 13, AMBER,
              center=(card.centerx, card.y + 28))

    difficulty_label = "SELECTED: EASY" if difficulty == "easy" else (
        "SELECTED: NORMAL" if difficulty == "normal" else (
            "SELECTED: HARD" if difficulty == "hard" else "SELECT DIFFICULTY"
        )
    )
    draw_text(screen, difficulty_label, 11, MUTED,
              center=(card.centerx, card.y + 54))
    draw_text(screen, "1 EASY   2 NORMAL   3 HARD", 12, TEXT,
              center=(card.centerx, card.y + 78))
    draw_text(screen, "ENTER YOUR NAME", 18, TEXT,
              center=(card.centerx, card.y + 116))

    field = pygame.Rect(0, 0, 300, 44)
    field.center = (card.centerx, card.y + 165)
    pygame.draw.rect(screen, FIELD, field, border_radius=8)
    pygame.draw.rect(screen, MINT_DARK, field, 1, border_radius=8)
    blink = pygame.time.get_ticks() // 500 % 2 == 0
    draw_text(screen, name + ("_" if blink else " "), 18, MINT,
              midleft=(field.x + 14, field.centery))

    if difficulty is None:
        hint = "SELECT DIFFICULTY FIRST"
    elif name:
        hint = "ENTER  START"
    else:
        hint = "TYPE A NAME TO START"
    draw_text(screen, hint, 10, MUTED, center=(card.centerx, card.y + 212))
    draw_text(screen, "ESC  QUIT", 10, MUTED,
              center=(card.centerx, card.y + 233))


def draw_pause(screen: pygame.Surface, game: Game,
               overlay: pygame.Surface) -> None:
    """Pauzes uzraksts virs laukuma."""
    if not game.paused:
        return
    overlay.fill((8, 12, 18, 170))
    screen.blit(overlay, BOARD)
    draw_text(screen, "PAUSED", 23, TEXT, center=BOARD.center)
    draw_text(screen, "PRESS P TO RESUME", 11, MUTED,
              center=(BOARD.centerx, BOARD.centery + 36))


def draw_game_over(screen: pygame.Surface, game: Game,
                   overlay: pygame.Surface, status: str = "",
                   status_color: Color = MUTED) -> None:
    """Aptumšo laukumu un kartīti ar rezultātu un servera statusu."""
    if not game.is_finished():
        return
    overlay.fill((8, 12, 18, 188))
    screen.blit(overlay, BOARD)

    card = pygame.Rect(0, 0, 340, 170)
    card.center = BOARD.center
    pygame.draw.rect(screen, PANEL, card, border_radius=16)
    pygame.draw.rect(screen, PANEL_EDGE, card, 1, border_radius=16)
    title = "FIELD CLEARED" if game.game_won else "GAME OVER"
    draw_text(screen, title, 23, TEXT, center=(card.centerx, card.y + 38))
    draw_text(screen, f"FINAL SCORE   {game.score}", 11, MINT,
              center=(card.centerx, card.y + 75))
    draw_text(screen, "PRESS R TO PLAY AGAIN", 11, MUTED,
              center=(card.centerx, card.y + 108))
    if status:
        draw_text(screen, status, 10, status_color,
                  center=(card.centerx, card.y + 141))


# ---------- Ievade un galvenā cilpa ----------

FPS = 60
MAX_NAME = 12  # Vārda garums (servera validācijai jābūt tādai pašai).
DIFFICULTY_KEYS = {
    pygame.K_1: "easy",
    pygame.K_2: "normal",
    pygame.K_3: "hard",
}

KEYS = {  # Taustiņi -> virzieni.
    pygame.K_UP: UP, pygame.K_w: UP,
    pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
}


def is_name_char(char: str) -> bool:
    """Vai simbolu drīkst likt spēlētāja vārdā (bez atstarpēm)."""
    return char.isalnum() or char in "_-"


def edit_name(event: pygame.event.Event, name: str) -> str:
    """Apstrādā taustiņu vārda ievadē un atgriež jauno vārdu."""
    if event.key == pygame.K_BACKSPACE:
        return name[:-1]
    if len(name) < MAX_NAME and event.unicode and is_name_char(event.unicode):
        return name + event.unicode
    return name


class App:
    """Programmas stāvoklis: izvēlne, spēle un animācijas dati."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Snake | Light & Dark")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.background = make_background()
        self.overlay = pygame.Surface(BOARD.size, pygame.SRCALPHA)

        self.game = Game(GRID_W, GRID_H, difficulty="normal")
        self.uploader = api_client.ScoreUploader()
        self.name = ""  # Spēlētāja vārds.
        self.difficulty: str | None = None
        self.game.set_difficulty(self.difficulty or "normal")
        self.in_menu = True
        self.running = True
        self.previous: list[Cell] = list(self.game.snake)  # Iepriekšējais.
        self.corners: dict[Cell, float] = {}  # Pagriezienu loku rādiusi.
        self.step_timer = 0.0

    # ----- Ievade -----

    def new_round(self) -> None:
        """Sāk jaunu spēli un aizmirst veco servera statusu."""
        if self.difficulty is None:
            self.difficulty = "normal"
        self.game.set_difficulty(self.difficulty)
        self.game.reset()
        self.previous = list(self.game.snake)
        self.corners.clear()
        self.step_timer = 0.0
        self.uploader.reset()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Sadala notikumu starp izvēlni un spēli."""
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if self.in_menu:
                self.handle_menu_key(event)
            else:
                self.handle_game_key(event)

    def handle_menu_key(self, event: pygame.event.Event) -> None:
        """Taustiņi izvēlnē: grūtības izvēle, vārda ievade, Enter, Esc."""
        if event.key in DIFFICULTY_KEYS:
            self.difficulty = DIFFICULTY_KEYS[event.key]
            if hasattr(self, "game"):
                self.game.set_difficulty(self.difficulty)
            return
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.name and self.difficulty is not None:
                self.in_menu = False
                self.new_round()
        else:
            self.name = edit_name(event, self.name)

    def handle_game_key(self, event: pygame.event.Event) -> None:
        """Taustiņi spēlē: pagriezieni, pauze, gaisma, restarts."""
        key = getattr(event, "key", None)
        scancode = getattr(event, "scancode", None)
        if key == pygame.K_ESCAPE:
            self.in_menu = True
        elif key == pygame.K_r or scancode == pygame.KSCAN_R:
            self.new_round()
        elif key == pygame.K_p or scancode == pygame.KSCAN_P:
            self.game.toggle_pause()
        elif key in KEYS:
            self.queue_turn(KEYS[key])
        elif key == pygame.K_SPACE:  # Atstarpe — gaismas impulss.
            self.game.light_pulse()

    def queue_turn(self, direction: Cell) -> None:
        """Pieņem pagriezienu un atceras, cik apaļš būs stūris."""
        game = self.game
        queued_before = len(game.queue)
        game.turn(direction)
        if len(game.queue) <= queued_before:
            return
        # Stūris sākas tur, kur galva atrodas tagad.
        hx, hy = game.snake[0]
        if queued_before == 0:
            radius = 0.0
            if has_moved(self.previous, game.snake):
                step_time = game.config.step_time
                radius = max(0.0, min(0.5, 1.0 - self.step_timer / step_time))
            self.corners[(hx, hy)] = radius
        else:
            dx, dy = game.queue[0]
            self.corners[(hx + dx, hy + dy)] = 0.5

    # ----- Atjaunošana un zīmēšana -----

    def update(self, dt: float) -> None:
        """Virza spēli; kad tā beidzas, nosūta rezultātu serverim."""
        if self.in_menu:
            return
        game = self.game
        game.update(dt)
        if game.is_finished():
            self.step_timer = 0.0
            if not self.uploader.started:
                self.uploader.start(self.name, game.score)
            return
        if game.paused:
            return

        self.step_timer += dt
        while self.step_timer >= max(0.01, game.config.step_time):
            self.step_timer -= max(0.01, game.config.step_time)
            self.previous = list(game.snake)
            game.step()
            if game.is_finished():
                break

    def render(self) -> None:
        """Uzzīmē visu kadru."""
        screen, game, overlay = self.screen, self.game, self.overlay
        screen.blit(self.background, (0, 0))
        draw_hud(screen, game)
        if self.in_menu:
            draw_menu(screen, self.name, self.difficulty, overlay)
        else:
            finished = game.is_finished()
            step_time = max(0.01, game.config.step_time)
            progress = 1.0 if finished else self.step_timer / step_time
            draw_dark_zones(screen, game)
            draw_apple(screen, game.apple)
            draw_cut_tails(screen, game)
            draw_snake(screen, game, self.previous, progress,
                            self.corners)
            draw_light(screen, game, overlay)
            draw_level_banner(screen, game)
            draw_pause(screen, game, overlay)
            color = CORAL if self.uploader.failed else MINT
            draw_game_over(screen, game, overlay,
                                self.uploader.status, color)
        pygame.display.flip()

    def run(self) -> None:
        """Galvenā cilpa."""
        while self.running:
            # Ierobežo laiku, lai pēc aizkavēšanās čūska nepārlēktu šūnas.
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.render()
        pygame.quit()


def main() -> None:
    """Palaiž spēli."""
    App().run()


if __name__ == "__main__":
    main()

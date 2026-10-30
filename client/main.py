"""Snake: Light & Dark Zones — zīmēšana ar Pygame un galvenā cilpa."""

import math
from functools import cache

import pygame

from game.logic import DOWN, LEFT, RIGHT, UP, ZONE_INTERVAL, Game

# ---------- Iestatījumi ----------

CELL = 20  # Vienas šūnas izmērs pikseļos.
GRID_W, GRID_H = 40, 24  # Laukuma izmērs šūnās.
BOARD_W, BOARD_H = GRID_W * CELL, GRID_H * CELL
WINDOW_W, WINDOW_H = 1000, 720
BOARD_X, BOARD_Y = (WINDOW_W - BOARD_W) // 2, 166  # Laukuma stūris logā.
BOARD = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)
FPS = 60
STEP_TIME = 0.135  # Cik sekundes ir viens čūskas solis.

# Krāsas.
BG = (12, 17, 23)
PANEL = (20, 27, 36)
PANEL_EDGE = (39, 49, 62)
FIELD = (17, 24, 32)
GRID_LINE = (25, 34, 44)
TEXT = (235, 241, 245)
MUTED = (133, 148, 164)
MINT = (99, 225, 178)
MINT_DARK = (43, 146, 117)
TAIL = (34, 103, 91)
CORAL = (255, 105, 112)
AMBER = (246, 193, 104)
DARK = (43, 52, 66)
DARK_EDGE = (55, 68, 84)

KEYS = {  # Taustiņi -> virzieni.
    pygame.K_UP: UP, pygame.K_w: UP,
    pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
}


# ---------- Palīgfunkcijas ----------

@cache
def font(size, bold=True):
    """Fonts (saglabā, lai neveidotu to katru kadru)."""
    return pygame.font.SysFont("dejavusans", size, bold=bold)


def draw_text(screen, string, size, color, bold=True, **position):
    """Uzzīmē tekstu. Pozīciju norāda ar, piemēram, topleft=(x, y)."""
    surface = font(size, bold).render(string, True, color)
    screen.blit(surface, surface.get_rect(**position))


def mix(a, b, t):
    """Sajauc divas krāsas: t=0 ir a, t=1 ir b."""
    t = max(0.0, min(1.0, t))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def cell_to_pixel(x, y):
    """Šūnas centrs logā (pikseļos)."""
    return round(BOARD_X + (x + 0.5) * CELL), round(BOARD_Y + (y + 0.5) * CELL)


def has_moved(previous, snake):
    """Vai galva kopš pēdējā soļa pārvietojās par vienu šūnu."""
    if not previous:
        return False
    (px, py), (hx, hy) = previous[0], snake[0]
    return abs(px - hx) + abs(py - hy) == 1


# ---------- Statiskais fons (zīmē vienu reizi) ----------

def make_background():
    """Uzzīmē fonu: virsrakstus, laukuma rāmi un režģi."""
    surface = pygame.Surface((WINDOW_W, WINDOW_H))
    surface.fill(BG)
    draw_text(surface, "SNAKE", 27, TEXT, topleft=(BOARD_X, 22))
    draw_text(surface, "LIGHT  /  DARK", 10, MUTED, topleft=(BOARD_X + 2, 55))
    draw_text(surface, "ARCADE  •  01", 10, MUTED, topright=(BOARD_X + BOARD_W, 35))
    draw_text(surface, "ARROWS / WASD  MOVE     SPACE  LIGHT PULSE (-3)     R  RESTART     ESC  QUIT",
              10, MUTED, center=(WINDOW_W // 2, 690))

    frame = BOARD.inflate(14, 14)
    pygame.draw.rect(surface, PANEL, frame, border_radius=16)
    pygame.draw.rect(surface, PANEL_EDGE, frame, 1, border_radius=16)
    pygame.draw.rect(surface, FIELD, BOARD, border_radius=10)
    for i in range(1, GRID_W):
        x = BOARD_X + i * CELL
        pygame.draw.line(surface, GRID_LINE, (x, BOARD_Y + 1), (x, BOARD.bottom - 1))
    for i in range(1, GRID_H):
        y = BOARD_Y + i * CELL
        pygame.draw.line(surface, GRID_LINE, (BOARD_X + 1, y), (BOARD.right - 1, y))
    return surface


# ---------- Informācijas kartītes (HUD) ----------

def draw_card(screen, rect, label, value, detail, accent, progress=None):
    """Viena informācijas kartīte ar virsrakstu, vērtību un apakšējo tekstu."""
    pygame.draw.rect(screen, PANEL, rect, border_radius=11)
    pygame.draw.rect(screen, PANEL_EDGE, rect, 1, border_radius=11)
    draw_text(screen, label, 9, MUTED, topleft=(rect.x + 13, rect.y + 9))
    draw_text(screen, value, 22, accent, topleft=(rect.x + 12, rect.y + 23))
    draw_text(screen, detail, 9, MUTED, bold=False, topright=(rect.right - 12, rect.y + 37))
    if progress is not None:  # Plāna progresa josla apakšā.
        bar = pygame.Rect(rect.x + 13, rect.bottom - 9, rect.width - 26, 3)
        pygame.draw.rect(screen, PANEL_EDGE, bar, border_radius=2)
        fill = pygame.Rect(bar.x, bar.y, round(bar.width * progress), bar.height)
        if fill.width > 0:
            pygame.draw.rect(screen, accent, fill, border_radius=2)


def draw_hud(screen, game):
    """Trīs kartītes virs laukuma: punkti, garums un tumsas taimeris."""
    score_card = pygame.Rect(BOARD_X, 78, 190, 68)
    length_card = score_card.move(198, 0)
    timer_card = pygame.Rect(length_card.right + 8, 78, BOARD_W - 396, 68)

    draw_card(screen, score_card, "SCORE", f"{game.score:03d}", "1 APPLE = 1 POINT", MINT)
    draw_card(screen, length_card, "LENGTH", f"{len(game.snake):02d}", "MINIMUM  01 CELL", TEXT)

    if game.light_on:
        label, accent = f"LIGHT ACTIVE  {game.light_timer:0.1f}s", MINT
    else:
        label, accent = "DARK AREAS SHIFT IN", AMBER
    left = ZONE_INTERVAL - game.zone_timer
    draw_card(screen, timer_card, label, f"{left:0.1f}s",
              "ANY BODY SEGMENT IN DARKNESS = DRAIN", accent,
              game.zone_timer / ZONE_INTERVAL)


# ---------- Laukums ----------

def draw_dark_zones(screen, game):
    """Tumšās zonas. Vecās un jaunās zonas pārklājas pārejas laikā."""
    t = game.fade_progress()
    for cell in game.dark_zones | game.old_dark_zones:
        new = cell in game.dark_zones
        old = cell in game.old_dark_zones
        amount = 1.0 if (new and old) else (t if new else 1.0 - t)
        if amount <= 0.01:
            continue
        rect = pygame.Rect(BOARD_X + cell[0] * CELL, BOARD_Y + cell[1] * CELL, CELL, CELL).inflate(-6, -6)
        pygame.draw.rect(screen, mix(FIELD, DARK, amount), rect, border_radius=6)
        if amount > 0.35:
            pygame.draw.rect(screen, mix(FIELD, DARK_EDGE, amount), rect, 1, border_radius=6)


def draw_apple(screen, cell):
    """Ābols ar kātiņu un lapiņu."""
    if cell[0] < 0:
        return
    cx, cy = cell_to_pixel(*cell)
    pygame.draw.circle(screen, (75, 36, 47), (cx, cy + 1), 9)
    pygame.draw.circle(screen, CORAL, (cx, cy), 7)
    pygame.draw.circle(screen, (255, 169, 164), (cx - 2, cy - 2), 2)
    pygame.draw.line(screen, (112, 157, 111), (cx + 1, cy - 6), (cx + 3, cy - 10), 2)
    pygame.draw.ellipse(screen, (118, 211, 145), (cx + 2, cy - 10, 6, 4))


def draw_cut_tails(screen, game):
    """Nogrieztās astes šūnas, kas pakāpeniski izzūd."""
    for effect in game.effects:
        p = effect.progress()
        if p < 1.0:
            color = mix((75, 183, 145), FIELD, p)
            pygame.draw.circle(screen, color, cell_to_pixel(*effect.cell), max(1, round(7 * (1 - p))))


# ---------- Čūska ----------

def segment_length(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def snake_points(game, previous, progress, corners):
    """Čūskas punkti no astes līdz galvai, pēc tam — ar noapaļotiem stūriem.

    Atgriež sarakstu ar galvu pirmajā vietā. Punkti ir ar daļskaitļiem,
    jo čūska pārvietojas starp šūnām.
    """
    progress = max(0.0, min(1.0, progress))

    # 1) Taisna līnija no astes līdz galvai (šūnu centri).
    line = list(reversed(game.snake))
    if previous:
        old_tail = previous[-1]
        # Ja aste pēdējā solī nobīdījās, sākumā pievienojam punktu, kas to parāda.
        if abs(old_tail[0] - line[0][0]) + abs(old_tail[1] - line[0][1]) == 1 and progress < 0.999:
            line.insert(0, lerp(line[0], old_tail, 1.0 - progress))

    head_index = len(line) - 1
    moving = has_moved(previous, game.snake) and head_index > 0
    if moving:
        # Gaidošie pagriezieni tiek pievienoti līnijas beigās.
        for dx, dy in game.queue:
            x, y = line[-1]
            line.append((x + dx, y + dy))

    # 2) Attālumi pa līniju (lai zinātu, kur atrodas galva).
    dist = [0.0]
    for a, b in zip(line, line[1:]):
        dist.append(dist[-1] + segment_length(a, b))

    head_at = dist[head_index]
    if moving:
        head_at = dist[head_index - 1] + (dist[head_index] - dist[head_index - 1]) * progress

    # 3) Stūri kļūst par lokiem.
    points = [(0.0, line[0])]
    used = 0.0  # Cik no iepriekšējā segmenta jau izmantots loka vajadzībām.
    for i in range(1, len(line) - 1):
        a, v, b = line[i - 1], line[i], line[i + 1]
        len_in = dist[i] - dist[i - 1]
        len_out = dist[i + 1] - dist[i]
        dir_in = ((v[0] - a[0]) / len_in, (v[1] - a[1]) / len_in)
        dir_out = ((b[0] - v[0]) / len_out, (b[1] - v[1]) / len_out)
        if dir_in == dir_out:  # Taisnā līnijā nav stūra.
            used = 0.0
            continue

        radius = corners.get((round(v[0]), round(v[1])), 0.5)
        radius = used = max(0.0, min(radius, len_in - used, len_out))
        if radius < 1e-3:
            points.append((dist[i], v))
            continue

        # Līkne no punkta "ieiet" līdz punktam "iziet" ar kontrolpunktu v.
        start = (v[0] - dir_in[0] * radius, v[1] - dir_in[1] * radius)
        end = (v[0] + dir_out[0] * radius, v[1] + dir_out[1] * radius)
        for k in range(9):
            t = k / 8
            px = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * v[0] + t * t * end[0]
            py = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * v[1] + t * t * end[1]
            points.append((dist[i] - radius + 2 * radius * t, (px, py)))
    points.append((dist[-1], line[-1]))

    # 4) Nogriežam līniju galvas vietā.
    cut = []
    for index, (at, point) in enumerate(points):
        if at <= head_at:
            cut.append(point)
            continue
        prev_at, prev_point = points[index - 1]
        t = (head_at - prev_at) / (at - prev_at) if at > prev_at else 0.0
        cut.append(lerp(prev_point, point, t))
        break
    return cut[::-1]


def draw_snake(screen, game, previous, progress, corners):
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


def draw_eyes(screen, head, points, fallback_dir):
    """Acis: skatās virzienā, kurā čūska pārvietojas."""
    # Virziens no galvas uz nākamo punktu, kas ir pietiekami tālu.
    dx, dy = fallback_dir
    for x, y in points[1:]:
        gap = segment_length(points[0], (x, y))
        if gap >= 0.12:
            dx, dy = (points[0][0] - x) / gap, (points[0][1] - y) / gap
            break
    # Perpendikuls — no tā atkarīgs, kur atrodas abas acis.
    px, py = -dy, dx
    for side in (1, -1):
        eye = (round(head[0] + dx * 2 + px * 4 * side), round(head[1] + dy * 2 + py * 4 * side))
        pygame.draw.circle(screen, (245, 255, 250), eye, 2)
        pupil = (round(eye[0] + dx), round(eye[1] + dy))
        pygame.draw.circle(screen, (24, 57, 49), pupil, 1)


def draw_light(screen, game, overlay):
    """Gaismas aura ap galvu (mirgo)."""
    if not game.light_on:
        return
    overlay.fill((0, 0, 0, 0))
    cx, cy = cell_to_pixel(*game.snake[0])
    center = (cx - BOARD_X, cy - BOARD_Y)
    pulse = 58 + 10 * math.sin(pygame.time.get_ticks() / 260.0)
    pygame.draw.circle(overlay, (*AMBER, 18), center, CELL * 3)
    pygame.draw.circle(overlay, (*AMBER, round(pulse)), center, CELL * 2, 2)
    screen.blit(overlay, BOARD)


def draw_game_over(screen, game, overlay):
    """Aptumšo laukumu un kartīti ar rezultātu."""
    if not game.is_finished():
        return
    overlay.fill((8, 12, 18, 188))
    screen.blit(overlay, BOARD)

    card = pygame.Rect(0, 0, 340, 140)
    card.center = BOARD.center
    pygame.draw.rect(screen, PANEL, card, border_radius=16)
    pygame.draw.rect(screen, PANEL_EDGE, card, 1, border_radius=16)
    title = "FIELD CLEARED" if game.game_won else "GAME OVER"
    draw_text(screen, title, 23, TEXT, center=(card.centerx, card.y + 38))
    draw_text(screen, f"FINAL SCORE   {game.score}", 11, MINT, center=(card.centerx, card.y + 75))
    draw_text(screen, "PRESS R TO PLAY AGAIN", 11, MUTED, center=(card.centerx, card.y + 108))


# ---------- Galvenā cilpa ----------

def main():
    pygame.init()
    pygame.display.set_caption("Snake | Light & Dark")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()
    background = make_background()
    overlay = pygame.Surface(BOARD.size, pygame.SRCALPHA)

    game = Game(GRID_W, GRID_H)
    previous = list(game.snake)  # Čūskas stāvoklis iepriekšējā solī.
    corners = {}  # Pagriezienu rādiusi: kur uz laukuma stūris un cik liels loks.
    step_timer = 0.0

    while True:
        # Ierobežo laiku, lai pēc loga aizkavēšanās čūska nepārlēktu vairākas šūnas.
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if event.type != pygame.KEYDOWN:
                continue

            if event.scancode == pygame.KSCAN_R:  # R — sākt no jauna.
                game.reset()
                previous = list(game.snake)
                corners.clear()
                step_timer = 0.0
            elif event.key in KEYS:
                queued_before = len(game.queue)
                game.turn(KEYS[event.key])
                if len(game.queue) > queued_before:
                    # Stūris sākas tur, kur galva atrodas tagad.
                    hx, hy = game.snake[0]
                    if queued_before == 0:
                        radius = 0.0
                        if has_moved(previous, game.snake):
                            radius = max(0.0, min(0.5, 1.0 - step_timer / STEP_TIME))
                        corners[(hx, hy)] = radius
                    else:
                        dx, dy = game.queue[0]
                        corners[(hx + dx, hy + dy)] = 0.5
            elif event.key == pygame.K_SPACE:  # Atstarpe — gaismas impulss.
                game.light_pulse()

        game.update(dt)

        # Čūska pārvietojas reizi STEP_TIME; starp soļiem zīmējam pakāpenisku pāreju.
        if game.is_finished():
            step_timer = 0.0
        else:
            step_timer += dt
            if step_timer >= STEP_TIME:
                step_timer -= STEP_TIME
                previous = list(game.snake)
                game.step()
        progress = 1.0 if game.is_finished() else step_timer / STEP_TIME

        screen.blit(background, (0, 0))
        draw_hud(screen, game)
        draw_dark_zones(screen, game)
        draw_apple(screen, game.apple)
        draw_cut_tails(screen, game)
        draw_snake(screen, game, previous, progress, corners)
        draw_light(screen, game, overlay)
        draw_game_over(screen, game, overlay)
        pygame.display.flip()


if __name__ == "__main__":
    main()

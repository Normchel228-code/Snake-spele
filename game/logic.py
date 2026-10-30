"""Spēles loģika: čūska, ābols, tumšās zonas un gaismas impulss."""

import random

# Virzieni kā pāri (x, y).
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

START_LENGTH = 2  # Sākuma garums.
MIN_LENGTH = 1  # Mazākais iespējamais garums.
MIN_SCORE = 0  # Mazākais iespējamais punktu skaits.
ZONE_INTERVAL = 7.0  # Cik sekundes starp tumšo zonu maiņām.
ZONE_FADE_TIME = 0.45  # Cik ilgi zona pāriet no vienas vietas uz otru.
DARK_DRAIN = 1.5  # Cik ātri tumsa noņem punktus un garumu (vienības sekundē).
LIGHT_COST = 3  # Cik punktus un garumu maksā gaismas impulss.
LIGHT_TIME = 4.0  # Cik ilgi gaisma deg.
LIGHT_RADIUS = 3  # Gaismas rādiuss šūnās.


def add(a, b):
    """Saskaita divus pārus."""
    return (a[0] + b[0], a[1] + b[1])


def is_opposite(a, b):
    """Vai virzieni a un b ir pretēji."""
    return add(a, b) == (0, 0)


class Effect:
    """Nogrieztā astes posma animācija."""

    def __init__(self, cell, delay):
        self.cell = cell
        self.age = 0.0
        self.delay = delay
        self.duration = 0.24

    def progress(self):
        """Animācijas progress no 0 līdz 1."""
        return max(0.0, min(1.0, (self.age - self.delay) / self.duration))

    def is_done(self):
        """Vai animācija beigusies."""
        return self.age >= self.delay + self.duration


class Game:
    """Glabā spēles stāvokli."""

    def __init__(self, width=34, height=20):
        if width < 5 or height < 5:
            raise ValueError("Laukumam jābūt vismaz 5 x 5 šūnas lielam.")
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        """Sāk spēli no jauna."""
        x, y = self.width // 2, self.height // 2
        self.snake = [(x - i, y) for i in range(START_LENGTH)]  # Galva ir pirmais elements.
        self.score = 0
        self.direction = RIGHT
        self.queue = []  # Nākamie pagriezieni.
        self.effects = []
        self.game_over = False
        self.game_won = False
        self.zone_timer = 0.0
        self.fade_timer = 0.0
        self.dark_acc = 0.0  # Uzkrātā tumsas "rēķina" daļa.
        self.light_on = False
        self.light_timer = 0.0
        self.dark_zones = set()
        self.old_dark_zones = set()
        self.apple = (-1, -1)
        self.spawn_apple()
        self.make_dark_zones(animate=False)

    def is_finished(self):
        """Vai spēle beigusies (zaudējums vai uzvara)."""
        return self.game_over or self.game_won

    def fade_progress(self):
        """Cik tālu pāreja starp zonām ir (0 līdz 1)."""
        if self.fade_timer <= 0:
            return 1.0
        return 1.0 - self.fade_timer / ZONE_FADE_TIME

    def make_dark_zones(self, animate=True):
        """Izveido jaunas tumšās zonas. Ābols vienmēr paliek gaišā vietā."""
        zones = set()
        target = int(self.width * self.height * random.uniform(0.14, 0.18))
        for _ in range(random.randint(4, 6)):
            # Katrs aplis ir viena tumša "sala".
            cx, cy = random.randrange(self.width), random.randrange(self.height)
            rx, ry = random.randint(2, 4), random.randint(2, 4)
            for x in range(max(0, cx - rx), min(self.width, cx + rx + 1)):
                for y in range(max(0, cy - ry), min(self.height, cy + ry + 1)):
                    inside = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
                    if inside and (x, y) != self.apple:
                        zones.add((x, y))
            if len(zones) >= target:
                break

        self.old_dark_zones = self.dark_zones if animate else set()
        self.dark_zones = zones
        self.fade_timer = ZONE_FADE_TIME if animate else 0.0

    def spawn_apple(self):
        """Novieto ābolu brīvā vietā, ja iespējams — gaišā."""
        free = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in self.snake
        ]
        light = [cell for cell in free if cell not in self.dark_zones]
        if free:
            self.apple = random.choice(light or free)
        else:
            self.apple = (-1, -1)
            self.game_won = True

    def turn(self, new_dir):
        """Pieņem jaunu virzienu, ja tas ir derīgs."""
        if self.is_finished() or len(self.queue) >= 2:
            return
        last = self.queue[-1] if self.queue else self.direction
        if new_dir != last and not is_opposite(new_dir, last):
            self.queue.append(new_dir)

    def lose(self, amount):
        """Atņem punktus un garumu, bet ne zem minimuma."""
        self.score = max(MIN_SCORE, self.score - amount)
        cuts = min(amount, len(self.snake) - MIN_LENGTH)
        for _ in range(cuts):
            tail = self.snake.pop()
            self.effects.append(Effect(tail, delay=len(self.effects) * 0.075))

    def light_pulse(self):
        """Ieslēdz gaismu, ja pēc maksas čūska paliek vismaz minimālā garumā."""
        if self.is_finished() or self.light_on:
            return
        if len(self.snake) - LIGHT_COST < MIN_LENGTH:
            return
        self.lose(LIGHT_COST)
        self.light_on = True
        self.light_timer = LIGHT_TIME

    def is_lit(self, cell):
        """Vai šūna ir gaismas rādiusā ap galvu."""
        if not self.light_on:
            return False
        hx, hy = self.snake[0]
        x, y = cell
        return (x - hx) ** 2 + (y - hy) ** 2 <= LIGHT_RADIUS ** 2

    def update(self, dt):
        """Atjauno taimerus un, ja čūska tumsā, noņem punktus un garumu."""
        dt = max(0.0, dt)
        self.update_effects(dt)
        self.update_zones(dt)
        if self.is_finished():
            return
        self.update_dark(dt)  # Tumsa jāskaita pirms gaismas laika samazināšanas.
        self.update_light(dt)

    def update_effects(self, dt):
        """Virza nogriezto astes posmu animācijas."""
        for effect in self.effects:
            effect.age += dt
        self.effects = [e for e in self.effects if not e.is_done()]

    def update_zones(self, dt):
        """Pārslēdz tumšās zonas laikā un noņem veco pārejas zonu."""
        self.fade_timer = max(0.0, self.fade_timer - dt)
        if self.fade_timer == 0:
            self.old_dark_zones = set()
        if self.is_finished():
            return
        self.zone_timer += dt
        if self.zone_timer >= ZONE_INTERVAL:
            self.zone_timer %= ZONE_INTERVAL
            self.make_dark_zones()

    def update_light(self, dt):
        """Samazina gaismas laiku."""
        if self.light_on:
            self.light_timer = max(0.0, self.light_timer - dt)
            self.light_on = self.light_timer > 0

    def update_dark(self, dt):
        """Ja čūskas daļa ir tumsā un nav gaismā, noņem punktus un garumu."""
        dark_parts = [part for part in self.snake if part in self.dark_zones]
        if not dark_parts:
            self.dark_acc = 0.0
            return
        if all(self.is_lit(part) for part in dark_parts):
            return

        self.dark_acc += dt * DARK_DRAIN
        lost = int(self.dark_acc)
        self.dark_acc -= lost
        self.lose(lost)
        if len(self.snake) == MIN_LENGTH and self.score == MIN_SCORE:
            self.dark_acc = 0.0

    def step(self):
        """Pārvieto čūsku par vienu šūnu."""
        if self.is_finished():
            return
        if self.queue:
            self.direction = self.queue.pop(0)

        head = add(self.snake[0], self.direction)
        eating = head == self.apple
        # Ja čūska neēd, astes šūna pēc soļa atbrīvojas, tāpēc to neskaitām.
        body = self.snake if eating else self.snake[:-1]

        out = not (0 <= head[0] < self.width and 0 <= head[1] < self.height)
        if out or head in body:
            self.game_over = True
            return

        self.snake.insert(0, head)
        if eating:
            self.score += 1
            self.spawn_apple()
        else:
            self.snake.pop()

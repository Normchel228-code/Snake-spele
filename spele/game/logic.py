"""Spēles loģika: čūska, ābols, tumšās zonas un gaismas impulss."""

import random
from typing import NamedTuple

Cell = tuple[int, int]

# Virzieni kā pāri (x, y).
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

START_LENGTH = 2  # Sākuma garums.
MIN_LENGTH = 1  # Mazākais iespējamais garums.
MIN_SCORE = 0  # Mazākais iespējamais punktu skaits.
ZONE_FADE_TIME = 0.45  # Cik ilgi zona pāriet no vienas vietas uz otru.
LIGHT_COST = 3  # Cik punktus un garumu maksā gaismas impulss.
LIGHT_TIME = 4.0  # Cik ilgi gaisma deg.
LIGHT_RADIUS = 3  # Gaismas rādiuss šūnās.
LEVEL_BANNER_TIME = 1.8  # Cik ilgi redzams uzraksts par jaunu līmeni.


class Level(NamedTuple):
    """Viena līmeņa grūtības iestatījumi."""

    apples: int  # Cik ābolu kopā jāapēd, lai līmenis sāktos.
    step_time: float  # Sekundes starp čūskas soļiem (mazāk = ātrāk).
    zone_interval: float  # Cik sekundes starp tumšo zonu maiņām.
    dark_drain: float  # Cik ātri tumsa noņem punktus un garumu (vienības/s).


# Katrā līmenī čūska ir ātrāka, zonas mainās biežāk un tumsa kož stiprāk.
LEVELS = (
    Level(apples=0, step_time=0.135, zone_interval=7.0, dark_drain=1.5),
    Level(apples=6, step_time=0.115, zone_interval=6.0, dark_drain=2.0),
    Level(apples=14, step_time=0.095, zone_interval=5.0, dark_drain=2.5),
)

DIFFICULTY_MULTIPLIERS = {
    "easy": 0.5,
    "normal": 1.0,
    "medium": 1.0,
    "hard": 1.5,
}


def add(a: Cell, b: Cell) -> Cell:
    """Saskaita divus pārus."""
    return (a[0] + b[0], a[1] + b[1])


def is_opposite(a: Cell, b: Cell) -> bool:
    """Vai virzieni a un b ir pretēji."""
    return add(a, b) == (0, 0)


class Effect:
    """Nogrieztā astes posma animācija."""

    def __init__(self, cell: Cell, delay: float) -> None:
        # cell = kura šūna izzūd; delay = cik ilgi gaidīt, līdz animācija sākas.
        self.cell = cell
        self.age = 0.0
        self.delay = delay
        self.duration = 0.24

    def progress(self) -> float:
        """Animācijas progress no 0 līdz 1."""
        # Kad age ir mazāks par delay, animācija vēl nav sākusies.
        # Kad age ir lielāks par delay + duration, animācija beigusies.
        return max(0.0, min(1.0, (self.age - self.delay) / self.duration))

    def is_done(self) -> bool:
        """Vai animācija beigusies."""
        return self.age >= self.delay + self.duration


class Game:
    """Glabā spēles stāvokli."""

    def __init__(self, width: int = 34, height: int = 20,
                 difficulty: str = "normal") -> None:
        if width < 5 or height < 5:
            raise ValueError("Laukumam jābūt vismaz 5 x 5 šūnas lielam.")
        self.width = width
        self.height = height
        self.difficulty = "normal"
        self.set_difficulty(difficulty)
        self.reset()

    def reset(self) -> None:
        """Sāk spēli no jauna."""
        x, y = self.width // 2, self.height // 2
        # Galva ir pirmais elements. Tādēļ čūska sākas ar horizontālu ķermeni.
        self.snake: list[Cell] = [(x - i, y) for i in range(START_LENGTH)]
        self.score = 0
        self.apples_eaten = 0  # Līmeni nosaka ābolu skaits, nevis punkti.
        self.banner_timer = 0.0  # Cik ilgi vēl rāda “LEVEL n”.
        self.direction = RIGHT
        self.queue: list[Cell] = []  # Nākamie pagriezieni; katrs tiek gaidīti rindā.
        self.effects: list[Effect] = []  # Izgrieztas astes animācijas fragmenti.
        self.game_over = False
        self.game_won = False
        self.paused = False
        self.zone_timer = 0.0  # Laiks kopš pēdējās tumšo zonu maiņas.
        self.fade_timer = 0.0  # Laiks, ko aizņem zonu pāreja.
        self.dark_acc = 0.0  # Uzkrātā tumsas “rēķina” daļa.
        self.light_on = False
        self.light_timer = 0.0
        self.dark_zones: set[Cell] = set()  # Pašreizējās tumšās šūnas.
        self.old_dark_zones: set[Cell] = set()  # Vecās zonas pārejas laikā.
        self.apple: Cell = (-1, -1)
        self.spawn_apple()
        self.make_dark_zones(animate=False)

    def is_finished(self) -> bool:
        """Vai spēle beigusies (zaudējums vai uzvara)."""
        return self.game_over or self.game_won

    @property
    def level(self) -> int:
        """Pašreizējais līmenis (no 1)."""
        return max(i for i, level in enumerate(LEVELS, 1)
                   if self.apples_eaten >= level.apples)

    @property
    def difficulty_multiplier(self) -> float:
        """Grūtības ātruma koeficients: >1 = ātrāk, <1 = lēnāk."""
        key = self.difficulty.lower()
        if key == "medium":
            key = "normal"
        return DIFFICULTY_MULTIPLIERS.get(key, 1.0)

    def set_difficulty(self, difficulty: str) -> None:
        """Maina spēles grūtību, pieņemot easy/normal/hard."""
        normalized = (difficulty or "normal").lower()
        if normalized == "medium":
            normalized = "normal"
        if normalized not in DIFFICULTY_MULTIPLIERS:
            normalized = "normal"
        self.difficulty = normalized

    @property
    def config(self) -> Level:
        """Pašreizējā līmeņa iestatījumi ar grūtības ātruma koeficientu."""
        base = LEVELS[self.level - 1]
        speed = self.difficulty_multiplier
        return Level(
            apples=base.apples,
            step_time=base.step_time / speed,
            zone_interval=base.zone_interval / speed,
            dark_drain=base.dark_drain * speed,
        )

    def apples_to_next(self) -> int | None:
        """Cik ābolu līdz nākamajam līmenim (None, ja līmenis pēdējais)."""
        if self.level >= len(LEVELS):
            return None
        return LEVELS[self.level].apples - self.apples_eaten

    def toggle_pause(self) -> None:
        """Ieslēdz vai izslēdz pauzi (beigušai spēlei pauzes nav)."""
        if not self.is_finished():
            self.paused = not self.paused

    def fade_progress(self) -> float:
        """Cik tālu pāreja starp zonām ir (0 līdz 1)."""
        if self.fade_timer <= 0:
            return 1.0
        return 1.0 - self.fade_timer / ZONE_FADE_TIME

    def make_dark_zones(self, animate: bool = True) -> None:
        """Izveido jaunas tumšās zonas.

        Ābols vienmēr paliek gaišā vietā. Spēles sākumā gaišas paliek
        arī čūskas šūnas, lai tā nesāktu tumsā.
        """
        # keep_clear ir “sargātās” šūnas: tās nedrīkst kļūt tumšas.
        # Tāpat kā ābols un sākumā arī čūska paliek ārpus tumšajām zonām.
        keep_clear = {self.apple}
        if not animate:
            keep_clear.update(self.snake)
        zones: set[Cell] = set()
        target = int(self.width * self.height * random.uniform(0.14, 0.18))
        for _ in range(random.randint(4, 6)):
            # Katrs aplis ir viena tumša “sala”, kas izplatās pa elipsi.
            cx = random.randrange(self.width)
            cy = random.randrange(self.height)
            rx, ry = random.randint(2, 4), random.randint(2, 4)
            for x in range(max(0, cx - rx), min(self.width, cx + rx + 1)):
                for y in range(max(0, cy - ry), min(self.height, cy + ry + 1)):
                    inside = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
                    if inside and (x, y) not in keep_clear:
                        zones.add((x, y))
            if len(zones) >= target:
                break

        # Pārejas laikā glabājam arī vecās zonas, lai tās pamazām izzustu,
        # nevis pēkšņi pazustu, kas izskatītos neglīti.
        self.old_dark_zones = self.dark_zones if animate else set()
        self.dark_zones = zones
        self.fade_timer = ZONE_FADE_TIME if animate else 0.0

    def spawn_apple(self) -> None:
        """Novieto ābolu brīvā vietā, ja iespējams — gaišā."""
        # free = visas vietas, kas nav čūskas ķermenis.
        free = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in self.snake
        ]
        # light = vietas, kas nav tumšās zonās; ja tās ir, izvēlas tām tuvāk.
        light = [cell for cell in free if cell not in self.dark_zones]
        if free:
            self.apple = random.choice(light or free)
        else:
            self.apple = (-1, -1)
            self.game_won = True

    def turn(self, new_dir: Cell) -> None:
        """Pieņem jaunu virzienu, ja tas ir derīgs."""
        # Jo ātrāk spiedīs taustiņus, jo vairāk virzienu var uzkrāt rindā.
        # Bet mēs neļaujam ieiet pašreizējā virzienā atpakaļ vai uzkrāt pārāk daudz.
        if self.is_finished() or self.paused or len(self.queue) >= 2:
            return
        last = self.queue[-1] if self.queue else self.direction
        if new_dir != last and not is_opposite(new_dir, last):
            self.queue.append(new_dir)

    def lose(self, amount: int) -> None:
        """Atņem punktus un garumu, bet ne zem minimuma."""
        # amount = cik daudz “svara” tumsai vai gaismai ir jāņem no čūskas.
        # Katrs zaudētais posms rada vienu animācijas efektu astes izgriešanai.
        self.score = max(MIN_SCORE, self.score - amount)
        cuts = min(amount, len(self.snake) - MIN_LENGTH)
        for _ in range(cuts):
            tail = self.snake.pop()
            delay = len(self.effects) * 0.075
            self.effects.append(Effect(tail, delay=delay))

    def light_pulse(self) -> None:
        """Ieslēdz gaismu, ja pēc maksas čūska paliek vismaz minimālā."""
        # Gaisma ir “izņēmums” no tumšās zonas: tā īslaicīgi padara daļu no laukuma
        # drošu, bet maksā zaudētu garumu un punktus.
        if self.is_finished() or self.paused or self.light_on:
            return
        if len(self.snake) - LIGHT_COST < MIN_LENGTH:
            return
        self.lose(LIGHT_COST)
        self.light_on = True
        self.light_timer = LIGHT_TIME

    def is_lit(self, cell: Cell) -> bool:
        """Vai šūna ir gaismas rādiusā ap galvu."""
        # Pārbaudam, vai šūna atrodas galvas apkārtnē ar rādiusu LIGHT_RADIUS.
        # Matemātiski tas ir rādiusa aplis: (x - hx)^2 + (y - hy)^2 <= r^2.
        if not self.light_on:
            return False
        hx, hy = self.snake[0]
        x, y = cell
        return (x - hx) ** 2 + (y - hy) ** 2 <= LIGHT_RADIUS ** 2

    def update(self, dt: float) -> None:
        """Atjauno taimerus; ja čūska tumsā, noņem punktus un garumu."""
        if self.paused:
            return
        dt = max(0.0, dt)
        # Katram kadram samazina banneru, animācijas un gaismu.
        self.banner_timer = max(0.0, self.banner_timer - dt)
        self.update_effects(dt)
        self.update_zones(dt)
        if self.is_finished():
            return
        # Tumsa tiek skaitīta pirms gaismas samazināšanas, lai spēle reāli justos tikpat,
        # kā cilvēka redze: tumsā jūtams drudzis, nevis “gaisma nodziest pirms vērtējuma”.
        self.update_dark(dt)
        self.update_light(dt)

    def update_effects(self, dt: float) -> None:
        """Virza nogriezto astes posmu animācijas."""
        for effect in self.effects:
            effect.age += dt
        self.effects = [e for e in self.effects if not e.is_done()]

    def update_zones(self, dt: float) -> None:
        """Pārslēdz tumšās zonas laikā un noņem veco pārejas zonu."""
        # fade_timer rāda, cik ilgi pagājušās zonas vēl mirdz vai izzūd.
        self.fade_timer = max(0.0, self.fade_timer - dt)
        if self.fade_timer == 0:
            self.old_dark_zones = set()
        if self.is_finished():
            return
        self.zone_timer += dt
        interval = self.config.zone_interval
        if self.zone_timer >= interval:
            # Kad pagājis intervals, maina tumšo zonu komplektu un sāk jaunu pāreju.
            self.zone_timer %= interval
            self.make_dark_zones()

    def update_light(self, dt: float) -> None:
        """Samazina gaismas laiku."""
        if self.light_on:
            self.light_timer = max(0.0, self.light_timer - dt)
            self.light_on = self.light_timer > 0

    def update_dark(self, dt: float) -> None:
        """Ja čūskas daļa ir tumsā un nav gaismā, noņem punktus un garumu."""
        # dark_parts = visas čūskas šūnas, kas atrodas tumšajā zonā.
        dark_parts = [part for part in self.snake if part in self.dark_zones]
        if not dark_parts:
            self.dark_acc = 0.0
            return
        # Ja visas tumšās šūnas joprojām ir apgaismotas, nav jūtams zaudējums.
        if all(self.is_lit(part) for part in dark_parts):
            return

        self.dark_acc += dt * self.config.dark_drain
        lost = int(self.dark_acc)
        self.dark_acc -= lost
        self.lose(lost)
        if len(self.snake) == MIN_LENGTH and self.score == MIN_SCORE:
            self.dark_acc = 0.0

    def step(self) -> None:
        """Pārvieto čūsku par vienu šūnu."""
        # Kad vienkārši “soļo”, vispirms izvēlas pagriezienu no rindas, ja tāds ir.
        if self.is_finished() or self.paused:
            return
        if self.queue:
            self.direction = self.queue.pop(0)

        head = add(self.snake[0], self.direction)
        eating = head == self.apple
        # Ja čūska ēd, aste paliek pilnībā, jo zvērs pieaug.
        # Ja neēd, astes pēdējais posms pazūd kā parasts solis.
        body = self.snake if eating else self.snake[:-1]

        out = not (0 <= head[0] < self.width and 0 <= head[1] < self.height)
        if out or head in body:
            self.game_over = True
            return

        self.snake.insert(0, head)
        if eating:
            level_before = self.level
            self.score += 1
            self.apples_eaten += 1
            if self.level != level_before:
                self.banner_timer = LEVEL_BANNER_TIME
            self.spawn_apple()
        else:
            self.snake.pop()

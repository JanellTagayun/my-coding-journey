"""
╔══════════════════════════════════════╗
║         NEON SNAKE  🐍               ║
║   Feature-rich Python Snake Game     ║
║   Requires: pip install pygame       ║
╚══════════════════════════════════════╝

Controls:
  Arrow Keys / WASD  → Move snake
  P                  → Pause
  R                  → Restart (game over screen)
  ESC                → Quit
"""

import pygame
import random
import sys
import math
import time

# ─── CONSTANTS ──────────────────────────────────────────────────────────────

TILE   = 20          # size of each grid cell in pixels
COLS   = 30          # grid columns
ROWS   = 26          # grid rows
W      = COLS * TILE # 600
H      = ROWS * TILE # 520
HUD    = 60          # HUD bar height
FPS    = 60

# Colours  (R, G, B)
BG          = (8,   10,  20)
GRID_COL    = (14,  18,  34)
SNAKE_HEAD  = (0,   255, 180)
SNAKE_BODY  = (0,   200, 130)
SNAKE_TAIL  = (0,   140,  90)
FOOD_COL    = (255,  60,  90)
BONUS_COL   = (255, 200,   0)
SHIELD_COL  = (80,  160, 255)
WALL_COL    = (50,   60, 100)
TEXT_COL    = (200, 220, 255)
DIM_COL     = (60,   70, 110)
NEON_CYAN   = (0,   255, 255)
NEON_PINK   = (255,  50, 180)
NEON_GREEN  = (50,  255, 100)

FONT_PATH   = None   # uses system default; swap in a TTF path if desired

# Directions
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# ─── HELPERS ────────────────────────────────────────────────────────────────

def cell_rect(cx, cy):
    return pygame.Rect(cx * TILE, HUD + cy * TILE, TILE, TILE)

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def glow_surface(radius, color, alpha=160):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = int(alpha * (1 - r / radius) ** 1.5)
        pygame.draw.circle(surf, (*color, a), (radius, radius), r)
    return surf

# ─── PARTICLE SYSTEM ────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 5)
        self.x  = x
        self.y  = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.col = color
        self.life = random.uniform(0.4, 1.0)
        self.max_life = self.life
        self.size = random.uniform(2, 5)

    def update(self, dt):
        self.x  += self.vx * dt * 60
        self.y  += self.vy * dt * 60
        self.vy += 50 * dt        # gravity
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        t     = self.life / self.max_life
        alpha = int(255 * t)
        r     = max(1, int(self.size * t))
        col   = (*self.col, alpha)
        s     = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (r, r), r)
        surf.blit(s, (int(self.x) - r, int(self.y) - r))


def burst(px, py, color, n=20):
    return [Particle(px, py, color) for _ in range(n)]

# ─── FOOD ────────────────────────────────────────────────────────────────────

class Food:
    def __init__(self, snake_cells, walls):
        self.pos   = self._spawn(snake_cells, walls)
        self.pulse = 0.0
        self.kind  = "normal"   # normal | bonus | shield
        self.timer = None       # seconds remaining for specials

    def _spawn(self, snake_cells, walls):
        occupied = set(snake_cells) | set(walls)
        while True:
            p = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if p not in occupied:
                return p

    def update(self, dt):
        self.pulse = (self.pulse + dt * 4) % math.tau
        if self.timer is not None:
            self.timer -= dt
            if self.timer <= 0:
                return False     # special expired
        return True

    @property
    def color(self):
        return {
            "normal": FOOD_COL,
            "bonus":  BONUS_COL,
            "shield": SHIELD_COL,
        }[self.kind]

    @property
    def points(self):
        return {"normal": 10, "bonus": 30, "shield": 15}[self.kind]

    def draw(self, surf):
        cx, cy = self.pos
        rx, ry = cx * TILE + TILE // 2, HUD + cy * TILE + TILE // 2
        pulse_r = int(TILE * 0.38 + math.sin(self.pulse) * 3)
        col = self.color

        # glow
        g = glow_surface(TILE, col, 100)
        surf.blit(g, (rx - TILE, ry - TILE))

        # body
        pygame.draw.circle(surf, col, (rx, ry), pulse_r)
        pygame.draw.circle(surf, (255, 255, 255), (rx - pulse_r // 3, ry - pulse_r // 3), max(2, pulse_r // 4))

        # shield icon
        if self.kind == "shield":
            pygame.draw.circle(surf, (255, 255, 255), (rx, ry), pulse_r, 2)

        # bonus star dots
        if self.kind == "bonus":
            for i in range(5):
                a = math.tau * i / 5 + self.pulse * 0.5
                sx = int(rx + math.cos(a) * (pulse_r + 5))
                sy = int(ry + math.sin(a) * (pulse_r + 5))
                pygame.draw.circle(surf, col, (sx, sy), 2)

# ─── SNAKE ───────────────────────────────────────────────────────────────────

class Snake:
    def __init__(self):
        sx, sy    = COLS // 2, ROWS // 2
        self.body = [(sx, sy), (sx - 1, sy), (sx - 2, sy)]
        self.dir  = RIGHT
        self.next_dir = RIGHT
        self.grow_pending = 0
        self.shielded = False
        self.shield_timer = 0.0

    @property
    def head(self):
        return self.body[0]

    @property
    def cells(self):
        return self.body

    def set_dir(self, d):
        # forbid 180° reversals
        if (d[0] + self.dir[0], d[1] + self.dir[1]) != (0, 0):
            self.next_dir = d

    def step(self):
        self.dir = self.next_dir
        hx, hy   = self.head
        new_head = ((hx + self.dir[0]) % COLS, (hy + self.dir[1]) % ROWS)
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def update(self, dt):
        if self.shielded:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shielded = False

    def grow(self, n=1):
        self.grow_pending += n

    def activate_shield(self, duration=8.0):
        self.shielded = True
        self.shield_timer = duration

    def self_collision(self):
        return self.head in self.body[1:]

    def draw(self, surf, t_frac):
        n = len(self.body)
        for i, (cx, cy) in enumerate(self.body):
            r = cell_rect(cx, cy)
            # gradient from head to tail
            frac  = i / max(n - 1, 1)
            col   = lerp_color(SNAKE_HEAD if i == 0 else SNAKE_BODY, SNAKE_TAIL, frac)
            inner = r.inflate(-4, -4)
            pygame.draw.rect(surf, col, inner, border_radius=6)

            # head eyes
            if i == 0:
                ex = r.centerx + self.dir[0] * 4
                ey = r.centery + self.dir[1] * 4
                perp = (-self.dir[1], self.dir[0])
                for sign in (-1, 1):
                    ox = ex + perp[0] * 4 * sign
                    oy = ey + perp[1] * 4 * sign
                    pygame.draw.circle(surf, (10, 10, 20), (ox, oy), 3)
                    pygame.draw.circle(surf, (255, 255, 255), (ox, oy), 1)

        # shield aura
        if self.shielded:
            hx, hy = self.head
            rx = hx * TILE + TILE // 2
            ry = HUD + hy * TILE + TILE // 2
            pulse = int(TILE * 0.8 + math.sin(t_frac * 6) * 4)
            aura  = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
            alpha = int(60 + 40 * math.sin(t_frac * 6))
            pygame.draw.circle(aura, (*SHIELD_COL, alpha), (pulse, pulse), pulse)
            surf.blit(aura, (rx - pulse, ry - pulse))

# ─── WALLS ───────────────────────────────────────────────────────────────────

def generate_walls(level):
    """Generate wall cells based on current level."""
    walls = set()
    if level < 2:
        return walls
    # Border walls for higher levels
    if level >= 3:
        for x in range(COLS):
            walls.add((x, 0))
            walls.add((x, ROWS - 1))
        for y in range(ROWS):
            walls.add((0, y))
            walls.add((COLS - 1, y))
    # Interior obstacles
    cx, cy = COLS // 2, ROWS // 2
    if level >= 2:
        for d in range(-3, 4):
            walls.add((cx + d, ROWS // 4))
            walls.add((cx + d, 3 * ROWS // 4))
    if level >= 4:
        for d in range(-2, 3):
            walls.add((COLS // 4, cy + d))
            walls.add((3 * COLS // 4, cy + d))
    return walls

# ─── FLOATING SCORE TEXT ─────────────────────────────────────────────────────

class FloatText:
    def __init__(self, text, x, y, color, font):
        self.text  = text
        self.x, self.y = float(x), float(y)
        self.color = color
        self.life  = 1.2
        self.font  = font

    def update(self, dt):
        self.y   -= 40 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        alpha = int(255 * min(1.0, self.life / 0.4))
        s = self.font.render(self.text, True, self.color)
        s.set_alpha(alpha)
        surf.blit(s, (int(self.x) - s.get_width() // 2, int(self.y)))

# ─── GAME ────────────────────────────────────────────────────────────────────

class Game:
    SPEEDS = {1: 7, 2: 9, 3: 11, 4: 13, 5: 16}   # steps/sec per level

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🐍  NEON SNAKE")
        self.screen   = pygame.display.set_mode((W, H + HUD))
        self.clock    = pygame.time.Clock()

        self.font_big  = pygame.font.SysFont("Consolas", 36, bold=True)
        self.font_med  = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_sm   = pygame.font.SysFont("Consolas", 15)

        # pre-render background grid
        self.grid_surf = self._make_grid()

        self.state = "menu"    # menu | playing | paused | dead
        self._new_game()

    # ── setup ────────────────────────────────────────────────────────────────

    def _new_game(self):
        self.score      = 0
        self.hi_score   = getattr(self, "hi_score", 0)
        self.level      = 1
        self.lives      = 3
        self.step_acc   = 0.0
        self.total_t    = 0.0
        self.walls      = generate_walls(self.level)
        self.snake      = Snake()
        self.food       = self._new_food()
        self.bonus_food = None
        self.bonus_timer = 0.0
        self.particles  = []
        self.float_texts = []
        self.combo      = 0
        self.combo_timer = 0.0

    def _new_food(self):
        return Food(self.snake.cells, self.walls)

    def _spawn_bonus(self, kind):
        f = Food(self.snake.cells, self.walls | {self.food.pos})
        f.kind  = kind
        f.timer = 8.0
        return f

    def _make_grid(self):
        s = pygame.Surface((W, H))
        s.fill(BG)
        for x in range(0, W, TILE):
            pygame.draw.line(s, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, TILE):
            pygame.draw.line(s, GRID_COL, (0, y), (W, y))
        return s

    # ── main loop ────────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()

            if self.state == "playing":
                self._update(dt)

            self._draw()
            pygame.display.flip()

    # ── events ───────────────────────────────────────────────────────────────

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                k = e.key

                if self.state == "menu":
                    if k in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "playing"

                elif self.state == "dead":
                    if k == pygame.K_r:
                        self._new_game()
                        self.state = "playing"

                elif self.state == "paused":
                    if k == pygame.K_p:
                        self.state = "playing"

                elif self.state == "playing":
                    dir_map = {
                        pygame.K_UP:    UP,    pygame.K_w: UP,
                        pygame.K_DOWN:  DOWN,  pygame.K_s: DOWN,
                        pygame.K_LEFT:  LEFT,  pygame.K_a: LEFT,
                        pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
                    }
                    if k in dir_map:
                        self.snake.set_dir(dir_map[k])
                    elif k == pygame.K_p:
                        self.state = "paused"

                if k == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

    # ── update ───────────────────────────────────────────────────────────────

    def _update(self, dt):
        self.total_t  += dt
        self.step_acc += dt
        self.snake.update(dt)

        # combo decay
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        # particles & float texts
        self.particles   = [p for p in self.particles   if p.update(dt)]
        self.float_texts = [f for f in self.float_texts if f.update(dt)]

        # bonus food expiry
        if self.bonus_food:
            if not self.bonus_food.update(dt):
                self.bonus_food = None
            else:
                self.bonus_food.update(0)   # pulse only

        # bonus food spawn timer
        self.bonus_timer -= dt
        if self.bonus_timer <= 0 and self.bonus_food is None:
            kind = random.choice(["bonus", "shield"])
            self.bonus_food  = self._spawn_bonus(kind)
            self.bonus_timer = random.uniform(15, 25)

        # step the snake
        speed   = self.SPEEDS.get(self.level, 16)
        step_dt = 1.0 / speed
        while self.step_acc >= step_dt:
            self.step_acc -= step_dt
            self._step()

        self.food.update(dt)

    def _step(self):
        self.snake.step()
        hx, hy = self.snake.head

        # wall collision
        if (hx, hy) in self.walls:
            self._die()
            return

        # self collision
        if self.snake.self_collision():
            if self.snake.shielded:
                self.snake.shielded = False   # shield absorbs
                self._emit_burst(hx, hy, SHIELD_COL)
            else:
                self._die()
                return

        # eat food
        if (hx, hy) == self.food.pos:
            self._eat(self.food)
            self.food = self._new_food()

        # eat bonus food
        if self.bonus_food and (hx, hy) == self.bonus_food.pos:
            self._eat(self.bonus_food)
            self.bonus_food = None

    def _eat(self, food):
        hx, hy = self.snake.head
        self.combo += 1
        self.combo_timer = 3.0
        multiplier = min(self.combo, 5)
        pts = food.points * multiplier

        self.score += pts
        self.hi_score = max(self.hi_score, self.score)

        grow = 3 if food.kind == "bonus" else 1
        self.snake.grow(grow)

        if food.kind == "shield":
            self.snake.activate_shield()

        px = hx * TILE + TILE // 2
        py = HUD + hy * TILE + TILE // 2
        self._emit_burst(hx, hy, food.color)

        label = f"+{pts}"
        if multiplier > 1:
            label += f"  x{multiplier}!"
        self.float_texts.append(FloatText(label, px, py - 10, food.color, self.font_med))

        # level up
        new_level = min(5, 1 + self.score // 200)
        if new_level > self.level:
            self.level = new_level
            self.walls = generate_walls(self.level)
            self.grid_surf = self._make_grid_with_walls()
            self.float_texts.append(
                FloatText(f"LEVEL {self.level}!", W // 2, H // 2 + HUD - 20,
                          NEON_CYAN, self.font_big)
            )

    def _make_grid_with_walls(self):
        s = self._make_grid()
        for wx, wy in self.walls:
            r = pygame.Rect(wx * TILE, wy * TILE, TILE, TILE)
            pygame.draw.rect(s, WALL_COL, r)
            pygame.draw.rect(s, (70, 80, 130), r, 1)
        return s

    def _die(self):
        hx, hy = self.snake.head
        self._emit_burst(hx, hy, SNAKE_HEAD, n=40)
        self.lives -= 1
        if self.lives <= 0:
            self.state = "dead"
        else:
            # respawn with shorter snake
            sx, sy    = COLS // 2, ROWS // 2
            self.snake.body = [(sx, sy), (sx - 1, sy), (sx - 2, sy)]
            self.snake.dir  = RIGHT
            self.snake.next_dir = RIGHT
            self.snake.shielded = False

    def _emit_burst(self, cx, cy, color, n=20):
        px = cx * TILE + TILE // 2
        py = HUD + cy * TILE + TILE // 2
        self.particles.extend(burst(px, py, color, n))

    # ── drawing ──────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(BG)

        if self.state == "menu":
            self._draw_menu()
            return

        # ── HUD ──────────────────────────────────────────────────────────────
        self._draw_hud()

        # ── game area ────────────────────────────────────────────────────────
        game_surf = pygame.Surface((W, H))
        game_surf.blit(self.grid_surf, (0, 0))

        # walls (already drawn into grid_surf if level > 1)
        for wx, wy in self.walls:
            r = pygame.Rect(wx * TILE, wy * TILE, TILE, TILE)
            pygame.draw.rect(game_surf, WALL_COL, r)
            pygame.draw.rect(game_surf, (70, 80, 130), r, 1)

        # food
        food_surf = pygame.Surface((W, H + HUD), pygame.SRCALPHA)
        self.food.draw(food_surf)
        if self.bonus_food:
            self.bonus_food.update(0)
            self.bonus_food.draw(food_surf)

        # snake
        self.snake.draw(game_surf, self.total_t)

        self.screen.blit(game_surf, (0, HUD))
        self.screen.blit(food_surf, (0, 0))

        # particles
        for p in self.particles:
            p.draw(self.screen)

        # float texts
        for f in self.float_texts:
            f.draw(self.screen)

        # overlays
        if self.state == "paused":
            self._draw_overlay("PAUSED", "Press P to resume", NEON_CYAN)
        elif self.state == "dead":
            self._draw_overlay(
                "GAME OVER",
                f"Score: {self.score}   Hi: {self.hi_score}   Press R",
                NEON_PINK,
            )

    def _draw_hud(self):
        hud = pygame.Surface((W, HUD), pygame.SRCALPHA)
        hud.fill((12, 15, 30, 220))
        self.screen.blit(hud, (0, 0))

        # score
        sc = self.font_big.render(f"{self.score:06d}", True, NEON_CYAN)
        self.screen.blit(sc, (16, 10))

        # hi-score
        hi = self.font_sm.render(f"BEST {self.hi_score:06d}", True, DIM_COL)
        self.screen.blit(hi, (16, 42))

        # level
        lv = self.font_med.render(f"LVL {self.level}", True, NEON_GREEN)
        self.screen.blit(lv, (W // 2 - lv.get_width() // 2, 8))

        # lives (hearts)
        for i in range(3):
            col = NEON_PINK if i < self.lives else DIM_COL
            pygame.draw.circle(self.screen, col, (W - 90 + i * 28, 20), 9)
            t = self.font_sm.render("♥", True, col)
            self.screen.blit(t, (W - 100 + i * 28, 12))

        # shield indicator
        if self.snake.shielded:
            st = self.font_sm.render(f"🛡 {self.snake.shield_timer:.1f}s", True, SHIELD_COL)
            self.screen.blit(st, (W - 110, 40))

        # combo
        if self.combo > 1:
            ct = self.font_med.render(f"COMBO x{min(self.combo, 5)}", True, BONUS_COL)
            self.screen.blit(ct, (W // 2 - ct.get_width() // 2, 34))

        # divider line
        pygame.draw.line(self.screen, (30, 40, 80), (0, HUD - 1), (W, HUD - 1), 2)

    def _draw_overlay(self, title, subtitle, color):
        overlay = pygame.Surface((W, H + HUD), pygame.SRCALPHA)
        overlay.fill((5, 8, 18, 180))
        self.screen.blit(overlay, (0, 0))

        t1 = self.font_big.render(title, True, color)
        t2 = self.font_med.render(subtitle, True, TEXT_COL)
        cx = W // 2
        cy = (H + HUD) // 2
        self.screen.blit(t1, (cx - t1.get_width() // 2, cy - 40))
        self.screen.blit(t2, (cx - t2.get_width() // 2, cy + 10))

        # pulsing border
        a = int(128 + 127 * math.sin(self.total_t * 3))
        border = pygame.Surface((W, H + HUD), pygame.SRCALPHA)
        pygame.draw.rect(border, (*color, a), (0, 0, W, H + HUD), 4)
        self.screen.blit(border, (0, 0))

    def _draw_menu(self):
        self.total_t += 0.016
        self.screen.fill(BG)

        # animated title
        title_colors = [NEON_CYAN, NEON_GREEN, NEON_PINK]
        title = "NEON SNAKE"
        for i, ch in enumerate(title):
            col = title_colors[i % len(title_colors)]
            t = self.font_big.render(ch, True, col)
            ox = int(math.sin(self.total_t * 2 + i * 0.5) * 4)
            self.screen.blit(t, (W // 2 - len(title) * 18 + i * 26 + ox,
                                 H // 2 - 100 + HUD // 2))

        lines = [
            ("Arrow keys / WASD  →  Move",   TEXT_COL),
            ("P                  →  Pause",   TEXT_COL),
            ("Eat 🟡 for bonus points",        BONUS_COL),
            ("Eat 🔵 for a shield",            SHIELD_COL),
            ("Build combos for multipliers!",  NEON_GREEN),
            ("",                               TEXT_COL),
            ("Press ENTER to start",           NEON_CYAN),
        ]
        for i, (line, col) in enumerate(lines):
            t = self.font_sm.render(line, True, col)
            self.screen.blit(t, (W // 2 - t.get_width() // 2,
                                 H // 2 - 20 + HUD // 2 + i * 24))

        # hi score
        hs = self.font_med.render(f"BEST  {self.hi_score:06d}", True, DIM_COL)
        self.screen.blit(hs, (W // 2 - hs.get_width() // 2, H + HUD - 40))


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    game = Game()
    game.run()
"""
╔══════════════════════════════════════════╗
║         TURBO RACER  🏎️                  ║
║   Pseudo-3D Racing Game in Python        ║
║   Requires: pip install pygame-ce        ║
╚══════════════════════════════════════════╝

Controls:
  LEFT / RIGHT arrow  → Steer
  UP arrow            → Accelerate
  DOWN arrow          → Brake
  ESC                 → Quit
"""

import pygame
import math
import random
import sys

# ─── CONSTANTS ───────────────────────────────────────────────────────────────

W, H       = 800, 600
FPS        = 60
DRAW_DIST  = 200       # how many road segments to draw
SEG_LEN    = 200       # 3D length of each segment
ROAD_W     = 2000      # world-space road width
CAM_DEPTH  = 0.84      # camera field of view
NUM_SEGS   = 1600      # total track length (loops)

# Colours
SKY_TOP    = (10,  10,  40)
SKY_BOT    = (30,  60, 120)
HILL_COL   = (20,  80,  40)
HILL2_COL  = (15,  60,  30)

ROAD_DARK  = (40,  40,  45)
ROAD_LIGHT = (50,  50,  55)
LANE_COL   = (220, 220, 220)
RUMBLE_D   = (160,  30,  30)
RUMBLE_L   = (220, 220, 220)
GRASS_D    = (20,  100,  40)
GRASS_L    = (22,  110,  44)

HUD_BG     = (8,   10,  20)
NEON_RED   = (255,  40,  60)
NEON_YEL   = (255, 210,   0)
NEON_CYAN  = (0,   230, 255)
NEON_GRN   = (50,  255, 120)
TEXT_COL   = (200, 220, 255)
DIM_COL    = (60,   70, 110)
WHITE      = (255, 255, 255)

# ─── TRACK BUILDER ───────────────────────────────────────────────────────────

def build_track():
    """Returns list of dicts with curve, hill, color_index."""
    segs = []

    def add(n, curve=0.0, hill=0.0):
        for _ in range(n):
            segs.append({"curve": curve, "hill": hill,
                         "idx": len(segs)})

    # straight
    add(80)
    # gentle left
    add(60, curve=-2.0)
    add(40)
    # hill up
    add(60, hill=100)
    add(40, curve=1.5, hill=50)
    # sharp right
    add(50, curve=3.5)
    add(30)
    # downhill
    add(60, hill=-120)
    add(50, curve=-2.5, hill=-60)
    add(40)
    # S-curve
    add(40, curve=2.0)
    add(40, curve=-2.0)
    add(60)
    # long straight into finish
    add(80)

    # pad/loop
    while len(segs) < NUM_SEGS:
        segs += segs[:min(len(segs), NUM_SEGS - len(segs))]

    return segs[:NUM_SEGS]

# ─── PROJECTION ──────────────────────────────────────────────────────────────

def project(cam_x, cam_y, cam_z, world_x, world_y, world_z):
    """Project a world point to screen space. Returns (sx, sy, sw) or None."""
    tz = world_z - cam_z
    if tz <= 0:
        return None
    scale = CAM_DEPTH / tz
    sx = (1 + scale * (world_x - cam_x)) * W / 2
    sy = (1 - scale * (world_y - cam_y)) * H / 2
    sw = scale * ROAD_W * W / 2
    return sx, sy, sw

# ─── DRAW HELPERS ─────────────────────────────────────────────────────────────

def draw_rect(surf, color, x1, y1, w1, x2, y2, w2):
    """Draw a trapezoid road segment slice."""
    pts = [
        (x1 - w1, y1), (x1 + w1, y1),
        (x2 + w2, y2), (x2 - w2, y2),
    ]
    if abs(y1 - y2) < 1:
        return
    pygame.draw.polygon(surf, color, pts)

def draw_segment(surf, seg_idx, x1, y1, w1, x2, y2, w2, grass_w=6):
    alt = (seg_idx // 4) % 2    # alternating colour

    # grass
    grass_col = GRASS_D if alt else GRASS_L
    draw_rect(surf, grass_col, x1, y1, w1 * grass_w, x2, y2, w2 * grass_w)

    # rumble strips
    rum = RUMBLE_D if alt else RUMBLE_L
    draw_rect(surf, rum, x1, y1, w1 * 1.25, x2, y2, w2 * 1.25)

    # road
    road = ROAD_DARK if alt else ROAD_LIGHT
    draw_rect(surf, road, x1, y1, w1, x2, y2, w2)

    # centre dashes
    if alt:
        lw = w1 * 0.04
        draw_rect(surf, LANE_COL, x1, y1, lw, x2, y2, w2 * 0.04)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ─── OPPONENT CAR ─────────────────────────────────────────────────────────────

class Opponent:
    COLORS = [NEON_RED, NEON_YEL, (100, 200, 255), (200, 100, 255)]

    def __init__(self, track_len):
        self.pos    = random.uniform(0, track_len)
        self.lane_x = random.uniform(-0.6, 0.6)  # -1..1 road offset
        self.speed  = random.uniform(60, 110)
        self.color  = random.choice(self.COLORS)
        self.track_len = track_len

    def update(self, dt):
        self.pos = (self.pos + self.speed * dt) % self.track_len

    def draw(self, surf, sx, sy, sw, scale):
        if sw < 10:
            return
        cw = int(sw * 0.6)
        ch = int(cw * 0.55)
        cx = int(sx + self.lane_x * sw)
        cy = int(sy - ch // 2)

        if cx < -cw or cx > W + cw or cy < 0 or cy > H:
            return

        # body
        body_r = pygame.Rect(cx - cw // 2, cy, cw, ch)
        pygame.draw.rect(surf, self.color, body_r, border_radius=max(2, cw // 8))

        # roof
        roof_w = int(cw * 0.55)
        roof_h = int(ch * 0.45)
        roof_r = pygame.Rect(cx - roof_w // 2, cy - roof_h + 2, roof_w, roof_h)
        roof_c = lerp_color(self.color, (200, 200, 220), 0.4)
        pygame.draw.rect(surf, roof_c, roof_r, border_radius=max(2, roof_w // 6))

        # wheels
        wh = max(3, int(ch * 0.28))
        ww = max(4, int(cw * 0.22))
        for wx_off in (-cw // 2 + ww // 2, cw // 2 - ww // 2):
            wr = pygame.Rect(cx + wx_off - ww // 2, cy + ch - wh, ww, wh)
            pygame.draw.rect(surf, (20, 20, 20), wr, border_radius=2)

        # headlights
        hl_size = max(2, int(cw * 0.1))
        for hx_off in (-cw // 3, cw // 3):
            pygame.draw.circle(surf, (255, 240, 180),
                               (cx + hx_off, cy + ch - hl_size - 1), hl_size)

# ─── PLAYER CAR ──────────────────────────────────────────────────────────────

class PlayerCar:
    def __init__(self):
        self.x       = 0.0    # -1..1 road position
        self.speed   = 0.0    # current speed (units/sec)
        self.max_spd = 280.0
        self.accel   = 140.0
        self.brake   = 220.0
        self.friction= 80.0
        self.steer   = 3.5
        self.tilt    = 0.0    # visual lean
        self.wobble  = 0.0

    def update(self, keys, dt, curve):
        # acceleration
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + self.accel * dt, self.max_spd)
        elif keys[pygame.K_DOWN]:
            self.speed = max(0, self.speed - self.brake * dt)
        else:
            self.speed = max(0, self.speed - self.friction * dt)

        # steering
        steer_amt = self.steer * (self.speed / self.max_spd) * dt
        target_tilt = 0.0
        if keys[pygame.K_LEFT]:
            self.x     -= steer_amt
            target_tilt = -1.0
        if keys[pygame.K_RIGHT]:
            self.x     += steer_amt
            target_tilt =  1.0

        self.tilt = lerp(self.tilt, target_tilt, 8 * dt)

        # road curve pushes car
        self.x -= curve * 0.0003 * self.speed * dt

        # clamp (off-road slows)
        if abs(self.x) > 1.0:
            self.speed *= 0.97
            self.x = max(-1.4, min(1.4, self.x))

        # wobble when off-road
        if abs(self.x) > 1.0:
            self.wobble = random.uniform(-0.01, 0.01)
        else:
            self.wobble = lerp(self.wobble, 0, 10 * dt)

    def draw(self, surf, tilt_extra=0.0):
        cx, cy = W // 2, H - 80
        cw, ch = 120, 56

        # shadow
        shadow = pygame.Surface((cw + 20, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())
        surf.blit(shadow, (cx - (cw + 20) // 2, cy + ch - 4))

        lean = int((self.tilt + tilt_extra + self.wobble) * 8)

        # body
        body_pts = [
            (cx - cw // 2 + lean, cy + ch),
            (cx + cw // 2 + lean, cy + ch),
            (cx + cw // 2 - lean, cy),
            (cx - cw // 2 - lean, cy),
        ]
        pygame.draw.polygon(surf, NEON_RED, body_pts)

        # roof
        roof_w, roof_h = 72, 30
        roof_pts = [
            (cx - roof_w // 2 - lean, cy),
            (cx + roof_w // 2 - lean, cy),
            (cx + roof_w // 2 + lean, cy - roof_h),
            (cx - roof_w // 2 + lean, cy - roof_h),
        ]
        pygame.draw.polygon(surf, (220, 50, 70), roof_pts)

        # windshield
        ws_pts = [
            (cx - roof_w // 2 + 8 - lean, cy - 4),
            (cx + roof_w // 2 - 8 - lean, cy - 4),
            (cx + roof_w // 2 - 12 + lean, cy - roof_h + 4),
            (cx - roof_w // 2 + 12 + lean, cy - roof_h + 4),
        ]
        pygame.draw.polygon(surf, (100, 180, 220), ws_pts)

        # wheels
        wheel_color = (20, 20, 20)
        rim_color   = (180, 180, 200)
        for wx, wy, ww, wh in [
            (cx - cw // 2 - 6 + lean, cy + 10, 22, 28),
            (cx + cw // 2 - 16 + lean, cy + 10, 22, 28),
            (cx - cw // 2 + 2 + lean, cy + ch - 20, 22, 24),
            (cx + cw // 2 - 24 + lean, cy + ch - 20, 22, 24),
        ]:
            pygame.draw.ellipse(surf, wheel_color, (wx, wy, ww, wh))
            pygame.draw.ellipse(surf, rim_color,   (wx + 4, wy + 4, ww - 8, wh - 8))

        # headlights
        hl_y = cy + ch - 8
        for hx in (cx - cw // 2 + 6, cx + cw // 2 - 22):
            pygame.draw.rect(surf, (255, 240, 150), (hx + lean, hl_y, 16, 8), border_radius=2)

        # spoiler
        sp_pts = [
            (cx - 44 - lean, cy - roof_h - 2),
            (cx + 44 - lean, cy - roof_h - 2),
            (cx + 38 + lean, cy - roof_h - 8),
            (cx - 38 + lean, cy - roof_h - 8),
        ]
        pygame.draw.polygon(surf, (180, 30, 50), sp_pts)

# ─── PARTICLE / SPEED LINES ──────────────────────────────────────────────────

class SpeedLine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x    = random.uniform(0, W)
        self.y    = random.uniform(H * 0.3, H * 0.8)
        self.len  = random.uniform(20, 80)
        self.spd  = random.uniform(8, 20)
        self.alpha= random.randint(40, 120)

    def update(self, speed_frac):
        self.x -= self.spd * speed_frac * 3
        if self.x + self.len < 0:
            self.reset()
            self.x = W + self.len

    def draw(self, surf, speed_frac):
        if speed_frac < 0.4:
            return
        a = int(self.alpha * speed_frac)
        s = pygame.Surface((int(self.len), 2), pygame.SRCALPHA)
        s.fill((255, 255, 255, a))
        surf.blit(s, (int(self.x), int(self.y)))

# ─── GAME ────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((W, H))
        pygame.display.set_caption("🏎️  TURBO RACER")
        self.clock   = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("Consolas", 38, bold=True)
        self.font_med = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_sm  = pygame.font.SysFont("Consolas", 15)

        self.track    = build_track()
        self.track_len= len(self.track) * SEG_LEN

        self.player   = PlayerCar()
        self.cam_pos  = 0.0   # position along track (world units)
        self.cam_h    = 1000  # camera height

        self.opponents = [Opponent(self.track_len) for _ in range(6)]
        self.speed_lines = [SpeedLine() for _ in range(30)]

        self.state    = "menu"
        self.lap      = 1
        self.max_laps = 3
        self.distance = 0.0
        self.best_lap = None
        self.lap_start= 0.0
        self.total_t  = 0.0
        self.score    = 0
        self.rank     = 7

        # sky gradient surface
        self.sky = self._make_sky()

    def _make_sky(self):
        s = pygame.Surface((W, H // 2))
        for y in range(H // 2):
            t   = y / (H // 2)
            col = lerp_color(SKY_TOP, SKY_BOT, t)
            pygame.draw.line(s, col, (0, y), (W, y))
        return s

    # ── main loop ────────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self._handle_events()
            if self.state == "playing":
                self._update(dt)
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if self.state in ("menu", "finish") and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._reset()
                    self.state = "playing"

    def _reset(self):
        self.player   = PlayerCar()
        self.cam_pos  = 0.0
        self.distance = 0.0
        self.lap      = 1
        self.lap_start= 0.0
        self.total_t  = 0.0
        self.score    = 0
        self.opponents = [Opponent(self.track_len) for _ in range(6)]

    # ── update ───────────────────────────────────────────────────────────────

    def _update(self, dt):
        self.total_t += dt
        keys = pygame.key.get_pressed()

        # get curve at player position
        seg_idx = int(self.cam_pos / SEG_LEN) % len(self.track)
        curve   = self.track[seg_idx]["curve"]

        self.player.update(keys, dt, curve)

        # advance camera
        self.cam_pos  += self.player.speed * dt
        self.distance += self.player.speed * dt

        # lap detection
        if self.cam_pos >= self.track_len:
            self.cam_pos -= self.track_len
            lap_time = self.total_t - self.lap_start
            if self.best_lap is None or lap_time < self.best_lap:
                self.best_lap = lap_time
            self.lap_start = self.total_t
            self.lap += 1
            if self.lap > self.max_laps:
                self.state = "finish"
                return

        # update opponents
        for opp in self.opponents:
            opp.update(dt)

        # speed lines
        spd_frac = self.player.speed / self.player.max_spd
        for sl in self.speed_lines:
            sl.update(spd_frac)

        # rank (based on position vs opponents)
        self.rank = 1
        for opp in self.opponents:
            if opp.pos > self.cam_pos:
                self.rank += 1

        self.score = int(self.distance / 10)

    # ── draw ─────────────────────────────────────────────────────────────────

    def _draw(self):
        if self.state == "menu":
            self._draw_menu(); return

        self.screen.fill((0, 0, 0))

        # sky
        spd_frac = self.player.speed / self.player.max_spd
        horizon_shift = int(30 * spd_frac)
        self.screen.blit(self.sky, (0, -horizon_shift))

        # hills (simple sine wave silhouette)
        self._draw_hills()

        # road
        self._draw_road()

        # player car
        self.player.draw(self.screen)

        # speed lines
        for sl in self.speed_lines:
            sl.draw(self.screen, spd_frac)

        # motion blur vignette at high speed
        if spd_frac > 0.7:
            self._draw_vignette(int(80 * (spd_frac - 0.7) / 0.3))

        # HUD
        self._draw_hud()

        if self.state == "finish":
            self._draw_finish()

    def _draw_hills(self):
        t = self.cam_pos * 0.00005
        pts = [(0, H // 2)]
        for x in range(0, W + 10, 10):
            y = H // 2 + int(math.sin(x * 0.008 + t) * 40
                            + math.sin(x * 0.003 + t * 0.5) * 25)
            pts.append((x, y))
        pts.append((W, H // 2))
        pygame.draw.polygon(self.screen, HILL_COL, pts)

        pts2 = [(0, H // 2)]
        for x in range(0, W + 10, 10):
            y = H // 2 + int(math.sin(x * 0.012 + t * 1.3 + 1) * 30
                            + math.sin(x * 0.005 + t * 0.7) * 18)
            pts2.append((x, y))
        pts2.append((W, H // 2))
        pygame.draw.polygon(self.screen, HILL2_COL, pts2)

    def _draw_road(self):
        cam_seg_idx = int(self.cam_pos / SEG_LEN) % len(self.track)
        cam_seg_off = self.cam_pos % SEG_LEN

        x_offset   = 0.0
        y_offset   = 0.0
        max_y      = H

        prev_x1 = W // 2
        prev_y1 = H // 2
        prev_w1 = 0

        for i in range(DRAW_DIST - 1, -1, -1):
            idx   = (cam_seg_idx + i) % len(self.track)
            seg   = self.track[idx]

            z_near  = (i)     * SEG_LEN - cam_seg_off
            z_far   = (i + 1) * SEG_LEN - cam_seg_off

            proj1 = project(0, self.cam_h, 0, x_offset, y_offset, z_near)
            proj2 = project(0, self.cam_h, 0, x_offset, y_offset, z_far)

            x_offset += seg["curve"]
            y_offset += seg["hill"]

            if proj1 is None or proj2 is None:
                continue

            x1, y1, w1 = proj1
            x2, y2, w2 = proj2

            if y1 >= max_y:
                continue
            max_y = y1

            draw_segment(self.screen, idx,
                         int(x1 + self.player.x * w1), int(y1), int(w1),
                         int(x2 + self.player.x * w2), int(y2), int(w2))

            # draw opponents in this segment
            for opp in self.opponents:
                opp_z = opp.pos - self.cam_pos
                if opp_z < 0:
                    opp_z += self.track_len
                opp_seg = int(opp_z / SEG_LEN)
                if opp_seg == i:
                    frac  = (opp_z % SEG_LEN) / SEG_LEN
                    ox    = lerp(x1, x2, frac) + opp.lane_x * lerp(w1, w2, frac)
                    oy    = lerp(y1, y2, frac)
                    ow    = lerp(w1, w2, frac) * 0.25
                    opp.draw(self.screen, ox, oy, ow, 1)

    def _draw_vignette(self, strength):
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        for r in range(min(W, H) // 2, 0, -5):
            a = int(strength * (1 - r / (min(W, H) / 2)) ** 2)
            pygame.draw.rect(v, (0, 0, 0, a),
                             (W // 2 - r, H // 2 - r, r * 2, r * 2), 5)
        self.screen.blit(v, (0, 0))

    def _draw_hud(self):
        # bottom bar
        hud_h = 70
        hud   = pygame.Surface((W, hud_h), pygame.SRCALPHA)
        hud.fill((8, 10, 22, 200))
        self.screen.blit(hud, (0, H - hud_h))
        pygame.draw.line(self.screen, (30, 50, 100), (0, H - hud_h), (W, H - hud_h), 2)

        spd   = int(self.player.speed * 0.8)  # km/h feel
        sp_t  = self.font_big.render(f"{spd:3d}", True, NEON_YEL)
        km_t  = self.font_sm.render("km/h", True, DIM_COL)
        self.screen.blit(sp_t, (20, H - 58))
        self.screen.blit(km_t, (20, H - 20))

        # speedometer bar
        bar_w = 180
        bar_h = 8
        bx, by = 100, H - 30
        pygame.draw.rect(self.screen, (30, 40, 60), (bx, by, bar_w, bar_h), border_radius=4)
        fill = int(bar_w * self.player.speed / self.player.max_spd)
        bar_col = lerp_color(NEON_GRN, NEON_RED, self.player.speed / self.player.max_spd)
        if fill > 0:
            pygame.draw.rect(self.screen, bar_col, (bx, by, fill, bar_h), border_radius=4)

        # lap counter
        lap_t = self.font_med.render(f"LAP  {min(self.lap, self.max_laps)}/{self.max_laps}", True, NEON_CYAN)
        self.screen.blit(lap_t, (W // 2 - lap_t.get_width() // 2, H - 58))

        # timer
        elapsed = self.total_t - self.lap_start
        tm = self.font_sm.render(f"{int(elapsed // 60):02d}:{elapsed % 60:05.2f}", True, TEXT_COL)
        self.screen.blit(tm, (W // 2 - tm.get_width() // 2, H - 25))

        # rank
        rank_t = self.font_big.render(f"P{self.rank}", True,
                                       NEON_GRN if self.rank == 1 else TEXT_COL)
        self.screen.blit(rank_t, (W - 90, H - 58))

        # best lap
        if self.best_lap:
            bl = self.font_sm.render(
                f"BEST {int(self.best_lap // 60):02d}:{self.best_lap % 60:05.2f}", True, NEON_YEL)
            self.screen.blit(bl, (W - bl.get_width() - 10, H - 22))

        # minimap (track dots)
        mx, my, mr = W - 55, 55, 40
        pygame.draw.circle(self.screen, (20, 25, 45), (mx, my), mr)
        pygame.draw.circle(self.screen, (40, 50, 90), (mx, my), mr, 2)
        # player dot
        frac = self.cam_pos / self.track_len
        pa   = frac * math.tau - math.pi / 2
        px   = int(mx + math.cos(pa) * (mr - 6))
        py   = int(my + math.sin(pa) * (mr - 6))
        pygame.draw.circle(self.screen, NEON_RED, (px, py), 5)
        # opponent dots
        for opp in self.opponents:
            fa   = (opp.pos / self.track_len) * math.tau - math.pi / 2
            ox   = int(mx + math.cos(fa) * (mr - 6))
            oy   = int(my + math.sin(fa) * (mr - 6))
            pygame.draw.circle(self.screen, opp.color, (ox, oy), 3)

    def _draw_menu(self):
        self.total_t += 0.016
        self.screen.fill(HUD_BG)
        self.screen.blit(self.sky, (0, 0))
        self._draw_hills()

        # title
        title  = "TURBO RACER"
        colors = [NEON_RED, NEON_YEL, NEON_RED]
        for i, ch in enumerate(title):
            col = colors[i % len(colors)]
            t   = self.font_big.render(ch, True, col)
            oy  = int(math.sin(self.total_t * 2 + i * 0.4) * 5)
            self.screen.blit(t, (W // 2 - len(title) * 20 + i * 28, 160 + oy))

        lines = [
            ("↑ / ↓   Accelerate / Brake",   TEXT_COL),
            ("← / →   Steer",                TEXT_COL),
            ("",                              TEXT_COL),
            (f"3 Laps · 6 Opponents",         NEON_YEL),
            ("",                              TEXT_COL),
            ("Press ENTER to race!",          NEON_CYAN),
        ]
        for i, (line, col) in enumerate(lines):
            t = self.font_sm.render(line, True, col)
            self.screen.blit(t, (W // 2 - t.get_width() // 2, 260 + i * 26))

    def _draw_finish(self):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 8, 18, 190))
        self.screen.blit(overlay, (0, 0))

        title = self.font_big.render("RACE FINISHED!", True, NEON_YEL)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 80))

        pos_col = NEON_GRN if self.rank == 1 else TEXT_COL
        pos_t   = self.font_big.render(f"POSITION  P{self.rank}", True, pos_col)
        self.screen.blit(pos_t, (W // 2 - pos_t.get_width() // 2, H // 2 - 30))

        elapsed = self.total_t
        time_t  = self.font_med.render(
            f"Time  {int(elapsed // 60):02d}:{elapsed % 60:05.2f}", True, TEXT_COL)
        self.screen.blit(time_t, (W // 2 - time_t.get_width() // 2, H // 2 + 20))

        if self.best_lap:
            bl_t = self.font_med.render(
                f"Best Lap  {int(self.best_lap // 60):02d}:{self.best_lap % 60:05.2f}",
                True, NEON_CYAN)
            self.screen.blit(bl_t, (W // 2 - bl_t.get_width() // 2, H // 2 + 55))

        restart = self.font_sm.render("Press ENTER to race again", True, DIM_COL)
        self.screen.blit(restart, (W // 2 - restart.get_width() // 2, H // 2 + 110))


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    game = Game()
    game.run()
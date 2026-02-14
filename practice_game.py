"""
╔══════════════════════════════╗
║       BLOCK BLAST! 💥        ║
║   Pure Python + tkinter      ║
╚══════════════════════════════╝

HOW TO PLAY
-----------
• Drag pieces from the bottom tray onto the 8×8 grid.
• Fill a complete row or column to clear it and score points.
• Clear multiple lines at once for a combo bonus!
• Game over when none of the 3 pieces can fit on the board.

RUN
---
  python block_blast.py
  (No installs needed — uses built-in tkinter)
"""

import tkinter as tk
import random

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
GRID_COLS  = 8
GRID_ROWS  = 8
CELL       = 58
GRID_X     = 56
GRID_Y     = 90
TRAY_Y     = GRID_Y + GRID_ROWS * CELL + 28

WIN_W      = GRID_X * 2 + GRID_COLS * CELL
WIN_H      = TRAY_Y + 185

PALETTE = [
    "#FF5566", "#FF9922", "#FFDD22", "#33DD88",
    "#22AAFF", "#9955FF", "#FF55CC", "#11DDCC",
]

SHAPES = [
    [(0,0)],
    [(0,0),(0,1)],
    [(0,0),(0,1),(0,2)],
    [(0,0),(0,1),(0,2),(0,3)],
    [(0,0),(0,1),(0,2),(0,3),(0,4)],
    [(0,0),(1,0)],
    [(0,0),(1,0),(2,0)],
    [(0,0),(1,0),(2,0),(3,0)],
    [(0,0),(1,0),(2,0),(3,0),(4,0)],
    [(0,0),(0,1),(1,0),(1,1)],
    [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)],
    [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2)],
    [(0,0),(0,1),(1,0),(1,1),(2,0),(2,1)],
    [(0,0),(1,0),(2,0),(2,1)],
    [(0,1),(1,1),(2,0),(2,1)],
    [(0,0),(0,1),(0,2),(1,1)],
    [(0,1),(0,2),(1,0),(1,1)],
    [(0,0),(0,1),(1,1),(1,2)],
    [(0,0),(1,0),(1,1)],
    [(0,0),(0,1),(1,1)],
    [(0,0),(0,1),(1,0)],
    [(0,1),(1,0),(1,1)],
]

# ─────────────────────────────────────────────
#  COLOUR HELPERS
# ─────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def lighten(h, amt=60):
    r,g,b = hex_to_rgb(h)
    return rgb_to_hex(min(255,r+amt), min(255,g+amt), min(255,b+amt))

def darken(h, amt=60):
    r,g,b = hex_to_rgb(h)
    return rgb_to_hex(max(0,r-amt), max(0,g-amt), max(0,b-amt))

def blend(h, bg=(15,12,35), t=1.0):
    r,g,b = hex_to_rgb(h)
    return rgb_to_hex(int(bg[0]+(r-bg[0])*t),
                      int(bg[1]+(g-bg[1])*t),
                      int(bg[2]+(b-bg[2])*t))

# ─────────────────────────────────────────────
#  PIECE
# ─────────────────────────────────────────────
class Piece:
    def __init__(self, shape=None, color=None):
        self.shape     = shape if shape is not None else random.choice(SHAPES)
        self.color     = color or random.choice(PALETTE)
        self.rows_span = max(r for r,c in self.shape) + 1
        self.cols_span = max(c for r,c in self.shape) + 1

# ─────────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.x  = x + random.uniform(-4,4)
        self.y  = y + random.uniform(-4,4)
        self.vx = random.uniform(-4,4)
        self.vy = random.uniform(-7,-1)
        self.color = color
        self.life  = random.uniform(0.6,1.0)
        self.size  = random.randint(4,9)
        sz = self.size
        self.id = canvas.create_oval(self.x-sz, self.y-sz,
                                      self.x+sz, self.y+sz,
                                      fill=color, outline="")
    def update(self):
        self.vy  += 0.35
        self.x   += self.vx
        self.y   += self.vy
        self.life -= 0.03
        if self.life <= 0:
            self.canvas.delete(self.id)
            return False
        sz = max(1, int(self.size*self.life))
        self.canvas.coords(self.id, self.x-sz, self.y-sz, self.x+sz, self.y+sz)
        self.canvas.itemconfig(self.id, fill=blend(self.color, t=self.life))
        return True

# ─────────────────────────────────────────────
#  FLOAT TEXT
# ─────────────────────────────────────────────
class FloatText:
    def __init__(self, canvas, text, x, y, color="#FFFFFF"):
        self.canvas = canvas
        self.x      = x
        self.y      = float(y)
        self.life   = 1.0
        self.orig   = color
        self.id = canvas.create_text(x, y, text=text,
                                      font=("Arial",20,"bold"), fill=color)
    def update(self):
        self.y    -= 1.8
        self.life -= 0.025
        if self.life <= 0:
            self.canvas.delete(self.id)
            return False
        self.canvas.coords(self.id, self.x, self.y)
        self.canvas.itemconfig(self.id, fill=blend(self.orig, t=self.life))
        return True

# ─────────────────────────────────────────────
#  MAIN GAME
# ─────────────────────────────────────────────
class BlockBlast:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Block Blast! 💥")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0c23")

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H,
                                bg="#0f0c23", highlightthickness=0)
        self.canvas.pack()

        self.best       = 0
        self.particles  = []
        self.floats     = []
        self.drag_piece = None
        self.drag_idx   = None
        self.drag_ids   = []
        self.ghost_ids  = []

        self.canvas.bind("<ButtonPress-1>",   self.on_press)
        self.canvas.bind("<B1-Motion>",       self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<r>", lambda e: self.reset())
        self.root.bind("<R>", lambda e: self.reset())

        self.reset()
        self.loop()
        self.root.mainloop()

    # ── reset ──────────────────────────────────
    def reset(self):
        self.canvas.delete("all")
        self.grid      = [[None]*GRID_COLS for _ in range(GRID_ROWS)]
        self.score     = 0
        self.combo     = 0
        self.game_over = False
        self.tray      = [Piece(), Piece(), Piece()]
        self.tray_used = [False, False, False]
        self.particles = []
        self.floats    = []
        self.drag_piece = None
        self.drag_ids   = []
        self.ghost_ids  = []
        self._draw_bg()

    def _draw_bg(self):
        for y in range(0, WIN_H, 3):
            t = y / WIN_H
            r = int(15 + 15*t); g = int(12 + 8*t); b = int(35 + 25*t)
            self.canvas.create_line(0,y,WIN_W,y, fill=rgb_to_hex(r,g,b), width=3)

    # ── tray helpers ───────────────────────────
    def tray_center(self, i):
        sw = WIN_W // 3
        return sw*i + sw//2, TRAY_Y + 75

    def tray_origin(self, i):
        p  = self.tray[i]
        cx, cy = self.tray_center(i)
        md  = max(p.rows_span, p.cols_span)
        sz  = min(42, int(120/md))
        ox  = cx - (p.cols_span*sz)//2
        oy  = cy - (p.rows_span*sz)//2
        return ox, oy, sz

    # ── draw one block ─────────────────────────
    def draw_block(self, x, y, size, color, alpha=1.0, tag=None):
        ids = []
        pad = 2
        c  = blend(color, t=alpha)
        sh = blend(darken(color, 55), t=alpha)
        li = blend(lighten(color, 70), t=alpha)
        kw = {"tags": tag} if tag else {}
        ids.append(self.canvas.create_rectangle(
            x+pad, y+pad, x+size-pad, y+size-pad,
            fill=c, outline=sh, width=2, **kw))
        ids.append(self.canvas.create_rectangle(
            x+pad+3, y+pad+3, x+pad+size//3, y+pad+size//4,
            fill=li, outline="", **kw))
        return ids

    def draw_piece(self, piece, px, py, size=CELL, alpha=1.0, tag=None):
        ids = []
        for (r,c) in piece.shape:
            ids += self.draw_block(px+c*size, py+r*size, size,
                                   piece.color, alpha, tag)
        return ids

    # ── full redraw ────────────────────────────
    def redraw(self):
        self.canvas.delete("dynamic")

        # grid card
        self.canvas.create_rectangle(
            GRID_X-10, GRID_Y-10,
            GRID_X+GRID_COLS*CELL+10, GRID_Y+GRID_ROWS*CELL+10,
            fill="#16143a", outline="#3a3468", width=2, tags="dynamic")

        # cells
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = GRID_X + c*CELL;  y = GRID_Y + r*CELL
                color = self.grid[r][c]
                if color:
                    self.draw_block(x, y, CELL, color, tag="dynamic")
                else:
                    self.canvas.create_rectangle(
                        x+3, y+3, x+CELL-3, y+CELL-3,
                        fill="#19173a", outline="#2e2a52",
                        width=1, tags="dynamic")

        # grid lines
        for r in range(GRID_ROWS+1):
            self.canvas.create_line(GRID_X, GRID_Y+r*CELL,
                GRID_X+GRID_COLS*CELL, GRID_Y+r*CELL,
                fill="#35306a", tags="dynamic")
        for c in range(GRID_COLS+1):
            self.canvas.create_line(GRID_X+c*CELL, GRID_Y,
                GRID_X+c*CELL, GRID_Y+GRID_ROWS*CELL,
                fill="#35306a", tags="dynamic")

        # tray card
        self.canvas.create_rectangle(
            8, TRAY_Y-12, WIN_W-8, TRAY_Y+158,
            fill="#16143a", outline="#3a3468", width=2, tags="dynamic")

        # tray pieces
        for i, piece in enumerate(self.tray):
            if self.tray_used[i] or self.drag_idx == i:
                continue
            ox, oy, sz = self.tray_origin(i)
            self.draw_piece(piece, ox, oy, sz, tag="dynamic")

        # HUD
        self.canvas.create_text(WIN_W//2, 18, text="SCORE",
            font=("Arial",11,"bold"), fill="#a090cc", tags="dynamic")
        self.canvas.create_text(WIN_W//2, 52, text=str(self.score),
            font=("Arial",32,"bold"), fill="#ffffff", tags="dynamic")
        self.canvas.create_text(WIN_W-16, 30, text=f"BEST  {self.best}",
            font=("Arial",12,"bold"), fill="#b09ee0",
            anchor="e", tags="dynamic")
        self.canvas.create_text(16, 30, text="R = restart",
            font=("Arial",10), fill="#6a608a",
            anchor="w", tags="dynamic")

    # ── ghost ──────────────────────────────────
    def clear_ghost(self):
        for g in self.ghost_ids: self.canvas.delete(g)
        self.ghost_ids = []

    def draw_ghost(self, piece, gr, gc):
        self.clear_ghost()
        for (r,c) in piece.shape:
            x = GRID_X + (gc+c)*CELL;  y = GRID_Y + (gr+r)*CELL
            gid = self.canvas.create_rectangle(
                x+3, y+3, x+CELL-3, y+CELL-3,
                fill=blend(piece.color, t=0.35),
                outline=lighten(piece.color, 40), width=2)
            self.ghost_ids.append(gid)

    # ── placement ──────────────────────────────
    def can_place(self, piece, gr, gc):
        for (r,c) in piece.shape:
            nr,nc = gr+r, gc+c
            if not (0<=nr<GRID_ROWS and 0<=nc<GRID_COLS): return False
            if self.grid[nr][nc]: return False
        return True

    def get_snap(self, piece, mx, my):
        gr = int((my-GRID_Y)/CELL - piece.rows_span/2 + 0.5)
        gc = int((mx-GRID_X)/CELL - piece.cols_span/2 + 0.5)
        return (gr,gc) if self.can_place(piece,gr,gc) else None

    def place_piece(self, piece, gr, gc):
        for (r,c) in piece.shape:
            self.grid[gr+r][gc+c] = piece.color
        self.score += len(piece.shape)

    # ── clear lines ────────────────────────────
    def clear_lines(self):
        rows = [r for r in range(GRID_ROWS)
                if all(self.grid[r][c] for c in range(GRID_COLS))]
        cols = [c for c in range(GRID_COLS)
                if all(self.grid[r][c] for r in range(GRID_ROWS))]
        if not rows and not cols:
            self.combo = 0;  return

        self.combo += 1
        pts = (len(rows)+len(cols)) * 80 * self.combo

        for r in rows:
            for c in range(GRID_COLS):
                col = self.grid[r][c] or "#ffffff"
                cx = GRID_X+c*CELL+CELL//2;  cy = GRID_Y+r*CELL+CELL//2
                for _ in range(5):
                    self.particles.append(Particle(self.canvas,cx,cy,col))
        for col in cols:
            for r in range(GRID_ROWS):
                color = self.grid[r][col] or "#ffffff"
                cx = GRID_X+col*CELL+CELL//2;  cy = GRID_Y+r*CELL+CELL//2
                for _ in range(5):
                    self.particles.append(Particle(self.canvas,cx,cy,color))

        cleared = {(r,c) for r in rows for c in range(GRID_COLS)} | \
                  {(r,c) for col in cols for r in range(GRID_ROWS) for c in [col]}
        for (r,c) in cleared:
            self.grid[r][c] = None

        self.score += pts
        if self.score > self.best: self.best = self.score

        cx = GRID_X+GRID_COLS*CELL//2;  cy = GRID_Y+GRID_ROWS*CELL//2
        self.floats.append(FloatText(self.canvas, f"+{pts}", cx, cy, "#FFEE55"))
        if self.combo > 1:
            self.floats.append(FloatText(self.canvas,
                f"x{self.combo} COMBO!", cx, cy-40, "#FF9944"))

    # ── game over ──────────────────────────────
    def check_game_over(self):
        for i,p in enumerate(self.tray):
            if self.tray_used[i]: continue
            for gr in range(GRID_ROWS):
                for gc in range(GRID_COLS):
                    if self.can_place(p,gr,gc): return False
        return True

    def draw_game_over_screen(self):
        self.canvas.delete("gameover")
        self.canvas.create_rectangle(0,0,WIN_W,WIN_H,
            fill="#0a0820", stipple="gray50", tags="gameover")
        bx1,by1 = WIN_W//2-175, WIN_H//2-125
        bx2,by2 = WIN_W//2+175, WIN_H//2+135
        self.canvas.create_rectangle(bx1,by1,bx2,by2,
            fill="#1e1840", outline="#7755ee", width=2, tags="gameover")
        self.canvas.create_text(WIN_W//2, WIN_H//2-88,
            text="GAME OVER", font=("Arial",30,"bold"),
            fill="#FF5566", tags="gameover")
        self.canvas.create_text(WIN_W//2, WIN_H//2-35,
            text=f"Score: {self.score}", font=("Arial",20,"bold"),
            fill="#ffffff", tags="gameover")
        self.canvas.create_text(WIN_W//2, WIN_H//2+5,
            text=f"Best:  {self.best}", font=("Arial",18,"bold"),
            fill="#FFD700", tags="gameover")
        bbx1,bby1 = WIN_W//2-90, WIN_H//2+52
        bbx2,bby2 = WIN_W//2+90, WIN_H//2+96
        self.canvas.create_rectangle(bbx1,bby1,bbx2,bby2,
            fill="#7755ee", outline="#aa88ff", width=2, tags="gameover")
        self.canvas.create_text(WIN_W//2, WIN_H//2+74,
            text="PLAY AGAIN", font=("Arial",15,"bold"),
            fill="#ffffff", tags="gameover")

        def on_click(ev):
            if bbx1<=ev.x<=bbx2 and bby1<=ev.y<=bby2:
                self.reset()
        self.canvas.tag_bind("gameover","<ButtonPress-1>", on_click)

    # ── mouse ──────────────────────────────────
    def on_press(self, ev):
        if self.game_over: return
        for i,p in enumerate(self.tray):
            if self.tray_used[i]: continue
            ox,oy,sz = self.tray_origin(i)
            tw = p.cols_span*sz;  th = p.rows_span*sz
            if ox-10<=ev.x<=ox+tw+10 and oy-10<=ev.y<=oy+th+10:
                self.drag_piece = p
                self.drag_idx   = i
                self.drag_ox    = ev.x - ox
                self.drag_oy    = ev.y - oy
                break

    def on_drag(self, ev):
        if not self.drag_piece: return
        for d in self.drag_ids: self.canvas.delete(d)
        self.clear_ghost()
        p  = self.drag_piece
        px = ev.x - self.drag_ox;  py = ev.y - self.drag_oy
        snap = self.get_snap(p, ev.x, ev.y)
        if snap: self.draw_ghost(p, *snap)
        self.drag_ids = self.draw_piece(p, px, py, CELL, 0.82)

    def on_release(self, ev):
        if not self.drag_piece: return
        p    = self.drag_piece
        snap = self.get_snap(p, ev.x, ev.y)
        for d in self.drag_ids: self.canvas.delete(d)
        self.clear_ghost()
        self.drag_ids = []
        if snap:
            self.place_piece(p, *snap)
            self.tray_used[self.drag_idx] = True
            self.clear_lines()
            if all(self.tray_used):
                self.tray      = [Piece(), Piece(), Piece()]
                self.tray_used = [False, False, False]
            if self.check_game_over():
                self.game_over = True
        self.drag_piece = None
        self.drag_idx   = None

    # ── main loop ──────────────────────────────
    def loop(self):
        self.redraw()
        self.particles = [p for p in self.particles if p.update()]
        self.floats    = [f for f in self.floats    if f.update()]
        for d in self.drag_ids:  self.canvas.tag_raise(d)
        for g in self.ghost_ids: self.canvas.tag_raise(g)
        if self.game_over:
            self.draw_game_over_screen()
        self.root.after(16, self.loop)

if __name__ == "__main__":
    BlockBlast()
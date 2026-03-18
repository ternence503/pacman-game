import pygame
import sys
import random
import math
import numpy as np

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# --- 音效引擎 ---
SAMPLE_RATE = 44100

def make_tone(freq, duration, volume=0.4, wave='sine', decay=True):
    """生成單一音調的 numpy 陣列"""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    if wave == 'sine':
        w = np.sin(2 * np.pi * freq * t)
    elif wave == 'square':
        w = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == 'saw':
        w = 2 * (t * freq - np.floor(t * freq + 0.5))
    else:
        w = np.sin(2 * np.pi * freq * t)
    if decay:
        env = np.linspace(1.0, 0.0, n)
        w = w * env
    w = (w * volume * 32767).astype(np.int16)
    return w

def make_sound(arrays):
    """將多個 numpy 陣列串接成 pygame.Sound"""
    data = np.concatenate(arrays)
    sound = pygame.sndarray.make_sound(data)
    return sound

def load_cjk_font(size):
    """嘗試載入支援中文的字型，找不到則退回預設"""
    candidates = [
        # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            continue
    return pygame.font.SysFont(None, size)

def build_sounds():
    sounds = {}

    # waka A / waka B：交替的兩個音調
    sounds['waka_a'] = make_sound([make_tone(480, 0.055, 0.35, 'square')])
    sounds['waka_b'] = make_sound([make_tone(320, 0.055, 0.35, 'square')])

    # 能量豆：短促上升音
    sounds['power'] = make_sound([
        make_tone(300, 0.06, 0.5, 'square'),
        make_tone(500, 0.06, 0.5, 'square'),
        make_tone(700, 0.08, 0.5, 'square'),
    ])

    # 吃鬼：快速上升 arpeggio
    sounds['eat_ghost'] = make_sound([
        make_tone(200, 0.04, 0.5, 'square'),
        make_tone(400, 0.04, 0.5, 'square'),
        make_tone(600, 0.04, 0.5, 'square'),
        make_tone(900, 0.08, 0.5, 'square'),
    ])

    # 死亡音效：下降音階
    sounds['death'] = make_sound([
        make_tone(880, 0.07, 0.5, 'square'),
        make_tone(784, 0.07, 0.5, 'square'),
        make_tone(698, 0.07, 0.5, 'square'),
        make_tone(622, 0.07, 0.5, 'square'),
        make_tone(554, 0.07, 0.5, 'square'),
        make_tone(494, 0.07, 0.5, 'square'),
        make_tone(440, 0.07, 0.5, 'square'),
        make_tone(392, 0.07, 0.5, 'square'),
        make_tone(349, 0.14, 0.5, 'square'),
    ])

    # 背景迴圈警報聲（兩音交替）
    siren_lo = make_tone(220, 0.18, 0.18, 'square', decay=False)
    siren_hi = make_tone(280, 0.18, 0.18, 'square', decay=False)
    sounds['siren'] = make_sound([siren_lo, siren_hi] * 4)

    # 鬼魂受驚迴圈（顫音）
    fright_a = make_tone(160, 0.12, 0.18, 'square', decay=False)
    fright_b = make_tone(130, 0.12, 0.18, 'square', decay=False)
    sounds['frightened'] = make_sound([fright_a, fright_b] * 4)

    # 過關音效
    sounds['clear'] = make_sound([
        make_tone(523, 0.08, 0.45, 'square'),
        make_tone(659, 0.08, 0.45, 'square'),
        make_tone(784, 0.08, 0.45, 'square'),
        make_tone(1047, 0.18, 0.45, 'square'),
    ])

    # 開場 jingle
    sounds['start'] = make_sound([
        make_tone(494, 0.10, 0.4, 'square'),
        make_tone(494, 0.10, 0.4, 'square'),
        make_tone(494, 0.10, 0.4, 'square'),
        make_tone(392, 0.15, 0.4, 'square'),
        make_tone(494, 0.10, 0.4, 'square'),
        make_tone(587, 0.25, 0.4, 'square'),
        make_tone(294, 0.25, 0.4, 'square'),
    ])

    return sounds

# --- 常數 ---
TILE = 24
COLS = 28
ROWS = 31
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + 80  # extra for score bar

FPS = 60

BLACK   = (0, 0, 0)
YELLOW  = (255, 220, 0)
WHITE   = (255, 255, 255)
BLUE    = (0, 0, 200)
WALL_C  = (33, 33, 255)
DOT_C   = (255, 184, 151)
POWER_C = (255, 184, 151)
RED     = (220, 0, 0)
PINK    = (255, 184, 222)
CYAN    = (0, 255, 222)
ORANGE  = (255, 148, 18)
SCARED  = (0, 0, 180)
SCARED2 = (255, 255, 255)
EATEN   = (200, 200, 200)
GRAY    = (100, 100, 100)

# 迷宮地圖 (0=牆, 1=點, 2=能量豆, 3=空, 4=鬼巢出入口, 5=鬼巢)
MAZE_TEMPLATE = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#2####.#####.##.#####.####2#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "######.##### ## #####.######",
    "######.##          ##.######",
    "######.## ###44### ##.######",
    "######.## #555555# ##.######",
    "      .   #555555#   .      ",
    "######.## #555555# ##.######",
    "######.## ######## ##.######",
    "######.##          ##.######",
    "######.## ######## ##.######",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#2..##.......  .......##..2#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

def build_map():
    tiles = []
    for row_str in MAZE_TEMPLATE:
        row = []
        for ch in row_str:
            if ch == '#':
                row.append(0)
            elif ch == '.':
                row.append(1)
            elif ch == '2':
                row.append(2)
            elif ch == '4':
                row.append(4)
            elif ch == '5':
                row.append(5)
            else:
                row.append(3)
        # pad/clip to 28
        while len(row) < COLS:
            row.append(3)
        tiles.append(row[:COLS])
    while len(tiles) < ROWS:
        tiles.append([3]*COLS)
    return tiles

# --- 繪圖工具 ---
def draw_wall_tile(surf, x, y):
    rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
    pygame.draw.rect(surf, WALL_C, rect)
    pygame.draw.rect(surf, (0, 0, 120), rect, 1)

def draw_dot(surf, x, y):
    cx = x*TILE + TILE//2
    cy = y*TILE + TILE//2
    pygame.draw.circle(surf, DOT_C, (cx, cy), 3)

def draw_power(surf, x, y, tick):
    cx = x*TILE + TILE//2
    cy = y*TILE + TILE//2
    r = 7 + int(3 * math.sin(tick * 0.08))
    pygame.draw.circle(surf, POWER_C, (cx, cy), r)

def draw_pacman(surf, cx, cy, mouth_angle, direction):
    r = TILE//2 - 2
    # direction -> start angle
    dir_map = {(1,0): 0, (-1,0): 180, (0,-1): 90, (0,1): 270}
    base = dir_map.get(direction, 0)
    start = base + mouth_angle
    end = base + 360 - mouth_angle
    # draw as arc pie
    rect = pygame.Rect(cx-r, cy-r, r*2, r*2)
    if mouth_angle > 1:
        pygame.draw.arc(surf, YELLOW, rect, math.radians(start), math.radians(end), r)
        # fill pie manually
        points = [(cx, cy)]
        steps = 36
        span = (end - start) % 360
        for i in range(steps+1):
            angle = math.radians(start + span*i/steps)
            px = cx + r * math.cos(angle)
            py = cy - r * math.sin(angle)
            points.append((px, py))
        if len(points) >= 3:
            pygame.draw.polygon(surf, YELLOW, points)
    else:
        pygame.draw.circle(surf, YELLOW, (cx, cy), r)

def draw_ghost(surf, cx, cy, color, scared, scared_flash, tick):
    r = TILE//2 - 1
    # body color
    if scared:
        if scared_flash and (tick//8) % 2 == 0:
            c = SCARED2
        else:
            c = SCARED
    else:
        c = color
    # body = circle top + rect bottom
    body_rect = pygame.Rect(cx-r, cy, r*2, r)
    pygame.draw.circle(surf, c, (cx, cy), r)
    pygame.draw.rect(surf, c, body_rect)
    # skirt wavy
    skirt_y = cy + r
    segs = 4
    sw = (r*2) // segs
    for i in range(segs):
        rx = cx - r + i*sw
        if i % 2 == 0:
            pygame.draw.circle(surf, c, (rx + sw//2, skirt_y), sw//2)
        # else leave notch
    # eyes
    if not scared:
        for ex, ey in [(cx-r//2, cy-2), (cx+r//2, cy-2)]:
            pygame.draw.circle(surf, WHITE, (ex, ey), 4)
            pygame.draw.circle(surf, BLUE, (ex, ey), 2)
    else:
        # scared eyes
        for ex, ey in [(cx-r//2, cy-2), (cx+r//2, cy-2)]:
            pygame.draw.circle(surf, SCARED2, (ex, ey), 3)

# --- 精靈類別 ---
class Pacman:
    def __init__(self, tiles):
        self.tiles = tiles
        self.reset()

    def reset(self):
        self.tx = 14.0
        self.ty = 23.0
        self.direction = (-1, 0)
        self.next_dir = (-1, 0)
        self.speed = 0.1
        self.mouth = 0
        self.mouth_dir = 1
        self.alive = True
        self.dead_anim = 0

    def can_move(self, tx, ty):
        ix, iy = int(round(tx)), int(round(ty))
        if ix < 0: ix = COLS-1
        if ix >= COLS: ix = 0
        if iy < 0 or iy >= ROWS: return False
        return self.tiles[iy][ix] != 0

    def update(self, keys):
        if not self.alive:
            self.dead_anim += 1
            return

        # input
        if keys[pygame.K_LEFT]:  self.next_dir = (-1, 0)
        if keys[pygame.K_RIGHT]: self.next_dir = (1, 0)
        if keys[pygame.K_UP]:    self.next_dir = (0, -1)
        if keys[pygame.K_DOWN]:  self.next_dir = (0, 1)

        # try to turn
        nx = self.tx + self.next_dir[0] * self.speed
        ny = self.ty + self.next_dir[1] * self.speed
        if self.can_move(nx, ny):
            self.direction = self.next_dir

        # move
        mx = self.tx + self.direction[0] * self.speed
        my = self.ty + self.direction[1] * self.speed
        if self.can_move(mx, my):
            self.tx = mx
            self.ty = my
        # tunnel wrap
        if self.tx < 0: self.tx = COLS - 1
        if self.tx >= COLS: self.tx = 0

        # mouth animation
        self.mouth += 5 * self.mouth_dir
        if self.mouth >= 45: self.mouth_dir = -1
        if self.mouth <= 0:  self.mouth_dir = 1

    def draw(self, surf):
        cx = int(self.tx * TILE + TILE//2)
        cy = int(self.ty * TILE + TILE//2)
        if not self.alive:
            # death spin
            angle = min(self.dead_anim * 10, 180)
            r = TILE//2 - 2
            rect = pygame.Rect(cx-r, cy-r, r*2, r*2)
            pygame.draw.arc(surf, YELLOW, rect, math.radians(angle//2), math.radians(360-angle//2), r)
        else:
            draw_pacman(surf, cx, cy, self.mouth, self.direction)

class Ghost:
    COLORS = [RED, PINK, CYAN, ORANGE]
    NAMES  = ['blinky','pinky','inky','clyde']
    # scatter targets
    SCATTER = [(COLS-3, 0), (3, 0), (COLS-1, ROWS-3), (0, ROWS-3)]
    # home positions in ghost pen
    HOME_X = [13.5, 13.5, 11.5, 15.5]
    HOME_Y = [14.0, 14.0, 14.0, 14.0]

    def __init__(self, idx, tiles):
        self.idx = idx
        self.tiles = tiles
        self.color = self.COLORS[idx]
        self.reset()

    def reset(self):
        self.tx = self.HOME_X[self.idx]
        self.ty = self.HOME_Y[self.idx]
        self.direction = (0, -1)
        self.speed = 0.08
        self.mode = 'house'  # house / scatter / chase / frightened / eaten
        self.scared = False
        self.scared_timer = 0
        self.eaten = False
        self.house_timer = self.idx * 120  # staggered release

    def can_move(self, tx, ty, allow_house=False):
        ix, iy = int(round(tx)), int(round(ty))
        if ix < 0: ix = COLS-1
        if ix >= COLS: ix = 0
        if iy < 0 or iy >= ROWS: return False
        t = self.tiles[iy][ix]
        if t == 0: return False
        if t == 5 and not allow_house: return False
        return True

    def get_directions(self, allow_house=False):
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        reverse = (-self.direction[0], -self.direction[1])
        result = []
        for d in dirs:
            if d == reverse: continue
            nx = self.tx + d[0]
            ny = self.ty + d[1]
            if self.can_move(nx, ny, allow_house):
                result.append(d)
        return result if result else [reverse]

    def dist(self, tx, ty, gx, gy):
        return (tx-gx)**2 + (ty-gy)**2

    def choose_dir(self, target_x, target_y, allow_house=False):
        dirs = self.get_directions(allow_house)
        best = None
        best_dist = float('inf')
        for d in dirs:
            nx = self.tx + d[0]
            ny = self.ty + d[1]
            dd = self.dist(nx, ny, target_x, target_y)
            if dd < best_dist:
                best_dist = dd
                best = d
        return best

    def update(self, pac, tick, scatter_mode):
        # handle scared timer
        if self.scared:
            self.scared_timer -= 1
            if self.scared_timer <= 0:
                self.scared = False
                if self.mode == 'frightened':
                    self.mode = 'chase'

        if self.eaten:
            # go back to house
            target = (13.5, 11.0)
            if abs(self.tx - target[0]) < 0.2 and abs(self.ty - target[1]) < 0.2:
                self.eaten = False
                self.scared = False
                self.mode = 'house'
                self.house_timer = 60
                self.tx = self.HOME_X[self.idx]
                self.ty = self.HOME_Y[self.idx]
            else:
                d = self.choose_dir(target[0], target[1], allow_house=True)
                if d:
                    self.direction = d
            spd = 0.15
            nx = self.tx + self.direction[0] * spd
            ny = self.ty + self.direction[1] * spd
            if self.can_move(nx, ny, allow_house=True):
                self.tx = nx
                self.ty = ny
            if self.tx < 0: self.tx = COLS-1
            if self.tx >= COLS: self.tx = 0
            return

        if self.mode == 'house':
            self.house_timer -= 1
            # bounce up/down in house
            self.ty += math.sin(tick * 0.1) * 0.05
            if self.house_timer <= 0:
                self.mode = 'scatter'
                self.tx = 13.5
                self.ty = 11.5
                self.direction = (0, -1)
            return

        spd = 0.05 if self.scared else self.speed
        # choose target
        if self.scared:
            # random
            dirs = self.get_directions()
            if (tick % 8) == 0:
                self.direction = random.choice(dirs)
        elif scatter_mode:
            sx, sy = self.SCATTER[self.idx]
            d = self.choose_dir(sx, sy)
            if d: self.direction = d
        else:
            # chase
            if self.idx == 0:  # blinky: target pac directly
                tx, ty = pac.tx, pac.ty
            elif self.idx == 1:  # pinky: 4 tiles ahead
                tx = pac.tx + pac.direction[0]*4
                ty = pac.ty + pac.direction[1]*4
            elif self.idx == 2:  # inky: blinky + vector
                tx, ty = pac.tx, pac.ty
            else:  # clyde: far=pac, close=scatter
                if self.dist(self.tx, self.ty, pac.tx, pac.ty) > 64:
                    tx, ty = pac.tx, pac.ty
                else:
                    tx, ty = self.SCATTER[self.idx]
            d = self.choose_dir(tx, ty)
            if d: self.direction = d

        nx = self.tx + self.direction[0] * spd
        ny = self.ty + self.direction[1] * spd
        if self.can_move(nx, ny):
            self.tx = nx
            self.ty = ny
        else:
            dirs = self.get_directions()
            if dirs:
                self.direction = dirs[0]
        if self.tx < 0: self.tx = COLS-1
        if self.tx >= COLS: self.tx = 0

    def frighten(self):
        if not self.eaten:
            self.scared = True
            self.scared_timer = 360
            self.mode = 'frightened'

    def draw(self, surf, tick):
        cx = int(self.tx * TILE + TILE//2)
        cy = int(self.ty * TILE + TILE//2)
        flash = self.scared and self.scared_timer < 120
        draw_ghost(surf, cx, cy, self.color, self.scared, flash, tick)
        if self.eaten:
            # draw eyes only
            r = TILE//2 - 1
            for ex, ey in [(cx-r//2, cy-2), (cx+r//2, cy-2)]:
                pygame.draw.circle(surf, WHITE, (ex, ey), 4)
                pygame.draw.circle(surf, BLUE, (ex, ey), 2)

# --- 遊戲主類別 ---
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("小精靈 Pac-Man")
        self.clock = pygame.time.Clock()
        self.font_big = load_cjk_font(36)
        self.font_med = load_cjk_font(24)
        self.font_sm  = load_cjk_font(20)
        self.sounds = build_sounds()
        self.waka_toggle = False
        self.siren_ch = pygame.mixer.Channel(0)
        self.fright_ch = pygame.mixer.Channel(1)
        self.sfx_ch    = pygame.mixer.Channel(2)
        self.init_game()

    def init_game(self):
        self.tiles = build_map()
        self.original_tiles = [row[:] for row in self.tiles]
        self.pacman = Pacman(self.tiles)
        self.ghosts = [Ghost(i, self.tiles) for i in range(4)]
        self.score = 0
        self.lives = 3
        self.level = 1
        self.tick = 0
        self.state = 'playing'
        self.dead_pause = 0
        self.scatter_timer = 0
        self.scatter_mode = True
        self.eat_combo = 0
        self.total_dots = sum(1 for row in self.tiles for t in row if t in (1,2))
        self.dots_eaten = 0
        self.blink_timer = 0
        self.any_frightened = False
        self.siren_ch.stop()
        self.fright_ch.stop()

    def reset_level(self):
        self.tiles = [row[:] for row in self.original_tiles]
        for g in self.ghosts:
            g.tiles = self.tiles
        self.pacman.tiles = self.tiles
        self.pacman.reset()
        for g in self.ghosts:
            g.reset()
        self.total_dots = sum(1 for row in self.tiles for t in row if t in (1,2))
        self.dots_eaten = 0
        self.scatter_timer = 0
        self.scatter_mode = True
        self.eat_combo = 0

    def next_level(self):
        self.level += 1
        self.tiles = build_map()
        self.original_tiles = [row[:] for row in self.tiles]
        for g in self.ghosts:
            g.tiles = self.tiles
            g.speed = min(0.08 + self.level*0.01, 0.14)
        self.pacman.tiles = self.tiles
        self.pacman.speed = min(0.1 + self.level*0.005, 0.15)
        self.pacman.reset()
        for g in self.ghosts:
            g.reset()
        self.total_dots = sum(1 for row in self.tiles for t in row if t in (1,2))
        self.dots_eaten = 0
        self.scatter_timer = 0
        self.scatter_mode = True
        self.eat_combo = 0
        self.state = 'playing'

    def check_eat(self):
        tx = int(round(self.pacman.tx))
        ty = int(round(self.pacman.ty))
        if 0 <= ty < ROWS and 0 <= tx < COLS:
            t = self.tiles[ty][tx]
            if t == 1:
                self.tiles[ty][tx] = 3
                self.score += 10
                self.dots_eaten += 1
                # waka waka 交替音
                self.waka_toggle = not self.waka_toggle
                key = 'waka_a' if self.waka_toggle else 'waka_b'
                self.sfx_ch.play(self.sounds[key])
            elif t == 2:
                self.tiles[ty][tx] = 3
                self.score += 50
                self.dots_eaten += 1
                self.eat_combo = 0
                for g in self.ghosts:
                    g.frighten()
                self.sfx_ch.play(self.sounds['power'])

    def check_ghost_collision(self):
        for g in self.ghosts:
            if g.mode == 'house': continue
            dist = math.hypot(self.pacman.tx - g.tx, self.pacman.ty - g.ty)
            if dist < 0.8:
                if g.scared and not g.eaten:
                    g.eaten = True
                    g.scared = False
                    self.eat_combo += 1
                    pts = 200 * (2 ** (self.eat_combo-1))
                    self.score += pts
                    self.sfx_ch.play(self.sounds['eat_ghost'])
                elif not g.eaten and not g.scared:
                    self.lives -= 1
                    self.state = 'dead_pause'
                    self.dead_pause = 150
                    self.pacman.alive = False
                    self.siren_ch.stop()
                    self.fright_ch.stop()
                    self.sfx_ch.play(self.sounds['death'])
                    return

    def update(self):
        self.tick += 1

        if self.state == 'dead_pause':
            self.dead_pause -= 1
            self.pacman.update(pygame.key.get_pressed())
            if self.dead_pause <= 0:
                if self.lives <= 0:
                    self.state = 'game_over'
                else:
                    self.reset_level()
                    self.state = 'playing'
            return

        if self.state != 'playing':
            return

        # scatter/chase cycle
        self.scatter_timer += 1
        if self.scatter_timer < 420:
            self.scatter_mode = True
        elif self.scatter_timer < 1200:
            self.scatter_mode = False
        elif self.scatter_timer < 1500:
            self.scatter_mode = True
        else:
            self.scatter_mode = False

        keys = pygame.key.get_pressed()
        self.pacman.update(keys)
        self.check_eat()
        for g in self.ghosts:
            g.update(self.pacman, self.tick, self.scatter_mode)
        self.check_ghost_collision()

        # 背景音效：有鬼受驚時播恐慌音，否則播警報聲
        frightened_now = any(g.scared and not g.eaten for g in self.ghosts)
        if frightened_now != self.any_frightened:
            self.any_frightened = frightened_now
            if frightened_now:
                self.siren_ch.stop()
                self.fright_ch.play(self.sounds['frightened'], loops=-1)
            else:
                self.fright_ch.stop()
                self.siren_ch.play(self.sounds['siren'], loops=-1)
        if not frightened_now and not self.siren_ch.get_busy():
            self.siren_ch.play(self.sounds['siren'], loops=-1)

        if self.dots_eaten >= self.total_dots:
            self.siren_ch.stop()
            self.fright_ch.stop()
            self.sfx_ch.play(self.sounds['clear'])
            self.next_level()

    def draw_maze(self):
        self.screen.fill(BLACK)
        for y in range(ROWS):
            for x in range(COLS):
                t = self.tiles[y][x]
                if t == 0:
                    draw_wall_tile(self.screen, x, y)
                elif t == 1:
                    draw_dot(self.screen, x, y)
                elif t == 2:
                    draw_power(self.screen, x, y, self.tick)

    def draw_hud(self):
        y0 = ROWS * TILE
        pygame.draw.rect(self.screen, (20, 20, 20), (0, y0, WIDTH, 80))

        score_surf = self.font_big.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (10, y0+8))

        level_surf = self.font_med.render(f"LEVEL {self.level}", True, YELLOW)
        self.screen.blit(level_surf, (WIDTH//2 - 30, y0+8))

        # lives
        for i in range(self.lives):
            cx = WIDTH - 30 - i*30
            cy = y0 + 20
            draw_pacman(self.screen, cx, cy, 20, (1, 0))

        # controls hint
        hint = self.font_sm.render("方向鍵移動  ESC離開  R重玩", True, GRAY)
        self.screen.blit(hint, (10, y0+50))

    def draw_overlay(self, text, sub=""):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        s = self.font_big.render(text, True, YELLOW)
        self.screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 - 40))
        if sub:
            s2 = self.font_med.render(sub, True, WHITE)
            self.screen.blit(s2, (WIDTH//2 - s2.get_width()//2, HEIGHT//2 + 10))

    def draw(self):
        self.draw_maze()
        self.pacman.draw(self.screen)
        for g in self.ghosts:
            g.draw(self.screen, self.tick)
        self.draw_hud()

        if self.state == 'game_over':
            self.draw_overlay("GAME OVER", f"最終分數: {self.score}  按 R 重新開始")
        elif self.state == 'win':
            self.draw_overlay("YOU WIN!", f"分數: {self.score}")

        pygame.display.flip()

    def run(self):
        # title screen
        self.screen.fill(BLACK)
        title = self.font_big.render("小精靈  PAC-MAN", True, YELLOW)
        sub1  = self.font_med.render("方向鍵控制  吃掉所有豆子", True, WHITE)
        sub2  = self.font_med.render("按任意鍵開始", True, DOT_C)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 60))
        self.screen.blit(sub1,  (WIDTH//2 - sub1.get_width()//2,  HEIGHT//2))
        self.screen.blit(sub2,  (WIDTH//2 - sub2.get_width()//2,  HEIGHT//2 + 40))
        pygame.display.flip()
        self.sfx_ch.play(self.sounds['start'])
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
                if e.type == pygame.KEYDOWN: waiting = False

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_r:
                        self.siren_ch.stop()
                        self.fright_ch.stop()
                        self.score = 0
                        self.lives = 3
                        self.level = 1
                        self.init_game()
                        self.sfx_ch.play(self.sounds['start'])

            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == '__main__':
    Game().run()

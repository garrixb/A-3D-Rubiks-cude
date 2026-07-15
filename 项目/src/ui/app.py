#!/usr/bin/env python3
"""
3D Rubik's Cube Interactive System
====================================
Features:
  - Light-themed background and UI
  - English buttons: Scramble / Solve / Reset / Appearance
  - Multiple solving methods (Kociemba two-phase + Reverse-history), guaranteed to solve
  - Smooth easing-based rotation animation (no float drift)
  - Mouse drag to rotate view (with boundary limits to prevent flipping)
  - Progress bar during long operations (Scramble/Solve)
  - Shift+key for inverse rotation (works for all layer keys)
  - 10 color themes (Standard, Dark, Pastel, HighContrast, Metallic, BlackGold, Cyberpunk, Morandi, Monochrome, Rainbow)
  - Compatible with Pygame 1.9.6+ and 2.0+

Controls:
  Mouse drag  - Rotate view (horizontal unlimited, vertical limited to ±89°)
  U/D/L/R/F/B - Rotate layer (Shift+key for inverse)
  S           - Scramble
  Space/Enter - Solve
  Backspace   - Reset
  M           - Cycle solve method
  A           - Cycle appearance theme
  ESC         - Quit
"""

import math
import random
import copy
import time
import sys

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from src.model.cube_model import RubiksCube, MOVE_TO_ALA, ALA_TO_MOVE
from src.solver.factory import SolverFactory

# ---------------------------------------------------------------------------
# 缓动函数
# ---------------------------------------------------------------------------
def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2

# ---------------------------------------------------------------------------
# Optional 求解器 libraries
# ---------------------------------------------------------------------------
try:
    import kociemba as _kociemba
    KOCIEMBA_AVAILABLE = True
except Exception:
    KOCIEMBA_AVAILABLE = False

# ---------------------------------------------------------------------------
# Window / 显示
# ---------------------------------------------------------------------------
DISPLAY_W, DISPLAY_H = 960, 720
UI_HEIGHT = 130  # bottom strip for buttons / 状态

# ---------------------------------------------------------------------------
# Colors  (食指 order: 0=right 1=left 2=up 3=down 4=front 5=back)
# ---------------------------------------------------------------------------
# 默认 theme (will be overridden by appearance switcher)
FACE_COLORS = {
    'right':  (0.80, 0.10, 0.12),   # red
    'left':   (1.00, 0.42, 0.00),   # orange
    'up':     (0.97, 0.97, 0.97),   # white
    'down':   (1.00, 0.83, 0.00),   # yellow
    'front':  (0.08, 0.42, 0.88),   # blue
    'back':   (0.08, 0.68, 0.22),   # green
    'internal': (0.07, 0.07, 0.08), # black
}

# ---------------------------------------------------------------------------
# 外观主题
# ---------------------------------------------------------------------------
APPEARANCES = {
    'Standard': {
        'right': (0.80, 0.10, 0.12),
        'left': (1.00, 0.42, 0.00),
        'up': (0.97, 0.97, 0.97),
        'down': (1.00, 0.83, 0.00),
        'front': (0.08, 0.42, 0.88),
        'back': (0.08, 0.68, 0.22),
        'internal': (0.07, 0.07, 0.08),
    },
    'Dark': {
        'right': (0.65, 0.05, 0.08),
        'left': (0.85, 0.30, 0.00),
        'up': (0.80, 0.80, 0.80),
        'down': (0.90, 0.70, 0.00),
        'front': (0.00, 0.25, 0.70),
        'back': (0.00, 0.55, 0.15),
        'internal': (0.02, 0.02, 0.03),
    },
    'Pastel': {
        'right': (1.0, 0.6, 0.6),
        'left': (1.0, 0.8, 0.4),
        'up': (0.95, 0.95, 0.95),
        'down': (1.0, 0.9, 0.5),
        'front': (0.6, 0.8, 1.0),
        'back': (0.6, 1.0, 0.6),
        'internal': (0.1, 0.1, 0.1),
    },
    'HighContrast': {
        'right': (1.0, 0.0, 0.0),
        'left': (1.0, 0.5, 0.0),
        'up': (1.0, 1.0, 1.0),
        'down': (1.0, 1.0, 0.0),
        'front': (0.0, 0.0, 1.0),
        'back': (0.0, 1.0, 0.0),
        'internal': (0.0, 0.0, 0.0),
    },
    'Metallic': {
        'right': (0.85, 0.15, 0.20),
        'left': (1.00, 0.55, 0.05),
        'up': (0.85, 0.85, 0.92),
        'down': (0.92, 0.75, 0.10),
        'front': (0.10, 0.45, 0.85),
        'back': (0.10, 0.72, 0.25),
        'internal': (0.20, 0.20, 0.22),
    },
    'BlackGold': {
        'right': (1.00, 0.05, 0.05),
        'left': (1.00, 0.50, 0.00),
        'up': (1.00, 0.84, 0.00),
        'down': (1.00, 1.00, 0.00),
        'front': (0.00, 0.30, 1.00),
        'back': (0.00, 0.90, 0.00),
        'internal': (0.00, 0.00, 0.00),
    },
    'Cyberpunk': {
        'right': (1.00, 0.10, 0.60),
        'left': (0.70, 0.20, 1.00),
        'up': (0.00, 1.00, 1.00),
        'down': (0.80, 1.00, 0.20),
        'front': (1.00, 0.60, 0.00),
        'back': (1.00, 0.00, 1.00),
        'internal': (0.10, 0.00, 0.20),
    },
    'Morandi': {
        'right': (0.80, 0.50, 0.50),
        'left': (0.70, 0.40, 0.20),
        'up': (0.90, 0.80, 0.70),
        'down': (0.50, 0.70, 0.50),
        'front': (0.40, 0.60, 0.80),
        'back': (0.60, 0.50, 0.70),
        'internal': (0.30, 0.28, 0.28),
    },
    'Monochrome': {
        'right': (0.70, 0.70, 0.70),
        'left': (0.40, 0.40, 0.40),
        'up': (0.90, 0.90, 0.90),
        'down': (0.60, 0.60, 0.60),
        'front': (0.80, 0.80, 0.80),
        'back': (0.30, 0.30, 0.30),
        'internal': (0.05, 0.05, 0.05),
    },
    'Rainbow': {
        'right': (1.00, 0.00, 0.00),
        'left': (1.00, 0.50, 0.00),
        'up': (1.00, 1.00, 0.00),
        'down': (0.00, 1.00, 0.00),
        'front': (0.00, 0.00, 1.00),
        'back': (0.50, 0.00, 0.50),
        'internal': (0.10, 0.10, 0.12),
    },
}


# ---------------------------------------------------------------------------
# 渲染辅助函数
# ---------------------------------------------------------------------------
CUBE_SIZE = 0.95
STICKER_INSET = 0.08

def draw_cube_piece(colors):
    """Draw a single cube piece (1x1x1) centered at the current model origin.
    colors: list of 6 color-name strings (right, left, up, down, front, back)."""
    glDisable(GL_LIGHTING)   # 纯色渲染，避免光照导致变黑
    s = CUBE_SIZE / 2.0
    # 黑色塑料主体
    glColor3f(*FACE_COLORS['internal'])
    glBegin(GL_QUADS)
    # 右面 (+x)
    glNormal3f(1, 0, 0);  glVertex3f(s, -s, -s); glVertex3f(s, s, -s); glVertex3f(s, s, s); glVertex3f(s, -s, s)
    # 左面 (-x)
    glNormal3f(-1, 0, 0); glVertex3f(-s, -s, s); glVertex3f(-s, s, s); glVertex3f(-s, s, -s); glVertex3f(-s, -s, -s)
    # 上面 (+y)
    glNormal3f(0, 1, 0);  glVertex3f(-s, s, -s); glVertex3f(-s, s, s); glVertex3f(s, s, s); glVertex3f(s, s, -s)
    # 下面 (-y)
    glNormal3f(0, -1, 0); glVertex3f(-s, -s, s); glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s); glVertex3f(s, -s, s)
    # 前面 (+z)
    glNormal3f(0, 0, 1);  glVertex3f(-s, -s, s); glVertex3f(s, -s, s); glVertex3f(s, s, s); glVertex3f(-s, s, s)
    # 后面 (-z)
    glNormal3f(0, 0, -1); glVertex3f(s, -s, -s); glVertex3f(-s, -s, -s); glVertex3f(-s, s, -s); glVertex3f(s, s, -s)
    glEnd()

    # 贴纸（略微凸起的彩色四边形）
    st = s - STICKER_INSET      # 贴纸 half-size
    off = s + 0.001             # tiny offset to avoid z-fighting
    def sticker(face):
        c = FACE_COLORS.get(colors[face], FACE_COLORS['internal'])
        glColor3f(*c)
        glBegin(GL_QUADS)
        if face == 0:    # right
            glNormal3f(1, 0, 0)
            glVertex3f(off, -st, -st); glVertex3f(off, st, -st); glVertex3f(off, st, st); glVertex3f(off, -st, st)
        elif face == 1:  # left
            glNormal3f(-1, 0, 0)
            glVertex3f(-off, -st, st); glVertex3f(-off, st, st); glVertex3f(-off, st, -st); glVertex3f(-off, -st, -st)
        elif face == 2:  # up
            glNormal3f(0, 1, 0)
            glVertex3f(-st, off, -st); glVertex3f(-st, off, st); glVertex3f(st, off, st); glVertex3f(st, off, -st)
        elif face == 3:  # down
            glNormal3f(0, -1, 0)
            glVertex3f(-st, -off, st); glVertex3f(-st, -off, -st); glVertex3f(st, -off, -st); glVertex3f(st, -off, st)
        elif face == 4:  # front
            glNormal3f(0, 0, 1)
            glVertex3f(-st, -st, off); glVertex3f(st, -st, off); glVertex3f(st, st, off); glVertex3f(-st, st, off)
        elif face == 5:  # back
            glNormal3f(0, 0, -1)
            glVertex3f(st, -st, -off); glVertex3f(-st, -st, -off); glVertex3f(-st, st, -off); glVertex3f(st, st, -off)
        glEnd()
    for f in range(6):
        if colors[f] != 'internal':
            sticker(f)

    glEnable(GL_LIGHTING)

# ---------------------------------------------------------------------------
# UI 按钮 (compatible with Pygame 1.9.6+)
# ---------------------------------------------------------------------------
class Button:
    _key_hint_font = None   # lazy-created shared small 字体

    def __init__(self, rect, label, color, key_hint='', font=None):
        if Button._key_hint_font is None:
            Button._key_hint_font = pygame.font.Font(None, 12)
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.key_hint = key_hint
        self.font = font          # optional per-按钮 字体 override
        self.hover = False
        self.press = False

    def draw(self, surf, font):
        r = self.rect
        btn_font = self.font or font   # use override if set
        # 阴影
        sh = pygame.Rect(r.x, r.y + 3, r.w, r.h)
        # 检查 Pygame 版本是否支持圆角边框
        if pygame.version.vernum >= (2, 0, 0):
            pygame.draw.rect(surf, (180, 184, 195), sh, border_radius=10)
        else:
            pygame.draw.rect(surf, (180, 184, 195), sh)

        # 主体背景
        base = self.color
        if self.press:
            base = tuple(max(0, c - 50) for c in base)
        elif self.hover:
            base = tuple(min(255, c + 18) for c in base)

        if pygame.version.vernum >= (2, 0, 0):
            pygame.draw.rect(surf, base, r, border_radius=10)
            pygame.draw.rect(surf, (255, 255, 255), r, width=2, border_radius=10)
        else:
            pygame.draw.rect(surf, base, r)
            pygame.draw.rect(surf, (255, 255, 255), r, 2)

        # 标签文字
        txt = btn_font.render(self.label, True, (255, 255, 255))
        tr = txt.get_rect(center=r.center)
        surf.blit(txt, tr)
        if self.key_hint:
            sf = Button._key_hint_font
            kt = sf.render(self.key_hint, True, (230, 230, 230))
            surf.blit(kt, (r.right - kt.get_width() - 6, r.bottom - kt.get_height() - 4))

    def handle(self, event):
        if event.type == MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.press = True
                return True
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.press = False
        return False

# ---------------------------------------------------------------------------
# 主 application
# ---------------------------------------------------------------------------
class App:
    @staticmethod
    def _load_cn_font(size):
        """Load a Chinese-capable font with fallback chain."""
        paths = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/STXIHEI.TTF',
            'C:/Windows/Fonts/Deng.ttf',
        ]
        for p in paths:
            try:
                return pygame.font.Font(p, size)
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def __init__(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        # 关闭文字输入模式，防止输入法拦截键盘事件
        pygame.key.stop_text_input()
        pygame.event.set_blocked(pygame.TEXTINPUT)
        pygame.display.set_caption("3D 魔方 - Rubik's Cube")
        flags = DOUBLEBUF | OPENGL
        try:
            self.screen = pygame.display.set_mode(
                (DISPLAY_W, DISPLAY_H), flags)
        except pygame.error:
            self.screen = pygame.display.set_mode(
                (DISPLAY_W, DISPLAY_H), flags, vsync=0)
        self.clock = pygame.time.Clock()

        self._init_gl()
        self.font_big = self._load_cn_font(22)
        self.font_med = self._load_cn_font(16)
        self.font_sm  = self._load_cn_font(13)

        self.cube = RubiksCube()
        self.gesture_ctrl = None   # GestureController, created on demand
        self.view_rot_x = -25.0
        self.view_rot_y = 30.0
        self.dragging = False
        self.last_mouse = (0, 0)

        # animation 状态
        self.anim = None          # dict: 轴, 层, target, elapsed, 持续时间, current
        self.queue = []           # pending (轴, 层, 角度) moves
        self.queue_label = ''     # text 标签 for current 队列 (打乱/求解/...)
        self.solve_method = '逆序还原'
        self.methods = self._build_methods()
        self.status_msg = '就绪'
        self.solution_text = ''
        self.move_count = 0
        self.total_moves = 0
        self.solve_speed = 1.0

        # 外观
        self.appearance_names = list(APPEARANCES.keys())
        self.current_appearance_index = 0
        self.apply_appearance(self.appearance_names[0])

        self._make_buttons()

    def _build_methods(self):
        """从 SolverFactory 获取可用方法列表。"""
        raw = SolverFactory.get_available_methods()
        # 确保 kociemba 可用时包含
        return raw

    def _make_buttons(self):
        y = DISPLAY_H - UI_HEIGHT + 56    # 56px from bottom of UI strip
        h = 58
        gap = 14
        w = 145
        x0 = 30
        self.btn_scramble = Button((x0, y, w, h), '打乱', (245, 158, 30), 'S',
                                   font=self.font_big)
        self.btn_solve    = Button((x0 + (w + gap), y, w, h), '复原', (45, 185, 72), 'Space',
                                   font=self.font_big)
        self.btn_reset    = Button((x0 + 2 * (w + gap), y, w, h), '重置', (110, 118, 135), 'Backspace')
        self.btn_method   = Button((x0 + 3 * (w + gap), y, w, h), '解法', (70, 115, 185), 'M')
        self.btn_appearance = Button((x0 + 4 * (w + gap), y, w, h), '外观', (155, 89, 182), 'A')
        self.btn_gesture  = Button((x0 + 5 * (w + gap), y, w, h), '手势', (200, 60, 60), 'G')
        self.buttons = [self.btn_scramble, self.btn_solve, self.btn_reset,
                        self.btn_method, self.btn_appearance, self.btn_gesture]

    def _init_gl(self):
        # 浅色背景
        glClearColor(0.90, 0.92, 0.95, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(42, (DISPLAY_W / (DISPLAY_H - UI_HEIGHT)), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.65, 0.65, 0.68, 1))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, (-6, 10, 8, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.35, 0.35, 0.35, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1))
        glLightfv(GL_LIGHT1, GL_POSITION, (6, 4, -5, 1))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.5, 0.5, 0.6, 1))
        glLightfv(GL_LIGHT1, GL_AMBIENT, (0.25, 0.25, 0.28, 1))
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glEnable(GL_MULTISAMPLE)

    # -- 外观 -----------------------------------------------------------
    def apply_appearance(self, name):
        """Apply a color theme by name."""
        if name in APPEARANCES:
            FACE_COLORS.update(APPEARANCES[name])
            self.status_msg = f'外观: {name}'
        else:
            self.status_msg = f'未知外观: {name}'

    def cycle_appearance(self):
        """Cycle to the next appearance theme."""
        self.current_appearance_index = (self.current_appearance_index + 1) % len(self.appearance_names)
        name = self.appearance_names[self.current_appearance_index]
        self.apply_appearance(name)

    # -- 动画 -----------------------------------------------------------
    def start_queue(self, moves, label, speed=1.0):
        if not moves:
            return
        self.queue = list(moves)
        self.queue_label = label
        self.total_moves = len(moves)
        self.move_count = 0
        self._next_anim(speed)

    def _next_anim(self, speed=1.0):
        if not self.queue:
            self.anim = None
            return
        axis, layer, angle = self.queue.pop(0)
        duration = 0.22 / speed
        self.anim = {
            'axis': axis, 'layer': layer, 'target': angle,
            'elapsed': 0.0, 'duration': duration, 'current': 0.0,
            'speed': speed,
        }

    def _finish_anim(self):
        """Apply the final move to state and start the next one."""
        a = self.anim
        self.cube.apply_move(a['axis'], a['layer'], a['target'])
        self.move_count += 1
        self.anim = None
        if self.queue:
            self._next_anim(self.queue_speed)
        else:
            self._on_queue_done()

    def _on_queue_done(self):
        if self.queue_label == 'Solve':
            if self.cube.is_solved():
                self.status_msg = '已还原！'
            else:
                self.status_msg = '还原不完整，请重试'
        elif self.queue_label == 'Scramble':
            self.status_msg = '已打乱'
        elif self.queue_label == 'Reset':
            self.status_msg = '已重置为初始状态'
        elif self.queue_label == 'Manual':
            self.status_msg = '就绪'
        self.queue_label = ''

    @property
    def queue_speed(self):
        if self.queue_label == 'Solve':
            return 1.8
        if self.queue_label == 'Scramble':
            return 1.5
        return 1.0

    # -- 操作 ------------------------------------------------------------
    def do_scramble(self):
        if self.anim or self.queue:
            return
        moves = self.cube.scramble(25)
        self.solution_text = ' '.join(self._ala_to_str(m) for m in moves)
        self.status_msg = '正在打乱...'
        self.start_queue(moves, 'Scramble', speed=1.5)

    def do_solve(self):
        if self.anim or self.queue:
            return
        if self.cube.is_solved():
            self.status_msg = '已经是还原状态'
            return

        method = self.solve_method
        solver = SolverFactory.get_solver(method)

        # Kociemba 库缺失 → 弹窗提示
        if not solver.is_available():
            self.status_msg = f'需要安装 kociemba 库: pip install kociemba'
            return

        moves = solver.solve(self.cube)
        if moves:
            self.solution_text = ' '.join(self._ala_to_str(m) for m in moves)
            self.status_msg = f'正在以 {solver.name} 还原（{len(moves)} 步）...'
            self.start_queue(moves, 'Solve', speed=self.solve_speed)
        else:
            self.status_msg = f'{solver.name}: 无法复原'

    def do_reset(self):
        if self.anim or self.queue:
            return
        self.cube.reset()
        self.solution_text = ''
        self.status_msg = '已重置为初始状态'
        self.move_count = 0
        self.total_moves = 0

    def cycle_method(self):
        idx = self.methods.index(self.solve_method)
        self.solve_method = self.methods[(idx + 1) % len(self.methods)]

    def do_rotate(self, move):
        if self.anim or self.queue:
            return
        axis, layer, angle = MOVE_TO_ALA[move]
        self.start_queue([(axis, layer, angle)], 'Manual')
        self.status_msg = f'旋转: {move}'

    @staticmethod
    def _ala_to_str(m):
        return ALA_TO_MOVE.get(m, '?')

    def _screen_to_ray(self, mx, my):
        """Convert screen (mx, my) to a ray (origin, dir) in world space."""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(42, DISPLAY_W / (DISPLAY_H - UI_HEIGHT), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -9.5)
        glRotatef(self.view_rot_x, 1, 0, 0)
        glRotatef(self.view_rot_y, 0, 1, 0)

        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        if len(viewport) < 4:
            viewport = (0, 0, DISPLAY_W, DISPLAY_H)

        gl_y = DISPLAY_H - my
        near = gluUnProject(mx, gl_y, 0.0, modelview, projection, viewport)
        far  = gluUnProject(mx, gl_y, 1.0, modelview, projection, viewport)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        if near is None or far is None:
            return None, None
        origin = (near[0], near[1], near[2])
        d = (far[0] - near[0], far[1] - near[1], far[2] - near[2])
        length = math.sqrt(d[0]**2 + d[1]**2 + d[2]**2)
        if length < 1e-12:
            return None, None
        d = (d[0]/length, d[1]/length, d[2]/length)
        return origin, d

    @staticmethod
    def _ray_aabb_intersect(origin, dir, aabb_min, aabb_max):
        """Ray-AABB slab intersection. Returns (t, face_normal) or None."""
        tmin = -1e9
        tmax = 1e9
        hit_axis = 0
        hit_sign = 0
        for i in range(3):
            if abs(dir[i]) < 1e-12:
                if origin[i] < aabb_min[i] or origin[i] > aabb_max[i]:
                    return None
            else:
                t1 = (aabb_min[i] - origin[i]) / dir[i]
                t2 = (aabb_max[i] - origin[i]) / dir[i]
                if t1 > t2:
                    t1, t2 = t2, t1
                if t1 > tmin:
                    tmin = t1
                    hit_axis = i
                    hit_sign = -1 if dir[i] > 0 else 1
                tmax = min(tmax, t2)
                if tmin > tmax:
                    return None
        if tmin < 0:
            return None
        normal = [0, 0, 0]
        normal[hit_axis] = hit_sign
        return tmin, tuple(normal)

    def _pick_face(self, mx, my):
        """Ray-cast to find which cube face was clicked.
        Returns (axis, layer, angle) for a standard move, or None."""
        if self.anim or self.queue:
            return None
        ray_origin, ray_dir = self._screen_to_ray(mx, my)
        if ray_origin is None:
            return None

        half = CUBE_SIZE / 2.0
        best_t = float('inf')
        best_info = None

        for cubie in self.cube.cubes:
            x, y, z = cubie['pos']
            rx, ry, rz = round(x), round(y), round(z)
            aabb_min = (rx - half, ry - half, rz - half)
            aabb_max = (rx + half, ry + half, rz + half)
            result = self._ray_aabb_intersect(ray_origin, ray_dir, aabb_min, aabb_max)
            if result:
                t, normal = result
                if t < best_t:
                    best_t = t
                    # Determine 轴 from 面 normal
                    ax, ay, az = abs(normal[0]), abs(normal[1]), abs(normal[2])
                    if ax >= ay and ax >= az:
                        axis = 'x'; layer = rx
                    elif ay >= ax and ay >= az:
                        axis = 'y'; layer = ry
                    else:
                        axis = 'z'; layer = rz
                    # 角度: normal pointing + → -90 (standard CW), normal pointing - → +90 (standard CCW)
                    nv = normal[0] + normal[1] + normal[2]
                    angle = -90 if nv > 0 else 90
                    best_info = (axis, layer, angle)
        return best_info

    # -- 主 循环 -----------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_s:
                        self.do_scramble()
                    elif event.key in (K_SPACE, K_RETURN):
                        self.do_solve()
                    elif event.key == K_BACKSPACE:
                        self.do_reset()
                    elif event.key == K_m:
                        self.cycle_method()
                    elif event.key == K_a:
                        self.cycle_appearance()
                    # --- 面旋转（支持 Shift 反向）---
                    elif event.key == K_u:
                        move = "U'" if event.mod & KMOD_SHIFT else 'U'
                        self.do_rotate(move)
                    elif event.key == K_d:
                        move = "D'" if event.mod & KMOD_SHIFT else 'D'
                        self.do_rotate(move)
                    elif event.key == K_l:
                        move = "L'" if event.mod & KMOD_SHIFT else 'L'
                        self.do_rotate(move)
                    elif event.key == K_r:
                        move = "R'" if event.mod & KMOD_SHIFT else 'R'
                        self.do_rotate(move)
                    elif event.key == K_f:
                        move = "F'" if event.mod & KMOD_SHIFT else 'F'
                        self.do_rotate(move)
                    elif event.key == K_b:
                        move = "B'" if event.mod & KMOD_SHIFT else 'B'
                        self.do_rotate(move)
                    elif event.key == K_g:
                        self.toggle_gesture()
                    elif event.key in (K_EQUALS, K_PLUS):
                        self.solve_speed = min(5.0, self.solve_speed + 0.3)
                        self.status_msg = f'复原速度: {self.solve_speed:.1f}x'
                    elif event.key == K_MINUS:
                        self.solve_speed = max(0.2, self.solve_speed - 0.3)
                        self.status_msg = f'复原速度: {self.solve_speed:.1f}x'

                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[1] < DISPLAY_H - UI_HEIGHT:
                        self.dragging = True
                        self.last_mouse = event.pos
                    else:
                        for b in self.buttons:
                            if b.handle(event):
                                self._on_button(b)
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False
                    for b in self.buttons:
                        b.handle(event)
                elif event.type == MOUSEBUTTONDOWN and event.button == 3:
                    if event.pos[1] < DISPLAY_H - UI_HEIGHT:
                        pick = self._pick_face(*event.pos)
                        if pick:
                            axis, layer, angle = pick
                            self.start_queue([(axis, layer, angle)], 'Manual')
                            # Show which 面 was clicked
                            face_names = {
                                ('x', 1): 'R', ('x', -1): 'L',
                                ('y', 1): 'U', ('y', -1): 'D',
                                ('z', 1): 'F', ('z', -1): 'B',
                            }
                            move_name = face_names.get((axis, layer), '?')
                            if angle == 90:
                                move_name += "'"
                            self.status_msg = f'右键: {move_name}'
                elif event.type == MOUSEMOTION:
                    for b in self.buttons:
                        b.handle(event)
                    if self.dragging:
                        dx = event.pos[0] - self.last_mouse[0]
                        dy = event.pos[1] - self.last_mouse[1]
                        self.view_rot_y += dx * 1.5
                        self.view_rot_x += dy * 1.5
                        # 限制上下角度防止翻转
                        self.view_rot_x = max(-89.0, min(89.0, self.view_rot_x))
                        self.view_rot_y %= 360.0
                        self.last_mouse = event.pos

            self._update(dt)
            self._handle_gesture()
            self._render()
            pygame.display.flip()
        if self.gesture_ctrl:
            self.gesture_ctrl.stop()
        pygame.quit()

    def _on_button(self, b):
        if b is self.btn_scramble:
            self.do_scramble()
        elif b is self.btn_solve:
            self.do_solve()
        elif b is self.btn_reset:
            self.do_reset()
        elif b is self.btn_method:
            self.cycle_method()
        elif b is self.btn_appearance:
            self.cycle_appearance()
        elif b is self.btn_gesture:
            self.toggle_gesture()

    def toggle_gesture(self):
        """Toggle camera gesture control on/off."""
        if self.gesture_ctrl is None:
            from src.ui.gesture_control import GestureController
            self.gesture_ctrl = GestureController()
        if self.gesture_ctrl.is_active:
            self.gesture_ctrl.stop()
            self.status_msg = '手势控制: 关闭'
            self.btn_gesture.color = (200, 60, 60)
        else:
            ok = self.gesture_ctrl.start()
            if ok:
                self.status_msg = '手势控制: 已开启 - 摄像头窗口已弹出'
                self.btn_gesture.color = (60, 180, 60)
            else:
                self.status_msg = '手势控制: 启动失败（检查摄像头）'
                self.btn_gesture.color = (200, 60, 60)

    def _handle_gesture(self):
        """Check gesture queue and execute commands (called each frame)."""
        if self.gesture_ctrl is None or not self.gesture_ctrl.is_active:
            return
        cmd = self.gesture_ctrl.get_command()
        if cmd is None:
            return
        if cmd == 'scramble':
            self.do_scramble()
        elif cmd == 'solve':
            self.do_solve()
        elif cmd in ('U', 'D', 'R', 'L', 'F', 'B'):
            self.do_rotate(cmd)
            self.status_msg = f'手势: {cmd}'

    def _update(self, dt):
        if self.anim:
            self.anim['elapsed'] += dt
            t = min(self.anim['elapsed'] / self.anim['duration'], 1.0)
            self.anim['current'] = self.anim['target'] * ease_in_out_cubic(t)
            if t >= 1.0:
                self._finish_anim()

    def _render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -9.5)
        glRotatef(self.view_rot_x, 1, 0, 0)
        glRotatef(self.view_rot_y, 0, 1, 0)

        # 绘制 cube
        anim = self.anim
        for cube in self.cube.cubes:
            x, y, z = cube['pos']
            rx, ry, rz = round(x), round(y), round(z)
            in_layer = False
            if anim:
                ax = anim['axis']; ly = anim['layer']
                if (ax == 'x' and rx == ly) or (ax == 'y' and ry == ly) or (ax == 'z' and rz == ly):
                    in_layer = True
            glPushMatrix()
            if in_layer:
                if anim['axis'] == 'x':
                    glRotatef(anim['current'], 1, 0, 0)
                elif anim['axis'] == 'y':
                    glRotatef(anim['current'], 0, 1, 0)
                else:
                    glRotatef(anim['current'], 0, 0, 1)
            glTranslatef(x, y, z)
            draw_cube_piece(cube['color'])
            glPopMatrix()

        # 2D 覆盖层
        self._draw_ui()

    def _draw_ui(self):
        # 切换到 2D 正交投影绘制 UI 栏
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, DISPLAY_W, DISPLAY_H, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        # UI background 面板
        glColor3f(0.96, 0.97, 0.99)
        glBegin(GL_QUADS)
        glVertex2f(0, DISPLAY_H - UI_HEIGHT)
        glVertex2f(DISPLAY_W, DISPLAY_H - UI_HEIGHT)
        glVertex2f(DISPLAY_W, DISPLAY_H)
        glVertex2f(0, DISPLAY_H)
        glEnd()
        # 顶部边框线
        glColor3f(0.72, 0.75, 0.82)
        glBegin(GL_QUADS)
        glVertex2f(0, DISPLAY_H - UI_HEIGHT)
        glVertex2f(DISPLAY_W, DISPLAY_H - UI_HEIGHT)
        glVertex2f(DISPLAY_W, DISPLAY_H - UI_HEIGHT + 2)
        glVertex2f(0, DISPLAY_H - UI_HEIGHT + 2)
        glEnd()

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # 绘制 pygame surfaces for text and buttons
        self._draw_pygame_ui()

    def _draw_pygame_ui(self):
        # 创建 a 表面 for the UI strip
        ui_surf = pygame.Surface((DISPLAY_W, UI_HEIGHT), pygame.SRCALPHA)
        # 状态 text (includes appearance if not in animation)
        status = self.font_big.render(self.status_msg, True, (40, 44, 55))
        ui_surf.blit(status, (30, 8))

        # 方法指示器 + 外观
        display_names = SolverFactory.get_solver_display_names()
        method_label = display_names.get(self.solve_method, self.solve_method)
        app_name = self.appearance_names[self.current_appearance_index]
        info_text = f'解法: {method_label}  |  主题: {app_name}  |  速度: {self.solve_speed:.1f}x'
        mt = self.font_med.render(info_text, True, (70, 78, 95))
        ui_surf.blit(mt, (30, 36))

        # 进度条（条状+文字）
        if self.total_moves > 0:
            # 进度条右对齐
            bar_w, bar_h = 260, 18
            bar_x = DISPLAY_W - bar_w - 30
            bar_y = 10
            progress = min(self.move_count / max(1, self.total_moves), 1.0)

            # 背景（圆角条）
            pygame.draw.rect(ui_surf, (195, 195, 200), (bar_x, bar_y, bar_w, bar_h), border_radius=9)

            # 渐变填充：从左(绿色)到右(亮绿)
            fill_width = int(bar_w * progress)
            if fill_width > 0:
                for i in range(fill_width):
                    t = i / max(1, bar_w - 1)
                    r = int(40 + t * 40)    # 40→80
                    g = int(170 + t * 85)   # 170→255
                    b = int(60 + t * 40)    # 60→100
                    pygame.draw.line(ui_surf, (r, g, b),
                                     (bar_x + i, bar_y + 2),
                                     (bar_x + i, bar_y + bar_h - 3))

            # 卡通角色：随进度移动的小圆脸
            if progress > 0.01:
                cx = bar_x + fill_width
                cy = bar_y + bar_h // 2
                r = 9
                # 身体（渐变圆）
                pygame.draw.circle(ui_surf, (255, 220, 80), (cx, cy), r)
                pygame.draw.circle(ui_surf, (255, 240, 140), (cx - 1, cy - 1), r - 1)
                # 眼睛
                eye_offset = 3
                pygame.draw.circle(ui_surf, (40, 44, 55), (cx - eye_offset, cy - 2), 2)
                pygame.draw.circle(ui_surf, (40, 44, 55), (cx + eye_offset, cy - 2), 2)
                # 微笑
                smile_y = cy + 3
                pygame.draw.arc(ui_surf, (40, 44, 55),
                                (cx - 4, smile_y - 2, 8, 5),
                                0.2, 2.9, 1)

            # 文字：步数/总数（在进度条上方）
            prog_text = self.font_sm.render(f"{self.move_count}/{self.total_moves}", True, (80, 86, 100))
            ui_surf.blit(prog_text, (bar_x - prog_text.get_width() - 10, bar_y))

        # 解法 text
        if self.solution_text:
            sol_label = self.font_sm.render('解法步骤:', True, (90, 96, 110))
            ui_surf.blit(sol_label, (30, 58))
            # wrap 解法 text
            sol = self.solution_text
            max_w = DISPLAY_W - 160
            words = sol.split()
            line = ''
            y_off = 76
            for w in words:
                test = (line + ' ' + w).strip()
                if self.font_sm.size(test)[0] > max_w and line:
                    t = self.font_sm.render(line, True, (55, 60, 72))
                    ui_surf.blit(t, (30, y_off))
                    y_off += 16
                    line = w
                else:
                    line = test
            if line:
                t = self.font_sm.render(line, True, (55, 60, 72))
                ui_surf.blit(t, (30, y_off))

        # 按钮
        for b in self.buttons:
            b.draw(ui_surf, self.font_med)

        # Blit the UI 表面 to screen via OpenGL
        self._blit_surface(ui_surf, 0, DISPLAY_H - UI_HEIGHT)

        # Also 绘制 top help text
        help_surf = pygame.Surface((DISPLAY_W, 28), pygame.SRCALPHA)
        # Use a smaller 字体 (10px) so the long help text fits within the window
        help_font = self._load_cn_font(10)
        ht = help_font.render(
            '拖拽: 旋转视角 | U/D/L/R/F/B: 旋转层(Shift反向) | S: 打乱 | Space: 复原 | Backspace: 重置 | M: 解法 | A: 主题 | G: 手势 | +/-: 速度 | 右键点击: 旋转面 | ESC: 退出',
            True, (80, 86, 100))
        help_surf.blit(ht, (30, 6))
        self._blit_surface(help_surf, 0, 0)

    def _blit_surface(self, surf, x, y):
        """Blit a pygame surface onto the OpenGL screen at pixel (x,y) top-left."""
        tex_data = pygame.image.tostring(surf, 'RGBA', True)
        w, h = surf.get_size()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, DISPLAY_W, DISPLAY_H, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)          # 左上
        glTexCoord2f(1, 1); glVertex2f(x + w, y)     # 右上
        glTexCoord2f(1, 0); glVertex2f(x + w, y + h) # 右下
        glTexCoord2f(0, 0); glVertex2f(x, y + h)     # 左下
        glEnd()
        glDeleteTextures([tex])
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


def main():
    app = App()
    app.run()

if __name__ == '__main__':
    main()

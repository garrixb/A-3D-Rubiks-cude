"""
魔方数据模型 — RubiksCube 类
管理 3×3×3 魔方的状态、旋转、面串输出。
"""
import copy
import math

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
SOLVED_FACELET_STRING = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB'

# 标准面顺序（Kociemba 顺序）：U, R, F, D, L, B
COLOR_TO_FACE = {'right': 'R', 'left': 'L', 'up': 'U',
                 'down': 'D', 'front': 'F', 'back': 'B'}

# Facelet 位置表 (cube_pos, color_index)，对应 54 个面块。
# 顺序遵循 Kociemba 标准：U R F D L B，每面逐行排列。
FACELET_MAP = {
    'U': [((-1,1,-1),2), ((0,1,-1),2), ((1,1,-1),2),
          ((-1,1, 0),2), ((0,1, 0),2), ((1,1, 0),2),
          ((-1,1, 1),2), ((0,1, 1),2), ((1,1, 1),2)],
    'R': [((1, 1, 1),0), ((1, 1, 0),0), ((1, 1,-1),0),
          ((1, 0, 1),0), ((1, 0, 0),0), ((1, 0,-1),0),
          ((1,-1, 1),0), ((1,-1, 0),0), ((1,-1,-1),0)],
    'F': [((-1,1, 1),4), ((0,1, 1),4), ((1,1, 1),4),
          ((-1,0, 1),4), ((0,0, 1),4), ((1,0, 1),4),
          ((-1,-1,1),4), ((0,-1,1),4), ((1,-1,1),4)],
    'D': [((-1,-1, 1),3), ((0,-1, 1),3), ((1,-1, 1),3),
          ((-1,-1, 0),3), ((0,-1, 0),3), ((1,-1, 0),3),
          ((-1,-1,-1),3), ((0,-1,-1),3), ((1,-1,-1),3)],
    'L': [((-1,1,-1),1), ((-1,1, 0),1), ((-1,1, 1),1),
          ((-1,0,-1),1), ((-1,0, 0),1), ((-1,0, 1),1),
          ((-1,-1,-1),1), ((-1,-1,0),1), ((-1,-1,1),1)],
    'B': [((1,1,-1),5), ((0,1,-1),5), ((-1,1,-1),5),
          ((1,0,-1),5), ((0,0,-1),5), ((-1,0,-1),5),
          ((1,-1,-1),5), ((0,-1,-1),5), ((-1,-1,-1),5)],
}

# 标准移动 → (axis, layer, angle)
MOVE_TO_ALA = {
    'U':  ('y',  1, -90), "U'": ('y',  1,  90), 'U2': ('y',  1, 180),
    'D':  ('y', -1,  90), "D'": ('y', -1, -90), 'D2': ('y', -1, 180),
    'R':  ('x',  1, -90), "R'": ('x',  1,  90), 'R2': ('x',  1, 180),
    'L':  ('x', -1,  90), "L'": ('x', -1, -90), 'L2': ('x', -1, 180),
    'F':  ('z',  1, -90), "F'": ('z',  1,  90), 'F2': ('z',  1, 180),
    'B':  ('z', -1,  90), "B'": ('z', -1, -90), 'B2': ('z', -1, 180),
}
ALA_TO_MOVE = {v: k for k, v in MOVE_TO_ALA.items()}


class RubiksCube:
    """3×3×3 魔方状态管理。"""

    FACE_ORDER = ('right', 'left', 'up', 'down', 'front', 'back')

    def __init__(self):
        self.cubes = None
        self.move_history = []   # [(轴, 层, 角度), ...]
        self.reset()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------
    def reset(self):
        """重置魔方到还原状态。"""
        self.cubes = []
        self.move_history.clear()
        for x in (-1, 0, 1):
            for y in (-1, 0, 1):
                for z in (-1, 0, 1):
                    colors = ['internal'] * 6
                    if x == 1:   colors[0] = 'right'
                    if x == -1:  colors[1] = 'left'
                    if y == 1:   colors[2] = 'up'
                    if y == -1:  colors[3] = 'down'
                    if z == 1:   colors[4] = 'front'
                    if z == -1:  colors[5] = 'back'
                    self.cubes.append({'pos': [x, y, z], 'color': colors})

    # ------------------------------------------------------------------
    # 旋转
    # ------------------------------------------------------------------
    def apply_move(self, axis, layer, angle, record=True):
        """对一个层执行旋转。record=False 时不记录历史（用于求解验证）。"""
        self._apply_to(self.cubes, axis, layer, angle)
        if record:
            self.move_history.append((axis, layer, angle))

    def apply_moves(self, moves):
        """批量执行旋转。moves: [(axis, layer, angle), ...]"""
        for axis, layer, angle in moves:
            self._apply_to(self.cubes, axis, layer, angle)
            self.move_history.append((axis, layer, angle))

    # -- 颜色旋转（与位置旋转完全对应）-----------------
    @staticmethod
    def _rotate_colors(colors, axis, angle):
        new = colors.copy()
        if abs(angle) == 180:
            if axis == 'x':
                new[2], new[3] = colors[3], colors[2]
                new[4], new[5] = colors[5], colors[4]
            elif axis == 'y':
                new[0], new[1] = colors[1], colors[0]
                new[4], new[5] = colors[5], colors[4]
            elif axis == 'z':
                new[0], new[1] = colors[1], colors[0]
                new[2], new[3] = colors[3], colors[2]
        elif axis == 'x':
            if angle > 0:   # +90 CCW from +x : up->front->down->back->up
                new[4], new[3], new[5], new[2] = colors[2], colors[4], colors[3], colors[5]
            else:           # -90 CW  from +x : up->back->down->front->up
                new[5], new[3], new[4], new[2] = colors[2], colors[5], colors[3], colors[4]
        elif axis == 'y':
            if angle > 0:   # +90 CCW from +y : right->back->left->front->right
                new[5], new[1], new[4], new[0] = colors[0], colors[5], colors[1], colors[4]
            else:
                new[4], new[1], new[5], new[0] = colors[0], colors[4], colors[1], colors[5]
        elif axis == 'z':
            if angle > 0:   # +90 CCW from +z : right->up->left->down->right
                new[2], new[1], new[3], new[0] = colors[0], colors[2], colors[1], colors[3]
            else:
                new[3], new[1], new[2], new[0] = colors[0], colors[3], colors[1], colors[2]
        return new

    @staticmethod
    def _apply_to(cubes, axis, layer, angle):
        angle = ((angle + 180) % 360) - 180
        if angle == 0:
            return
        if angle == 90:     cos_a, sin_a = 0, 1
        elif angle == -90:  cos_a, sin_a = 0, -1
        else:               cos_a, sin_a = -1, 0   # 180
        for cube in cubes:
            x, y, z = cube['pos']
            rx, ry, rz = round(x), round(y), round(z)
            if axis == 'x' and rx == layer:
                ny = y * cos_a - z * sin_a
                nz = y * sin_a + z * cos_a
                cube['pos'] = [float(rx), round(ny), round(nz)]
                cube['color'] = RubiksCube._rotate_colors(cube['color'], axis, angle)
            elif axis == 'y' and ry == layer:
                nx = x * cos_a + z * sin_a
                nz = -x * sin_a + z * cos_a
                cube['pos'] = [round(nx), float(ry), round(nz)]
                cube['color'] = RubiksCube._rotate_colors(cube['color'], axis, angle)
            elif axis == 'z' and rz == layer:
                nx = x * cos_a - y * sin_a
                ny = x * sin_a + y * cos_a
                cube['pos'] = [round(nx), round(ny), float(rz)]
                cube['color'] = RubiksCube._rotate_colors(cube['color'], axis, angle)

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------
    def is_solved(self):
        return self.get_facelet_string() == SOLVED_FACELET_STRING

    # -- 面块字符串（用于 Kociemba）---------------------------------------
    def get_facelet_string(self):
        pos_map = {}
        for cube in self.cubes:
            x, y, z = cube['pos']
            pos_map[(round(x), round(y), round(z))] = cube['color']
        s = ''
        for face in ('U', 'R', 'F', 'D', 'L', 'B'):
            for (cp, ci) in FACELET_MAP[face]:
                s += COLOR_TO_FACE[pos_map[cp][ci]]
        return s

    def verify(self, moves):
        """Apply moves to a copy and check solved."""
        snap = copy.deepcopy(self.cubes)
        for a, l, ang in moves:
            self._apply_to(snap, a, l, ang)
        fs = ''
        pos_map = {}
        for cube in snap:
            x, y, z = cube['pos']
            pos_map[(round(x), round(y), round(z))] = cube['color']
        for face in ('U', 'R', 'F', 'D', 'L', 'B'):
            for (cp, ci) in FACELET_MAP[face]:
                fs += COLOR_TO_FACE[pos_map[cp][ci]]
        return fs == SOLVED_FACELET_STRING

    def copy_state(self):
        """返回当前状态的深拷贝（用于求解器）。"""
        return copy.deepcopy(self)

    def scramble(self, n=25):
        """生成随机打乱序列。返回 move 列表 [(axis, layer, angle), ...]"""
        faces = [
            ('x', 1), ('x', -1),
            ('y', 1), ('y', -1),
            ('z', 1), ('z', -1),
        ]
        moves = []
        prev = None
        import random
        for _ in range(n):
            while True:
                f = random.choice(faces)
                if f != prev:
                    break
            prev = f
            angle = random.choice([-90, 90, 180])
            moves.append((f[0], f[1], angle))
        return moves

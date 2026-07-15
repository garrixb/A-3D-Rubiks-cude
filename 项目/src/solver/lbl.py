"""
层先法(LBL)求解器 — 使用 MagicCube 开源库
"""
from magiccube import Cube as MagicCube
from magiccube.solver.basic.basic_solver import BasicSolver
from src.model.cube_model import RubiksCube, MOVE_TO_ALA
from src.solver.base import SolverBase


class LBLSolver(SolverBase):
    name = '层先法(LBL)'
    description = '基于MagicCube开源库的层先法求解器'
    requires_lib = True  # 明确依赖MagicCube

    # 类级别映射表，静态且只读
    ALA_TO_MAGIC = {
        ('x', 1, -90): 'R',   ('x', 1, 90): "R'",   ('x', 1, 180): 'R2',
        ('x', -1, 90): 'L',   ('x', -1, -90): "L'", ('x', -1, 180): 'L2',
        ('y', 1, -90): 'U',   ('y', 1, 90): "U'",   ('y', 1, 180): 'U2',
        ('y', -1, 90): 'D',   ('y', -1, -90): "D'", ('y', -1, 180): 'D2',
        ('z', 1, -90): 'F',   ('z', 1, 90): "F'",   ('z', 1, 180): 'F2',
        ('z', -1, 90): 'B',   ('z', -1, -90): "B'", ('z', -1, 180): 'B2',
    }

    MAGIC_TO_ALA = {
        'R': ('x', 1, -90),   "R'": ('x', 1, 90),   'R2': ('x', 1, 180),
        'L': ('x', -1, 90),   "L'": ('x', -1, -90), 'L2': ('x', -1, 180),
        'U': ('y', 1, -90),   "U'": ('y', 1, 90),   'U2': ('y', 1, 180),
        'D': ('y', -1, 90),   "D'": ('y', -1, -90), 'D2': ('y', -1, 180),
        'F': ('z', 1, -90),   "F'": ('z', 1, 90),   'F2': ('z', 1, 180),
        'B': ('z', -1, 90),   "B'": ('z', -1, -90), 'B2': ('z', -1, 180),
    }

    def solve(self, cube, method=''):
        # 1. 将当前cube状态转换为MagicCube并应用移动历史
        mc = MagicCube(3)
        for axis, layer, angle in cube.move_history:
            magic_move = self.ALA_TO_MAGIC.get((axis, layer, angle))
            if magic_move:
                mc.rotate(magic_move)
            # 若映射不存在，可记录警告（此处省略）

        # 2. 调用MagicCube的层先求解器
        solver = BasicSolver(mc)
        solution = solver.solve()  # 返回类似 ['R', "U'", ...] 的列表

        # 3. 将MagicCube移动转换为项目内部移动表示
        moves = [self.MAGIC_TO_ALA.get(str(move)) for move in solution]
        moves = [m for m in moves if m is not None]  # 过滤无效移动（理论上不会发生）

        # 4. 验证解的有效性：应用到副本检查是否还原
        test_cube = cube.copy_state()
        test_cube.apply_moves(moves)
        return moves if test_cube.is_solved() else []
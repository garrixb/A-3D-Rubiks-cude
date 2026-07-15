"""
Kociemba 两阶段最优求解器。
若 kociemba 库未安装，弹出提示弹窗并标记为不可用。
"""
import sys
from src.model.cube_model import RubiksCube, MOVE_TO_ALA, SOLVED_FACELET_STRING, FACELET_MAP, COLOR_TO_FACE
from src.solver.base import SolverBase

# ---------------------------------------------------------------------------
# 尝试导入 kociemba 库
# ---------------------------------------------------------------------------
KOCIEMBA_AVAILABLE = False
_kociemba = None
try:
    import kociemba as _kociemba
    KOCIEMBA_AVAILABLE = True
except ImportError:
    KOCIEMBA_AVAILABLE = False


class KociembaSolver(SolverBase):
    name = 'Kociemba(最优)'
    description = '使用 kociemba 库的两阶段最优算法，计算最短解法'
    requires_lib = True
    lib_name = 'kociemba'

    def __init__(self):
        super().__init__()
        self._lib_available = KOCIEMBA_AVAILABLE

    def solve(self, cube: RubiksCube, method: str = '') -> list:
        if not self._lib_available:
            return []
        fs = cube.get_facelet_string()
        if fs == SOLVED_FACELET_STRING:
            return []
        try:
            solution = _kociemba.solve(fs)
            moves = self._parse_solution(solution)
            if moves and cube.verify(moves):
                return moves
        except Exception:
            pass
        return []

    @staticmethod
    def _parse_solution(solution_str):
        """将 kociemba 输出的空格分隔字符串解析为 ALA 格式。"""
        moves = []
        for token in solution_str.strip().split():
            if token in MOVE_TO_ALA:
                moves.append(MOVE_TO_ALA[token])
        return moves

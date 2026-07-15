"""
逆序求解器 — Reverse Solver
将打乱历史反转取反，原路返回。
总是可用，无需额外库。
"""
from src.model.cube_model import RubiksCube, MOVE_TO_ALA
from src.solver.base import SolverBase


class ReverseSolver(SolverBase):
    name = '逆序还原'
    description = '将打乱步骤反转取反，原路返回（100% 成功）'
    requires_lib = False

    def solve(self, cube: RubiksCube, method: str = '') -> list:
        moves = cube.move_history.copy()
        if not moves:
            return []
        reversed_moves = [(a, l, -ang) for a, l, ang in reversed(moves)]
        return self._optimize(reversed_moves)

    @staticmethod
    def _optimize(moves):
        """Merge / cancel consecutive moves on the same face."""
        if not moves:
            return []
        result = [moves[0]]
        for mv in moves[1:]:
            if result:
                p = result[-1]
                if p[0] == mv[0] and p[1] == mv[1]:
                    combined = ((p[2] + mv[2] + 180) % 360) - 180
                    result.pop()
                    if combined != 0:
                        result.append((p[0], p[1], combined))
                    continue
            result.append(mv)
        return result

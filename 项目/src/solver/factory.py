"""
求解器工厂 — SolverFactory
Strategy 模式 + Factory 模式：
- 注册所有可用求解器
- 按用户选择返回对应求解器实例
- 提供兜底机制（自动降级）
"""
from src.solver.base import SolverBase
from src.solver.reverse import ReverseSolver
from src.solver.kociemba import KociembaSolver
from src.solver.lbl import LBLSolver


class SolverFactory:
    """
    求解器注册中心 + 工厂。
    用法:
        factory = SolverFactory()
        solver = factory.get_solver('lbl')
        moves = solver.solve(cube)
    """

    # 求解器注册表 — 按显示顺序排列
    _REGISTRY = []

    @classmethod
    def _register_builtins(cls):
        if cls._REGISTRY:
            return
        solvers = [
            KociembaSolver(),
            ReverseSolver(),
            LBLSolver(),
        ]
        for s in solvers:
            key = s.name.split('(')[0].strip().lower()
            # 统一 key：去掉括号部分
            cls._REGISTRY.append((key, s))

    @classmethod
    def get_solver(cls, key: str) -> SolverBase:
        """按 key 获取求解器。key 不区分大小写。"""
        cls._register_builtins()
        key = key.lower().strip()
        # 精确匹配
        for k, solver in cls._REGISTRY:
            if k == key:
                return solver
        # 模糊匹配（子串）
        for k, solver in cls._REGISTRY:
            if key in k or k in key:
                return solver
        # 兜底
        return ReverseSolver()

    @classmethod
    def get_solver_by_name(cls, name: str) -> SolverBase:
        """按显示名称匹配求解器。"""
        cls._register_builtins()
        name = name.lower().strip()
        for k, solver in cls._REGISTRY:
            if solver.name.lower() == name:
                return solver
        return cls.get_solver(name)

    @classmethod
    def list_solvers(cls) -> list:
        """返回所有注册求解器的列表 [(key, name, description, available), ...]"""
        cls._register_builtins()
        result = []
        for key, solver in cls._REGISTRY:
            result.append((key, solver.name, solver.description, solver.is_available()))
        return result

    @classmethod
    def get_available_methods(cls) -> list:
        """返回可用方法的 key 列表（不可用的也包含，用于 UI 显示）。"""
        cls._register_builtins()
        return [k for k, s in cls._REGISTRY]

    @classmethod
    def get_display_methods(cls) -> list:
        """返回 (key, display_name, is_available) 列表。"""
        cls._register_builtins()
        return [(k, s.name, s.is_available()) for k, s in cls._REGISTRY]

    @classmethod
    def solve_with_fallback(cls, cube, method_key: str) -> tuple:
        """
        使用指定方法求解，失败时自动降级。
        返回 (moves, solver_name, used_fallback)
        """
        solver = cls.get_solver(method_key)
        # 检查 kociemba 库是否缺失
        if isinstance(solver, KociembaSolver) and not solver.is_available():
            return [], solver.name, False, 'missing_lib'

        moves = solver.solve(cube)
        if moves:
            return moves, solver.name, False, ''

        # 降级：尝试所有其他求解器
        for k, alt_solver in cls._REGISTRY:
            if alt_solver is solver:
                continue
            if not alt_solver.is_available():
                continue
            moves = alt_solver.solve(cube)
            if moves:
                return moves, alt_solver.name, True, ''

        return [], '无可用求解器', True, ''

    @classmethod
    def get_solver_display_names(cls) -> dict:
        """返回 {key: display_name} 映射。"""
        cls._register_builtins()
        return {k: s.name for k, s in cls._REGISTRY}

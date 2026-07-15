"""
求解器抽象基类 — Strategy 模式
所有具体求解器继承此基类，通过 SolverFactory 注册。
"""
from abc import ABC, abstractmethod
from src.model.cube_model import RubiksCube, MOVE_TO_ALA, SOLVED_FACELET_STRING


class SolverBase(ABC):
    """所有求解器的抽象基类。"""

    # 求解器元信息 — 子类覆盖
    name = '未命名'          # 显示名称
    description = ''         # 简要说明
    requires_lib = False     # 是否需要额外库
    lib_name = ''            # 库名（供提示用）

    def __init__(self):
        self._lib_available = True

    @abstractmethod
    def solve(self, cube: RubiksCube, method: str = '') -> list:
        """
        对给定的魔方求解，返回 moves 列表 [(axis, layer, angle), ...]。
        若无法求解返回空列表。
        """
        ...

    def is_available(self) -> bool:
        """检查求解器是否可用（例如依赖库是否已安装）。"""
        return self._lib_available

    def get_error_message(self) -> str:
        """返回不可用时的提示信息。"""
        if self.requires_lib and not self._lib_available:
            return f'需要安装 {self.lib_name} 库：pip install {self.lib_name}'
        return ''

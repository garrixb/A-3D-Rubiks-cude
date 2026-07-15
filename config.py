# config.py
"""
魔方系统配置文件
统一管理所有可配置参数，支持环境变量覆盖
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


# ============================================================================
# 路径配置
# ============================================================================
class PathConfig:
    """路径相关配置"""
    
    # 项目根目录
    ROOT_DIR = Path(__file__).parent.absolute()
    
    # 资源目录
    ASSETS_DIR = ROOT_DIR / "src" / "assets"
    MODEL_DIR = ROOT_DIR / "src" / "model"
    SOLVER_DIR = ROOT_DIR / "src" / "solver"
    UI_DIR = ROOT_DIR / "src" / "ui"
    
    # 模型文件路径
    HAND_LANDMARKER_PATH = ASSETS_DIR / "hand_landmarker.task"
    
    # 日志目录
    LOG_DIR = ROOT_DIR / "logs"
    
    @classmethod
    def ensure_dirs(cls):
        """确保所有必要的目录存在"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 显示配置
# ============================================================================
class DisplayConfig:
    """显示相关配置"""
    
    # 窗口大小
    WINDOW_WIDTH = 960
    WINDOW_HEIGHT = 720
    
    # UI 高度（底部按钮区域）
    UI_HEIGHT = 130
    
    # 背景颜色 (RGB, 0-1)
    BACKGROUND_COLOR = (0.90, 0.92, 0.95)
    
    # 3D 相机
    CAMERA_DISTANCE = 9.5
    CAMERA_FOV = 42
    
    # 默认视角
    DEFAULT_VIEW_X = -25.0
    DEFAULT_VIEW_Y = 30.0
    
    # 视角限制（防止翻转）
    VIEW_LIMIT_X_MIN = -89.0
    VIEW_LIMIT_X_MAX = 89.0
    
    # 抗锯齿
    MULTISAMPLE_BUFFERS = 1
    MULTISAMPLE_SAMPLES = 4


# ============================================================================
# 魔方配置
# ============================================================================
class CubeConfig:
    """魔方物理配置"""
    
    # 小方块大小
    CUBE_SIZE = 0.95
    
    # 贴纸内缩（相对于小方块大小）
    STICKER_INSET = 0.08
    
    # 默认打乱步数
    DEFAULT_SCRAMBLE_MOVES = 25
    
    # 颜色顺序 (索引: 0=右, 1=左, 2=上, 3=下, 4=前, 5=后)
    FACE_ORDER = ('right', 'left', 'up', 'down', 'front', 'back')
    
    # 标准面顺序（Kociemba格式）
    KOCIEMBA_FACE_ORDER = ('U', 'R', 'F', 'D', 'L', 'B')


# ============================================================================
# 动画配置
# ============================================================================
class AnimationConfig:
    """动画相关配置"""
    
    # 单步旋转动画时长（秒）
    MOVE_DURATION = 0.22
    
    # 打乱速度倍率
    SCRAMBLE_SPEED = 1.5
    
    # 求解速度倍率
    SOLVE_SPEED = 1.8
    
    # 手动操作速度
    MANUAL_SPEED = 1.0
    
    # 速度范围
    SPEED_MIN = 0.2
    SPEED_MAX = 5.0
    SPEED_DEFAULT = 1.0


# ============================================================================
# 手势控制配置
# ============================================================================
class GestureConfig:
    """手势识别配置"""
    
    # MediaPipe 模型参数
    MIN_DETECTION_CONFIDENCE = 0.6
    MIN_TRACKING_CONFIDENCE = 0.5
    NUM_HANDS = 1
    
    # 摄像头
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    
    # 手势检测参数
    POSE_HOLD_FRAMES = 3          # 确认姿态所需的连续帧数
    POSE_COOLDOWN = 1.0           # 姿态触发冷却时间（秒）
    GUN_COOLDOWN = 0.5            # 手枪指向冷却时间（秒）
    
    # 手势命令
    CMD_SCRAMBLE = 'scramble'
    CMD_SOLVE = 'solve'
    CMD_NONE = None


# ============================================================================
# 求解器配置
# ============================================================================
class SolverConfig:
    """求解器相关配置"""
    
    # 默认求解方法（按优先级）
    DEFAULT_METHOD = 'kociemba'
    FALLBACK_METHOD = '逆序还原'
    
    # 是否启用自动降级
    AUTO_FALLBACK = True
    
    # 求解器显示名称映射
    DISPLAY_NAMES = {
        'kociemba': 'Kociemba(最优)',
        'lbl': '层先法(LBL)',
        'reverse': '逆序还原',
    }
    
    # 依赖库检查
    REQUIRED_LIBS = {
        'kociemba': 'kociemba',
        'magiccube': 'magiccube',
        'mediapipe': 'mediapipe',
    }


# ============================================================================
# 外观主题配置
# ============================================================================
class AppearanceConfig:
    """外观主题配置"""
    
    # 默认主题
    DEFAULT_THEME = 'Standard'
    
    # 所有主题名称（按显示顺序）
    THEME_NAMES = [
        'Standard',
        'Dark',
        'Pastel',
        'HighContrast',
        'Metallic',
        'BlackGold',
        'Cyberpunk',
        'Morandi',
        'Monochrome',
        'Rainbow',
    ]
    
    # 主题颜色定义
    THEMES = {
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


# ============================================================================
# 按键映射配置
# ============================================================================
class KeyMappingConfig:
    """键盘按键映射配置"""
    
    # 面旋转 (键值 → 移动名称)
    FACE_KEYS = {
        'u': 'U',
        'd': 'D',
        'l': 'L',
        'r': 'R',
        'f': 'F',
        'b': 'B',
    }
    
    # 功能键
    FUNCTION_KEYS = {
        's': 'scramble',
        'space': 'solve',
        'return': 'solve',
        'backspace': 'reset',
        'm': 'cycle_method',
        'a': 'cycle_appearance',
        'g': 'toggle_gesture',
        'equal': 'speed_up',
        'plus': 'speed_up',
        'minus': 'speed_down',
        'escape': 'quit',
    }
    
    # Shift + 键 → 反向旋转
    SHIFT_REVERSE = True


# ============================================================================
# 日志配置
# ============================================================================
class LogConfig:
    """日志相关配置"""
    
    # 日志级别
    LEVEL = 'INFO'
    
    # 日志格式
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 日期格式
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 日志文件
    FILE_NAME = 'rubiks_cube.log'
    FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    FILE_BACKUP_COUNT = 5


# ============================================================================
# 配置管理器（统一接口 + 环境变量覆盖）
# ============================================================================
class Config:
    """
    统一配置管理器
    
    支持：
    - 从环境变量覆盖配置
    - 从JSON文件加载/保存
    - 访问路径：Config.Display.WINDOW_WIDTH
    """
    
    # 所有配置类
    Path = PathConfig
    Display = DisplayConfig
    Cube = CubeConfig
    Animation = AnimationConfig
    Gesture = GestureConfig
    Solver = SolverConfig
    Appearance = AppearanceConfig
    KeyMapping = KeyMappingConfig
    Log = LogConfig
    
    _config_file: Optional[Path] = None
    _loaded = False
    
    @classmethod
    def load_from_env(cls):
        """从环境变量加载配置（覆盖默认值）"""
        # 窗口大小
        if os.getenv('RUBIKS_WINDOW_WIDTH'):
            DisplayConfig.WINDOW_WIDTH = int(os.getenv('RUBIKS_WINDOW_WIDTH'))
        if os.getenv('RUBIKS_WINDOW_HEIGHT'):
            DisplayConfig.WINDOW_HEIGHT = int(os.getenv('RUBIKS_WINDOW_HEIGHT'))
        
        # 打乱步数
        if os.getenv('RUBIKS_SCRAMBLE_MOVES'):
            CubeConfig.DEFAULT_SCRAMBLE_MOVES = int(os.getenv('RUBIKS_SCRAMBLE_MOVES'))
        
        # 动画速度
        if os.getenv('RUBIKS_ANIMATION_SPEED'):
            AnimationConfig.SOLVE_SPEED = float(os.getenv('RUBIKS_ANIMATION_SPEED'))
        
        # 默认求解方法
        if os.getenv('RUBIKS_DEFAULT_SOLVER'):
            SolverConfig.DEFAULT_METHOD = os.getenv('RUBIKS_DEFAULT_SOLVER')
        
        # 日志级别
        if os.getenv('RUBIKS_LOG_LEVEL'):
            LogConfig.LEVEL = os.getenv('RUBIKS_LOG_LEVEL')
        
        cls._loaded = True
    
    @classmethod
    def load_from_file(cls, path: Path):
        """从JSON文件加载配置"""
        if not path.exists():
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cls._apply_dict(data)
        cls._config_file = path
        cls._loaded = True
    
    @classmethod
    def save_to_file(cls, path: Path):
        """保存当前配置到JSON文件"""
        data = cls._dump_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        cls._config_file = path
    
    @classmethod
    def _apply_dict(cls, data: Dict[str, Any], prefix: str = ''):
        """递归应用字典配置"""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                cls._apply_dict(value, full_key)
            else:
                cls._set_value(full_key, value)
    
    @classmethod
    def _set_value(cls, path: str, value: Any):
        """按路径设置配置值"""
        parts = path.split('.')
        if len(parts) == 0:
            return
        
        # 找到目标配置类
        obj = cls
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return
        
        # 设置值
        last = parts[-1]
        if hasattr(obj, last):
            setattr(obj, last, value)
    
    @classmethod
    def _dump_dict(cls) -> Dict[str, Any]:
        """导出所有配置为字典"""
        result = {}
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if isinstance(attr, type):
                result[attr_name] = cls._dump_class(attr)
        return result
    
    @classmethod
    def _dump_class(cls, obj) -> Dict[str, Any]:
        """导出类配置为字典"""
        result = {}
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            attr = getattr(obj, attr_name)
            if not callable(attr) and not isinstance(attr, type):
                result[attr_name] = attr
        return result


# ============================================================================
# 运行时配置（可动态修改）
# ============================================================================
class RuntimeConfig:
    """运行时配置（程序运行期间可修改）"""
    
    def __init__(self):
        # 当前外观主题
        self.current_theme = AppearanceConfig.DEFAULT_THEME
        
        # 当前求解方法
        self.current_solver = SolverConfig.DEFAULT_METHOD
        
        # 当前动画速度
        self.current_speed = AnimationConfig.SPEED_DEFAULT
        
        # 手势控制状态
        self.gesture_enabled = False
        
        # 显示当前状态
        self.status_message = '就绪'
        
        # 解法步骤文本
        self.solution_text = ''
    
    def reset(self):
        """重置运行时状态"""
        self.current_theme = AppearanceConfig.DEFAULT_THEME
        self.current_solver = SolverConfig.DEFAULT_METHOD
        self.current_speed = AnimationConfig.SPEED_DEFAULT
        self.gesture_enabled = False
        self.status_message = '就绪'
        self.solution_text = ''


# ============================================================================
# 初始化
# ============================================================================
# 确保必要目录存在
PathConfig.ensure_dirs()

# 从环境变量加载配置
Config.load_from_env()

# 创建全局运行时配置实例
runtime = RuntimeConfig()


# ============================================================================
# 便捷函数
# ============================================================================
def get_theme_colors(theme_name: str) -> Dict[str, Tuple[float, float, float]]:
    """获取主题颜色"""
    return AppearanceConfig.THEMES.get(theme_name, AppearanceConfig.THEMES[AppearanceConfig.DEFAULT_THEME])


def get_theme_names() -> List[str]:
    """获取所有主题名称"""
    return AppearanceConfig.THEME_NAMES.copy()


def get_solver_names() -> List[str]:
    """获取所有求解器名称"""
    return list(SolverConfig.DISPLAY_NAMES.keys())


def get_solver_display_name(key: str) -> str:
    """获取求解器显示名称"""
    return SolverConfig.DISPLAY_NAMES.get(key, key)


def get_face_color(face: str, theme: Optional[str] = None) -> Tuple[float, float, float]:
    """
    获取指定面的颜色
    
    Args:
        face: 面名称 ('right', 'left', 'up', 'down', 'front', 'back', 'internal')
        theme: 主题名称，None表示使用当前主题
    
    Returns:
        RGB元组 (0-1)
    """
    if theme is None:
        theme = runtime.current_theme
    colors = get_theme_colors(theme)
    return colors.get(face, (0.5, 0.5, 0.5))


# ============================================================================
# 配置校验
# ============================================================================
def validate_config() -> List[str]:
    """验证配置有效性，返回错误列表"""
    errors = []
    
    # 校验窗口大小
    if Config.Display.WINDOW_WIDTH < 640:
        errors.append("窗口宽度不能小于640")
    if Config.Display.WINDOW_HEIGHT < 480:
        errors.append("窗口高度不能小于480")
    
    # 校验速度范围
    if not (AnimationConfig.SPEED_MIN < AnimationConfig.SPEED_MAX):
        errors.append("速度最小值必须小于最大值")
    if not (AnimationConfig.SPEED_MIN <= AnimationConfig.SPEED_DEFAULT <= AnimationConfig.SPEED_MAX):
        errors.append("默认速度超出范围")
    
    # 校验求解器
    if Config.Solver.DEFAULT_METHOD not in get_solver_names():
        errors.append(f"未知的默认求解器: {Config.Solver.DEFAULT_METHOD}")
    
    # 校验主题
    if Config.Appearance.DEFAULT_THEME not in get_theme_names():
        errors.append(f"未知的默认主题: {Config.Appearance.DEFAULT_THEME}")
    
    return errors


# ============================================================================
# 打印配置（调试用）
# ============================================================================
def print_config():
    """打印当前所有配置（调试用）"""
    print("=" * 60)
    print("魔方系统配置")
    print("=" * 60)
    
    print("\n[路径配置]")
    print(f"  根目录: {PathConfig.ROOT_DIR}")
    print(f"  资源目录: {PathConfig.ASSETS_DIR}")
    print(f"  模型文件: {PathConfig.HAND_LANDMARKER_PATH}")
    
    print("\n[显示配置]")
    print(f"  窗口: {DisplayConfig.WINDOW_WIDTH}x{DisplayConfig.WINDOW_HEIGHT}")
    print(f"  UI高度: {DisplayConfig.UI_HEIGHT}")
    print(f"  默认视角: ({DisplayConfig.DEFAULT_VIEW_X}, {DisplayConfig.DEFAULT_VIEW_Y})")
    
    print("\n[魔方配置]")
    print(f"  小方块大小: {CubeConfig.CUBE_SIZE}")
    print(f"  默认打乱步数: {CubeConfig.DEFAULT_SCRAMBLE_MOVES}")
    
    print("\n[动画配置]")
    print(f"  单步时长: {AnimationConfig.MOVE_DURATION}s")
    print(f"  求解速度: {AnimationConfig.SOLVE_SPEED}x")
    print(f"  速度范围: {AnimationConfig.SPEED_MIN} - {AnimationConfig.SPEED_MAX}")
    
    print("\n[求解器配置]")
    print(f"  默认方法: {SolverConfig.DEFAULT_METHOD}")
    print(f"  自动降级: {SolverConfig.AUTO_FALLBACK}")
    print(f"  可用方法: {get_solver_names()}")
    
    print("\n[手势配置]")
    print(f"  姿态确认帧数: {GestureConfig.POSE_HOLD_FRAMES}")
    print(f"  姿态冷却: {GestureConfig.POSE_COOLDOWN}s")
    print(f"  指向冷却: {GestureConfig.GUN_COOLDOWN}s")
    
    print("\n[外观配置]")
    print(f"  默认主题: {AppearanceConfig.DEFAULT_THEME}")
    print(f"  可用主题: {get_theme_names()}")
    
    print("\n[运行时]")
    print(f"  当前主题: {runtime.current_theme}")
    print(f"  当前求解器: {runtime.current_solver}")
    print(f"  当前速度: {runtime.current_speed}x")
    print(f"  手势控制: {'开启' if runtime.gesture_enabled else '关闭'}")
    
    # 校验结果
    errors = validate_config()
    if errors:
        print("\n[⚠ 配置警告]")
        for err in errors:
            print(f"  - {err}")
    else:
        print("\n[✓ 配置验证通过]")
    
    print("=" * 60)


# 如果直接运行，打印配置
if __name__ == '__main__':
    print_config()

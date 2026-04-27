"""
Asciimatics Web Editor 兼容性层

这个模块解决以下问题：
1. Windows上win32console DLL导入失败的问题
2. 无需终端GUI即可使用asciimatics的渲染功能
3. 全平台兼容（Windows/Linux/macOS）

设计原则：
- 不修改原库代码
- 无侵入式，通过环境隔离和monkey patching实现
- 只加载我们需要的部分，不触发不必要的平台特定代码
"""

import sys
import os
from types import ModuleType
from typing import Any, Optional


class _DummyModule(ModuleType):
    """
    虚拟模块，用于替代缺失的平台特定模块。
    当访问不存在的属性时，返回一个可调用的dummy对象。
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self._name = name
    
    def __getattr__(self, attr: str) -> Any:
        if attr.startswith('_'):
            raise AttributeError(f"{self._name} has no attribute '{attr}'")
        
        class DummyCallable:
            def __init__(self, name: str):
                self._name = name
            
            def __call__(self, *args, **kwargs):
                return self
            
            def __getattr__(self, item):
                return DummyCallable(f"{self._name}.{item}")
            
            def __int__(self):
                return 0
            
            def __or__(self, other):
                return self
            
            def __and__(self, other):
                return self
        
        return DummyCallable(f"{self._name}.{attr}")


def _create_dummy_modules():
    """
    创建虚拟模块来替代Windows特定的模块。
    这些模块只在实际的Windows Screen实现中使用，
    而我们的VirtualScreen/TemporaryCanvas不需要它们。
    """
    dummy_modules = [
        "win32console",
        "win32con",
        "win32event",
        "win32file",
        "win32gui",
        "win32api",
        "pywintypes",
    ]
    
    for mod_name in dummy_modules:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = _DummyModule(mod_name)


def _patch_screen_module():
    """
    在导入screen.py之前，确保我们的兼容性层已就绪。
    
    关键观察：
    1. TemporaryCanvas 类在 screen.py 中定义，但它不依赖任何平台特定代码
    2. TemporaryCanvas 只使用 _DoubleBuffer 和 _AbstractCanvas 的功能
    3. _WindowsScreen 和 _CursesScreen 是实际的终端实现，我们不需要它们
    
    我们的策略：
    1. 先创建虚拟模块防止导入崩溃
    2. 允许asciimatics正常导入
    3. 我们自己的代码只使用 TemporaryCanvas 相关的功能
    """
    _create_dummy_modules()


def _safe_import_asciimatics():
    """
    安全地导入asciimatics，处理所有平台兼容性问题。
    """
    _patch_screen_module()
    
    try:
        import asciimatics
    except ImportError as e:
        if "win32console" in str(e) or "pywintypes" in str(e):
            _create_dummy_modules()
            import asciimatics
        else:
            raise


def init_compatibility_layer():
    """
    初始化兼容性层。
    在导入任何asciimatics模块之前调用此函数。
    """
    if sys.platform == "win32":
        try:
            import win32console
        except ImportError:
            _patch_screen_module()
    else:
        pass
    
    try:
        import asciimatics.version
    except ImportError:
        _patch_screen_module()


_IS_INITIALIZED = False

def ensure_compatibility():
    """
    确保兼容性层已初始化。
    可以多次调用，只会初始化一次。
    """
    global _IS_INITIALIZED
    if _IS_INITIALIZED:
        return
    
    init_compatibility_layer()
    _IS_INITIALIZED = True


class SafeTemporaryCanvas:
    """
    安全的TemporaryCanvas包装器。
    
    这个类提供与asciimatics的TemporaryCanvas相同的接口，
    但确保在导入时不会触发平台特定的问题。
    
    实际上，一旦兼容性层初始化完成，我们就可以直接使用
    原始的TemporaryCanvas。这个类作为额外的安全层。
    """
    
    def __new__(cls, height: int, width: int):
        ensure_compatibility()
        from asciimatics.screen import TemporaryCanvas
        return TemporaryCanvas(height, width)


def get_screen_class():
    """
    获取Screen类，但确保只使用我们需要的常量和功能。
    """
    ensure_compatibility()
    from asciimatics.screen import Screen
    return Screen


def get_renderer_classes():
    """
    获取所有Renderer类，安全导入。
    """
    ensure_compatibility()
    from asciimatics.renderers.base import Renderer, StaticRenderer, DynamicRenderer
    return Renderer, StaticRenderer, DynamicRenderer


def get_effect_classes():
    """
    获取Effect类，安全导入。
    """
    ensure_compatibility()
    from asciimatics.effects import (
        Effect,
        Cycle,
        Stars,
        Print,
        BannerText,
        Mirage,
        Scroll,
        Matrix,
        Wipe,
        Snow,
        Clock,
        Cog,
        RandomNoise,
        Julia,
        Background,
    )
    return (
        Effect, Cycle, Stars, Print, BannerText, Mirage, Scroll,
        Matrix, Wipe, Snow, Clock, Cog, RandomNoise, Julia, Background
    )


def get_all_renderers():
    """
    获取所有可用的Renderer类型。
    严格按照asciimatics 1.15.1的真实导出结构。
    """
    ensure_compatibility()
    from asciimatics.renderers import (
        FigletText,
        ImageFile,
        ColourImageFile,
        Fire,
        Plasma,
        Rainbow,
        Kaleidoscope,
        Box,
        SpeechBubble,
        Scale,
        VScale,
        RotatedDuplicate,
        BarChart,
        VBarChart,
        Typewriter,
        AbstractScreenPlayer,
        AnsiArtPlayer,
        AsciinemaPlayer,
    )
    return {
        "FigletText": FigletText,
        "ImageFile": ImageFile,
        "ColourImageFile": ColourImageFile,
        "Fire": Fire,
        "Plasma": Plasma,
        "Rainbow": Rainbow,
        "Kaleidoscope": Kaleidoscope,
        "Box": Box,
        "SpeechBubble": SpeechBubble,
        "Scale": Scale,
        "VScale": VScale,
        "RotatedDuplicate": RotatedDuplicate,
        "BarChart": BarChart,
        "VBarChart": VBarChart,
        "Typewriter": Typewriter,
        "AbstractScreenPlayer": AbstractScreenPlayer,
        "AnsiArtPlayer": AnsiArtPlayer,
        "AsciinemaPlayer": AsciinemaPlayer,
    }


__all__ = [
    "ensure_compatibility",
    "SafeTemporaryCanvas",
    "get_screen_class",
    "get_renderer_classes",
    "get_effect_classes",
    "get_all_renderers",
    "_DummyModule",
    "_patch_screen_module",
]

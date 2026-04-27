import inspect
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from .compat import ensure_compatibility

ensure_compatibility()

from asciimatics.renderers.base import Renderer, StaticRenderer, DynamicRenderer
from asciimatics.screen import TemporaryCanvas
from asciimatics.scene import Scene
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


@dataclass
class RenderConfig:
    width: int = 80
    height: int = 24
    colours: int = 256
    fps: int = 20
    duration: int = 100


@dataclass
class FrameData:
    frame_number: int
    plain_image: List[str]
    colour_map: List[List[Tuple[Optional[int], Optional[int], Optional[int]]]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_number": self.frame_number,
            "plain_image": self.plain_image,
            "colour_map": [[list(c) if c else None for c in row] for row in self.colour_map],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrameData":
        colour_map = []
        for row in data["colour_map"]:
            row_data = []
            for c in row:
                if c:
                    row_data.append(tuple(c))
                else:
                    row_data.append((None, None, None))
            colour_map.append(row_data)
        
        return cls(
            frame_number=data["frame_number"],
            plain_image=data["plain_image"],
            colour_map=colour_map,
        )


class VirtualScreen(TemporaryCanvas):
    """
    虚拟屏幕，用于在不实际打开终端的情况下渲染ASCII动画。
    继承自TemporaryCanvas，添加Effect所需的Screen方法。
    """
    
    COLOUR_DEFAULT = 7
    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7
    
    A_BOLD = 1
    A_NORMAL = 2
    A_REVERSE = 3
    A_UNDERLINE = 4
    
    _8_palette = [
        0x00, 0x00, 0x00,
        0x80, 0x00, 0x00,
        0x00, 0x80, 0x00,
        0x80, 0x80, 0x00,
        0x00, 0x00, 0x80,
        0x80, 0x00, 0x80,
        0x00, 0x80, 0x80,
        0xc0, 0xc0, 0xc0,
    ] + [0x00 for _ in range(248 * 3)]
    
    _256_palette = [
        0x00, 0x00, 0x00,
        0x80, 0x00, 0x00,
        0x00, 0x80, 0x00,
        0x80, 0x80, 0x00,
        0x00, 0x00, 0x80,
        0x80, 0x00, 0x80,
        0x00, 0x80, 0x80,
        0xc0, 0xc0, 0xc0,
        0x80, 0x80, 0x80,
        0xff, 0x00, 0x00,
        0x00, 0xff, 0x00,
        0xff, 0xff, 0x00,
        0x00, 0x00, 0xff,
        0xff, 0x00, 0xff,
        0x00, 0xff, 0xff,
        0xff, 0xff, 0xff,
    ] + [
        (r // 5 * 40 + 55 if r > 0 else 0,
         g // 5 * 40 + 55 if g > 0 else 0,
         b // 5 * 40 + 55 if b > 0 else 0)
        for r in range(6) for g in range(6) for b in range(6)
        for _ in range(3)
    ] + [
        c for i in range(24)
        for c in [8 + i * 10, 8 + i * 10, 8 + i * 10]
    ]
    
    def __init__(self, height: int, width: int, colours: int = 256):
        super().__init__(height, width)
        self._start_line = 0
        self._scenes: List[Scene] = []
        self._scene_index = 0
        self._frame = 0
        self._forced_update = False
        self._colours_override = colours
        self.colours = colours
    
    @property
    def colours(self) -> int:
        return self._colours_override
    
    @colours.setter
    def colours(self, value: int):
        self._colours_override = value
    
    @property
    def unicode_aware(self) -> bool:
        return True
    
    @property
    def palette(self) -> List[int]:
        if self.colours >= 256:
            return self._256_palette
        return self._8_palette
    
    def is_visible(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and self._start_line <= y < self._start_line + self.height
    
    def get_from(self, x: int, y: int) -> Optional[Tuple[int, Optional[int], Optional[int], Optional[int]]]:
        y -= self._start_line
        if y < 0 or y >= self.height or x < 0 or x >= self.width:
            return None
        cell = self._buffer.get(x, y)
        return ord(cell[0]), cell[1], cell[2], cell[3]
    
    def block_transfer(self, buffer: Any, x: int, y: int):
        self._buffer.block_transfer(buffer, x, y)
    
    def set_scenes(self, scenes: List[Scene], **kwargs):
        self._scenes = scenes
        self._scene_index = 0
        self._frame = 0
    
    def draw_next_frame(self, repeat: bool = True) -> bool:
        if not self._scenes:
            return False
        
        scene = self._scenes[self._scene_index]
        if self._frame == 0:
            scene.reset(None, self)
        
        self.clear_buffer(None, 0, 0)
        
        for effect in scene.effects:
            effect.update(self._frame)
        
        self._frame += 1
        
        if self._frame >= scene.duration:
            self._scene_index += 1
            self._frame = 0
            if self._scene_index >= len(self._scenes):
                if repeat:
                    self._scene_index = 0
                else:
                    return False
        
        return True
    
    @property
    def current_frame_data(self) -> FrameData:
        return FrameData(
            frame_number=self._frame,
            plain_image=self.plain_image,
            colour_map=self.colour_map,
        )


class RendererCreationError(Exception):
    """渲染器创建错误"""
    pass


class EffectCreationError(Exception):
    """效果创建错误"""
    pass


class SafeStaticRenderer(StaticRenderer):
    """
    安全的备用渲染器，当其他渲染器创建失败时使用。
    """
    
    def __init__(self, text: str = "Renderer Error", width: int = 80):
        super().__init__()
        centered = text.center(min(len(text) + 4, width))
        border = "+" + "-" * (len(centered) + 2) + "+"
        empty = "|" + " " * (len(centered) + 2) + "|"
        message = "| " + centered + " |"
        self._images = [
            border,
            empty,
            message,
            empty,
            border,
        ]


class EffectRegistry:
    """
    Effect注册器，用于管理可用的Effect类型和它们的配置。
    严格按照asciimatics 1.15.1的真实导出结构。
    """
    
    EFFECT_TYPES: Dict[str, Type[Effect]] = {
        "Cycle": Cycle,
        "Stars": Stars,
        "Print": Print,
        "BannerText": BannerText,
        "Mirage": Mirage,
        "Scroll": Scroll,
        "Matrix": Matrix,
        "Wipe": Wipe,
        "Snow": Snow,
        "Clock": Clock,
        "Cog": Cog,
        "RandomNoise": RandomNoise,
        "Julia": Julia,
        "Background": Background,
    }
    
    RENDERER_TYPES: Dict[str, Type[Renderer]] = {
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
    
    _RENDERER_SPECIAL_PARAMS: Dict[str, List[str]] = {
        "Rainbow": ["renderer"],
        "Kaleidoscope": ["cell"],
        "Typewriter": ["source"],
        "RotatedDuplicate": ["renderer"],
        "SpeechBubble": ["text"],
    }
    
    _EFFECT_SPECIAL_PARAMS: Dict[str, List[str]] = {
        "Cycle": ["renderer"],
        "Print": ["renderer"],
        "BannerText": ["renderer"],
        "Mirage": ["renderer"],
        "RandomNoise": ["signal"],
    }
    
    @classmethod
    def list_effects(cls) -> List[str]:
        return list(cls.EFFECT_TYPES.keys())
    
    @classmethod
    def list_renderers(cls) -> List[str]:
        return list(cls.RENDERER_TYPES.keys())
    
    @classmethod
    def get_renderer_special_params(cls, renderer_type: str) -> List[str]:
        return cls._RENDERER_SPECIAL_PARAMS.get(renderer_type, [])
    
    @classmethod
    def get_effect_special_params(cls, effect_type: str) -> List[str]:
        return cls._EFFECT_SPECIAL_PARAMS.get(effect_type, [])


def get_class_init_params(cls: Type[Any]) -> Dict[str, Tuple[Any, Any]]:
    """
    获取类的__init__方法参数信息（不包括self）。
    
    返回格式: {参数名: (类型注解, 默认值)}
    如果没有默认值，默认值为inspect.Parameter.empty
    """
    try:
        sig = inspect.signature(cls.__init__)
        params = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            params[name] = (param.annotation, param.default)
        return params
    except (ValueError, TypeError):
        return {}


def filter_kwargs_for_class(
    cls: Type[Any], 
    kwargs: Dict[str, Any],
    exclude_params: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    过滤kwargs，只保留类__init__方法接受的参数。
    
    :param cls: 目标类
    :param kwargs: 参数字典
    :param exclude_params: 需要排除的参数列表（用于特殊处理的参数）
    :return: 过滤后的参数字典
    """
    valid_params = get_class_init_params(cls)
    exclude = set(exclude_params or [])
    
    filtered = {}
    for key, value in kwargs.items():
        if key in valid_params and key not in exclude:
            filtered[key] = value
    
    return filtered


def get_missing_required_params(
    cls: Type[Any],
    provided_kwargs: Dict[str, Any],
    exclude_params: Optional[List[str]] = None
) -> List[str]:
    """
    获取缺失的必需参数（没有默认值的参数）。
    
    :param cls: 目标类
    :param provided_kwargs: 已提供的参数
    :param exclude_params: 需要排除的参数列表
    :return: 缺失的必需参数名列表
    """
    valid_params = get_class_init_params(cls)
    exclude = set(exclude_params or [])
    provided = set(provided_kwargs.keys())
    
    missing = []
    for name, (annotation, default) in valid_params.items():
        if name in exclude:
            continue
        if default is inspect.Parameter.empty and name not in provided:
            missing.append(name)
    
    return missing


def create_safe_figlet_text(
    text: Optional[str] = None,
    font: Optional[str] = None,
    width: int = 80,
    **kwargs
) -> FigletText:
    """
    安全创建FigletText渲染器，提供默认值。
    """
    from pyfiglet import DEFAULT_FONT
    
    safe_text = text if text is not None else "Hello"
    safe_font = font if font is not None else DEFAULT_FONT
    safe_width = max(20, width)
    
    return FigletText(text=safe_text, font=safe_font, width=safe_width)


def create_safe_fire(
    height: int = 24,
    width: int = 80,
    emitter: Optional[str] = None,
    intensity: float = 0.8,
    spot: int = 40,
    colours: int = 256,
    bg: bool = False,
    **kwargs
) -> Fire:
    """
    安全创建Fire渲染器，提供默认值。
    """
    safe_emitter = emitter if emitter is not None else (
        "   *   *   *   \n"
        "  *** *** ***  \n"
        " ************* \n"
        "***************"
    )
    safe_height = max(5, height)
    safe_width = max(10, width)
    safe_intensity = max(0.1, min(1.0, intensity))
    safe_spot = max(1, spot)
    
    return Fire(
        height=safe_height,
        width=safe_width,
        emitter=safe_emitter,
        intensity=safe_intensity,
        spot=safe_spot,
        colours=colours,
        bg=bg,
    )


def create_safe_plasma(
    height: int = 24,
    width: int = 80,
    colours: int = 256,
    **kwargs
) -> Plasma:
    """
    安全创建Plasma渲染器，提供默认值。
    """
    safe_height = max(5, height)
    safe_width = max(10, width)
    
    return Plasma(height=safe_height, width=safe_width, colours=colours)


def create_safe_box(
    width: int = 40,
    height: int = 10,
    uni: bool = False,
    style: int = 0,
    **kwargs
) -> Box:
    """
    安全创建Box渲染器，提供默认值。
    """
    from asciimatics.constants import SINGLE_LINE
    
    safe_width = max(3, width)
    safe_height = max(3, height)
    safe_style = style if style in [0, 1, 2] else SINGLE_LINE
    
    return Box(width=safe_width, height=safe_height, uni=uni, style=safe_style)


def create_safe_scale(width: int = 80, **kwargs) -> Scale:
    """安全创建Scale渲染器"""
    safe_width = max(1, width)
    return Scale(width=safe_width)


def create_safe_vscale(height: int = 24, **kwargs) -> VScale:
    """安全创建VScale渲染器"""
    safe_height = max(1, height)
    return VScale(height=safe_height)


def create_safe_speech_bubble(
    text: Optional[Union[str, Renderer]] = None,
    tail: Optional[str] = None,
    uni: bool = False,
    **kwargs
) -> SpeechBubble:
    """
    安全创建SpeechBubble渲染器。
    注意：text参数可以是字符串或Renderer实例。
    """
    safe_text = text if text is not None else "Hello!"
    
    if tail not in [None, "L", "R"]:
        tail = None
    
    return SpeechBubble(text=safe_text, tail=tail, uni=uni)


_SAFE_RENDERER_CREATORS: Dict[str, Callable] = {
    "FigletText": create_safe_figlet_text,
    "Fire": create_safe_fire,
    "Plasma": create_safe_plasma,
    "Box": create_safe_box,
    "Scale": create_safe_scale,
    "VScale": create_safe_vscale,
    "SpeechBubble": create_safe_speech_bubble,
}


@dataclass
class EffectConfig:
    effect_type: str
    renderer_type: Optional[str] = None
    renderer_config: Dict[str, Any] = field(default_factory=dict)
    effect_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "renderer_type": self.renderer_type,
            "renderer_config": self.renderer_config,
            "effect_config": self.effect_config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EffectConfig":
        return cls(
            effect_type=data["effect_type"],
            renderer_type=data.get("renderer_type"),
            renderer_config=data.get("renderer_config", {}),
            effect_config=data.get("effect_config", {}),
        )


class AnimationRenderer:
    """
    动画渲染器，负责管理动画项目的渲染。
    无侵入地使用asciimatics库，不修改原有代码。
    """
    
    def __init__(self, config: RenderConfig):
        self.config = config
        self._screen: Optional[VirtualScreen] = None
        self._scene: Optional[Scene] = None
        self._effects: List[Effect] = []
        self._effect_configs: List[EffectConfig] = []
    
    def _create_screen(self) -> VirtualScreen:
        return VirtualScreen(
            height=self.config.height,
            width=self.config.width,
            colours=self.config.colours,
        )
    
    def _create_nested_renderer(
        self,
        param_name: str,
        config: Any,
        screen: VirtualScreen
    ) -> Optional[Renderer]:
        """
        创建嵌套的Renderer实例（用于链式渲染器）。
        
        config可以是：
        - 字典: {"type": "RendererType", "config": {...}}
        - 字符串: 已创建的渲染器标识（暂不支持）
        - Renderer实例: 直接返回
        """
        if isinstance(config, Renderer):
            return config
        
        if isinstance(config, dict):
            renderer_type = config.get("type")
            renderer_config = config.get("config", {})
            
            if renderer_type:
                try:
                    return self._create_renderer_safe(renderer_type, renderer_config, screen)
                except Exception:
                    pass
        
        return None
    
    def _create_renderer_safe(
        self,
        renderer_type: str,
        config: Dict[str, Any],
        screen: VirtualScreen
    ) -> Renderer:
        """
        安全创建Renderer实例，兼容所有内置渲染器。
        
        策略：
        1. 首先检查是否有特殊的安全创建器
        2. 否则过滤参数并尝试直接创建
        3. 处理需要嵌套Renderer的链式渲染器
        4. 失败时返回安全的备用渲染器
        """
        renderer_class = EffectRegistry.RENDERER_TYPES.get(renderer_type)
        if not renderer_class:
            raise RendererCreationError(f"Unknown renderer type: {renderer_type}")
        
        special_params = EffectRegistry.get_renderer_special_params(renderer_type)
        
        if renderer_type in _SAFE_RENDERER_CREATORS:
            try:
                creator = _SAFE_RENDERER_CREATORS[renderer_type]
                return creator(**config)
            except Exception as e:
                raise RendererCreationError(f"Failed to create {renderer_type}: {e}")
        
        nested_renderers = {}
        remaining_config = {}
        
        for key, value in config.items():
            if key in special_params:
                nested = self._create_nested_renderer(key, value, screen)
                if nested is not None:
                    nested_renderers[key] = nested
            else:
                remaining_config[key] = value
        
        if renderer_type == "ColourImageFile":
            try:
                filtered = filter_kwargs_for_class(
                    renderer_class, 
                    remaining_config,
                    exclude_params=["screen"]
                )
                return renderer_class(screen=screen, **filtered)
            except Exception as e:
                raise RendererCreationError(f"Failed to create ColourImageFile: {e}")
        
        if renderer_type == "Rainbow":
            try:
                inner_renderer = nested_renderers.get("renderer")
                if inner_renderer is None:
                    inner_renderer = SafeStaticRenderer("Rainbow", width=screen.width)
                return Rainbow(screen=screen, renderer=inner_renderer)
            except Exception as e:
                raise RendererCreationError(f"Failed to create Rainbow: {e}")
        
        if renderer_type == "Kaleidoscope":
            try:
                cell = nested_renderers.get("cell")
                if cell is None:
                    cell = SafeStaticRenderer("Kaleidoscope", width=min(screen.width // 2, 20))
                
                filtered = filter_kwargs_for_class(
                    renderer_class,
                    remaining_config,
                    exclude_params=["cell"]
                )
                
                height = filtered.get("height", screen.height)
                width = filtered.get("width", screen.width)
                symmetry = filtered.get("symmetry", 6)
                
                return Kaleidoscope(height=height, width=width, cell=cell, symmetry=symmetry)
            except Exception as e:
                raise RendererCreationError(f"Failed to create Kaleidoscope: {e}")
        
        if renderer_type == "Typewriter":
            try:
                source = nested_renderers.get("source")
                if source is None:
                    source = SafeStaticRenderer("Typewriter", width=screen.width)
                return Typewriter(source=source)
            except Exception as e:
                raise RendererCreationError(f"Failed to create Typewriter: {e}")
        
        if renderer_type == "RotatedDuplicate":
            try:
                inner_renderer = nested_renderers.get("renderer")
                if inner_renderer is None:
                    inner_renderer = SafeStaticRenderer("Rotated", width=min(screen.width // 2, 20))
                
                filtered = filter_kwargs_for_class(
                    renderer_class,
                    remaining_config,
                    exclude_params=["renderer"]
                )
                
                width = filtered.get("width", screen.width)
                height = filtered.get("height", screen.height)
                
                return RotatedDuplicate(width=width, height=height, renderer=inner_renderer)
            except Exception as e:
                raise RendererCreationError(f"Failed to create RotatedDuplicate: {e}")
        
        if renderer_type in ["BarChart", "VBarChart"]:
            try:
                filtered = filter_kwargs_for_class(renderer_class, remaining_config)
                
                if "functions" not in filtered:
                    filtered["functions"] = [lambda: 0.5, lambda: 0.3]
                
                height = filtered.get("height", screen.height)
                width = filtered.get("width", screen.width)
                functions = filtered.get("functions", [lambda: 0.5])
                
                other_kwargs = {k: v for k, v in filtered.items() 
                               if k not in ["height", "width", "functions"]}
                
                return renderer_class(height=height, width=width, functions=functions, **other_kwargs)
            except Exception as e:
                raise RendererCreationError(f"Failed to create {renderer_type}: {e}")
        
        if renderer_type in ["ImageFile", "AnsiArtPlayer", "AsciinemaPlayer", "AbstractScreenPlayer"]:
            try:
                filtered = filter_kwargs_for_class(renderer_class, remaining_config)
                
                if "filename" in filtered:
                    return renderer_class(**filtered)
                else:
                    raise RendererCreationError(
                        f"{renderer_type} requires a filename parameter which was not provided"
                    )
            except RendererCreationError:
                raise
            except Exception as e:
                raise RendererCreationError(f"Failed to create {renderer_type}: {e}")
        
        try:
            filtered = filter_kwargs_for_class(renderer_class, remaining_config)
            return renderer_class(**filtered)
        except Exception as e:
            raise RendererCreationError(f"Failed to create {renderer_type}: {e}")
    
    def _create_renderer(
        self,
        renderer_type: str,
        config: Dict[str, Any],
        screen: VirtualScreen
    ) -> Renderer:
        """
        创建Renderer实例，包含错误处理和回退机制。
        """
        try:
            return self._create_renderer_safe(renderer_type, config, screen)
        except RendererCreationError:
            return SafeStaticRenderer(
                text=f"Renderer: {renderer_type}",
                width=screen.width
            )
    
    def _create_effect_safe(
        self,
        config: EffectConfig,
        screen: VirtualScreen
    ) -> Effect:
        """
        安全创建Effect实例。
        """
        effect_class = EffectRegistry.EFFECT_TYPES.get(config.effect_type)
        if not effect_class:
            raise EffectCreationError(f"Unknown effect type: {config.effect_type}")
        
        special_params = EffectRegistry.get_effect_special_params(config.effect_type)
        
        effect_kwargs = config.effect_config.copy()
        
        renderer = None
        if config.renderer_type:
            renderer = self._create_renderer(config.renderer_type, config.renderer_config, screen)
        
        if config.effect_type in ["Cycle", "Print", "BannerText", "Mirage"]:
            if renderer is not None:
                effect_kwargs["renderer"] = renderer
            elif "renderer" not in effect_kwargs:
                effect_kwargs["renderer"] = SafeStaticRenderer(
                    text=f"Effect: {config.effect_type}",
                    width=screen.width
                )
        
        if config.effect_type == "RandomNoise":
            if "signal" in effect_kwargs:
                signal_config = effect_kwargs["signal"]
                signal = self._create_nested_renderer("signal", signal_config, screen)
                if signal:
                    effect_kwargs["signal"] = signal
                else:
                    effect_kwargs.pop("signal", None)
        
        if config.effect_type == "Print":
            if "y" not in effect_kwargs:
                effect_kwargs["y"] = screen.height // 4
            effect_kwargs["y"] = min(effect_kwargs["y"], screen.height - 1)
        
        if config.effect_type == "Cycle":
            if "y" not in effect_kwargs:
                effect_kwargs["y"] = screen.height // 4
            effect_kwargs["y"] = min(effect_kwargs["y"], screen.height - 1)
        
        if config.effect_type == "BannerText":
            if "y" not in effect_kwargs:
                effect_kwargs["y"] = screen.height // 4
            if "colour" not in effect_kwargs:
                effect_kwargs["colour"] = 7
            effect_kwargs["y"] = min(effect_kwargs["y"], screen.height - 1)
        
        if config.effect_type == "Mirage":
            if "y" not in effect_kwargs:
                effect_kwargs["y"] = screen.height // 4
            if "colour" not in effect_kwargs:
                effect_kwargs["colour"] = 7
            effect_kwargs["y"] = min(effect_kwargs["y"], screen.height - 1)
        
        if config.effect_type == "Stars":
            if "count" not in effect_kwargs:
                effect_kwargs["count"] = max(10, screen.width * screen.height // 40)
        
        if config.effect_type == "Scroll":
            if "rate" not in effect_kwargs:
                effect_kwargs["rate"] = 5
        
        if config.effect_type == "Clock":
            if "x" not in effect_kwargs:
                effect_kwargs["x"] = screen.width // 2
            if "y" not in effect_kwargs:
                effect_kwargs["y"] = screen.height // 2
            if "r" not in effect_kwargs:
                effect_kwargs["r"] = min(screen.width // 4, screen.height // 3)
            effect_kwargs["x"] = min(effect_kwargs["x"], screen.width - 1)
            effect_kwargs["y"] = min(effect_kwargs["y"], screen.height - 1)
        
        if config.effect_type == "Cog":
            if "x" not in effect_kwargs:
                effect_kwargs["x"] = screen.width // 2
            if "y" not in effect_kwargs:
                effect_kwargs["y"] = screen.height // 2
            if "radius" not in effect_kwargs:
                effect_kwargs["radius"] = min(screen.width // 4, screen.height // 3)
            effect_kwargs["x"] = min(effect_kwargs["x"], screen.width - 1)
            effect_kwargs["y"] = min(effect_kwargs["y"], screen.height - 1)
        
        if config.effect_type == "Background":
            if "bg" not in effect_kwargs:
                effect_kwargs["bg"] = 0
        
        if config.effect_type == "Wipe":
            if "bg" not in effect_kwargs:
                effect_kwargs["bg"] = 0
        
        try:
            filtered = filter_kwargs_for_class(
                effect_class,
                effect_kwargs,
                exclude_params=["screen"]
            )
            return effect_class(screen, **filtered)
        except Exception as e:
            raise EffectCreationError(f"Failed to create {config.effect_type}: {e}")
    
    def _create_effect(
        self,
        config: EffectConfig,
        screen: VirtualScreen
    ) -> Effect:
        """
        创建Effect实例，包含错误处理和回退机制。
        """
        try:
            return self._create_effect_safe(config, screen)
        except EffectCreationError:
            return Stars(
                screen,
                count=max(10, screen.width * screen.height // 40)
            )
    
    def set_effects(self, effect_configs: List[EffectConfig]):
        self._effect_configs = effect_configs
    
    def add_effect(self, effect_config: EffectConfig):
        self._effect_configs.append(effect_config)
    
    def clear_effects(self):
        self._effect_configs = []
    
    def _prepare_scene(self):
        self._screen = self._create_screen()
        self._effects = []
        
        for config in self._effect_configs:
            effect = self._create_effect(config, self._screen)
            self._effects.append(effect)
        
        self._scene = Scene(
            self._effects,
            duration=self.config.duration,
            clear=True,
        )
    
    def render_single_frame(self, frame_number: int = 0) -> FrameData:
        if not self._screen or not self._scene:
            self._prepare_scene()
        
        assert self._screen is not None
        assert self._scene is not None
        
        self._screen.clear_buffer(None, 0, 0)
        self._scene.reset(None, self._screen)
        
        for effect in self._scene.effects:
            effect.update(frame_number)
        
        return self._screen.current_frame_data
    
    def render_all_frames(self, max_frames: Optional[int] = None) -> List[FrameData]:
        if not self._screen or not self._scene:
            self._prepare_scene()
        
        assert self._screen is not None
        assert self._scene is not None
        
        frames = []
        total_frames = max_frames if max_frames else self.config.duration
        
        for frame_no in range(total_frames):
            self._screen.clear_buffer(None, 0, 0)
            for effect in self._scene.effects:
                effect.update(frame_no)
            frames.append(self._screen.current_frame_data)
        
        return frames
    
    def render_animation(self, duration: Optional[int] = None) -> Dict[str, Any]:
        actual_duration = duration if duration else self.config.duration
        frames = self.render_all_frames(max_frames=actual_duration)
        
        return {
            "config": {
                "width": self.config.width,
                "height": self.config.height,
                "colours": self.config.colours,
                "fps": self.config.fps,
                "frame_count": len(frames),
            },
            "frames": [f.to_dict() for f in frames],
            "effect_configs": [ec.to_dict() for ec in self._effect_configs],
        }
    
    @staticmethod
    def from_animation_data(data: Dict[str, Any]) -> "AnimationRenderer":
        config = RenderConfig(
            width=data["config"]["width"],
            height=data["config"]["height"],
            colours=data["config"]["colours"],
            fps=data["config"]["fps"],
            duration=data["config"]["frame_count"],
        )
        
        renderer = AnimationRenderer(config)
        
        for ec_data in data.get("effect_configs", []):
            renderer.add_effect(EffectConfig.from_dict(ec_data))
        
        return renderer

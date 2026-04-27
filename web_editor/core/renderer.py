import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

from asciimatics.renderers.base import Renderer, StaticRenderer, DynamicRenderer
from asciimatics.screen import TemporaryCanvas
from asciimatics.scene import Scene
from asciimatics.effects import Effect, Cycle, Stars, Print, BannerText, Mirage, Scroll
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
    FigletText,
    Scale,
    RotatedDuplicate,
    Chart,
    BarChart,
    Player,
    Typewriter,
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
    
    def __init__(self, height: int, width: int, colours: int = 256):
        super().__init__(height, width)
        self._colours = colours
        self._start_line = 0
        self._scenes: List[Scene] = []
        self._scene_index = 0
        self._frame = 0
        self._forced_update = False
    
    @property
    def colours(self) -> int:
        return self._colours
    
    @property
    def unicode_aware(self) -> bool:
        return True
    
    @property
    def palette(self) -> List[int]:
        if self._colours >= 256:
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


class EffectRegistry:
    """
    Effect注册器，用于管理可用的Effect类型和它们的配置。
    """
    
    EFFECT_TYPES: Dict[str, Type[Effect]] = {
        "Cycle": Cycle,
        "Stars": Stars,
        "Print": Print,
        "BannerText": BannerText,
        "Mirage": Mirage,
        "Scroll": Scroll,
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
        "RotatedDuplicate": RotatedDuplicate,
        "Chart": Chart,
        "BarChart": BarChart,
        "Player": Player,
        "Typewriter": Typewriter,
    }
    
    @classmethod
    def list_effects(cls) -> List[str]:
        return list(cls.EFFECT_TYPES.keys())
    
    @classmethod
    def list_renderers(cls) -> List[str]:
        return list(cls.RENDERER_TYPES.keys())


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
    
    def _create_renderer(self, renderer_type: str, config: Dict[str, Any], screen: VirtualScreen) -> Renderer:
        renderer_class = EffectRegistry.RENDERER_TYPES.get(renderer_type)
        if not renderer_class:
            raise ValueError(f"Unknown renderer type: {renderer_type}")
        
        if renderer_type in ["ColourImageFile"]:
            return renderer_class(screen=screen, **config)
        
        return renderer_class(**config)
    
    def _create_effect(self, config: EffectConfig, screen: VirtualScreen) -> Effect:
        effect_class = EffectRegistry.EFFECT_TYPES.get(config.effect_type)
        if not effect_class:
            raise ValueError(f"Unknown effect type: {config.effect_type}")
        
        effect_kwargs = config.effect_config.copy()
        
        if config.renderer_type:
            renderer = self._create_renderer(config.renderer_type, config.renderer_config, screen)
            effect_kwargs["renderer"] = renderer
        
        if "y" not in effect_kwargs:
            effect_kwargs["y"] = screen.height // 2 - 4
        
        return effect_class(screen, **effect_kwargs)
    
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

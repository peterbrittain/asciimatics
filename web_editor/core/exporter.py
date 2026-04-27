import io
import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

from .renderer import FrameData, AnimationRenderer, EffectConfig, RenderConfig, VirtualScreen


class ExportFormat(Enum):
    TEXT = "text"
    ANSI = "ansi"
    PNG = "png"
    GIF = "gif"
    PYTHON = "python"
    JSON = "json"


ANSI_COLORS_16 = [
    (0, 0, 0),       # 0: Black
    (128, 0, 0),     # 1: Red
    (0, 128, 0),     # 2: Green
    (128, 128, 0),   # 3: Yellow
    (0, 0, 128),     # 4: Blue
    (128, 0, 128),   # 5: Magenta
    (0, 128, 128),   # 6: Cyan
    (192, 192, 192), # 7: White
    (128, 128, 128), # 8: Bright Black
    (255, 0, 0),     # 9: Bright Red
    (0, 255, 0),     # 10: Bright Green
    (255, 255, 0),   # 11: Bright Yellow
    (0, 0, 255),     # 12: Bright Blue
    (255, 0, 255),   # 13: Bright Magenta
    (0, 255, 255),   # 14: Bright Cyan
    (255, 255, 255), # 15: Bright White
]

ANSI_COLORS_256 = ANSI_COLORS_16.copy()
for r in range(6):
    for g in range(6):
        for b in range(6):
            ANSI_COLORS_256.append((
                r * 40 + 55 if r > 0 else 0,
                g * 40 + 55 if g > 0 else 0,
                b * 40 + 55 if b > 0 else 0,
            ))
for i in range(24):
    grey = i * 10 + 8
    ANSI_COLORS_256.append((grey, grey, grey))


def get_color_rgb(color_index: Optional[int], is_256: bool = True) -> tuple:
    if color_index is None:
        return (0, 0, 0)
    
    colors = ANSI_COLORS_256 if is_256 else ANSI_COLORS_16
    if 0 <= color_index < len(colors):
        return colors[color_index]
    return (255, 255, 255)


def frame_to_image(
    frame: FrameData,
    cell_width: int = 8,
    cell_height: int = 16,
    colors: int = 256,
    bg_color: tuple = (0, 0, 0),
) -> Image.Image:
    width = len(frame.plain_image[0]) if frame.plain_image else 80
    height = len(frame.plain_image)
    
    img_width = width * cell_width
    img_height = height * cell_height
    
    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("consola.ttf", cell_height - 2)
    except:
        try:
            font = ImageFont.truetype("Courier New.ttf", cell_height - 2)
        except:
            font = ImageFont.load_default()
    
    is_256 = colors >= 256
    
    for y, line in enumerate(frame.plain_image):
        color_row = frame.colour_map[y] if y < len(frame.colour_map) else []
        for x, char in enumerate(line):
            if x >= len(color_row):
                continue
            
            fg, attr, bg = color_row[x]
            
            fg_rgb = get_color_rgb(fg, is_256)
            bg_rgb = get_color_rgb(bg, is_256)
            
            if bg is not None:
                draw.rectangle(
                    [
                        x * cell_width,
                        y * cell_height,
                        (x + 1) * cell_width - 1,
                        (y + 1) * cell_height - 1,
                    ],
                    fill=bg_rgb,
                )
            
            if char != " ":
                draw.text(
                    (x * cell_width, y * cell_height),
                    char,
                    fill=fg_rgb,
                    font=font,
                )
    
    return img


class Exporter:
    """
    导出器，负责将动画导出为各种格式。
    """
    
    @staticmethod
    def to_text(frames: List[FrameData], include_colors: bool = False) -> str:
        """
        导出为纯文本格式。
        """
        output = []
        for frame in frames:
            output.append(f"=== Frame {frame.frame_number} ===")
            output.extend(frame.plain_image)
            output.append("")
        return "\n".join(output)
    
    @staticmethod
    def to_ansi(frames: List[FrameData], colors: int = 256) -> str:
        """
        导出为ANSI转义序列格式（带颜色）。
        """
        output = []
        
        for frame in frames:
            output.append(f"\033[H\033[2J")
            
            for y, line in enumerate(frame.plain_image):
                if y >= len(frame.colour_map):
                    output.append(line)
                    continue
                
                color_row = frame.colour_map[y]
                line_output = []
                current_fg = None
                current_bg = None
                
                for x, char in enumerate(line):
                    if x >= len(color_row):
                        line_output.append(char)
                        continue
                    
                    fg, attr, bg = color_row[x]
                    
                    if fg != current_fg or bg != current_bg:
                        reset = "\033[0m"
                        fg_code = f"\033[38;5;{fg}m" if fg is not None and colors >= 256 else (f"\033[{30 + fg}m" if fg is not None else "")
                        bg_code = f"\033[48;5;{bg}m" if bg is not None and colors >= 256 else (f"\033[{40 + bg}m" if bg is not None else "")
                        
                        line_output.append(reset + fg_code + bg_code)
                        current_fg = fg
                        current_bg = bg
                    
                    line_output.append(char)
                
                output.append("".join(line_output))
            
            output.append("\033[0m\n")
        
        return "".join(output)
    
    @staticmethod
    def to_png(
        frames: List[FrameData],
        cell_width: int = 8,
        cell_height: int = 16,
        colors: int = 256,
    ) -> bytes:
        """
        导出为PNG图片（只导出第一帧）。
        """
        if not frames:
            return b""
        
        img = frame_to_image(frames[0], cell_width, cell_height, colors)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    @staticmethod
    def to_gif(
        frames: List[FrameData],
        cell_width: int = 8,
        cell_height: int = 16,
        colors: int = 256,
        fps: int = 20,
        loop: int = 0,
    ) -> bytes:
        """
        导出为GIF动画。
        """
        if not frames:
            return b""
        
        images = []
        for frame in frames:
            img = frame_to_image(frame, cell_width, cell_height, colors)
            images.append(img)
        
        buffer = io.BytesIO()
        duration = int(1000 / fps)
        
        images[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=loop,
        )
        
        return buffer.getvalue()
    
    @staticmethod
    def to_python_script(
        render_config: RenderConfig,
        effect_configs: List[EffectConfig],
        project_name: str = "MyAnimation",
    ) -> str:
        """
        导出为可执行的Python脚本。
        """
        imports = [
            "from asciimatics.effects import Cycle, Stars, Print, BannerText, Mirage, Scroll",
            "from asciimatics.renderers import FigletText, ImageFile, ColourImageFile",
            "from asciimatics.scene import Scene",
            "from asciimatics.screen import Screen",
        ]
        
        effect_imports = set()
        renderer_imports = set()
        
        for ec in effect_configs:
            effect_imports.add(ec.effect_type)
            if ec.renderer_type:
                renderer_imports.add(ec.renderer_type)
        
        import_lines = []
        if effect_imports:
            import_lines.append(f"from asciimatics.effects import {', '.join(sorted(effect_imports))}")
        if renderer_imports:
            import_lines.append(f"from asciimatics.renderers import {', '.join(sorted(renderer_imports))}")
        
        import_lines.extend([
            "from asciimatics.scene import Scene",
            "from asciimatics.screen import Screen",
        ])
        
        script_parts = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            '"""',
            f"ASCII Animation: {project_name}",
            f"Generated by Asciimatics Web Editor",
            '"""',
            "",
        ]
        
        script_parts.extend(import_lines)
        script_parts.append("")
        
        script_parts.extend([
            f"def {project_name.lower()}(screen):",
            f"    # Animation: {project_name}",
            "",
            "    effects = []",
            "",
        ])
        
        var_counter = 0
        for i, ec in enumerate(effect_configs):
            if ec.renderer_type:
                var_name = f"renderer_{var_counter}"
                var_counter += 1
                
                render_args = []
                for key, value in ec.renderer_config.items():
                    if isinstance(value, str):
                        render_args.append(f"{key}={repr(value)}")
                    else:
                        render_args.append(f"{key}={value}")
                
                render_args_str = ", ".join(render_args)
                script_parts.append(f"    {var_name} = {ec.renderer_type}({render_args_str})")
                
                effect_args = [f"screen", f"renderer={var_name}"]
            else:
                effect_args = ["screen"]
            
            for key, value in ec.effect_config.items():
                if isinstance(value, str):
                    effect_args.append(f"{key}={repr(value)}")
                else:
                    effect_args.append(f"{key}={value}")
            
            effect_args_str = ", ".join(effect_args)
            script_parts.append(f"    effects.append({ec.effect_type}({effect_args_str}))")
            script_parts.append("")
        
        script_parts.extend([
            f"    scene = Scene(effects, duration={render_config.duration})",
            "    screen.play([scene], repeat=True)",
            "",
            "",
            "if __name__ == \"__main__\":",
            f"    Screen.wrapper({project_name.lower()})",
        ])
        
        return "\n".join(script_parts)
    
    @staticmethod
    def to_json(
        render_config: RenderConfig,
        effect_configs: List[EffectConfig],
        frames: Optional[List[FrameData]] = None,
    ) -> str:
        """
        导出为JSON格式。
        """
        data = {
            "render_config": {
                "width": render_config.width,
                "height": render_config.height,
                "colours": render_config.colours,
                "fps": render_config.fps,
                "duration": render_config.duration,
            },
            "effect_configs": [ec.to_dict() for ec in effect_configs],
        }
        
        if frames:
            data["frames"] = [f.to_dict() for f in frames]
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def export(
        cls,
        format: ExportFormat,
        renderer: Optional[AnimationRenderer] = None,
        frames: Optional[List[FrameData]] = None,
        render_config: Optional[RenderConfig] = None,
        effect_configs: Optional[List[EffectConfig]] = None,
        **kwargs,
    ) -> Any:
        """
        通用导出方法。
        """
        if renderer:
            if render_config is None:
                render_config = renderer.config
            if effect_configs is None:
                effect_configs = renderer._effect_configs
        
        if frames is None and renderer:
            frames = renderer.render_all_frames()
        
        if format == ExportFormat.TEXT:
            return cls.to_text(frames or [], include_colors=kwargs.get("include_colors", False))
        
        elif format == ExportFormat.ANSI:
            colors = render_config.colours if render_config else 256
            return cls.to_ansi(frames or [], colors)
        
        elif format == ExportFormat.PNG:
            cell_width = kwargs.get("cell_width", 8)
            cell_height = kwargs.get("cell_height", 16)
            colors = render_config.colours if render_config else 256
            return cls.to_png(frames or [], cell_width, cell_height, colors)
        
        elif format == ExportFormat.GIF:
            cell_width = kwargs.get("cell_width", 8)
            cell_height = kwargs.get("cell_height", 16)
            colors = render_config.colours if render_config else 256
            fps = render_config.fps if render_config else 20
            loop = kwargs.get("loop", 0)
            return cls.to_gif(frames or [], cell_width, cell_height, colors, fps, loop)
        
        elif format == ExportFormat.PYTHON:
            if not render_config or not effect_configs:
                raise ValueError("render_config and effect_configs are required for Python export")
            project_name = kwargs.get("project_name", "MyAnimation")
            return cls.to_python_script(render_config, effect_configs, project_name)
        
        elif format == ExportFormat.JSON:
            if not render_config or not effect_configs:
                raise ValueError("render_config and effect_configs are required for JSON export")
            return cls.to_json(render_config, effect_configs, frames)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

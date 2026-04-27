import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .renderer import EffectConfig, RenderConfig


class TemplateCategory(Enum):
    ANIMATION = "animation"
    TEXT = "text"
    MENU = "menu"
    UI = "ui"
    CUSTOM = "custom"


@dataclass
class Template:
    template_id: str
    name: str
    description: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    
    render_config: RenderConfig = field(default_factory=RenderConfig)
    effect_configs: List[EffectConfig] = field(default_factory=list)
    
    preview_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_builtin: bool = False
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "render_config": {
                "width": self.render_config.width,
                "height": self.render_config.height,
                "colours": self.render_config.colours,
                "fps": self.render_config.fps,
                "duration": self.render_config.duration,
            },
            "effect_configs": [ec.to_dict() for ec in self.effect_configs],
            "preview_data": self.preview_data,
            "tags": self.tags,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        render_config = RenderConfig(
            width=data["render_config"].get("width", 80),
            height=data["render_config"].get("height", 24),
            colours=data["render_config"].get("colours", 256),
            fps=data["render_config"].get("fps", 20),
            duration=data["render_config"].get("duration", 100),
        )
        
        effect_configs = [EffectConfig.from_dict(ec) for ec in data.get("effect_configs", [])]
        
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data.get("description", ""),
            category=TemplateCategory(data.get("category", "custom")),
            render_config=render_config,
            effect_configs=effect_configs,
            preview_data=data.get("preview_data", {}),
            tags=data.get("tags", []),
            is_builtin=data.get("is_builtin", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data.get("updated_at", data["created_at"])),
        )


class TemplateManager:
    """
    模板管理器，负责模板的存储、检索和管理。
    """
    
    BUILTIN_TEMPLATES: List[Dict[str, Any]] = [
        {
            "template_id": "builtin_hello_world",
            "name": "Hello World",
            "description": "一个简单的文字动画模板，展示彩色文字效果",
            "category": "text",
            "render_config": {"width": 80, "height": 24, "colours": 256, "fps": 20, "duration": 100},
            "effect_configs": [
                {
                    "effect_type": "Cycle",
                    "renderer_type": "FigletText",
                    "renderer_config": {"text": "HELLO", "font": "big"},
                    "effect_config": {"y": 4},
                },
                {
                    "effect_type": "Cycle",
                    "renderer_type": "FigletText",
                    "renderer_config": {"text": "WORLD", "font": "big"},
                    "effect_config": {"y": 14},
                },
            ],
            "tags": ["simple", "text", "colours"],
            "is_builtin": True,
        },
        {
            "template_id": "builtin_stars",
            "name": "星空效果",
            "description": "闪烁的星空背景模板",
            "category": "animation",
            "render_config": {"width": 80, "height": 24, "colours": 256, "fps": 20, "duration": 200},
            "effect_configs": [
                {
                    "effect_type": "Stars",
                    "renderer_type": None,
                    "renderer_config": {},
                    "effect_config": {"count": 50},
                },
            ],
            "tags": ["animation", "background", "stars"],
            "is_builtin": True,
        },
        {
            "template_id": "builtin_banner",
            "name": "滚动横幅",
            "description": "水平滚动的文字横幅模板",
            "category": "animation",
            "render_config": {"width": 80, "height": 24, "colours": 256, "fps": 20, "duration": 300},
            "effect_configs": [
                {
                    "effect_type": "BannerText",
                    "renderer_type": "FigletText",
                    "renderer_config": {"text": "WELCOME TO ASCIIMATICS ", "font": "slant"},
                    "effect_config": {"y": 10, "colour": 2},
                },
            ],
            "tags": ["banner", "scroll", "text"],
            "is_builtin": True,
        },
        {
            "template_id": "builtin_mirage",
            "name": "幻影文字",
            "description": "文字渐显渐隐效果",
            "category": "text",
            "render_config": {"width": 80, "height": 24, "colours": 256, "fps": 20, "duration": 150},
            "effect_configs": [
                {
                    "effect_type": "Mirage",
                    "renderer_type": "FigletText",
                    "renderer_config": {"text": "MAGIC", "font": "big"},
                    "effect_config": {"y": 8, "colour": 5},
                },
            ],
            "tags": ["text", "fade", "magic"],
            "is_builtin": True,
        },
    ]
    
    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        self._builtin_templates: List[Template] = []
        self._init_builtin_templates()
    
    def _init_builtin_templates(self):
        for data in self.BUILTIN_TEMPLATES:
            data["created_at"] = datetime.now().isoformat()
            data["updated_at"] = datetime.now().isoformat()
            self._builtin_templates.append(Template.from_dict(data))
    
    def _get_template_path(self, template_id: str) -> str:
        return os.path.join(self.templates_dir, f"{template_id}.json")
    
    def save_template(self, template: Template) -> str:
        template.updated_at = datetime.now()
        path = self._get_template_path(template.template_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        return path
    
    def load_template(self, template_id: str) -> Optional[Template]:
        for builtin in self._builtin_templates:
            if builtin.template_id == template_id:
                return builtin
        
        path = self._get_template_path(template_id)
        if not os.path.exists(path):
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return Template.from_dict(data)
    
    def delete_template(self, template_id: str) -> bool:
        for builtin in self._builtin_templates:
            if builtin.template_id == template_id:
                return False
        
        path = self._get_template_path(template_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        include_builtin: bool = True,
        include_custom: bool = True,
    ) -> List[Template]:
        templates: List[Template] = []
        
        if include_builtin:
            for builtin in self._builtin_templates:
                if category is None or builtin.category == category:
                    templates.append(builtin)
        
        if include_custom:
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(".json"):
                    template_id = filename[:-5]
                    template = self.load_template(template_id)
                    if template:
                        if category is None or template.category == category:
                            templates.append(template)
        
        templates.sort(key=lambda t: (t.is_builtin, t.updated_at), reverse=True)
        return templates
    
    def create_template(
        self,
        name: str,
        description: str,
        render_config: RenderConfig,
        effect_configs: List[EffectConfig],
        category: TemplateCategory = TemplateCategory.CUSTOM,
        tags: List[str] = None,
        preview_data: Dict[str, Any] = None,
    ) -> Template:
        template_id = f"tpl_{int(time.time())}_{os.urandom(4).hex()}"
        
        template = Template(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            render_config=render_config,
            effect_configs=[EffectConfig.from_dict(ec.to_dict()) for ec in effect_configs],
            preview_data=preview_data or {},
            tags=tags or [],
            is_builtin=False,
        )
        
        self.save_template(template)
        return template
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        render_config: Optional[RenderConfig] = None,
        effect_configs: Optional[List[EffectConfig]] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Template]:
        template = self.load_template(template_id)
        if not template:
            return None
        
        if template.is_builtin:
            return None
        
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if category is not None:
            template.category = category
        if render_config is not None:
            template.render_config = render_config
        if effect_configs is not None:
            template.effect_configs = effect_configs
        if tags is not None:
            template.tags = tags
        
        self.save_template(template)
        return template
    
    def search_templates(self, query: str) -> List[Template]:
        results = []
        query_lower = query.lower()
        
        for template in self.list_templates():
            if (
                query_lower in template.name.lower()
                or query_lower in template.description.lower()
                or any(query_lower in tag.lower() for tag in template.tags)
            ):
                results.append(template)
        
        return results
    
    def get_categories(self) -> List[Dict[str, Any]]:
        categories = {}
        for template in self.list_templates():
            cat = template.category.value
            if cat not in categories:
                categories[cat] = {"count": 0, "templates": []}
            categories[cat]["count"] += 1
        
        return [
            {"category": cat, "count": data["count"]}
            for cat, data in categories.items()
        ]

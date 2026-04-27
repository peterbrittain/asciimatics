import json
import os
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .renderer import EffectConfig, RenderConfig


class ProjectStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class Version:
    version_id: str
    version_number: int
    created_at: datetime
    description: str = ""
    effect_configs: List[Dict[str, Any]] = field(default_factory=list)
    render_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "effect_configs": self.effect_configs,
            "render_config": self.render_config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Version":
        return cls(
            version_id=data["version_id"],
            version_number=data["version_number"],
            created_at=datetime.fromisoformat(data["created_at"]),
            description=data.get("description", ""),
            effect_configs=data.get("effect_configs", []),
            render_config=data.get("render_config", {}),
        )


@dataclass
class AnimationProject:
    project_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: ProjectStatus = ProjectStatus.DRAFT
    
    render_config: RenderConfig = field(default_factory=RenderConfig)
    effect_configs: List[EffectConfig] = field(default_factory=list)
    
    versions: List[Version] = field(default_factory=list)
    current_version: Optional[int] = None
    
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "render_config": {
                "width": self.render_config.width,
                "height": self.render_config.height,
                "colours": self.render_config.colours,
                "fps": self.render_config.fps,
                "duration": self.render_config.duration,
            },
            "effect_configs": [ec.to_dict() for ec in self.effect_configs],
            "versions": [v.to_dict() for v in self.versions],
            "current_version": self.current_version,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationProject":
        render_config = RenderConfig(
            width=data["render_config"].get("width", 80),
            height=data["render_config"].get("height", 24),
            colours=data["render_config"].get("colours", 256),
            fps=data["render_config"].get("fps", 20),
            duration=data["render_config"].get("duration", 100),
        )
        
        effect_configs = [EffectConfig.from_dict(ec) for ec in data.get("effect_configs", [])]
        versions = [Version.from_dict(v) for v in data.get("versions", [])]
        
        return cls(
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data.get("updated_at", data["created_at"])),
            status=ProjectStatus(data.get("status", "draft")),
            render_config=render_config,
            effect_configs=effect_configs,
            versions=versions,
            current_version=data.get("current_version"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def create_version(self, description: str = "") -> Version:
        version_number = len(self.versions) + 1
        version = Version(
            version_id=f"{self.project_id}_v{version_number}_{int(time.time())}",
            version_number=version_number,
            created_at=datetime.now(),
            description=description,
            effect_configs=[ec.to_dict() for ec in self.effect_configs],
            render_config={
                "width": self.render_config.width,
                "height": self.render_config.height,
                "colours": self.render_config.colours,
                "fps": self.render_config.fps,
                "duration": self.render_config.duration,
            },
        )
        self.versions.append(version)
        self.current_version = version_number
        self.updated_at = datetime.now()
        return version
    
    def restore_version(self, version_number: int) -> bool:
        for version in self.versions:
            if version.version_number == version_number:
                self.render_config = RenderConfig(
                    width=version.render_config.get("width", 80),
                    height=version.render_config.get("height", 24),
                    colours=version.render_config.get("colours", 256),
                    fps=version.render_config.get("fps", 20),
                    duration=version.render_config.get("duration", 100),
                )
                self.effect_configs = [EffectConfig.from_dict(ec) for ec in version.effect_configs]
                self.current_version = version_number
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_version(self, version_number: int) -> Optional[Version]:
        for version in self.versions:
            if version.version_number == version_number:
                return version
        return None


class Storage:
    """
    存储管理器，负责项目的持久化存储。
    """
    
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.projects_dir = os.path.join(storage_dir, "projects")
        self.templates_dir = os.path.join(storage_dir, "templates")
        self.exports_dir = os.path.join(storage_dir, "exports")
        
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
    
    def _get_project_path(self, project_id: str) -> str:
        return os.path.join(self.projects_dir, f"{project_id}.json")
    
    def save_project(self, project: AnimationProject) -> str:
        project.updated_at = datetime.now()
        path = self._get_project_path(project.project_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
        return path
    
    def load_project(self, project_id: str) -> Optional[AnimationProject]:
        path = self._get_project_path(project_id)
        if not os.path.exists(path):
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return AnimationProject.from_dict(data)
    
    def delete_project(self, project_id: str) -> bool:
        path = self._get_project_path(project_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def list_projects(self, include_archived: bool = False) -> List[AnimationProject]:
        projects = []
        for filename in os.listdir(self.projects_dir):
            if filename.endswith(".json"):
                project_id = filename[:-5]
                project = self.load_project(project_id)
                if project:
                    if not include_archived and project.status == ProjectStatus.ARCHIVED:
                        continue
                    projects.append(project)
        
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        return projects
    
    def create_project(
        self,
        name: str,
        description: str = "",
        width: int = 80,
        height: int = 24,
        colours: int = 256,
        fps: int = 20,
        duration: int = 100,
    ) -> AnimationProject:
        project_id = f"proj_{int(time.time())}_{os.urandom(4).hex()}"
        
        project = AnimationProject(
            project_id=project_id,
            name=name,
            description=description,
            render_config=RenderConfig(
                width=width,
                height=height,
                colours=colours,
                fps=fps,
                duration=duration,
            ),
        )
        
        self.save_project(project)
        return project
    
    def duplicate_project(self, project_id: str, new_name: str) -> Optional[AnimationProject]:
        original = self.load_project(project_id)
        if not original:
            return None
        
        new_id = f"proj_{int(time.time())}_{os.urandom(4).hex()}"
        new_project = AnimationProject(
            project_id=new_id,
            name=new_name,
            description=f"Duplicated from: {original.name}\n{original.description}",
            render_config=RenderConfig(
                width=original.render_config.width,
                height=original.render_config.height,
                colours=original.render_config.colours,
                fps=original.render_config.fps,
                duration=original.render_config.duration,
            ),
            effect_configs=[EffectConfig.from_dict(ec.to_dict()) for ec in original.effect_configs],
        )
        
        self.save_project(new_project)
        return new_project
    
    def archive_project(self, project_id: str) -> bool:
        project = self.load_project(project_id)
        if not project:
            return False
        
        project.status = ProjectStatus.ARCHIVED
        self.save_project(project)
        return True
    
    def get_export_path(self, filename: str) -> str:
        return os.path.join(self.exports_dir, filename)

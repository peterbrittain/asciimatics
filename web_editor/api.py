import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
web_editor_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, web_editor_root)

from web_editor.core.compat import ensure_compatibility
ensure_compatibility()

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
    StreamingResponse,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from web_editor.core.renderer import (
    AnimationRenderer,
    RenderConfig,
    EffectConfig,
    EffectRegistry,
    FrameData,
)
from web_editor.core.storage import (
    Storage,
    AnimationProject,
    Version,
    ProjectStatus,
)
from web_editor.core.templates import (
    TemplateManager,
    Template,
    TemplateCategory,
)
from web_editor.core.exporter import (
    Exporter,
    ExportFormat,
)


STORAGE_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(STORAGE_DIR, exist_ok=True)

storage = Storage(STORAGE_DIR)
template_manager = TemplateManager(os.path.join(STORAGE_DIR, "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Asciimatics Web Editor...")
    print(f"Storage directory: {STORAGE_DIR}")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Asciimatics Web Editor API",
    description="Web可视化ASCII动画编辑器API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RenderConfigModel(BaseModel):
    width: int = Field(default=80, ge=20, le=200)
    height: int = Field(default=24, ge=10, le=100)
    colours: int = Field(default=256, ge=8, le=256)
    fps: int = Field(default=20, ge=1, le=60)
    duration: int = Field(default=100, ge=1, le=10000)


class EffectConfigModel(BaseModel):
    effect_type: str
    renderer_type: Optional[str] = None
    renderer_config: Dict[str, Any] = Field(default_factory=dict)
    effect_config: Dict[str, Any] = Field(default_factory=dict)


class CreateProjectModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    render_config: Optional[RenderConfigModel] = None
    effect_configs: List[EffectConfigModel] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class UpdateProjectModel(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    render_config: Optional[RenderConfigModel] = None
    effect_configs: Optional[List[EffectConfigModel]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class CreateVersionModel(BaseModel):
    description: str = Field(default="", max_length=200)


class RenderFrameModel(BaseModel):
    render_config: RenderConfigModel
    effect_configs: List[EffectConfigModel]
    frame_number: int = Field(default=0, ge=0)


class RenderAnimationModel(BaseModel):
    render_config: RenderConfigModel
    effect_configs: List[EffectConfigModel]
    max_frames: Optional[int] = Field(None, ge=1)


class CreateTemplateModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    category: str = Field(default="custom")
    render_config: RenderConfigModel
    effect_configs: List[EffectConfigModel]
    tags: List[str] = Field(default_factory=list)


def to_render_config(model: RenderConfigModel) -> RenderConfig:
    return RenderConfig(
        width=model.width,
        height=model.height,
        colours=model.colours,
        fps=model.fps,
        duration=model.duration,
    )


def to_effect_config(model: EffectConfigModel) -> EffectConfig:
    return EffectConfig(
        effect_type=model.effect_type,
        renderer_type=model.renderer_type,
        renderer_config=model.renderer_config,
        effect_config=model.effect_config,
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/effects")
async def list_effects():
    return {"effects": EffectRegistry.list_effects()}


@app.get("/api/renderers")
async def list_renderers():
    return {"renderers": EffectRegistry.list_renderers()}


@app.get("/api/projects")
async def list_projects(
    include_archived: bool = Query(False, description="Include archived projects"),
):
    projects = storage.list_projects(include_archived=include_archived)
    return {"projects": [p.to_dict() for p in projects], "count": len(projects)}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@app.post("/api/projects")
async def create_project(data: CreateProjectModel):
    render_config = RenderConfig()
    if data.render_config:
        render_config = to_render_config(data.render_config)
    
    effect_configs = [to_effect_config(ec) for ec in data.effect_configs]
    
    project = storage.create_project(
        name=data.name,
        description=data.description,
        width=render_config.width,
        height=render_config.height,
        colours=render_config.colours,
        fps=render_config.fps,
        duration=render_config.duration,
    )
    
    project.effect_configs = effect_configs
    project.tags = data.tags
    storage.save_project(project)
    
    return project.to_dict()


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, data: UpdateProjectModel):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.render_config is not None:
        project.render_config = RenderConfig(
            width=data.render_config.width,
            height=data.render_config.height,
            colours=data.render_config.colours,
            fps=data.render_config.fps,
            duration=data.render_config.duration,
        )
    if data.effect_configs is not None:
        project.effect_configs = [to_effect_config(ec) for ec in data.effect_configs]
    if data.tags is not None:
        project.tags = data.tags
    if data.status is not None:
        project.status = ProjectStatus(data.status)
    
    storage.save_project(project)
    return project.to_dict()


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    success = storage.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": "Project deleted"}


@app.post("/api/projects/{project_id}/duplicate")
async def duplicate_project(project_id: str, new_name: str = Query(..., description="New project name")):
    project = storage.duplicate_project(project_id, new_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@app.post("/api/projects/{project_id}/archive")
async def archive_project(project_id: str):
    success = storage.archive_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": "Project archived"}


@app.get("/api/projects/{project_id}/versions")
async def list_versions(project_id: str):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"versions": [v.to_dict() for v in project.versions]}


@app.post("/api/projects/{project_id}/versions")
async def create_version(project_id: str, description: str = Query(default="", description="Version description")):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    version = project.create_version(description)
    storage.save_project(project)
    return version.to_dict()


@app.post("/api/projects/{project_id}/versions/{version_number}/restore")
async def restore_version(project_id: str, version_number: int):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    success = project.restore_version(version_number)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    
    storage.save_project(project)
    return {"status": "success", "message": f"Restored to version {version_number}", "project": project.to_dict()}


@app.get("/api/templates")
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    include_builtin: bool = Query(True, description="Include builtin templates"),
    include_custom: bool = Query(True, description="Include custom templates"),
):
    category_enum = TemplateCategory(category) if category else None
    templates = template_manager.list_templates(
        category=category_enum,
        include_builtin=include_builtin,
        include_custom=include_custom,
    )
    return {"templates": [t.to_dict() for t in templates], "count": len(templates)}


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    template = template_manager.load_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@app.post("/api/templates")
async def create_template(data: CreateProjectModel):
    render_config = RenderConfig()
    if data.render_config:
        render_config = RenderConfig(
            width=data.render_config.width,
            height=data.render_config.height,
            colours=data.render_config.colours,
            fps=data.render_config.fps,
            duration=data.render_config.duration,
        )
    
    effect_configs = [to_effect_config(ec) for ec in data.effect_configs]
    
    template = template_manager.create_template(
        name=data.name,
        description=data.description,
        render_config=render_config,
        effect_configs=effect_configs,
        tags=data.tags,
    )
    
    return template.to_dict()


@app.get("/api/templates/categories")
async def get_template_categories():
    return {"categories": template_manager.get_categories()}


@app.get("/api/templates/search")
async def search_templates(query: str = Query(..., description="Search query")):
    templates = template_manager.search_templates(query)
    return {"templates": [t.to_dict() for t in templates], "count": len(templates)}


@app.post("/api/render/frame")
async def render_frame(
    render_config: RenderConfigModel,
    effect_configs: List[EffectConfigModel],
    frame_number: int = Query(default=0, ge=0),
):
    config = RenderConfig(
        width=render_config.width,
        height=render_config.height,
        colours=render_config.colours,
        fps=render_config.fps,
        duration=render_config.duration,
    )
    
    renderer = AnimationRenderer(config)
    for ec in effect_configs:
        renderer.add_effect(to_effect_config(ec))
    
    frame = renderer.render_single_frame(frame_number)
    return frame.to_dict()


@app.post("/api/render/animation")
async def render_animation(
    render_config: RenderConfigModel,
    effect_configs: List[EffectConfigModel],
    max_frames: Optional[int] = Query(None, ge=1),
):
    config = RenderConfig(
        width=render_config.width,
        height=render_config.height,
        colours=render_config.colours,
        fps=render_config.fps,
        duration=render_config.duration,
    )
    
    renderer = AnimationRenderer(config)
    for ec in effect_configs:
        renderer.add_effect(to_effect_config(ec))
    
    animation_data = renderer.render_animation(max_frames)
    return animation_data


@app.post("/api/render/project/{project_id}")
async def render_project(project_id: str, max_frames: Optional[int] = Query(None, ge=1)):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    renderer = AnimationRenderer(project.render_config)
    for ec in project.effect_configs:
        renderer.add_effect(ec)
    
    animation_data = renderer.render_animation(max_frames)
    return animation_data


@app.post("/api/export/{format}")
async def export_animation(
    format: str,
    render_config: RenderConfigModel,
    effect_configs: List[EffectConfigModel],
    project_name: str = Query(default="MyAnimation"),
    cell_width: int = Query(default=8, ge=4, le=32),
    cell_height: int = Query(default=16, ge=8, le=64),
):
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    config = RenderConfig(
        width=render_config.width,
        height=render_config.height,
        colours=render_config.colours,
        fps=render_config.fps,
        duration=render_config.duration,
    )
    
    effects = [to_effect_config(ec) for ec in effect_configs]
    
    renderer = AnimationRenderer(config)
    for ec in effects:
        renderer.add_effect(ec)
    
    frames = renderer.render_all_frames()
    
    result = Exporter.export(
        format=export_format,
        renderer=renderer,
        frames=frames,
        project_name=project_name,
        cell_width=cell_width,
        cell_height=cell_height,
    )
    
    if export_format in [ExportFormat.PNG, ExportFormat.GIF]:
        filename = f"export_{int(__import__('time').time())}.{format}"
        filepath = storage.get_export_path(filename)
        with open(filepath, "wb") as f:
            f.write(result)
        
        return {
            "format": format,
            "filename": filename,
            "download_url": f"/api/exports/{filename}",
        }
    
    elif export_format in [ExportFormat.TEXT, ExportFormat.ANSI, ExportFormat.PYTHON, ExportFormat.JSON]:
        return {
            "format": format,
            "content": result,
        }
    
    return {"status": "success"}


@app.get("/api/exports/{filename}")
async def download_export(filename: str):
    filepath = storage.get_export_path(filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        filepath,
        media_type="application/octet-stream",
        filename=filename,
    )


@app.post("/api/export/project/{project_id}/{format}")
async def export_project(
    project_id: str,
    format: str,
    project_name: str = Query(default="MyAnimation"),
    cell_width: int = Query(default=8, ge=4, le=32),
    cell_height: int = Query(default=16, ge=8, le=64),
):
    project = storage.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    renderer = AnimationRenderer(project.render_config)
    for ec in project.effect_configs:
        renderer.add_effect(ec)
    
    frames = renderer.render_all_frames()
    
    result = Exporter.export(
        format=export_format,
        renderer=renderer,
        frames=frames,
        project_name=project_name or project.name,
        cell_width=cell_width,
        cell_height=cell_height,
    )
    
    if export_format in [ExportFormat.PNG, ExportFormat.GIF]:
        filename = f"{project_id}_{int(__import__('time').time())}.{format}"
        filepath = storage.get_export_path(filename)
        with open(filepath, "wb") as f:
            f.write(result)
        
        return {
            "format": format,
            "filename": filename,
            "download_url": f"/api/exports/{filename}",
        }
    
    elif export_format in [ExportFormat.TEXT, ExportFormat.ANSI, ExportFormat.PYTHON, ExportFormat.JSON]:
        return {
            "format": format,
            "content": result,
        }
    
    return {"status": "success"}


@app.get("/api/tools/effects")
async def get_effect_info():
    return {
        "effects": EffectRegistry.list_effects(),
        "renderers": EffectRegistry.list_renderers(),
    }


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Asciimatics Web Editor</title>
    <style>
        body { font-family: monospace; padding: 2rem; background: #1a1a2e; color: #eee; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #4ade80; }
        .api-link { color: #60a5fa; text-decoration: none; }
        .api-link:hover { text-decoration: underline; }
        pre { background: #16213e; padding: 1rem; border-radius: 8px; overflow-x: auto; }
        code { color: #f97316; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ASCIIMATICS Web Editor</h1>
        <p>Web可视化ASCII动画编辑器</p>
        <h2>API文档</h2>
        <ul>
            <li><a class="api-link" href="/docs">Swagger UI</a> - 交互式API文档</li>
            <li><a class="api-link" href="/redoc">ReDoc</a> - 另一种API文档</li>
            <li><a class="api-link" href="/openapi.json">OpenAPI Schema</a></li>
        </ul>
        <h2>功能特性</h2>
        <ul>
            <li>项目管理：创建、编辑、删除、复制、归档项目</li>
            <li>版本控制：创建版本、历史回溯</li>
            <li>模板管理：内置模板、自定义模板</li>
            <li>渲染：单帧渲染、完整动画渲染</li>
            <li>导出：TEXT、ANSI、PNG、GIF、Python脚本、JSON</li>
        </ul>
    </div>
</body>
</html>
""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

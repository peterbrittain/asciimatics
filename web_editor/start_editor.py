#!/usr/bin/env python3
"""
Asciimatics Web Editor 启动脚本

使用方法:
    python start_editor.py

然后在浏览器中访问:
    http://localhost:8000
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from web_editor.core.compat import ensure_compatibility
ensure_compatibility()

def check_dependencies():
    missing = []
    
    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")
    
    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")
    
    try:
        import pydantic
    except ImportError:
        missing.append("pydantic")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("pillow")
    
    try:
        import asciimatics
    except ImportError as e:
        if "win32console" in str(e) or "pywintypes" in str(e):
            pass
        else:
            missing.append("asciimatics (本项目内置)")
    
    if missing:
        print("❌ 缺少依赖包:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("")
        print("请运行以下命令安装依赖:")
        print(f"   pip install -r {os.path.join(os.path.dirname(__file__), 'requirements.txt')}")
        return False
    
    print("✅ 所有依赖已就绪")
    return True


def main():
    print("=" * 60)
    print("  ASCIIMATICS Web Editor")
    print("  Web可视化ASCII动画编辑器")
    print("=" * 60)
    print("")
    
    if not check_dependencies():
        sys.exit(1)
    
    print("")
    print("正在启动服务器...")
    print("")
    
    import uvicorn
    from web_editor.api import app
    
    print("=" * 60)
    print("  服务器已启动!")
    print("=" * 60)
    print("")
    print("  🌐 访问地址:")
    print(f"     主页面:  http://localhost:8000")
    print(f"     API文档:  http://localhost:8000/docs")
    print(f"     ReDoc:    http://localhost:8000/redoc")
    print("")
    print("  ⚙️  按 Ctrl+C 停止服务器")
    print("")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()

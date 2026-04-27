"""
测试兼容性层是否解决了win32console的DLL导入问题

这个测试不依赖pyfiglet或其他可选依赖，
只验证核心的兼容性层是否正常工作。
"""

import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.dirname(test_dir)
web_editor_dir = os.path.dirname(core_dir)
project_root = os.path.dirname(web_editor_dir)

sys.path.insert(0, project_root)
sys.path.insert(0, web_editor_dir)

print(f"Project root: {project_root}")
print(f"Web editor dir: {web_editor_dir}")
print("")

print("=" * 60)
print("Testing win32console compatibility layer...")
print("=" * 60)
print("")

print("Step 1: Checking if we're on Windows...")
print(f"  sys.platform = {sys.platform}")
print("")

print("Step 2: Importing compatibility layer...")
from core.compat import _create_dummy_modules, _DummyModule, ensure_compatibility
ensure_compatibility()
print("  Compatibility layer loaded")
print("")

print("Step 3: Verifying dummy modules are in sys.modules...")
dummy_modules = [
    "win32console",
    "win32con", 
    "win32event",
    "win32file",
    "pywintypes",
]
for mod_name in dummy_modules:
    if mod_name in sys.modules:
        module = sys.modules[mod_name]
        print(f"  ✓ {mod_name}: {type(module).__name__}")
        
        dummy_attr = module.some_test_attribute
        print(f"    - Attribute access returns: {type(dummy_attr).__name__}")
        print(f"    - Callable test: {dummy_attr()} returns: {type(dummy_attr()).__name__}")
        print(f"    - Int conversion: int({dummy_attr}) = {int(dummy_attr)}")
    else:
        print(f"  ✗ {mod_name}: NOT FOUND")
print("")

print("Step 4: Testing screen.py import (the key test!)...")
print("  This is the critical test - does screen.py load without win32console DLL errors?")
print("")

try:
    from asciimatics.screen import Screen, TemporaryCanvas, _AbstractCanvas
    print("  ✓ SUCCESS! screen.py imported successfully")
    print("")
    print("  Classes available:")
    print(f"    - Screen: {Screen}")
    print(f"    - TemporaryCanvas: {TemporaryCanvas}")
    print(f"    - _AbstractCanvas: {_AbstractCanvas}")
    print("")
    
    print("  Screen constants available:")
    print(f"    - COLOUR_BLACK: {Screen.COLOUR_BLACK}")
    print(f"    - COLOUR_WHITE: {Screen.COLOUR_WHITE}")
    print(f"    - COLOUR_RED: {Screen.COLOUR_RED}")
    print(f"    - A_BOLD: {Screen.A_BOLD}")
    print(f"    - A_NORMAL: {Screen.A_NORMAL}")
    print("")
    
    print("Step 5: Testing TemporaryCanvas instantiation...")
    try:
        canvas = TemporaryCanvas(height=24, width=80)
        print(f"  ✓ TemporaryCanvas created: {canvas.width}x{canvas.height}")
        print(f"    - colours property: {canvas.colours}")
        print(f"    - unicode_aware: {canvas.unicode_aware}")
        print("")
        
        print("Step 6: Testing canvas drawing...")
        canvas.print_at("Hello, World!", 0, 0, colour=2)
        canvas.print_at("Testing 123", 0, 1, colour=3)
        
        plain_image = canvas.plain_image
        print(f"  ✓ plain_image has {len(plain_image)} lines")
        print(f"    - Line 0: {repr(plain_image[0][:20])}...")
        print(f"    - Line 1: {repr(plain_image[1][:20])}...")
        print("")
        
        colour_map = canvas.colour_map
        print(f"  ✓ colour_map has {len(colour_map)} rows")
        print(f"    - First row first cell: {colour_map[0][0]}")
        print("")
        
        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("")
        print("Summary:")
        print("  ✓ win32console compatibility layer is working")
        print("  ✓ screen.py can be imported without DLL errors")
        print("  ✓ TemporaryCanvas works correctly")
        print("  ✓ Drawing to canvas works")
        print("")
        print("The web editor should now work on Windows without")
        print("win32console DLL issues.")
        print("")
        print("Note: pyfiglet is still required for FigletText renderer.")
        print("Install it with: pip install pyfiglet")
        print("")
        
    except Exception as e:
        print(f"  ✗ FAILED to create TemporaryCanvas: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"  ✗ FAILED to import screen.py: {e}")
    print("")
    if "win32console" in str(e) or "pywintypes" in str(e) or "DLL" in str(e):
        print("ERROR: win32console compatibility layer did not work.")
        print("This indicates a problem with the dummy module approach.")
    else:
        print(f"This seems to be a different error (not win32console DLL related).")
    
    import traceback
    traceback.print_exc()

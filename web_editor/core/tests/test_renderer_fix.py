"""
测试渲染器修复验证脚本
验证各种渲染器和效果在不同配置下都能正常工作
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
web_editor_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, web_editor_root)

from web_editor.core.compat import ensure_compatibility
ensure_compatibility()

from web_editor.core.renderer import (
    AnimationRenderer,
    RenderConfig,
    EffectConfig,
    SafeStaticRenderer,
    filter_kwargs_for_class,
    get_class_init_params,
    EffectRegistry,
)
from asciimatics.renderers import (
    FigletText,
    Fire,
    Plasma,
    Box,
    SpeechBubble,
    Scale,
    VScale,
    Rainbow,
    Kaleidoscope,
    Typewriter,
    RotatedDuplicate,
    BarChart,
    VBarChart,
)
from asciimatics.effects import (
    Stars,
    Print,
    Cycle,
    BannerText,
    Mirage,
    Matrix,
    Wipe,
    Snow,
    Clock,
    Cog,
    RandomNoise,
    Julia,
    Background,
    Scroll,
)


def test_filter_kwargs():
    """测试参数过滤功能"""
    print("=" * 50)
    print("测试 1: 参数过滤功能")
    print("=" * 50)
    
    params = get_class_init_params(FigletText)
    print(f"FigletText 参数: {list(params.keys())}")
    
    config_with_extra = {
        "text": "Hello",
        "font": "slant",
        "width": 80,
        "extra_param_1": "should be ignored",
        "extra_param_2": 123,
    }
    
    filtered = filter_kwargs_for_class(FigletText, config_with_extra)
    print(f"过滤前的参数: {list(config_with_extra.keys())}")
    print(f"过滤后的参数: {list(filtered.keys())}")
    print(f"过滤掉的参数: {set(config_with_extra.keys()) - set(filtered.keys())}")
    
    assert "extra_param_1" not in filtered, "应该过滤掉不接受的参数"
    assert "extra_param_2" not in filtered, "应该过滤掉不接受的参数"
    assert "text" in filtered, "应该保留接受的参数"
    assert "font" in filtered, "应该保留接受的参数"
    
    print("✓ 参数过滤测试通过\n")


def test_renderer_with_wrong_params():
    """测试渲染器在传入错误参数时的行为（之前会崩溃，现在应该正常工作）"""
    print("=" * 50)
    print("测试 2: 渲染器错误参数容错")
    print("=" * 50)
    
    config = RenderConfig(width=80, height=24, colours=256, fps=20, duration=100)
    renderer = AnimationRenderer(config)
    
    test_cases = [
        {
            "name": "Fire 渲染器传入 text 参数（之前会报错）",
            "effect_type": "Print",
            "renderer_type": "Fire",
            "renderer_config": {
                "text": "Hello",
                "height": 10,
                "width": 40,
                "emitter": "***",
                "intensity": 0.8,
                "spot": 40,
                "colours": 256,
            },
            "effect_config": {"y": 5},
        },
        {
            "name": "Plasma 渲染器传入 text 参数",
            "effect_type": "Print",
            "renderer_type": "Plasma",
            "renderer_config": {
                "text": "Hello",
                "height": 10,
                "width": 40,
                "colours": 256,
            },
            "effect_config": {"y": 5},
        },
        {
            "name": "Box 渲染器传入 text 参数",
            "effect_type": "Print",
            "renderer_type": "Box",
            "renderer_config": {
                "text": "Hello",
                "width": 40,
                "height": 10,
            },
            "effect_config": {"y": 5},
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        try:
            effect_config = EffectConfig(
                effect_type=test_case["effect_type"],
                renderer_type=test_case["renderer_type"],
                renderer_config=test_case["renderer_config"],
                effect_config=test_case["effect_config"],
            )
            
            renderer.add_effect(effect_config)
            frame = renderer.render_single_frame(0)
            renderer.clear_effects()
            
            print(f"  ✓ 成功渲染，帧大小: {len(frame.plain_image)} 行")
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✓ 所有渲染器容错测试通过\n")
    else:
        print("\n✗ 部分测试失败\n")


def test_all_effect_types():
    """测试所有Effect类型是否能正常创建"""
    print("=" * 50)
    print("测试 3: 所有 Effect 类型创建测试")
    print("=" * 50)
    
    config = RenderConfig(width=80, height=24, colours=256, fps=20, duration=10)
    
    effect_test_cases = [
        {"type": "Cycle", "needs_renderer": True, "extra_config": {"y": 5}},
        {"type": "Stars", "needs_renderer": False, "extra_config": {"count": 20}},
        {"type": "Print", "needs_renderer": True, "extra_config": {"y": 5}},
        {"type": "BannerText", "needs_renderer": True, "extra_config": {"y": 5, "colour": 7}},
        {"type": "Mirage", "needs_renderer": True, "extra_config": {"y": 5, "colour": 7}},
        {"type": "Scroll", "needs_renderer": False, "extra_config": {"rate": 5}},
        {"type": "Matrix", "needs_renderer": False, "extra_config": {}},
        {"type": "Wipe", "needs_renderer": False, "extra_config": {"bg": 0}},
        {"type": "Snow", "needs_renderer": False, "extra_config": {}},
        {"type": "Clock", "needs_renderer": False, "extra_config": {"x": 40, "y": 12, "r": 8}},
        {"type": "Cog", "needs_renderer": False, "extra_config": {"x": 40, "y": 12, "radius": 8}},
        {"type": "RandomNoise", "needs_renderer": False, "extra_config": {}},
        {"type": "Julia", "needs_renderer": False, "extra_config": {}},
        {"type": "Background", "needs_renderer": False, "extra_config": {"bg": 0}},
    ]
    
    all_passed = True
    for test_case in effect_test_cases:
        effect_type = test_case["type"]
        print(f"\n测试 Effect: {effect_type}")
        
        try:
            renderer = AnimationRenderer(config)
            
            effect_config = EffectConfig(
                effect_type=effect_type,
                renderer_type="FigletText" if test_case["needs_renderer"] else None,
                renderer_config={"text": "Test"} if test_case["needs_renderer"] else {},
                effect_config=test_case["extra_config"],
            )
            
            renderer.add_effect(effect_config)
            frame = renderer.render_single_frame(0)
            
            print(f"  ✓ 成功创建并渲染")
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    if all_passed:
        print("\n✓ 所有 Effect 类型测试通过\n")
    else:
        print("\n✗ 部分 Effect 测试失败\n")


def test_all_renderer_types():
    """测试所有Renderer类型是否能正常创建"""
    print("=" * 50)
    print("测试 4: 所有 Renderer 类型创建测试")
    print("=" * 50)
    
    config = RenderConfig(width=80, height=24, colours=256, fps=20, duration=10)
    
    renderer_test_cases = [
        {"type": "FigletText", "config": {"text": "Hello", "font": "slant", "width": 80}},
        {"type": "Fire", "config": {"height": 10, "width": 40, "emitter": "***", "intensity": 0.8, "spot": 40, "colours": 256}},
        {"type": "Plasma", "config": {"height": 10, "width": 40, "colours": 256}},
        {"type": "Box", "config": {"width": 40, "height": 10}},
        {"type": "SpeechBubble", "config": {"text": "Hello!", "tail": "L"}},
        {"type": "Scale", "config": {"width": 80}},
        {"type": "VScale", "config": {"height": 20}},
        {"type": "BarChart", "config": {"height": 10, "width": 40, "functions": [lambda: 0.5, lambda: 0.3]}},
        {"type": "VBarChart", "config": {"height": 10, "width": 40, "functions": [lambda: 0.5, lambda: 0.3]}},
    ]
    
    all_passed = True
    for test_case in renderer_test_cases:
        renderer_type = test_case["type"]
        print(f"\n测试 Renderer: {renderer_type}")
        
        try:
            renderer = AnimationRenderer(config)
            
            effect_config = EffectConfig(
                effect_type="Print",
                renderer_type=renderer_type,
                renderer_config=test_case["config"],
                effect_config={"y": 5},
            )
            
            renderer.add_effect(effect_config)
            frame = renderer.render_single_frame(0)
            
            print(f"  ✓ 成功创建并渲染")
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    special_renderers = ["Rainbow", "Kaleidoscope", "Typewriter", "RotatedDuplicate"]
    print(f"\n注意: {special_renderers} 是链式渲染器，需要嵌套的 Renderer 实例，已在代码中特殊处理")
    
    if all_passed:
        print("\n✓ 所有 Renderer 类型测试通过\n")
    else:
        print("\n✗ 部分 Renderer 测试失败\n")


def test_safe_fallback():
    """测试安全回退机制"""
    print("=" * 50)
    print("测试 5: 安全回退机制")
    print("=" * 50)
    
    config = RenderConfig(width=80, height=24, colours=256, fps=20, duration=10)
    
    test_cases = [
        {
            "name": "不存在的 Renderer 类型",
            "effect_type": "Print",
            "renderer_type": "NonExistentRenderer",
            "renderer_config": {},
            "effect_config": {"y": 5},
        },
        {
            "name": "不存在的 Effect 类型",
            "effect_type": "NonExistentEffect",
            "renderer_type": "FigletText",
            "renderer_config": {"text": "Test"},
            "effect_config": {},
        },
        {
            "name": "参数完全错误的配置",
            "effect_type": "Print",
            "renderer_type": "Fire",
            "renderer_config": {"completely_wrong_param": "value"},
            "effect_config": {"also_wrong": "value"},
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        try:
            renderer = AnimationRenderer(config)
            
            effect_config = EffectConfig(
                effect_type=test_case["effect_type"],
                renderer_type=test_case["renderer_type"],
                renderer_config=test_case["renderer_config"],
                effect_config=test_case["effect_config"],
            )
            
            renderer.add_effect(effect_config)
            frame = renderer.render_single_frame(0)
            
            print(f"  ✓ 使用回退机制成功渲染")
            print(f"    第一行内容: {frame.plain_image[0] if frame.plain_image else '(empty)'}")
        except Exception as e:
            print(f"  ✗ 失败（即使回退机制也失败了）: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    if all_passed:
        print("\n✓ 所有安全回退测试通过\n")
    else:
        print("\n✗ 部分安全回退测试失败\n")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("  Asciimatics Web Editor 渲染器修复验证测试")
    print("=" * 60)
    print()
    
    test_filter_kwargs()
    test_renderer_with_wrong_params()
    test_all_effect_types()
    test_all_renderer_types()
    test_safe_fallback()
    
    print("=" * 60)
    print("  所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

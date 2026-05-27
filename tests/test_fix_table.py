"""测试表格修复功能."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.renderer import CardRenderer


def main():
    """测试修复表格 Markdown."""
    renderer = CardRenderer()

    # 测试 1: 不规范的表格（没有空行）
    md1 = """扩展元数据：
| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |"""

    print("=" * 60)
    print("测试 1: 不规范的表格")
    print("=" * 60)
    print("原始:")
    print(repr(md1))
    print("\n修复后:")
    fixed1 = renderer._fix_table_markdown(md1)
    print(repr(fixed1))
    print("\n渲染结果:")
    result1 = renderer._markdown_filter(md1)
    print(result1[:500])
    print(f"\n包含 <table>: {'<table>' in result1}")

    # 测试 2: 正确的表格（有空行）
    md2 = """扩展元数据：

| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |"""

    print("\n" + "=" * 60)
    print("测试 2: 正确的表格（有空行）")
    print("=" * 60)
    print("原始:")
    print(repr(md2))
    print("\n渲染结果:")
    result2 = renderer._markdown_filter(md2)
    print(result2[:500])
    print(f"\n包含 <table>: {'<table>' in result2}")


if __name__ == "__main__":
    main()

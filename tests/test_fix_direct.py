"""直接测试 _fix_table_markdown 方法."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.renderer import CardRenderer


def main():
    """测试修复方法."""
    renderer = CardRenderer()

    # PR #9507 的实际内容（表格部分）
    pr_body = """### 备注

扩展元数据：
| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |
| **作词** | `尹纯青Eyn` |"""

    print("=" * 60)
    print("原始内容 (repr):")
    print("=" * 60)
    print(repr(pr_body))

    print("\n" + "=" * 60)
    print("修复后的内容:")
    print("=" * 60)
    fixed = renderer._fix_table_markdown(pr_body)
    print(repr(fixed))

    print("\n" + "=" * 60)
    print("渲染结果:")
    print("=" * 60)
    result = renderer._markdown_filter(pr_body)
    print(result[:1000])
    print(f"\n包含 <table>: {'<table>' in result}")


if __name__ == "__main__":
    main()

"""测试 markdown_to_text 函数处理 PR #9507 的描述."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils import markdown_to_text

# PR #9507 的原始描述（部分）
pr_body = """### 歌词议题
#9506

### 歌词作者
@ranhengzhang

### 音乐名称

- `Befall`
- `崩坏3《女王降临》动画短片印象曲`

### 扩展元数据

| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |
| **作词** | `尹纯青Eyn` |
| **出品** | `HOYO-MiX` |
| **制作人** | `蔡近翰Zoe` |
| **演唱** | `尚雯婕` |

### 歌词内容

```
[00:00.00] 测试歌词
[00:05.00] 第二行歌词
```

其他说明文字。
"""

print("=" * 60)
print("原始内容:")
print("=" * 60)
print(pr_body)
print("\n" + "=" * 60)
print("转换后的内容:")
print("=" * 60)
result = markdown_to_text(pr_body)
print(result)
print("\n" + "=" * 60)
print(f"原始长度: {len(pr_body)} 字符")
print(f"转换后长度: {len(result)} 字符")

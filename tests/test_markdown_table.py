"""测试 Markdown 表格解析."""

import markdown

# 测试 1: 表格前面有文本但没有空行（当前情况）
md1 = """扩展元数据：
| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |"""

# 测试 2: 表格前面有文本和空行
md2 = """扩展元数据：

| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |"""

# 测试 3: 只有表格
md3 = """| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |"""

print("=" * 60)
print("测试 1: 表格前面有文本但没有空行")
print("=" * 60)
result1 = markdown.markdown(md1, extensions=["tables"])
print(result1)
print(f"包含 <table>: {'<table>' in result1}")

print("\n" + "=" * 60)
print("测试 2: 表格前面有文本和空行")
print("=" * 60)
result2 = markdown.markdown(md2, extensions=["tables"])
print(result2)
print(f"包含 <table>: {'<table>' in result2}")

print("\n" + "=" * 60)
print("测试 3: 只有表格")
print("=" * 60)
result3 = markdown.markdown(md3, extensions=["tables"])
print(result3)
print(f"包含 <table>: {'<table>' in result3}")

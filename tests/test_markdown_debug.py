"""调试 Markdown 表格解析."""

import markdown

# 打印版本
print(f"Markdown 库版本: {markdown.__version__}")

# 测试标准表格格式
md = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""

print("\n标准表格格式:")
print(repr(md))
print("\n渲染结果:")
result = markdown.markdown(md, extensions=["tables"])
print(result)
print(f"包含 <table>: {'<table>' in result}")

# 测试带空行的表格
md2 = """Some text

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""

print("\n" + "=" * 60)
print("带空行的表格:")
print(repr(md2))
print("\n渲染结果:")
result2 = markdown.markdown(md2, extensions=["tables"])
print(result2)
print(f"包含 <table>: {'<table>' in result2}")

# 测试带对齐的表格
md3 = """| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |"""

print("\n" + "=" * 60)
print("带对齐的表格:")
print(repr(md3))
print("\n渲染结果:")
result3 = markdown.markdown(md3, extensions=["tables"])
print(result3)
print(f"包含 <table>: {'<table>' in result3}")

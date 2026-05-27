"""测试 nl2br 扩展对表格的影响."""

import markdown

md = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""

print("=" * 60)
print("不使用 nl2br:")
print("=" * 60)
result1 = markdown.markdown(md, extensions=["tables"])
print(result1)
print(f"包含 <table>: {'<table>' in result1}")

print("\n" + "=" * 60)
print("使用 nl2br:")
print("=" * 60)
result2 = markdown.markdown(md, extensions=["nl2br", "tables"])
print(result2)
print(f"包含 <table>: {'<table>' in result2}")

print("\n" + "=" * 60)
print("扩展顺序: tables 在前:")
print("=" * 60)
result3 = markdown.markdown(md, extensions=["tables", "nl2br"])
print(result3)
print(f"包含 <table>: {'<table>' in result3}")

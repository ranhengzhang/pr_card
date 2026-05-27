"""测试 PR #9507 实际内容的渲染."""

import markdown

# PR #9507 的实际内容（表格部分）
pr_body = """### 备注

扩展元数据：
| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |
| **作词** | `尹纯青Eyn` |"""

print("=" * 60)
print("PR #9507 实际内容")
print("=" * 60)
print("原始内容 (repr):")
print(repr(pr_body))

print("\n" + "=" * 60)
print("渲染结果 (只使用 tables 扩展):")
print("=" * 60)
result1 = markdown.markdown(pr_body, extensions=["tables"])
print(result1)
print(f"\n包含 <table>: {'<table>' in result1}")

print("\n" + "=" * 60)
print("渲染结果 (使用 nl2br + tables):")
print("=" * 60)
result2 = markdown.markdown(pr_body, extensions=["nl2br", "tables"])
print(result2)
print(f"\n包含 <table>: {'<table>' in result2}")

# 测试修复后的内容
print("\n" + "=" * 60)
print("修复后的内容 (表格前添加空行):")
print("=" * 60)
fixed_body = """### 备注

扩展元数据：

| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |
| **作词** | `尹纯青Eyn` |"""

print("原始内容 (repr):")
print(repr(fixed_body))

print("\n渲染结果:")
result3 = markdown.markdown(fixed_body, extensions=["nl2br", "tables"])
print(result3)
print(f"\n包含 <table>: {'<table>' in result3}")

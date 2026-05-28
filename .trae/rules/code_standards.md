---
alwaysApply: true
---
# PR Card 项目代码规范

本规范基于项目现有代码风格提炼，所有新增和修改代码必须遵循。

---

## 1. 项目结构

```
pr_card/
├── main.py                  # CLI 入口
├── src/
│   ├── __init__.py
│   ├── config.py            # 配置管理 (Pydantic Settings)
│   ├── fetcher.py           # GitHub API 数据获取
│   ├── renderer.py          # HTML 卡片渲染 (Jinja2 + Vue 模板)
│   ├── screenshot.py        # Playwright 截图
│   ├── markdown_utils.py    # Markdown 文本处理
│   ├── format_utils.py      # 数字/文本/文件名格式化
│   ├── logger.py            # 日志 (loguru)
│   └── utils.py             # 仓库解析、URL 验证等通用工具
├── templates/
│   ├── pr_card_vue.html     # Vue 模板
│   └── style.css            # 样式
├── tests/
│   ├── common.py            # 测试基类和 mock 工厂
│   ├── test_config.py
│   ├── test_fetcher.py
│   ├── test_renderer.py
│   ├── test_screenshot.py
│   ├── test_markdown.py
│   ├── test_format_utils.py
│   └── test_utils.py
└── pyproject.toml
```

### 模块职责原则

- **单一职责**：每个模块只做一件事。`utils.py` 仅放无法归入其他模块的通用函数
- **禁止上帝模块**：当 `utils.py` 超过 5 个不相关函数时，必须拆分出新模块
- **禁止根目录调试文件**：调试脚本和临时输出文件不应出现在项目根目录

---

## 2. 导入规范

### 2.1 导入顺序

```python
from __future__ import annotations

# 标准库
import re
from pathlib import Path
from typing import Optional, Dict, Any

# 第三方库
from github import Github
from loguru import logger
from pydantic import Field

# 本地模块
from src.config import get_config
from src.fetcher import PRData
```

三组之间各空一行。`from __future__ import annotations` 始终在第一行。

### 2.2 禁止内联导入

- 所有 import 必须在文件顶部，禁止在函数/方法体内 `import`
- 唯一例外：避免循环依赖时，可在函数内延迟导入，但必须加注释说明原因

### 2.3 禁止未使用的导入

- 每次修改后确认无未使用的 import

---

## 3. 命名规范

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块 | `snake_case` | `markdown_utils.py` |
| 类 | `PascalCase` | `CardRenderer`, `PRData` |
| 函数/方法 | `snake_case` | `fetch_pr_data` |
| 私有方法 | `_leading_underscore` | `_extract_pr_data` |
| 常量 | `UPPER_SNAKE_CASE` | `DEFAULT_STYLE` |
| 变量 | `snake_case` | `pr_number`, `output_path` |

### 禁止项

- 禁止单字母变量名（循环变量 `i` 除外）
- 禁止与内置函数同名的变量（如 `id`, `list`, `dict`, `input`）
- 缩写保持一致：`PR` (非 `Pr`/`pr`), `URL` (非 `Url`), `HTML` (非 `Html`)

---

## 4. 类型注解

### 4.1 强制类型注解

所有公开函数必须有完整的参数和返回值类型注解：

```python
def fetch_pr_data(self, owner: str, repo_name: str, pr_number: int) -> PRData:
    ...
```

### 4.2 Optional 用法

可能为 `None` 的参数/返回值必须标注 `Optional`：

```python
def render(self, pr_data: PRData, style: Optional[str] = None) -> str:
    ...
```

### 4.3 容器类型必须标注元素类型

```python
labels: List[Dict[str, str]]
comments: List[Dict[str, Any]]
```

### 4.4 使用 `from __future__ import annotations`

所有 `.py` 文件第一行必须包含，以支持前向引用和更简洁的类型写法。

---

## 5. Docstring 规范

### 5.1 风格：Google Style

所有模块、类、公开函数必须使用 Google 风格 docstring。

### 5.2 模块级 Docstring

```python
"""模块简述.

详细描述模块的职责和功能.
"""
```

### 5.3 类级 Docstring

```python
class CardRenderer:
    """卡片渲染器.

    负责将 PR 数据渲染为 HTML 卡片.

    Attributes:
        _env: Jinja2 模板环境.
        _config: 配置管理器.
    """
```

### 5.4 函数级 Docstring

```python
def fetch_pr_data(self, owner: str, repo_name: str, pr_number: int) -> PRData:
    """获取 PR 数据.

    Args:
        owner: 仓库所有者.
        repo_name: 仓库名称.
        pr_number: PR 编号.

    Returns:
        PRData 对象.

    Raises:
        ValueError: 当仓库或 PR 不存在时.
    """
```

### 5.5 Docstring 质量要求

- 描述"做了什么"和"为什么"，而非简单重复函数名
- 私有方法（`_` 前缀）也应有 docstring，但可以简短
- `Raises` 段仅在函数确实抛出异常时才写

---

## 6. 注释规范

### 6.1 行注释

行注释以 `# ` 开头，位于代码右侧或单独一行。

**仅用于解释"为什么"**，代码本身已清晰时禁止添加：

```python
# ❌ 禁止：重复代码意图
events.sort(key=lambda x: x["date"])  # 按时间排序

# ✅ 允许：解释"为什么"
text = self._fix_table_markdown(text)  # Markdown 规范要求表格前必须有空行
```

**禁止调试性行注释**：

```python
# ❌ 禁止
# TODO: 临时修复，后续优化
# HACK: 绕过某个 bug
# DEBUG: 打印调试信息
```

**禁止注释掉的代码**：被注释掉的代码直接删除，需要时从 git 历史恢复.

### 6.2 块注释

块注释由多行连续的 `# ` 组成，用于说明大段代码的逻辑.

**格式规则**：
- 每行以 `# ` 开头（井号加空格）
- 与上方代码之间留一个空行，与下方代码之间不留空行
- 句末使用句号 `.` 结尾

```python
# 处理数据：先过滤无效项，再按时间排序，最后去除重复记录.
# 过滤条件为 status != 'deleted' 且 timestamp 在有效范围内.
result = process_data(data)
```

**步骤标注**：时间线等逻辑中的步骤标注允许保留，但应简洁：

```python
# 1. PR 创建事件
# 2. 提交记录
# 3. 标签事件
```

**禁止用行尾注释代替块注释**：大段逻辑说明不应塞进行尾注释：

```python
# ❌ 禁止：行尾注释无法充分说明大段逻辑
result = process_data(data)  # 处理数据，先过滤再排序，最后去重

# ✅ 正确：使用块注释
# 处理数据：先过滤无效项，再按时间排序，最后去除重复记录.
# 过滤条件为 status != 'deleted' 且 timestamp 在有效范围内.
result = process_data(data)
```

### 6.3 字符串注释

**禁止用多行字符串当注释**：Python 中的 `"""..."""` 是 docstring 而非注释，不得用于代码逻辑说明：

```python
# ❌ 禁止：用多行字符串当注释
"""
这段代码负责处理数据：
1. 过滤无效项
2. 按时间排序
3. 去除重复记录
"""
result = process_data(data)

# ✅ 正确：使用块注释
# 处理数据：先过滤无效项，再按时间排序，最后去除重复记录.
# 过滤条件为 status != 'deleted' 且 timestamp 在有效范围内.
result = process_data(data)
```

**docstring 与注释的边界**：`"""..."""` 仅用于模块、类、函数的 docstring（见第 5 节），不得用于代码段说明.

---

## 7. 代码重复防范

### 7.1 DRY 原则

同一段逻辑出现两次及以上时，必须提取为函数或方法。

### 7.2 常见重复模式检查清单

| 重复模式 | 正确做法 |
|----------|---------|
| 数据转字典 | 复用 `PRData.to_dict()`，不要手动构建 |
| 数字格式化 | 统一使用 `format_utils.format_number()` |
| URL 解析 | 统一使用 `fetcher._parse_pr_url()` 或提取为公开函数 |
| 代理配置 | 统一使用 `config.get_proxy_for_*` 方法 |
| 输出路径生成 | 统一使用 `format_utils.generate_output_filename()` |
| Markdown 转文本 | 统一使用 `markdown_utils.markdown_to_text()` |

### 7.3 Jinja2 过滤器与工具函数

renderer 中的过滤器方法（如 `_format_number_filter`）必须委托给对应的工具函数，不要重新实现：

```python
def _format_number_filter(self, num: int) -> str:
    return format_number(num)
```

---

## 8. 数据模型规范

### 8.1 dataclass 字段

- 使用 `dataclass` 定义数据结构
- 所有字段必须有类型注解
- 可选字段使用 `Optional` 和默认值 `None`

### 8.2 `to_dict()` 方法

- dataclass 如需序列化，提供 `to_dict()` 方法
- 确保每个键只出现一次（禁止重复键）
- `datetime` 字段统一使用 `.isoformat()` 转换

### 8.3 字典键名一致性

API 返回的字典结构与 `to_dict()` 输出保持键名一致。

---

## 9. 测试规范

### 9.1 测试文件组织

- 测试文件与 `src/` 模块一一对应：`test_<module>.py`
- 禁止创建针对特定 bug 编号的临时测试文件（如 `test_pr_9507.py`）
- 集成测试（依赖真实 API）放在 `tests/integration/` 目录

### 9.2 测试基类

- 使用 `tests/common.py` 中的 `AsyncTestCase` 作为异步测试基类
- 使用 `create_mock_pr_data()` 创建 mock 数据，不要在每个测试中手动构建

### 9.3 Mock 数据类型正确性

- `PRData.labels` 类型为 `List[Dict[str, str]]`，mock 数据必须匹配：
  ```python
  # ❌ 错误
  labels=["bug", "enhancement"]
  # ✅ 正确
  labels=[{"name": "bug", "color": "d73a4a"}, {"name": "enhancement", "color": "a2eeef"}]
  ```

### 9.4 测试覆盖要求

- 每个公开函数至少有一个正向测试
- 关键路径（渲染、数据获取、截图）需要边界条件测试
- 禁止仅用于手动调试的测试

---

## 10. 异步代码规范

### 10.1 上下文管理器

使用 Playwright 等异步资源时，必须使用 `async with` 上下文管理器：

```python
async with ScreenshotTaker() as taker:
    result = await taker.take_screenshot(html_content, output_path)
```

### 10.2 异步函数命名

异步函数不加 `async_` 前缀，通过 `async def` 关键字即可区分。

### 10.3 同步包装函数

提供同步包装时，使用 `asyncio.run()` 并在 docstring 中标注：

```python
def capture_html_sync(html_content: str, output_path: Optional[Path] = None) -> Path:
    """同步便捷函数: 捕获 HTML 为图片."""
    return asyncio.run(capture_html(html_content, output_path))
```

---

## 11. 配置规范

### 11.1 配置优先级

命令行参数 > 环境变量 > `.env` 文件 > 代码默认值

### 11.2 新增配置项

- 在 `Settings` 类中添加字段，使用 `Field(default=..., description="...")`
- 需要 `.env` 映射时使用 `alias="ENV_VAR_NAME"`
- 需要 CLI 覆盖时在 `main.py` 的 `setup_config` 中添加映射

### 11.3 禁止硬编码

- 路径、URL、超时时间等不应硬编码在业务逻辑中
- 应提取为 `Settings` 字段或函数参数

---

## 12. 错误处理规范

### 12.1 自定义异常

- 使用 `ValueError` 表示调用方错误
- 使用 `RuntimeError` 表示运行时状态错误
- 不使用裸 `Exception`

### 12.2 异常链

包装底层异常时使用 `from` 保留原始堆栈：

```python
raise ValueError(f"仓库 '{owner}/{name}' 不存在") from e
```

### 12.3 错误信息

- 错误信息必须包含足够的上下文（如具体的仓库名、PR 编号）
- 使用中文错误信息，与项目现有风格一致

---

## 13. 安全规范

### 13.1 Token 处理

- GitHub Token 不得出现在日志、错误信息或输出文件中
- 禁止将 Token 写入代码或提交到版本控制

### 13.2 用户输入

- 所有外部输入（URL、仓库名等）必须验证后再使用
- 文件名必须经过 `sanitize_filename()` 清理

---

## 14. 变更前检查清单

每次修改代码前，必须确认：

- [ ] 修改的函数/类是否被其他模块依赖？运行影响分析
- [ ] 是否引入了重复逻辑？检查 7.2 中的检查清单
- [ ] 新增函数是否有完整的类型注解和 docstring？
- [ ] 新增配置项是否在 `Settings` 中注册？
- [ ] 测试是否覆盖了修改的逻辑？
- [ ] 是否有未使用的 import 或变量？
- [ ] 是否有调试代码或注释掉的代码残留？

每次修改代码后，必须确认：

- [ ] `pytest tests/` 全部通过
- [ ] `ruff check src/ tests/` 无错误
- [ ] 变更影响范围与预期一致（运行变更检测）

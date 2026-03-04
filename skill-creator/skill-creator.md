---
name: skill-creator
version: 1.0.0
description: >
  Meta-skill for creating production-quality skill files. Use this when the user
  wants to create a new skill, improve an existing skill, or understand skill
  authoring best practices. Guides through requirements gathering, architecture
  selection, skill file generation, script creation, and validation.
  Supports script-based, MCP-based, and prompt-based skill types.
  Output is ready-to-deploy skill files for Trae AI, Cursor, or other AI IDE.
triggers:
  keywords: ["创建skill", "写skill", "新建技能", "skill模板", "create skill",
             "new skill", "skill template", "编写skill", "生成skill",
             "改进skill", "优化skill", "skill最佳实践"]
platform: [windows, macos, linux]
---

# Skill Creator — 生产级 Skill 生成器

## Overview

This meta-skill guides you through creating complete, production-quality skill
files. It encodes best practices learned from real-world skill deployment in
Windows IDE environments (Trae AI, Cursor, etc.).

A well-crafted skill is NOT just documentation — it is a **Standard Operating
Procedure (SOP)** for AI agents, including:
- When and why to activate (trigger conditions)
- What tools/scripts to use and how (interface spec)
- How to make decisions under ambiguity (decision logic)
- What can go wrong and how to recover (error handling)
- How to adapt to different environments (platform compatibility)

## Phase 1: Requirements Discovery

> [!CRITICAL]
> Do NOT start writing skill files immediately. Always complete the discovery
> phase first. A skill built on wrong assumptions will fail in production.

### 1.1 Core Questions to Ask the User

Ask these questions (adapt language to user's preference). You don't need to
ask all at once — interleave with clarifying follow-ups:

**Functional Scope:**
```
1. 这个 skill 要解决什么问题？（用一句话描述）
2. 用户会怎么触发它？（上传文件？说某个关键词？还是特定场景？）
3. 期望的输出是什么？（文件？对话内容？代码？可视化？）
4. 有没有现有的工具/脚本/API 可以复用？
5. 需要处理的数据量大概多大？（几行 vs 几万行 vs 几百万行）
```

**Environment:**
```
6. 主要在什么 IDE 中使用？（Trae AI / Cursor / Windsurf / 其他）
7. 操作系统？（Windows / macOS / Linux / 都需要支持）
8. 需要联网吗？还是必须纯离线？
9. 是否已有 MCP server 可用？还是需要纯本地方案？
10. 目标用户的技术水平？（开发者 / 数据分析师 / 非技术人员）
```

**Constraints:**
```
11. 有没有安全/隐私约束？（数据不能上传到云端？）
12. 有没有性能要求？（必须秒级响应？还是可以等几分钟？）
13. 需要支持中文场景吗？（中文文件名/列名/内容）
14. 需要与其他 skill 联动吗？
```

### 1.2 Architecture Decision

Based on answers, determine the skill type:

```
                    需要调用外部工具/服务吗？
                    ┌────────┴────────┐
                   YES                NO
                    │                  │
              工具在哪里？         纯提示词型 (Type C)
           ┌────┴────┐            输出：仅 .md 文件
          本地       云端               │
           │          │           例：代码审查、文案风格
      脚本驱动型    通过什么协议？
      (Type A)    ┌───┴───┐
       │        MCP     HTTP API
       │       (Type B)  (Type B 变体)
       │         │         │
  需要写脚本   需要配置    需要处理
  管理依赖    MCP连接     认证/限流
  处理路径    处理认证
  适配平台    处理降级
```

**Decision Matrix:**

| 条件 | 推荐类型 | 理由 |
|------|---------|------|
| 需要处理本地文件 + 离线可用 | Type A (脚本) | 本地脚本无网络依赖 |
| 需要调用云端 SaaS（Google/Notion/Slack 等） | Type B (MCP) | MCP 是标准化的工具协议 |
| 无外部工具，纯靠 AI 推理能力 | Type C (提示词) | 无需脚本或 API |
| 需要本地处理 + 云端联动 | Type A+B 混合 | 本地分析 + 云端同步 |
| 已有 REST API 但无 MCP server | Type A (脚本封装 API 调用) | 用脚本封装 HTTP 请求 |

### 1.3 Confirm Understanding

Before proceeding, summarize back to the user:

```
📋 Skill 需求确认：
- 名称：{name}
- 功能：{one-sentence description}
- 类型：{Type A/B/C}
- 触发条件：{triggers}
- 输入：{what user provides}
- 输出：{what skill produces}
- 平台：{OS + IDE}
- 特殊要求：{constraints}

请确认是否正确，或补充修改。
```

## Phase 2: Skill File Structure Design

### 2.1 File Structure by Type

**Type A — 脚本驱动型：**
```
{skill-name}/
├── {skill-name}.md           # Skill 定义文件
└── scripts/
    ├── {main-script}.py      # 主执行脚本
    ├── setup_env.py          # 环境配置助手（推荐）
    └── requirements.txt      # Python 依赖
```

**Type B — MCP 工具型：**
```
{skill-name}/
└── {skill-name}.md           # Skill 定义文件（通常只需要这一个）
```

**Type C — 纯提示词型：**
```
{skill-name}/
└── {skill-name}.md           # Skill 定义文件
```

**Type A+B 混合型：**
```
{skill-name}/
├── {skill-name}.md           # Skill 定义文件
└── scripts/
    ├── {local-script}.py     # 本地处理脚本
    └── requirements.txt
```

### 2.2 Frontmatter Schema

Every skill MUST start with a YAML frontmatter block:

```yaml
---
# ── 必填字段 ──
name: {kebab-case-name}
description: >
  {完整描述，包含：
   1. 触发条件（什么时候用这个 skill）
   2. 核心能力（能做什么）
   3. 关键约束（不能做什么或边界条件）}

# ── 推荐字段 ──
version: {semver, e.g., 1.0.0}
triggers:
  file_extensions: [".xxx"]     # 文件类型触发（Type A 常用）
  keywords: ["关键词1", "keyword2"]  # 意图关键词触发
platform: [windows, macos, linux]   # 支持的平台

# ── 条件字段（按类型选用）──
requires:                        # Type B: MCP 依赖
  mcp: [server-name]
dependencies:                    # Type A: 运行时依赖
  runtime: "python>=3.9"
  packages: ["pkg1", "pkg2"]
---
```

**Frontmatter 编写要诀：**

```
description 字段是 skill 能否被正确匹配的关键。必须包含：

✅ 好的 description：
"Use this skill when the user uploads Excel or CSV files and wants to
 perform data analysis, generate statistics, create summaries, or
 execute SQL queries against structured data."
 → 包含了：触发条件(uploads files) + 文件类型(Excel/CSV) + 动作列表(analysis/statistics/summaries/SQL)

❌ 差的 description：
"Data analysis tool"
 → 太笼统，AI 无法判断何时触发

❌ 差的 description：
"Uses DuckDB to run SQL queries on local files via Python script"
 → 描述了实现方式而非用户意图，用户不会说"我想用 DuckDB"
```

## Phase 3: Skill Content Generation

### 3.1 Universal Skeleton（所有类型通用的骨架）

```markdown
# {Skill Name}

## Overview
{2-3 sentences: what it does, key design principles}

## Prerequisites / Setup
{环境要求、依赖安装、认证配置}
{首次使用的检查步骤}

## Decision Tree
{用户意图 → 执行路径的判断逻辑}

## Core Workflows
### Workflow 1: {name}
{步骤、命令/工具调用、参数说明}

### Workflow 2: {name}
...

## Parameter Reference
{所有参数的表格}

## Pattern Library / Templates
{常用操作模式的代码/SQL/配置模板}

## Error Handling
{错误 → 原因 → 恢复动作 的映射表}
{错误恢复工作流图}

## Complete Examples
{至少 2 个端到端示例，包括中文场景}

## Platform-Specific Notes
{Windows / macOS / Linux 差异}

## Known Pitfalls
{反直觉行为、常见陷阱}

## Notes
{补充说明、性能提示、限制}
```

### 3.2 Type A 专项规则（脚本驱动型）

#### 规则 A1：路径永远动态发现

```markdown
## 必须包含的内容：

### 脚本定位方法（写在 Setup 或 Step 0 中）

不要写：
  python /path/to/script/analyze.py

要写：
  Step 0: 用 find/Get-ChildItem 命令搜索 analyze.py
  找到后记住路径，在整个会话中复用

### 提供 locate action：
  python analyze.py --action locate
  → 脚本自报自己的绝对路径
```

#### 规则 A2：复杂参数走文件，不走命令行

```markdown
## 核心原则：

任何包含以下特征的参数，都不能通过 --arg "value" 传递：
- 中文字符
- 嵌套引号（SQL、JSON 等）
- 多行内容
- 特殊字符（& | < > ' " ` $ ! ; 等）

替代方案：
1. --sql-file query.sql      （SQL 查询）
2. --config-file config.json  （复杂配置）
3. --input-file data.txt      （输入数据）
4. 标准输入 (stdin)            （最后手段）

这是因为 trae-sandbox 和各种 shell 的参数解析行为不一致，
文件引用是唯一跨平台可靠的方式。
```

#### 规则 A3：脚本必须包含的功能

```python
## 每个主脚本必须支持的 action：

--action check-env    # 检查环境依赖，输出诊断报告
--action locate       # 输出脚本自身的绝对路径
--action {core-actions}  # 业务功能

## 每个主脚本必须遵循的约定：

1. 结果输出到 stdout，诊断信息输出到 stderr
2. 成功退出码 0，失败退出码非 0
3. 错误信息必须包含恢复建议（💡 Suggestion: ...）
4. 所有文件路径参数都接受正斜杠 /（跨平台）
5. 中文文件名/路径必须能正确处理
6. 异常情况给出 check-env 提示
```

#### 规则 A4：环境依赖管理

```markdown
## 必须提供：

1. requirements.txt — 列出所有 pip 依赖及版本
2. setup_env.py — 一键检查 + 安装
3. check-env action — 运行时环境诊断

## 在 Skill 文档中必须说明：

- Python 版本要求
- pip install 命令
- 虚拟环境建议（可选）
- 首次安装后的验证步骤
```

### 3.3 Type B 专项规则（MCP 工具型）

#### 规则 B1：认证配置必须详述

```markdown
## 必须包含的内容：

### MCP Server 配置方法
- 适配目标 IDE（Trae AI / Cursor / 其他）的配置方式
- 完整的配置文件示例（JSON）
- 需要的 OAuth scope 或 API key

### 连接验证方法
- 用最简单的工具调用测试连接
- 连接失败的排障步骤

### Fallback 方案
- MCP 不可用时的替代方案
- 是否可以降级到本地脚本
```

#### 规则 B2：工具选择决策逻辑

```markdown
## 当 skill 包含多个工具时，必须提供决策指导：

用户意图           → 应该用哪个工具
─────────────────────────────────────
"创建新表格"       → CREATE_SPREADSHEET
"写入数据"         → BATCH_UPDATE（全量）或 UPSERT_ROWS（增量）
"更新某些行"       → UPSERT_ROWS（有 key column）
"读取数据"         → BATCH_GET
"添加新 sheet"     → ADD_SHEET
...

## 必须标注工具间参数命名不一致之处
```

#### 规则 B3：幂等性和回滚

```markdown
## 必须说明每个写操作的幂等性：

| 工具 | 幂等？ | 重复调用的后果 |
|------|--------|---------------|
| CREATE_WORKBOOK | ❌ 非幂等 | 创建多个文件 |
| BATCH_UPDATE | ⚠️ 部分 | 覆盖已有数据 |
| UPSERT_ROWS | ✅ 幂等 | 更新为相同值 |

## 必须提供回滚/撤销指导（如果可能）
```

### 3.4 Type C 专项规则（纯提示词型）

#### 规则 C1：输出格式必须精确控制

```markdown
## 必须包含：

### 输出格式规范
- 明确的输出结构（Markdown 段落？JSON？表格？）
- 字段定义和必填/可选标记
- 长度约束（如果有）

### 示例输出
- 至少 2 个完整的输入→输出示例
- 覆盖正常 case 和边界 case
```

#### 规则 C2：领域知识的嵌入方式

```markdown
## 避免：在 skill 中堆砌大段知识文本（浪费 token）

## 推荐：
1. 提供决策框架（规则/公式），让 AI 用框架推理
2. 提供参考示例（few-shot），让 AI 学习模式
3. 提供检查清单（checklist），让 AI 自我验证
```

### 3.5 通用质量规则（所有类型）

#### 规则 U1：错误处理表必须包含

```markdown
## 每个 skill 必须有 Error Handling 章节，包含：

### 1. 错误映射表
| 错误现象 | 可能原因 | 恢复动作 |
|---------|---------|---------|
| {具体错误消息或模式} | {根因} | {用户/AI 应该做什么} |

### 2. 错误恢复工作流
命令失败
├─ 是哪类错误？
│  ├─ 环境/依赖错误 → ...
│  ├─ 文件/路径错误 → ...
│  ├─ 认证/权限错误 → ...
│  ├─ 输入/参数错误 → ...
│  └─ 未知错误 → ...
```

#### 规则 U2：负面指令（做什么 AND 不做什么）

```markdown
## 每个 skill 都应该包含明确的"不要做"指令：

> [!IMPORTANT]
> - Do NOT read or modify the script source code
> - Do NOT list directory contents unless explicitly asked
> - Do NOT install packages without user confirmation
> - Do NOT pass complex data through CLI arguments (use file instead)
> - Do NOT hardcode file paths
```

#### 规则 U3：中文场景覆盖

```markdown
## 如果 skill 可能被中文用户使用（Trae AI 场景），必须：

1. 提供中文示例（文件名、列名、数据内容）
2. 说明编码处理（GBK vs UTF-8）
3. SQL/代码示例中使用双引号包裹中文标识符
4. 说明 Windows 中文环境的特殊注意事项
```

#### 规则 U4：决策树/意图路由

```markdown
## 每个 skill 必须有决策树，至少覆盖：

1. 用户需求模糊时 → 怎么主动分析并建议
2. 用户需求明确时 → 直接执行哪个路径
3. 多种方案可选时 → 怎么选择最优方案
4. 前置条件未满足时 → 怎么引导用户完成
```

#### 规则 U5：示例必须端到端

```markdown
## 示例的黄金标准：

❌ 差的示例（只有片段）：
  "Use TOOL_X with parameter Y"

✅ 好的示例（端到端）：
  用户说："帮我分析销售数据"
  
  Step 1: [AI 先做什么]
  → 具体命令/工具调用
  → 预期输出
  
  Step 2: [基于 Step 1 结果做什么]
  → 具体命令
  → 预期输出
  
  Step 3: [呈现结果]
  → 具体的回复模板
```

## Phase 4: Script Generation（Type A only）

### 4.1 Python 脚本模板

When generating scripts for Type A skills, use this template:

```python
#!/usr/bin/env python3
"""
{Script description}

Usage:
    python {script_name}.py --action check-env
    python {script_name}.py --action locate
    python {script_name}.py --action {main-action} [--params ...]
"""

import argparse
import sys
import traceback
from pathlib import Path

__version__ = "1.0.0"


# ── Error Classes ──

class SkillError(Exception):
    """Base error with recovery suggestion."""
    def __init__(self, message: str, suggestion: str = None):
        super().__init__(message)
        self.suggestion = suggestion
    def format(self) -> str:
        msg = f"❌ Error: {self}"
        if self.suggestion:
            msg += f"\n💡 Suggestion: {self.suggestion}"
        return msg


# ── Environment Check ──

def check_environment() -> dict:
    """Check runtime dependencies. Returns status dict."""
    result = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_path": sys.executable,
        "platform": sys.platform,
        "script_path": str(Path(__file__).resolve()),
        "packages": {},
        "all_ok": True,
        "errors": [],
    }
    # Check Python version
    if sys.version_info < (3, 9):
        result["errors"].append(f"Python 3.9+ required")
        result["all_ok"] = False
    # Check packages — customize per skill
    for pkg in ["REQUIRED_PACKAGES_HERE"]:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "?")
            result["packages"][pkg] = {"status": "ok", "version": str(ver)}
        except ImportError:
            result["packages"][pkg] = {"status": "missing"}
            result["errors"].append(f"Missing: {pkg}")
            result["all_ok"] = False
    return result


def print_env_report(info: dict):
    """Pretty-print environment check."""
    print("=" * 50)
    print("🔍 ENVIRONMENT CHECK")
    print("=" * 50)
    print(f"  Python  : {info['python_version']}")
    print(f"  Path    : {info['python_path']}")
    print(f"  Platform: {info['platform']}")
    print(f"  Script  : {info['script_path']}")
    for pkg, st in info["packages"].items():
        icon = "✅" if st["status"] == "ok" else "❌"
        ver = st.get("version", "MISSING")
        print(f"  {icon} {pkg}: {ver}")
    if info["all_ok"]:
        print("\n  ✅ All good!")
    else:
        for e in info["errors"]:
            print(f"  ❌ {e}")
    print("=" * 50)


# ── Core Logic ──

# {IMPLEMENT YOUR CORE FUNCTIONALITY HERE}


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description=f"{__doc__}")
    parser.add_argument("--action", required=True,
                        choices=["check-env", "locate", "YOUR_ACTIONS_HERE"])
    # Add your parameters here
    # For complex input, prefer --xxx-file over --xxx
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    if args.action == "locate":
        print(f"Script: {Path(__file__).resolve()}")
        print(f"Dir:    {Path(__file__).resolve().parent}")
        sys.exit(0)

    if args.action == "check-env":
        info = check_environment()
        print_env_report(info)
        sys.exit(0 if info["all_ok"] else 1)

    # Main logic
    try:
        # {YOUR LOGIC HERE}
        pass
    except SkillError as e:
        print(e.format(), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"\n💡 Try: python \"{__file}\" --action check-env",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 4.2 setup_env.py 模板

```python
#!/usr/bin/env python3
"""Environment setup helper. Checks and installs dependencies."""
import subprocess, sys
from pathlib import Path

REQUIRED = {
    # "package_name": {"pip": "package>=version", "desc": "description"},
}
MIN_PY = (3, 9)

def check_pkg(name):
    try:
        mod = __import__(name)
        return True, str(getattr(mod, "__version__", "?"))
    except ImportError:
        return False, None

def install(spec):
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "install", spec, "--quiet"],
                          capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except Exception:
        return False

def main():
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} @ {sys.executable}")
    if sys.version_info < MIN_PY:
        print(f"❌ Need Python {MIN_PY[0]}.{MIN_PY[1]}+")
        sys.exit(1)

    missing = []
    for pkg, info in REQUIRED.items():
        ok, ver = check_pkg(pkg)
        print(f"  {'✅' if ok else '❌'} {pkg}: {ver or 'MISSING'}")
        if not ok:
            missing.append(info["pip"])

    if missing and "--check-only" not in sys.argv:
        for spec in missing:
            print(f"  Installing {spec}...")
            if not install(spec):
                print(f"  ❌ Failed. Run manually: pip install {spec}")
                sys.exit(1)
        print("✅ All installed!")
    elif missing:
        print(f"❌ Missing: pip install {' '.join(missing)}")
        sys.exit(1)
    else:
        print("✅ Ready!")

if __name__ == "__main__":
    main()
```

## Phase 5: Validation

### 5.1 Skill Quality Checklist

After generating skill files, validate against this checklist:

```
═══════════════════════════════════════════
  SKILL QUALITY CHECKLIST
═══════════════════════════════════════════

FRONTMATTER:
  □ name 是 kebab-case
  □ description 包含触发条件 + 能力列表
  □ description 用用户语言而非技术实现
  □ version 使用 semver
  □ triggers 包含中英文关键词
  □ platform 明确列出支持的平台
  □ 依赖声明完整（requires/dependencies）

SETUP:
  □ 首次使用的检查步骤完整
  □ 环境依赖有安装命令
  □ [Type A] 脚本路径发现方法（非硬编码）
  □ [Type B] MCP 连接配置方法
  □ [Type B] 认证获取步骤
  □ 环境检查 action 可用

DECISION LOGIC:
  □ 有决策树覆盖模糊/明确/边界情况
  □ 多工具/多路径时有选择指导
  □ 前置条件未满足时有引导流程

WORKFLOWS:
  □ 每个工作流有清晰的步骤序列
  □ [Type A] 复杂参数走文件（--sql-file 等）
  □ [Type A] 命令使用双引号包裹路径
  □ [Type B] 工具调用有完整参数示例
  □ 有负面指令（不要做什么）

PARAMETERS:
  □ 参数表格包含：名称、必选/可选、说明
  □ 参数命名不一致处有警告标注
  □ 有 Shell 引号使用指南（如适用）

ERROR HANDLING:
  □ 有错误映射表（错误 → 原因 → 恢复）
  □ 覆盖至少 8 种常见错误场景
  □ 有错误恢复工作流图
  □ [Type A] 包含依赖缺失、路径错误、编码错误
  □ [Type B] 包含认证失败、API 限流、网络错误
  □ 有降级/fallback 方案

EXAMPLES:
  □ 至少 2 个完整的端到端示例
  □ 至少 1 个中文场景示例（如适用）
  □ 示例包含用户原始需求 → 全部步骤 → 最终输出
  □ 示例覆盖正常路径和异常路径

PLATFORM:
  □ 路径使用正斜杠 / 或参数化
  □ Windows 特殊注意事项（如适用）
  □ Python 命令兼容性说明
  □ Shell 差异说明

CHINESE SUPPORT:
  □ 中文文件名处理说明
  □ 中文列名/标识符引号说明
  □ 编码检测和 GBK 支持
  □ 有中文数据示例

KNOWN PITFALLS:
  □ 列出反直觉的 API/工具行为
  □ 列出常见的用户误解
  □ 每个陷阱有解决方案

SCRIPTS (Type A):
  □ 支持 --action check-env
  □ 支持 --action locate
  □ 结果 → stdout，诊断 → stderr
  □ 错误消息包含 💡 Suggestion
  □ 退出码：成功 0，失败非 0
  □ 有 requirements.txt
  □ 有 setup_env.py

═══════════════════════════════════════════
```

### 5.2 Automated Validation

Use the validation script to check generated skill files programmatically.

```
python {SKILL_SCRIPTS}/validate_skill.py --skill-dir /path/to/new-skill/
```

## Phase 6: Deployment

### 6.1 Deployment Instructions

After validation, provide the user with deployment instructions:

**Trae AI：**
```
1. 将 skill 目录复制到项目中的约定位置
   （通常是 .trae/skills/ 或项目根目录下的 skills/）
2. 重启 Trae AI 或刷新 skill 列表
3. 测试 skill 触发（输入触发关键词）
4. 验证首次执行流程
```

**Cursor：**
```
1. 将 skill 目录放到 .cursor/skills/ 或 .cursorrules 引用的位置
2. 在 .cursorrules 中 include 新 skill（如需要）
3. 测试 skill 触发
```

### 6.2 Iteration Guidance

```
首次部署后的优化循环：

1. 观察 AI 的实际执行行为
2. 记录失败场景和根因
3. 更新 Error Handling 表
4. 补充遗漏的决策分支
5. 丰富示例库
6. 更新 version 号
```

## Output Format

When generating skill files, output them in this order:

1. **先输出目录结构总览**
2. **然后逐个输出文件内容**，每个文件用完整的文件路径标题
3. **最后输出部署指南和验证步骤**

```
📁 文件结构：
{tree view}

📄 文件 1：{path}
```{language}
{content}
```

📄 文件 2：{path}
...

🚀 部署指南：
{deployment steps}

✅ 验证步骤：
{verification steps}
```

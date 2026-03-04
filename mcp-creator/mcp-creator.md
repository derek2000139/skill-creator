---
name: mcp-creator
version: 1.0.0
description: >
  Meta-skill for creating production-quality MCP (Model Context Protocol) servers.
  Use this when the user wants to create a new MCP server to expose APIs, databases,
  file systems, or custom business logic as AI-callable tools. Generates complete
  server code (Python), IDE configuration, companion skill files, and test scripts.
  Supports API wrappers, database connectors, file system tools, and custom logic.
  Output is ready-to-deploy for Trae AI, Cursor, Claude Desktop, and other MCP-compatible IDEs.
triggers:
  keywords: ["创建mcp", "mcp server", "mcp服务", "新建mcp", "create mcp",
             "封装api", "wrap api", "工具服务器", "tool server",
             "mcp模板", "mcp template", "建mcp", "写mcp"]
platform: [windows, macos, linux]
dependencies:
  runtime: "python>=3.10"
  packages: ["mcp>=1.0.0", "httpx>=0.27.0"]
---

# MCP Creator Skill

## Overview

This meta-skill creates complete, production-quality MCP servers. Given a user's
description of what capability they want to expose to AI, it generates all the
code, configuration, and documentation needed to deploy a working MCP server.

**What is an MCP Server?**
A program that exposes "tools" (functions) to AI agents via the standardized
Model Context Protocol. The AI can discover and call these tools to interact
with APIs, databases, file systems, and more.

**What this skill produces:**

```
{server-name}/
├── server.py              # MCP Server main entry point
├── tools.py               # Tool implementations
├── security.py            # Security utilities
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── test_server.py         # Smoke test script
├── README.md              # Human-readable documentation
├── ide_configs/
│   ├── trae_config.json   # Trae AI MCP configuration
│   ├── cursor_mcp.json    # Cursor MCP configuration
│   └── claude_config.json # Claude Desktop configuration
└── skill/
    └── {name}.md          # Companion skill file for AI guidance
```

## Step 0: Locate Generator Script

> [!CRITICAL]
> Never hardcode the generator script path. Locate dynamically.

**Windows PowerShell:**
```powershell
Get-ChildItem -Path . -Recurse -Filter "generate_server.py" | Where-Object { $_.DirectoryName -match "scripts" }
```

**macOS/Linux:**
```bash
find . -path "*/scripts/generate_server.py" 2>/dev/null
```

Once found, verify:
```
python "{FOUND_PATH}" --action check-env
```

## Phase 1: Requirements Discovery

> [!CRITICAL]
> Always complete discovery before generating code. A server built on
> wrong assumptions is worse than no server (it will run with bugs).

### 1.1 Questions to Ask

**Core functionality:**
```
1. 这个 MCP Server 要封装什么能力？
   - 封装某个 REST API？（如 GitHub、天气、翻译）
   - 连接数据库？（如 SQLite、PostgreSQL、MySQL）
   - 操作本地文件/程序？
   - 自定义业务逻辑？

2. 需要暴露哪些工具（Tools）？
   - 列出每个工具的名称和功能
   - 每个工具需要什么输入参数？
   - 每个工具返回什么结果？

3. 有没有现成的 API 文档或 SDK？
   - OpenAPI/Swagger 文档？
   - API 的 base URL 是什么？
   - 认证方式是什么？（API Key / OAuth / Basic Auth）
```

**Environment & deployment:**
```
4. 使用什么 IDE？（Trae AI / Cursor / Claude Desktop / 其他）
5. 操作系统？（Windows / macOS / Linux）
6. 传输方式偏好？
   - stdio：最简单，IDE 直接管理进程（推荐本地开发）
   - SSE：独立HTTP服务，支持远程访问
7. 有没有安全/隐私约束？
   - API Key 如何管理？
   - 数据是否敏感？
```

### 1.2 Category Decision

```
用户要封装的能力
├─ REST/GraphQL API → Category A: API Wrapper
│  特征：有 base_url, 需要 HTTP 调用, 需要 API Key
│  自动化程度：⭐⭐⭐⭐⭐（几乎全自动）
│
├─ 数据库 → Category B: Database Connector
│  特征：需要连接字符串, SQL 查询, 结果格式化
│  自动化程度：⭐⭐⭐⭐（高度自动）
│
├─ 本地文件/程序 → Category C: File System Tool
│  特征：文件读写, 本地命令执行, 路径处理
│  自动化程度：⭐⭐⭐（需要安全审查）
│
└─ 自定义逻辑 → Category D: Custom Logic
   特征：复杂业务规则, 不属于以上三类
   自动化程度：⭐⭐（生成骨架，用户填充逻辑）
```

### 1.3 Build Spec File

Based on discovery, write a spec JSON file. **This is the core input to the generator.**

> [!CRITICAL]
> Always write the spec to a JSON file, then pass via --config-file.
> Never pass complex JSON via command-line arguments (trae-sandbox incompatible).

#### Spec File Format

```json
{
  "name": "server-name",
  "display_name": "Human-Readable Server Name",
  "description": "Server 的功能描述",
  "version": "1.0.0",
  "category": "api_wrapper | database | filesystem | custom",
  "transport": "stdio | sse",
  "language": "python",

  "api": {
    "base_url": "https://api.example.com/v1",
    "auth_method": "api_key | bearer_token | basic_auth | none",
    "auth_env_var": "EXAMPLE_API_KEY",
    "auth_location": "header | query_param",
    "auth_header_name": "Authorization",
    "auth_header_prefix": "Bearer",
    "auth_param_name": "api_key",
    "default_headers": {
      "Content-Type": "application/json"
    },
    "rate_limit": {
      "requests_per_minute": 60,
      "retry_after_seconds": 5
    }
  },

  "database": {
    "type": "sqlite | postgresql | mysql",
    "env_var": "DATABASE_URL",
    "default_path": "./data.db",
    "read_only": false,
    "max_rows": 1000
  },

  "filesystem": {
    "allowed_directories": ["./workspace"],
    "allowed_extensions": [".txt", ".md", ".json", ".csv"],
    "max_file_size_mb": 10,
    "allow_write": false,
    "allow_delete": false
  },

  "tools": [
    {
      "name": "tool_name",
      "description": "工具的详细描述，AI 根据这个决定是否调用",
      "parameters": [
        {
          "name": "param_name",
          "type": "string | integer | number | boolean | array | object",
          "description": "参数描述",
          "required": true,
          "default": null,
          "enum": null
        }
      ],
      "endpoint": "/api/endpoint",
      "method": "GET | POST | PUT | DELETE",
      "request_body_template": null,
      "response_format": "text | json_summary | full_json"
    }
  ],

  "ide_targets": ["trae", "cursor", "claude_desktop"],
  "generate_skill": true,
  "generate_tests": true,

  "security": {
    "sanitize_sql": true,
    "validate_paths": true,
    "mask_secrets_in_logs": true,
    "max_request_size_kb": 1024
  }
}
```

#### Spec Example: Weather API

Write file `weather_spec.json`:
```json
{
  "name": "weather-server",
  "display_name": "Weather MCP Server",
  "description": "获取全球城市天气信息，支持当前天气和未来预报",
  "version": "1.0.0",
  "category": "api_wrapper",
  "transport": "stdio",
  "language": "python",
  "api": {
    "base_url": "https://api.openweathermap.org/data/2.5",
    "auth_method": "api_key",
    "auth_env_var": "OPENWEATHER_API_KEY",
    "auth_location": "query_param",
    "auth_param_name": "appid",
    "rate_limit": {
      "requests_per_minute": 60,
      "retry_after_seconds": 2
    }
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "获取指定城市的当前天气信息，包括温度、湿度、风速、天气状况。支持中文城市名。",
      "parameters": [
        {
          "name": "city",
          "type": "string",
          "description": "城市名称，如 '北京', 'London', 'Tokyo'",
          "required": true
        },
        {
          "name": "units",
          "type": "string",
          "description": "温度单位：metric(摄氏度) 或 imperial(华氏度)",
          "required": false,
          "default": "metric",
          "enum": ["metric", "imperial"]
        }
      ],
      "endpoint": "/weather",
      "method": "GET",
      "response_format": "text"
    },
    {
      "name": "get_forecast",
      "description": "获取指定城市未来5天的天气预报",
      "parameters": [
        {
          "name": "city",
          "type": "string",
          "description": "城市名称",
          "required": true
        },
        {
          "name": "days",
          "type": "integer",
          "description": "预报天数(1-5)",
          "required": false,
          "default": 3
        }
      ],
      "endpoint": "/forecast",
      "method": "GET",
      "response_format": "text"
    }
  ],
  "ide_targets": ["trae", "cursor"],
  "generate_skill": true,
  "generate_tests": true
}
```

## Phase 2: Generate Server

### 2.1 Execute Generator

```
python "{GENERATOR_PATH}" --action generate --config-file weather_spec.json --output-dir ./weather-server
```

### 2.2 Generator Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--action` | Yes | `generate`, `validate-spec`, `check-env`, `locate` |
| `--config-file` | For generate | Path to spec JSON file |
| `--output-dir` | For generate | Output directory (created if needed) |
| `--force` | No | Overwrite existing files |
| `--no-skill` | No | Skip companion skill generation |
| `--no-tests` | No | Skip test script generation |
| `--transport` | No | Override transport (stdio/sse) |

> [!IMPORTANT]
> Do NOT read or modify the generator script. Just call it with parameters.

### 2.3 Generated Output

The generator creates a complete, ready-to-run MCP server:

```
weather-server/                      (--output-dir)
├── server.py                        # MCP Server 主入口
│   - Server 初始化
│   - Tool 注册
│   - 传输层启动
│
├── tools.py                         # Tool 实现
│   - 每个 tool 的处理函数
│   - 参数验证
│   - API 调用 / DB 查询 / 文件操作
│   - 结果格式化
│
├── security.py                      # 安全工具
│   - 输入验证/清洗
│   - SQL 注入防护
│   - 路径穿越防护
│   - 日志脱敏
│
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
│
├── test_server.py                   # 冒烟测试
│   - 环境检查
│   - 工具列表验证
│   - 模拟调用测试
│
├── README.md                        # 使用文档
│
├── ide_configs/
│   ├── trae_config.json
│   ├── cursor_mcp.json
│   └── claude_config.json
│
└── skill/
    └── weather-server.md            # 配套 Skill 文件
```

## Phase 3: Deploy & Configure

### 3.1 Install Dependencies

```
cd weather-server
pip install -r requirements.txt
```

### 3.2 Configure Environment

```
# 复制环境变量模板
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux

# 编辑 .env，填入实际的 API Key
```

> [!WARNING]
> **Never commit .env to version control!**
> Add `.env` to `.gitignore`.

### 3.3 Run Smoke Test

```
python test_server.py
```

Expected output:
```
✅ Python version: OK (3.12)
✅ Dependencies: OK
✅ Environment variables: OK
✅ Tool listing: OK (2 tools found)
✅ Tool call test: OK
🎉 All tests passed! Server is ready.
```

### 3.4 Configure IDE

#### Trae AI

1. 打开 Trae AI → 设置 → MCP
2. 添加服务器：
   - 使用 `ide_configs/trae_config.json` 中的配置
   - 或手动配置：
     - 名称：weather-server
     - 命令：python
     - 参数：`["{absolute_path}/server.py"]`
     - 环境变量：从 .env 文件复制

#### Cursor

复制 `ide_configs/cursor_mcp.json` 的内容到项目的 `.cursor/mcp.json`：
```json
{
  "mcpServers": {
    "weather-server": {
      "command": "python",
      "args": ["path/to/weather-server/server.py"],
      "env": {
        "OPENWEATHER_API_KEY": "your-key-here"
      }
    }
  }
}
```

> [!IMPORTANT]
> **修改 path 为实际绝对路径！**
> Windows 示例：`"C:/Users/zhangsan/projects/weather-server/server.py"`

#### Claude Desktop

将 `ide_configs/claude_config.json` 的内容合并到：
- Windows：`%APPDATA%/Claude/claude_desktop_config.json`
- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`

### 3.5 Deploy Companion Skill

将 `skill/weather-server.md` 复制到 IDE 的 skill 目录：
- Trae AI：`.trae/skills/weather-server/weather-server.md`
- Cursor：`.cursor/skills/weather-server/weather-server.md`

## Phase 4: Verification

After deployment, verify end-to-end:

1. **在 IDE 中测试**：输入与 Server 相关的请求
2. **观察**：AI 是否正确选择了 MCP 工具
3. **检查**：工具调用参数是否正确
4. **验证**：返回结果是否符合预期

如果出现问题，参考 Error Handling 章节。

## Spec File Patterns by Category

### Category A: API Wrapper

```json
{
  "category": "api_wrapper",
  "api": {
    "base_url": "https://api.example.com/v1",
    "auth_method": "api_key",
    "auth_env_var": "API_KEY",
    "auth_location": "header",
    "auth_header_name": "X-API-Key"
  },
  "tools": [
    {
      "name": "search_items",
      "description": "搜索项目",
      "parameters": [
        {"name": "query", "type": "string", "required": true},
        {"name": "limit", "type": "integer", "default": 10}
      ],
      "endpoint": "/search",
      "method": "GET"
    },
    {
      "name": "create_item",
      "description": "创建新项目",
      "parameters": [
        {"name": "title", "type": "string", "required": true},
        {"name": "content", "type": "string", "required": true}
      ],
      "endpoint": "/items",
      "method": "POST",
      "request_body_template": {"title": "{title}", "content": "{content}"}
    }
  ]
}
```

### Category B: Database Connector

```json
{
  "category": "database",
  "database": {
    "type": "sqlite",
    "env_var": "DATABASE_PATH",
    "default_path": "./data.db",
    "read_only": false,
    "max_rows": 500
  },
  "tools": [
    {
      "name": "list_tables",
      "description": "列出数据库中所有表",
      "parameters": []
    },
    {
      "name": "describe_table",
      "description": "查看表结构",
      "parameters": [
        {"name": "table_name", "type": "string", "required": true}
      ]
    },
    {
      "name": "query",
      "description": "执行SQL查询（只读）",
      "parameters": [
        {"name": "sql", "type": "string", "required": true, "description": "SQL查询语句（仅SELECT）"},
        {"name": "limit", "type": "integer", "default": 100}
      ]
    },
    {
      "name": "execute",
      "description": "执行SQL写操作（INSERT/UPDATE/DELETE）",
      "parameters": [
        {"name": "sql", "type": "string", "required": true},
        {"name": "params", "type": "array", "description": "参数化查询的参数列表"}
      ]
    }
  ]
}
```

### Category C: File System Tool

```json
{
  "category": "filesystem",
  "filesystem": {
    "allowed_directories": ["./workspace"],
    "allowed_extensions": [".txt", ".md", ".json", ".csv", ".py"],
    "max_file_size_mb": 10,
    "allow_write": true,
    "allow_delete": false
  },
  "tools": [
    {
      "name": "list_files",
      "description": "列出目录下的文件",
      "parameters": [
        {"name": "directory", "type": "string", "default": "."},
        {"name": "pattern", "type": "string", "description": "文件名匹配模式，如 *.py"}
      ]
    },
    {
      "name": "read_file",
      "description": "读取文件内容",
      "parameters": [
        {"name": "path", "type": "string", "required": true}
      ]
    },
    {
      "name": "write_file",
      "description": "写入文件",
      "parameters": [
        {"name": "path", "type": "string", "required": true},
        {"name": "content", "type": "string", "required": true}
      ]
    },
    {
      "name": "search_in_files",
      "description": "在文件中搜索文本",
      "parameters": [
        {"name": "query", "type": "string", "required": true},
        {"name": "directory", "type": "string", "default": "."},
        {"name": "file_pattern", "type": "string", "default": "*.*"}
      ]
    }
  ]
}
```

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `ModuleNotFoundError: mcp` | MCP SDK not installed | `pip install mcp` |
| `ModuleNotFoundError: httpx` | httpx not installed | `pip install httpx` |
| `spec validation failed` | Spec JSON format error | Check spec against format reference |
| `EADDRINUSE` (SSE mode) | Port occupied | Change port or stop other process |
| `API Key not set` | Missing env variable | Set in .env or system environment |
| `Connection refused` (IDE) | Server not running | Start server first; check config path |
| `Tool not found` (IDE) | Tool name mismatch | Verify tool names match between server and IDE |
| `Permission denied` | File/port access denied | Run with appropriate permissions |
| `asyncio` errors on Windows | Event loop policy | Script auto-applies `WindowsSelectorEventLoopPolicy` |

### Error Recovery Workflow

```
Server/Generator 报错
│
├─ generate 阶段出错
│  ├─ "spec validation" → 检查 spec JSON 格式 → 修正 → 重新生成
│  ├─ "output dir exists" → 加 --force 覆盖 或 换目录
│  └─ Import error → run check-env → install packages
│
├─ 启动阶段出错
│  ├─ Import error → pip install -r requirements.txt
│  ├─ Env var missing → 检查 .env 文件
│  ├─ Port in use → 换端口 或 停止占用进程
│  └─ asyncio error (Windows) → 检查 Python 版本 ≥ 3.10
│
├─ IDE 连接出错
│  ├─ Server not found → 检查 command/args 路径是否正确
│  ├─ Connection refused → Server 是否已启动？
│  ├─ Tool list empty → Server 代码是否正确注册了 tools？
│  └─ Auth error → 检查 env 变量是否传递
│
└─ 运行时出错
   ├─ API error → 检查 API Key、网络、rate limit
   ├─ SQL error → 检查 SQL 语法、表名
   ├─ File not found → 检查路径、权限
   └─ Unknown → 查看 server stderr 日志
```

## Security Checklist

> [!CRITICAL]
> Every generated MCP server should be reviewed against this checklist
> before production use.

```
CREDENTIAL MANAGEMENT:
  □ API Keys stored in environment variables, NOT in code
  □ .env file is in .gitignore
  □ Secrets not logged or returned in tool responses
  □ .env.example contains placeholder values only

INPUT VALIDATION:
  □ All string inputs have max length limits
  □ SQL queries are parameterized (no string concatenation)
  □ File paths validated against allowed directories
  □ No shell command injection possible
  □ Numeric inputs have range validation

ACCESS CONTROL:
  □ Database connections use minimal required permissions
  □ File system access restricted to allowed directories
  □ Read-only mode available and documented
  □ Dangerous operations require explicit confirmation

ERROR HANDLING:
  □ Errors don't leak internal paths or credentials
  □ Stack traces only shown in debug mode
  □ Graceful degradation on external service failure

NETWORK:
  □ SSE mode: CORS configured if needed
  □ SSE mode: Authentication on HTTP endpoints
  □ API calls use HTTPS
  □ Timeout configured for all HTTP requests
```

## MCP Protocol Quick Reference

### Tool Definition Structure

```python
Tool(
    name="tool_name",                    # 唯一标识符 (snake_case)
    description="详细描述，AI 据此决定"   # 越详细越好
        "是否调用此工具。"
        "说明：输入什么、返回什么、什么场景适用。",
    inputSchema={                        # JSON Schema
        "type": "object",
        "properties": {
            "param": {
                "type": "string",        # string/integer/number/boolean/array/object
                "description": "参数描述",
                "enum": ["val1", "val2"], # 可选：限制可选值
                "default": "val1"         # 可选：默认值
            }
        },
        "required": ["param"]            # 必填参数列表
    }
)
```

### Tool Description Best Practices

```
❌ 差的 description:
   "Query the database"
   → AI 不知道什么时候该用，什么时候不该用

✅ 好的 description:
   "Execute a read-only SQL query against the application database. "
   "Returns results as a formatted table. "
   "Use this when the user asks about data, statistics, or records. "
   "Supports standard SQL SELECT statements. "
   "Maximum 1000 rows returned. "
   "Do NOT use for write operations (INSERT/UPDATE/DELETE) — "
   "use the 'execute_write' tool instead."
   → 包含：能做什么、何时用、限制、与其他工具的区分
```

### Transport Comparison

| | stdio | SSE | Streamable HTTP |
|-|-------|-----|-----------------|
| 启动方式 | IDE 启动进程 | 手动启动服务 | 手动/serverless |
| 网络 | 不需要 | 需要(本地/远程) | 需要 |
| 配置复杂度 | 低 | 中 | 中 |
| 多用户 | 不支持 | 支持 | 支持 |
| 推荐场景 | 个人本地开发 | 团队共享 | 云端部署 |

## Platform Notes

### Windows (Trae AI)

- Python 命令：通常是 `python` 或 `py`（不是 `python3`）
- asyncio：Python 3.10+ 自动处理 Windows 事件循环
- 路径：server.py 中使用正斜杠 `/` 或 `Path` 对象
- 文件锁：如果 .db 文件被其他程序打开可能失败
- 防火墙：SSE 模式可能需要放行端口

### macOS / Linux

- Python 命令：通常是 `python3`
- 权限：可能需要 `chmod +x server.py`
- 端口：< 1024 需要 sudo（避免使用）

## Notes

- MCP SDK 版本要求：`mcp >= 1.0.0`
- 生成的代码使用 `async/await`，需要 Python 3.10+
- 每个 Tool 的 description 是 AI 选择工具的唯一依据——写得越清晰越好
- 生成代码后务必进行人工安全审查
- 首次使用需配置 IDE 的 MCP 设置（各 IDE 方式不同）
- stdio 模式下 IDE 自动管理 Server 进程生命周期
- SSE 模式需要手动启动 Server 并管理进程
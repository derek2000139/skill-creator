# MCP Creator Skill

## 📁 项目结构

```
mcp-creator/
├── mcp-creator.md                        # Meta-Skill 定义文件
├── README.md                             # 本文件
└── scripts/
    ├── generate_server.py                # MCP Server 代码生成器
    ├── validate_server.py                # 生成物验证工具
    ├── setup_env.py                      # 环境配置助手
    ├── requirements.txt                  # 依赖清单
    └── examples/                         # 示例配置
        ├── weather_api_spec.json         # 示例：天气 API Wrapper
        ├── sqlite_db_spec.json           # 示例：SQLite 数据库连接器
        └── filesystem_spec.json          # 示例：文件系统工具
```

## 🚀 快速开始

### 1. 环境检查

```bash
# 检查 Python 版本和依赖
python scripts/generate_server.py --action check-env
```

### 2. 生成 MCP Server

```bash
# 使用示例配置生成天气 API 服务器
python scripts/generate_server.py \
    --action generate \
    --config-file scripts/examples/weather_api_spec.json \
    --output-dir ./weather-server
```

### 3. 验证生成结果

```bash
# 验证生成的服务器
python scripts/validate_server.py --path ./weather-server
```

### 4. 安装依赖

```bash
# 安装 MCP 相关依赖
python scripts/setup_env.py --action install-deps

# 为生成的服务器创建 .env 文件
python scripts/setup_env.py --action create-env --path ./weather-server
```

## 📖 使用指南

### 生成器参数

| 参数 | 说明 | 必需 |
|------|------|------|
| `--action` | 操作类型：generate、validate-spec、check-env、locate | 是 |
| `--config-file` | 配置文件路径（generate 时需要） | 是 |
| `--output-dir` | 输出目录（generate 时需要） | 是 |
| `--force` | 覆盖现有文件 | 否 |
| `--no-skill` | 跳过生成配套 skill 文件 | 否 |
| `--no-tests` | 跳过生成测试文件 | 否 |
| `--transport` | 覆盖传输方式（stdio/sse） | 否 |

### 配置文件格式

配置文件是 JSON 格式，包含以下主要字段：

- `name`: 服务器名称（kebab-case）
- `display_name`: 显示名称
- `description`: 服务器描述
- `category`: 类别（api_wrapper、database、filesystem、custom）
- `transport`: 传输方式（stdio、sse）
- `tools`: 工具列表
- `api`/`database`/`filesystem`: 类别特定配置

详细格式见 `mcp-creator.md` 文件。

## 🔧 工具说明

1. **generate_server.py**: 核心生成器，根据配置文件生成完整的 MCP 服务器代码
2. **validate_server.py**: 验证生成的服务器是否完整和安全
3. **setup_env.py**: 环境配置助手，安装依赖和创建环境文件

## 📚 示例

### 1. 天气 API Wrapper

```bash
python scripts/generate_server.py \
    --action generate \
    --config-file scripts/examples/weather_api_spec.json \
    --output-dir ./weather-server
```

### 2. SQLite 数据库连接器

```bash
python scripts/generate_server.py \
    --action generate \
    --config-file scripts/examples/sqlite_db_spec.json \
    --output-dir ./sqlite-server
```

### 3. 文件系统工具

```bash
python scripts/generate_server.py \
    --action generate \
    --config-file scripts/examples/filesystem_spec.json \
    --output-dir ./filesystem-server
```

## 🛠️ 技术栈

- **Python 3.10+**
- **MCP SDK** (`mcp>=1.0.0`)
- **HTTP Client** (`httpx>=0.27.0`)
- **SSE Transport** (可选, 需要 `uvicorn` 和 `starlette`)
- **Database Drivers** (可选, 如 `asyncpg` 用于 PostgreSQL)

## 📝 注意事项

1. **安全**: 生成的服务器包含基本的安全措施，但生产环境使用前请进行安全审查
2. **依赖**: 生成的服务器需要安装 `mcp` 和 `httpx` 包
3. **配置**: 需要在 `.env` 文件中设置 API Key 等敏感信息
4. **IDE 配置**: 根据 IDE 类型使用 `ide_configs` 目录中的配置文件

## 🐛 故障排除

- **ModuleNotFoundError: mcp**: 运行 `python scripts/setup_env.py --action install-deps`
- **API Key not set**: 检查 `.env` 文件中的环境变量
- **Connection refused**: 确保服务器正在运行且路径配置正确
- **Tool not found**: 检查工具名称是否匹配

## 📄 许可证

MIT License

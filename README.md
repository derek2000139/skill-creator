# AI Skill Factory - 智能技能工厂

## 项目概述

AI Skill Factory 是一个专注于创建和管理生产级 AI skill 的项目。核心功能是通过 `skill-creator` 元技能，指导 AI 生成高质量的 skill 文件，实现技能的快速开发和部署。

AI Skill Factory is a project focused on creating and managing production-grade AI skills. The core functionality is through the `skill-creator` meta-skill, which guides AI to generate high-quality skill files, enabling rapid skill development and deployment.

## 核心功能

### 1. Skill Creator 元技能
- **需求分析**：系统性收集用户需求，确保 skill 设计基于正确的假设
- **架构选择**：根据需求自动推荐适合的 skill 类型（脚本驱动型、MCP 工具型或纯提示词型）
- **文件生成**：生成符合最佳实践的 skill 文件结构和内容
- **质量验证**：内置验证工具，确保生成的 skill 符合生产级质量标准
- **中文支持**：完整支持中文场景，包括中文文件名、列名和内容

### 1. Skill Creator Meta-Skill
- **Requirements Analysis**：Systematically collect user requirements to ensure skill design is based on correct assumptions
- **Architecture Selection**：Automatically recommend suitable skill types based on requirements (script-based, MCP tool-based, or prompt-based)
- **File Generation**：Generate skill file structures and content that follow best practices
- **Quality Validation**：Built-in validation tools to ensure generated skills meet production-level quality standards
- **Chinese Support**：Full support for Chinese scenarios, including Chinese file names, column names, and content

## 项目特点

### 质量层级优势

```
         ▲
        /7\     自我进化：能根据使用反馈优化自身
       /───\
      / 6   \   可组合性：能与其他 skill 协作联动
     /───────\
    /   5     \  防御性：完整的错误处理和降级方案
   /───────────\
  /     4       \ 平台适配：跨 OS、跨 IDE、跨 shell
 /───────────────\
/       3         \ 决策智能：decision tree，意图路由
├─────────────────┤
|       2         | 工具接口：清晰的参数、示例、约束
├─────────────────┤
|       1         | 基础结构：frontmatter、workflow、notes
└─────────────────┘
```

**多数 skill 只做到了 1-2 层。生产级需要到 5 层。** 我们的 meta-skill 指导 AI 产出 5 层质量的 skill，确保：

- **完整的错误处理**：包含错误映射表和恢复策略
- **跨平台兼容**：支持 Windows、macOS 和 Linux
- **中文场景支持**：处理中文文件名、编码和标识符
- **安全最佳实践**：避免硬编码路径和敏感信息
- **可维护性**：清晰的结构和文档

### Quality Level Advantages

Most skills only reach levels 1-2, while production-level skills need to reach level 5. Our meta-skill guides AI to produce skills of level 5 quality, ensuring:

- **Complete error handling**：Including error mapping tables and recovery strategies
- **Cross-platform compatibility**：Support for Windows, macOS, and Linux
- **Chinese scenario support**：Handling Chinese file names, encoding, and identifiers
- **Security best practices**：Avoiding hardcoded paths and sensitive information
- **Maintainability**：Clear structure and documentation

## 项目结构

```
AI/
├── README.md                # 项目说明文档
├── skill-creator/          # Skill Creator 元技能
│   ├── skill-creator.md     # 元技能定义文件
│   ├── README.md            # 元技能说明文档
│   └── scripts/
│       └── validate_skill.py # Skill 验证工具
├── file-reader/            # 示例 Skill：文件读取器
│   ├── file-reader.md       # Skill 定义文件
│   └── scripts/
│       ├── file_reader.py   # 主执行脚本
│       ├── setup_env.py     # 环境配置助手
│       └── requirements.txt # Python 依赖
├── mcp-creator/            # MCP 服务器生成器
│   ├── mcp-creator.md       # Meta-Skill 定义文件
│   ├── README.md            # 项目说明文档
│   └── scripts/
│       ├── generate_server.py # MCP Server 代码生成器
│       ├── validate_server.py # 生成物验证工具
│       ├── setup_env.py       # 环境配置助手
│       ├── requirements.txt   # 依赖清单
│       └── examples/          # 示例配置
│           ├── weather_api_spec.json         # 示例：天气 API Wrapper
│           ├── sqlite_db_spec.json           # 示例：SQLite 数据库连接器
│           └── filesystem_spec.json          # 示例：文件系统工具
└── [其他生成的 skills]      # 后续通过 skill-creator 生成的 skills
```

## 安装与使用

### 基本要求
- Python 3.9+
- Trae AI 或其他支持 skill 的 IDE

### 安装步骤
1. 克隆或下载项目到本地
2. 确保 Python 3.9+ 已安装
3. 对于需要依赖的 skill，运行 `setup_env.py` 安装依赖

### 使用方法

#### 1. 使用 Skill Creator 生成新 Skill
- 在 Trae AI 中输入触发关键词（如 "创建skill"、"写skill" 等）
- 回答关于功能需求、环境和约束的问题
- 确认需求后，AI 会生成完整的 skill 文件

#### 2. 验证 Skill 质量
```bash
python skill-creator/scripts/validate_skill.py --skill-dir /path/to/your-skill/
```

#### 3. 部署 Skill
- **Trae AI**：将 skill 目录复制到 `.trae/skills/` 或项目根目录的 `skills/` 文件夹
- **其他 IDE**：根据各 IDE 的要求进行配置

## 不同 IDE 的配置注意事项

### Trae AI（免费版本）
- 优点：免费使用，功能完整
- 配置：直接将 skill 目录复制到 `.trae/skills/` 文件夹
- 注意：免费版本可能有一些功能限制，但基本的 skill 功能都可以使用

### 其他 IDE 配置注意事项

#### Claude
- **配置**：需要在 Claude 的配置文件中指定 skill 目录
- **注意**：Claude 的 skill 格式可能与 Trae AI 略有不同，需要调整 frontmatter 格式
- **优势**：强大的自然语言理解能力

#### Codex
- **配置**：通过 `.vscode/extensions` 目录或相关配置文件
- **注意**：Codex 更注重代码生成，skill 执行环境可能需要额外配置
- **优势**：出色的代码理解和生成能力

#### Cursor
- **配置**：将 skill 目录放到 `.cursor/skills/` 或 `.cursorrules` 引用的位置
- **注意**：Cursor 使用不同的 skill 激活机制，需要在 `.cursorrules` 中正确配置
- **优势**：专为代码编辑优化的界面

## 中文支持

本项目特别注重中文支持：
- **中文文件名处理**：正确处理包含中文字符的文件路径
- **中文内容分析**：支持中文文本的分析和处理
- **中文错误信息**：错误提示和建议使用中文
- **中文示例**：提供中文场景的完整示例

Chinese support is a key feature of this project:
- **Chinese file name handling**：Correctly process file paths containing Chinese characters
- **Chinese content analysis**：Support analysis and processing of Chinese text
- **Chinese error messages**：Error prompts and suggestions in Chinese
- **Chinese examples**：Provide complete examples for Chinese scenarios

## 项目目标

- **降低技能开发门槛**：通过标准化流程，让任何人都能创建高质量的 AI skill
- **提高技能质量**：确保所有生成的 skill 达到生产级质量标准
- **促进技能生态**：鼓励创建和分享各种领域的专业 skill
- **支持全球用户**：提供中英文双语支持，服务全球用户

## 贡献

欢迎提交问题和改进建议！如果您有好的 skill 创意或改进方案，欢迎贡献到项目中。

Contributions are welcome! If you have good skill ideas or improvement suggestions, please contribute to the project.

## 许可证

MIT License

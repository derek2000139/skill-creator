# Skill Creator - 生产级 Skill 生成器

## 项目概述

Skill Creator 是一个元技能（Meta-Skill），用于帮助用户创建、改进和管理生产级别的 AI skill 文件。它提供了完整的流程指导，从需求分析到架构设计，再到文件生成和验证。

## 功能特性

- **需求发现**：系统性收集用户需求，确保 skill 设计基于正确的假设
- **架构选择**：根据需求自动推荐适合的 skill 类型（脚本驱动型、MCP 工具型或纯提示词型）
- **文件生成**：生成符合最佳实践的 skill 文件结构和内容
- **脚本模板**：提供 Python 脚本模板，包含环境检查、错误处理等标准功能
- **质量验证**：内置验证工具，确保生成的 skill 符合生产级质量标准
- **中文支持**：完整支持中文场景，包括中文文件名、列名和内容

## 目录结构

```
skill-creator/
├── skill-creator.md              # 元技能定义文件
├── README.md                     # 项目说明文档
└── scripts/
    └── validate_skill.py         # Skill 验证工具
```

## 安装与使用

### 安装

1. 将 `skill-creator` 目录复制到你的项目中
2. 确保 Python 3.9+ 已安装
3. 无需额外依赖，验证工具使用标准库

### 使用方法

1. **在 Trae AI 中使用**：
   - 将 `skill-creator` 目录复制到 `.trae/skills/` 或项目根目录的 `skills/` 文件夹
   - 重启 Trae AI 或刷新 skill 列表
   - 输入触发关键词（如 "创建skill"、"写skill" 等）

2. **在 Cursor 中使用**：
   - 将 `skill-creator` 目录放到 `.cursor/skills/` 或 `.cursorrules` 引用的位置
   - 在 `.cursorrules` 中 include 新 skill（如需要）
   - 测试 skill 触发

3. **验证已生成的 skill**：
   ```bash
   python skill-creator/scripts/validate_skill.py --skill-dir /path/to/your-skill/
   ```

## 工作流程

1. **需求分析**：回答关于功能范围、环境和约束的问题
2. **架构决策**：根据需求选择合适的 skill 类型
3. **文件结构设计**：生成符合类型的文件结构
4. **内容生成**：创建 skill 定义文件和必要的脚本
5. **验证**：使用内置工具验证 skill 质量
6. **部署**：将生成的 skill 部署到目标 IDE

## 支持的 Skill 类型

- **Type A - 脚本驱动型**：本地执行，离线可用，适合处理本地文件
- **Type B - MCP 工具型**：通过 MCP 协议调用云端服务
- **Type C - 纯提示词型**：无依赖，即时可用，适合纯推理任务

## 质量标准

Skill Creator 遵循严格的质量标准，确保生成的 skill 达到生产级别：

- **完整的错误处理**：包含错误映射表和恢复策略
- **跨平台兼容**：支持 Windows、macOS 和 Linux
- **中文场景支持**：处理中文文件名、编码和标识符
- **安全最佳实践**：避免硬编码路径和敏感信息
- **可维护性**：清晰的结构和文档

## 示例

### 创建新 Skill 的对话示例

```
用户：我想创建一个 skill，可以帮我自动生成 API 文档

AI（使用 skill-creator）：

📋 让我先了解一下需求：

1. API 文档的来源是什么？
   - 读取代码中的注释/装饰器？（如 FastAPI、Flask）
   - 解析 OpenAPI/Swagger JSON？
   - 还是让 AI 根据代码推断？

2. 输出格式是什么？
   - Markdown 文档？
   - HTML 页面？
   - 还是更新到 Notion/Confluence？

3. 主要使用什么 IDE 和操作系统？

4. 需要支持什么编程语言的 API？

... （收集需求后）

📋 Skill 需求确认：
- 名称：api-doc-generator
- 功能：扫描 Python FastAPI 项目源码，自动生成 Markdown 格式的 API 文档
- 类型：Type A（脚本驱动）
- 触发条件：用户说"生成API文档"或指定 Python 项目目录
- 输入：项目目录路径
- 输出：Markdown 文档文件
- 平台：Windows (Trae AI)
- 特殊要求：支持中文注释

请确认是否正确？

... （确认后，生成完整的 skill 文件）
```

## 版本历史

- **1.0.0**：初始版本，包含完整的 meta-skill 定义和验证工具

## 贡献

欢迎提交问题和改进建议！

## 许可证

MIT License

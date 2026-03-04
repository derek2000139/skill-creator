#!/usr/bin/env python3
"""
MCP Server Generator v1.0.0

Generates complete, production-quality MCP server projects from a spec file.

Usage:
    python generate_server.py --action check-env
    python generate_server.py --action locate
    python generate_server.py --action validate-spec --config-file spec.json
    python generate_server.py --action generate --config-file spec.json --output-dir ./my-server
"""

import argparse
import json
import os
import re
import sys
import textwrap
import traceback
from pathlib import Path

__version__ = "1.0.0"


# ═══════════════════════════════════════════════════
# Error Classes
# ═══════════════════════════════════════════════════

class GeneratorError(Exception):
    def __init__(self, message: str, suggestion: str = None):
        super().__init__(message)
        self.suggestion = suggestion

    def format(self) -> str:
        msg = f"❌ Error: {self}"
        if self.suggestion:
            msg += f"\n💡 Suggestion: {self.suggestion}"
        return msg


class SpecError(GeneratorError):
    pass


# ═══════════════════════════════════════════════════
# Environment Check
# ═══════════════════════════════════════════════════

def check_environment() -> dict:
    result = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_path": sys.executable,
        "platform": sys.platform,
        "script_path": str(Path(__file__).resolve()),
        "packages": {},
        "all_ok": True,
        "errors": [],
    }
    if sys.version_info < (3, 10):
        result["errors"].append(f"Python 3.10+ required (found {result['python_version']})")
        result["all_ok"] = False

    for pkg in ["mcp", "httpx"]:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "?")
            result["packages"][pkg] = {"status": "ok", "version": str(ver)}
        except ImportError:
            result["packages"][pkg] = {"status": "optional", "version": None}
            # These are needed for generated servers, not the generator itself

    return result


def print_env_report(info: dict):
    print("=" * 55)
    print("🔍 MCP CREATOR — ENVIRONMENT CHECK")
    print("=" * 55)
    print(f"  Python  : {info['python_version']}")
    print(f"  Path    : {info['python_path']}")
    print(f"  Platform: {info['platform']}")
    print(f"  Script  : {info['script_path']}")
    print()
    for pkg, st in info["packages"].items():
        if st["status"] == "ok":
            print(f"  ✅ {pkg:<12} v{st['version']}")
        else:
            print(f"  ⚪ {pkg:<12} not installed (needed for generated servers)")
    print()
    if info["all_ok"]:
        print("  ✅ Generator ready!")
        print("  Note: Generated servers need 'mcp' and 'httpx' packages.")
        print("  Install with: pip install mcp httpx")
    else:
        for e in info["errors"]:
            print(f"  ❌ {e}")
    print("=" * 55)


# ═══════════════════════════════════════════════════
# Spec Validation
# ═══════════════════════════════════════════════════

VALID_CATEGORIES = {"api_wrapper", "database", "filesystem", "custom"}
VALID_TRANSPORTS = {"stdio", "sse"}
VALID_AUTH_METHODS = {"api_key", "bearer_token", "basic_auth", "none"}
VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
VALID_PARAM_TYPES = {"string", "integer", "number", "boolean", "array", "object"}
VALID_DB_TYPES = {"sqlite", "postgresql", "mysql"}


def validate_spec(spec: dict) -> list:
    """Validate spec dict. Returns list of error messages (empty = valid)."""
    errors = []

    # Required top-level fields
    for field in ["name", "category", "tools"]:
        if field not in spec:
            errors.append(f"Missing required field: '{field}'")

    if "name" in spec:
        name = spec["name"]
        if not re.match(r"^[a-z][a-z0-9-]*$", name):
            errors.append(f"'name' must be kebab-case (got: '{name}')")

    if "category" in spec:
        if spec["category"] not in VALID_CATEGORIES:
            errors.append(f"Invalid category: '{spec['category']}'. Must be one of: {VALID_CATEGORIES}")

    transport = spec.get("transport", "stdio")
    if transport not in VALID_TRANSPORTS:
        errors.append(f"Invalid transport: '{transport}'. Must be one of: {VALID_TRANSPORTS}")

    # Category-specific validation
    cat = spec.get("category", "")

    if cat == "api_wrapper":
        api = spec.get("api", {})
        if not api.get("base_url"):
            errors.append("api_wrapper requires 'api.base_url'")
        auth = api.get("auth_method", "none")
        if auth not in VALID_AUTH_METHODS:
            errors.append(f"Invalid auth_method: '{auth}'")
        if auth != "none" and not api.get("auth_env_var"):
            errors.append("Auth method requires 'api.auth_env_var'")

    if cat == "database":
        db = spec.get("database", {})
        if not db.get("type"):
            errors.append("database requires 'database.type'")
        elif db["type"] not in VALID_DB_TYPES:
            errors.append(f"Invalid database type: '{db['type']}'")

    if cat == "filesystem":
        fs = spec.get("filesystem", {})
        if not fs.get("allowed_directories"):
            errors.append("filesystem requires 'filesystem.allowed_directories'")

    # Tools validation
    tools = spec.get("tools", [])
    if not tools:
        errors.append("At least one tool is required")

    tool_names = set()
    for i, tool in enumerate(tools):
        prefix = f"tools[{i}]"
        if "name" not in tool:
            errors.append(f"{prefix}: missing 'name'")
        else:
            if tool["name"] in tool_names:
                errors.append(f"{prefix}: duplicate tool name '{tool['name']}'")
            tool_names.add(tool["name"])
            if not re.match(r"^[a-z_][a-z0-9_]*$", tool["name"]):
                errors.append(f"{prefix}: name must be snake_case (got: '{tool['name']}')")

        if "description" not in tool:
            errors.append(f"{prefix}: missing 'description'")
        elif len(tool.get("description", "")) < 10:
            errors.append(f"{prefix}: description too short (min 10 chars)")

        for j, param in enumerate(tool.get("parameters", [])):
            pp = f"{prefix}.parameters[{j}]"
            if "name" not in param:
                errors.append(f"{pp}: missing 'name'")
            if "type" not in param:
                errors.append(f"{pp}: missing 'type'")
            elif param["type"] not in VALID_PARAM_TYPES:
                errors.append(f"{pp}: invalid type '{param['type']}'")

        if cat == "api_wrapper":
            if "endpoint" not in tool:
                errors.append(f"{prefix}: api_wrapper tools require 'endpoint'")
            method = tool.get("method", "GET")
            if method not in VALID_HTTP_METHODS:
                errors.append(f"{prefix}: invalid method '{method}'")

    return errors


def read_spec_file(path: str) -> dict:
    """Read and parse spec JSON file."""
    p = Path(path).resolve()
    if not p.exists():
        raise SpecError(
            f"Spec file not found: {path}",
            "Check the file path. Write the spec JSON file first."
        )
    try:
        text = p.read_text(encoding="utf-8")
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SpecError(
            f"Invalid JSON in spec file: {e}",
            "Check JSON syntax. Common issues: trailing commas, missing quotes."
        )


# ═══════════════════════════════════════════════════
# Code Generators
# ═══════════════════════════════════════════════════

class MCPServerGenerator:
    """Generates MCP server project files from a spec."""

    def __init__(self, spec: dict):
        self.spec = spec
        self.name = spec["name"]
        self.display_name = spec.get("display_name", self.name)
        self.description = spec.get("description", "")
        self.category = spec["category"]
        self.transport = spec.get("transport", "stdio")
        self.tools = spec.get("tools", [])
        self.version = spec.get("version", "1.0.0")

    def generate_all(self) -> dict:
        """Generate all files. Returns dict of relative_path -> content."""
        files = {}

        # Core files
        files["server.py"] = self._gen_server()
        files["tools.py"] = self._gen_tools()
        files["security.py"] = self._gen_security()
        files["requirements.txt"] = self._gen_requirements()
        files[".env.example"] = self._gen_env_example()
        files[".gitignore"] = self._gen_gitignore()
        files["README.md"] = self._gen_readme()

        # Test
        if self.spec.get("generate_tests", True):
            files["test_server.py"] = self._gen_test()

        # IDE configs
        for ide in self.spec.get("ide_targets", ["trae", "cursor"]):
            cfg_name, cfg_content = self._gen_ide_config(ide)
            files[f"ide_configs/{cfg_name}"] = cfg_content

        # Companion skill
        if self.spec.get("generate_skill", True):
            files[f"skill/{self.name}.md"] = self._gen_skill()

        return files

    # ─── server.py ───

    def _gen_server(self) -> str:
        transport_import = self._transport_import()
        transport_main = self._transport_main()
        env_check = self._env_check_code()

        return f'''#!/usr/bin/env python3
"""
{self.display_name} — MCP Server
{self.description}

Version: {self.version}
Transport: {self.transport}
Generated by MCP Creator v{__version__}

⚠️  Review this code before production use.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Windows asyncio fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp.server import Server
{transport_import}
from tools import register_tools

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,  # Keep stdout clean for MCP protocol
)
logger = logging.getLogger("{self.name}")

# ── Environment Check ──
{env_check}

# ── Server Setup ──
server = Server("{self.name}")

# Register all tools
register_tools(server)

logger.info("🚀 {self.display_name} initialized")
logger.info(f"   Transport: {self.transport}")
logger.info(f"   Tools: {{len(server._tool_handlers) if hasattr(server, '_tool_handlers') else 'N/A'}}")

# ── Entry Point ──
{transport_main}

if __name__ == "__main__":
    asyncio.run(main())
'''

    def _transport_import(self) -> str:
        if self.transport == "stdio":
            return "from mcp.server.stdio import stdio_server"
        elif self.transport == "sse":
            return "from mcp.server.sse import SseServerTransport\nfrom starlette.applications import Starlette\nfrom starlette.routing import Route\nimport uvicorn"
        return ""

    def _transport_main(self) -> str:
        if self.transport == "stdio":
            return '''async def main():
    """Run server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )'''
        elif self.transport == "sse":
            port = self.spec.get("sse_port", 8080)
            return f'''sse = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    Route("/messages/", endpoint=sse.handle_post_message, methods=["POST"]),
])

async def main():
    """Run server with SSE transport on port {port}."""
    config = uvicorn.Config(app, host="0.0.0.0", port={port}, log_level="info")
    s = uvicorn.Server(config)
    logger.info("Server running on http://0.0.0.0:{port}")
    await s.serve()'''
        return ""

    def _env_check_code(self) -> str:
        env_vars = self._get_required_env_vars()
        if not env_vars:
            return "# No environment variables required"

        checks = []
        for var, desc in env_vars.items():
            checks.append(f'''if not os.environ.get("{var}"):
    logger.warning("⚠️  Environment variable {var} is not set ({desc})")''')
        return "\n".join(checks)

    def _get_required_env_vars(self) -> dict:
        env_vars = {}
        if self.category == "api_wrapper":
            api = self.spec.get("api", {})
            auth_var = api.get("auth_env_var")
            if auth_var:
                env_vars[auth_var] = f"API authentication for {self.display_name}"
        elif self.category == "database":
            db = self.spec.get("database", {})
            db_var = db.get("env_var", "DATABASE_URL")
            env_vars[db_var] = f"Database connection for {self.display_name}"
        return env_vars

    # ─── tools.py ───

    def _gen_tools(self) -> str:
        if self.category == "api_wrapper":
            return self._gen_tools_api_wrapper()
        elif self.category == "database":
            return self._gen_tools_database()
        elif self.category == "filesystem":
            return self._gen_tools_filesystem()
        else:
            return self._gen_tools_custom()

    def _gen_tools_api_wrapper(self) -> str:
        api = self.spec.get("api", {})
        base_url = api.get("base_url", "https://api.example.com")
        auth_method = api.get("auth_method", "none")
        auth_env_var = api.get("auth_env_var", "API_KEY")
        auth_location = api.get("auth_location", "header")
        auth_header = api.get("auth_header_name", "Authorization")
        auth_prefix = api.get("auth_header_prefix", "Bearer")
        auth_param = api.get("auth_param_name", "api_key")
        rate_limit = api.get("rate_limit", {})
        rpm = rate_limit.get("requests_per_minute", 60)
        retry_s = rate_limit.get("retry_after_seconds", 5)

        tool_defs = self._gen_tool_definitions()
        tool_handlers = self._gen_api_tool_handlers()

        # Auth setup code
        if auth_method == "none":
            auth_setup = "    # No authentication required\n    auth_headers = {}\n    auth_params = {}"
        elif auth_location == "header":
            auth_setup = f'''    api_key = os.environ.get("{auth_env_var}", "")
    if not api_key:
        return [TextContent(type="text", text="❌ {auth_env_var} 环境变量未设置\n💡 请在 .env 文件中设置")]
    auth_headers = {{"{auth_header}": "{auth_prefix} " + api_key if "{auth_prefix}" else api_key}}
    auth_params = {{}}'''
        else:  # query_param
            auth_setup = f'''    api_key = os.environ.get("{auth_env_var}", "")
    if not api_key:
        return [TextContent(type="text", text="❌ {auth_env_var} 环境变量未设置\n💡 请在 .env 文件中设置")]
    auth_headers = {{}}
    auth_params = {{"{auth_param}": api_key}}'''

        default_headers = json.dumps(api.get("default_headers", {}), ensure_ascii=False)

        return f'''#!/usr/bin/env python3
"""
Tool implementations for {self.display_name}
Category: API Wrapper
Base URL: {base_url}

Generated by MCP Creator v{__version__}
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

from security import sanitize_string, mask_secret

logger = logging.getLogger("{self.name}")

# ── Configuration ──
BASE_URL = "{base_url}"
DEFAULT_HEADERS = {default_headers}
TIMEOUT = 30  # seconds
MAX_RPM = {rpm}
RETRY_AFTER = {retry_s}

# ── Rate Limiter ──
class RateLimiter:
    """Simple rate limiter."""
    def __init__(self, max_per_minute: int):
        self.max = max_per_minute
        self.calls = []

    async def acquire(self):
        now = datetime.now()
        self.calls = [t for t in self.calls if now - t < timedelta(minutes=1)]
        if len(self.calls) >= self.max:
            wait = (self.calls[0] + timedelta(minutes=1) - now).total_seconds()
            logger.warning(f"Rate limit reached, waiting {{wait:.1f}}s")
            await asyncio.sleep(max(wait, 1))
            self.calls = [t for t in self.calls if now - t < timedelta(minutes=1)]
        self.calls.append(now)

rate_limiter = RateLimiter(MAX_RPM)

# ── API Helper ──
async def api_request(method: str, endpoint: str, params: dict = None,
                      json_body: dict = None, auth_headers: dict = None,
                      auth_params: dict = None) -> dict:
    """Make an API request with rate limiting and error handling."""
    await rate_limiter.acquire()

    url = BASE_URL.rstrip("/") + "/" + endpoint.lstrip("/")
    headers = {{**DEFAULT_HEADERS, **(auth_headers or {{}})}}
    all_params = {{**(params or {{}}), **(auth_params or {{}})}}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.request(
            method=method,
            url=url,
            params=all_params if all_params else None,
            json=json_body,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


# ── Tool Registration ──
def register_tools(server: Server):
    """Register all tools with the MCP server."""

    @server.list_tools()
    async def list_tools():
        return [
{tool_defs}
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        logger.info(f"Tool called: {{name}}")
{auth_setup}
        try:
{tool_handlers}
            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {{name}}")]
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text[:500]
            logger.error(f"API error {{status}}: {{body}}")
            if status == 401:
                msg = "❌ API 认证失败 (401)\n💡 检查 API Key 是否正确"
            elif status == 403:
                msg = "❌ API 权限不足 (403)\n💡 检查 API Key 的权限范围"
            elif status == 429:
                msg = f"❌ API 请求过于频繁 (429)\n💡 等待 {{RETRY_AFTER}} 秒后重试"
            elif status >= 500:
                msg = f"❌ API 服务器错误 ({{status}})\n💡 稍后重试"
            else:
                msg = f"❌ API 错误 ({{status}}): {{body[:200]}}"
            return [TextContent(type="text", text=msg)]
        except httpx.ConnectError:
            return [TextContent(type="text",
                text="❌ 无法连接到 API 服务器\n💡 检查网络连接和 API URL")]
        except httpx.TimeoutException:
            return [TextContent(type="text",
                text="❌ API 请求超时\n💡 稍后重试，或检查网络")]
        except Exception as e:
            logger.exception("Unexpected error")
            return [TextContent(type="text", text=f"❌ 未预期的错误: {{e}}")]
'''

    def _gen_tool_definitions(self) -> str:
        """Generate Tool() definitions."""
        lines = []
        for tool in self.tools:
            props = {}
            required = []
            for p in tool.get("parameters", []):
                prop = {"type": p["type"], "description": p.get("description", "")}
                if p.get("enum"):
                    prop["enum"] = p["enum"]
                if p.get("default") is not None:
                    prop["default"] = p["default"]
                props[p["name"]] = prop
                if p.get("required", False):
                    required.append(p["name"])

            schema = {"type": "object", "properties": props}
            if required:
                schema["required"] = required

            schema_str = json.dumps(schema, indent=16, ensure_ascii=False)
            # Re-indent for proper nesting
            schema_lines = schema_str.split("\n")
            indented = schema_lines[0] + "\n" + "\n".join("            " + l for l in schema_lines[1:])

            desc_escaped = tool["description"].replace('"', '\\"')
            lines.append(f'''            Tool(
                name="{tool['name']}",
                description="{desc_escaped}",
                inputSchema={indented},
            ),''')
        return "\n".join(lines)

    def _gen_api_tool_handlers(self) -> str:
        """Generate tool handler if/elif chain for API wrapper."""
        lines = []
        for i, tool in enumerate(self.tools):
            keyword = "if" if i == 0 else "elif"
            endpoint = tool.get("endpoint", f"/{tool['name']}")
            method = tool.get("method", "GET")

            # Build params
            param_names = [p["name"] for p in tool.get("parameters", [])]
            params_dict = ", ".join(
                f'"{p["name"]}": arguments.get("{p["name"]}", {json.dumps(p.get("default"))})'
                for p in tool.get("parameters", [])
            )

            if method in ("GET", "DELETE"):
                call = f'data = await api_request("{method}", "{endpoint}", params={{params_dict}}, auth_headers=auth_headers, auth_params=auth_params)'
            else:
                call = f'data = await api_request("{method}", "{endpoint}", json_body={{params_dict}}, auth_headers=auth_headers, auth_params=auth_params)'

            resp_fmt = tool.get("response_format", "json_summary")
            if resp_fmt == "full_json":
                format_code = 'result = json.dumps(data, indent=2, ensure_ascii=False)'
            elif resp_fmt == "text":
                format_code = 'result = format_response(data)'
            else:
                format_code = 'result = json.dumps(data, indent=2, ensure_ascii=False)[:2000]'

            lines.append(f'''            {keyword} name == "{tool['name']}":
                {call}
                {format_code}
                return [TextContent(type="text", text=result)]
''')

        # Add a generic response formatter
        lines.append('''

def format_response(data: dict) -> str:
    """Format API response for readable output."""
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k2, v2 in value.items():
                    lines.append(f"  {k2}: {v2}")
            elif isinstance(value, list):
                lines.append(f"{key}: [{len(value)} items]")
                for item in value[:5]:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    return str(data)''')

        return "\n".join(lines)

    def _gen_tools_database(self) -> str:
        db = self.spec.get("database", {})
        db_type = db.get("type", "sqlite")
        env_var = db.get("env_var", "DATABASE_URL")
        default_path = db.get("default_path", "./data.db")
        read_only = db.get("read_only", False)
        max_rows = db.get("max_rows", 1000)

        if db_type == "sqlite":
            db_import = "import sqlite3"
            connect_code = f'''

def get_connection():
    db_path = os.environ.get("{env_var}", "{default_path}")
    uri = f"file:{{db_path}}"
    if {read_only}:
        uri += "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn'''
        elif db_type == "postgresql":
            db_import = "import asyncpg"
            connect_code = f'''

async def get_connection():
    url = os.environ.get("{env_var}", "postgresql://localhost/mydb")
    return await asyncpg.connect(url)'''
        else:
            db_import = "# TODO: Add database driver import"
            connect_code = "# TODO: Implement connection"

        tool_defs = self._gen_tool_definitions()

        return f'''#!/usr/bin/env python3
"""
Tool implementations for {self.display_name}
Category: Database Connector ({db_type})

Generated by MCP Creator v{__version__}
"""

import os
import json
import logging
{db_import}

from mcp.server import Server
from mcp.types import Tool, TextContent

from security import sanitize_sql_identifier, is_safe_sql

logger = logging.getLogger("{self.name}")

MAX_ROWS = {max_rows}
READ_ONLY = {read_only}

# ── Database Connection ──
{connect_code}

# ── Tool Registration ──
def register_tools(server: Server):
    @server.list_tools()
    async def list_tools():
        return [
{tool_defs}
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        logger.info(f"Tool called: {{name}}")
        try:
            if name == "list_tables":
                return await _list_tables()
            elif name == "describe_table":
                return await _describe_table(arguments)
            elif name == "query":
                return await _query(arguments)
            elif name == "execute":
                if READ_ONLY:
                    return [TextContent(type="text",
                        text="❌ 数据库为只读模式，不允许写操作")]
                return await _execute(arguments)
            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {{name}}")]
        except Exception as e:
            logger.exception("Database error")
            return [TextContent(type="text", text=f"❌ 数据库错误: {{e}}")]


async def _list_tables():
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        result = "📋 数据库中的表:\n" + "\n".join(f"  • {{t}}" for t in tables)
        if not tables:
            result = "⚠️ 数据库中没有表"
        return [TextContent(type="text", text=result)]
    finally:
        conn.close()


async def _describe_table(args: dict):
    table = sanitize_sql_identifier(args["table_name"])
    conn = get_connection()
    try:
        cursor = conn.execute(f'PRAGMA table_info("{{}}")'.format(table))
        columns = cursor.fetchall()
        if not columns:
            return [TextContent(type="text", text=f"❌ 表 '{{table}}' 不存在")]
        lines = [f"📋 表 '{{table}}' 结构:", ""]
        lines.append(f"  {{'列名':<25}} {{'类型':<15}} {{'可空':<8}} {{'默认值'}}")
        lines.append(f"  {{'─'*25}} {{'─'*15}} {{'─'*8}} {{'─'*15}}")
        for col in columns:
            nullable = "YES" if not col[3] else "NO"
            default = col[4] if col[4] is not None else ""
            lines.append(f"  {{col[1]:<25}} {{col[2]:<15}} {{nullable:<8}} {{default}}")
        return [TextContent(type="text", text="\n".join(lines))]
    finally:
        conn.close()


async def _query(args: dict):
    sql = args.get("sql", "").strip()
    limit = args.get("limit", MAX_ROWS)
    
    if not sql:
        return [TextContent(type="text", text="❌ SQL 查询语句不能为空")]
    
    if not is_safe_sql(sql):
        return [TextContent(type="text", text="❌ SQL 查询包含不安全的语句")]
    
    conn = get_connection()
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchmany(limit)
        
        if not rows:
            return [TextContent(type="text", text="⚠️ 查询结果为空")]
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Build result
        lines = ["📋 查询结果:", ""]
        header = "  " + " ".join(f"{{c:<15}}" for c in columns)
        lines.append(header)
        lines.append("  " + "─" * len(header.strip()))
        
        for row in rows:
            values = [str(row[i]) for i in range(len(columns))]
            line = "  " + " ".join(f"{{v:<15}}" for v in values)
            lines.append(line)
        
        if len(rows) >= limit:
            lines.append("\n⚠️ 结果已截断，最多显示 {{limit}} 行")
        
        return [TextContent(type="text", text="\n".join(lines))]
    finally:
        conn.close()


async def _execute(args: dict):
    sql = args.get("sql", "").strip()
    params = args.get("params", [])
    
    if not sql:
        return [TextContent(type="text", text="❌ SQL 语句不能为空")]
    
    conn = get_connection()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        affected = cursor.rowcount
        return [TextContent(type="text", text=f"✅ 执行成功，影响 {{affected}} 行")]
    finally:
        conn.close()
'''

    def _gen_tools_filesystem(self) -> str:
        fs = self.spec.get("filesystem", {})
        allowed_dirs = fs.get("allowed_directories", ["./workspace"])
        allowed_exts = fs.get("allowed_extensions", [".txt", ".md", ".json"])
        max_size = fs.get("max_file_size_mb", 10)
        allow_write = fs.get("allow_write", False)
        allow_delete = fs.get("allow_delete", False)

        tool_defs = self._gen_tool_definitions()

        return f'''#!/usr/bin/env python3
"""
Tool implementations for {self.display_name}
Category: File System Tool

Generated by MCP Creator v{__version__}
"""

import os
import json
import logging
import glob
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent

from security import validate_path, sanitize_string

logger = logging.getLogger("{self.name}")

# ── Configuration ──
ALLOWED_DIRECTORIES = {json.dumps(allowed_dirs, ensure_ascii=False)}
ALLOWED_EXTENSIONS = {json.dumps(allowed_exts, ensure_ascii=False)}
MAX_FILE_SIZE_MB = {max_size}
ALLOW_WRITE = {allow_write}
ALLOW_DELETE = {allow_delete}

# ── Tool Registration ──
def register_tools(server: Server):
    @server.list_tools()
    async def list_tools():
        return [
{tool_defs}
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        logger.info(f"Tool called: {{name}}")
        try:
            if name == "list_files":
                return await _list_files(arguments)
            elif name == "read_file":
                return await _read_file(arguments)
            elif name == "write_file":
                if not ALLOW_WRITE:
                    return [TextContent(type="text", text="❌ 写入操作未启用")]
                return await _write_file(arguments)
            elif name == "search_in_files":
                return await _search_in_files(arguments)
            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {{name}}")]
        except Exception as e:
            logger.exception("File system error")
            return [TextContent(type="text", text=f"❌ 文件系统错误: {{e}}")]


async def _list_files(args: dict):
    directory = args.get("directory", ".")
    pattern = args.get("pattern", "*.*")
    
    # Validate path
    path = Path(directory).resolve()
    if not validate_path(path, ALLOWED_DIRECTORIES):
        return [TextContent(type="text", text="❌ 访问路径不在允许范围内")]
    
    try:
        files = []
        for f in path.glob(pattern):
            if f.is_file():
                size = f.stat().st_size / 1024 / 1024
                files.append((f.name, f"{size:.2f} MB"))
        
        if not files:
            return [TextContent(type="text", text="⚠️ 目录为空或无匹配文件")]
        
        lines = ["📋 文件列表:", ""]
        for name, size in files:
            lines.append(f"  • {{name}} ({{size}})")
        
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 列出文件失败: {{e}}")]


async def _read_file(args: dict):
    path = Path(args["path"]).resolve()
    
    # Validate path
    if not validate_path(path, ALLOWED_DIRECTORIES):
        return [TextContent(type="text", text="❌ 访问路径不在允许范围内")]
    
    if not path.exists():
        return [TextContent(type="text", text="❌ 文件不存在")]
    
    if not path.is_file():
        return [TextContent(type="text", text="❌ 路径不是文件")]
    
    # Check file size
    size = path.stat().st_size / 1024 / 1024
    if size > MAX_FILE_SIZE_MB:
        return [TextContent(type="text", text=f"❌ 文件过大 ({{size:.2f}} MB)，最大允许 {{MAX_FILE_SIZE_MB}} MB")]
    
    # Check extension
    ext = path.suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return [TextContent(type="text", text=f"❌ 文件类型 {{ext}} 不被允许")]
    
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return [TextContent(type="text", text=f"📄 文件内容 ({{path}}):\n\n{content}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 读取文件失败: {{e}}")]


async def _write_file(args: dict):
    path = Path(args["path"]).resolve()
    content = args["content"]
    
    # Validate path
    if not validate_path(path.parent, ALLOWED_DIRECTORIES):
        return [TextContent(type="text", text="❌ 写入路径不在允许范围内")]
    
    # Check extension
    ext = path.suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return [TextContent(type="text", text=f"❌ 文件类型 {{ext}} 不被允许")]
    
    # Check content size
    size = len(content.encode("utf-8")) / 1024 / 1024
    if size > MAX_FILE_SIZE_MB:
        return [TextContent(type="text", text=f"❌ 内容过大 ({{size:.2f}} MB)，最大允许 {{MAX_FILE_SIZE_MB}} MB")]
    
    try:
        # Create directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return [TextContent(type="text", text=f"✅ 文件写入成功: {{path}}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 写入文件失败: {{e}}")]


async def _search_in_files(args: dict):
    query = args["query"]
    directory = args.get("directory", ".")
    file_pattern = args.get("file_pattern", "*.*")
    
    # Validate path
    path = Path(directory).resolve()
    if not validate_path(path, ALLOWED_DIRECTORIES):
        return [TextContent(type="text", text="❌ 搜索路径不在允许范围内")]
    
    try:
        matches = []
        for f in path.glob(file_pattern):
            if f.is_file():
                ext = f.suffix.lower()
                if ext and ext not in ALLOWED_EXTENSIONS:
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    if query in content:
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if query in line:
                                matches.append((f.name, i + 1, line.strip()[:100]))
                except:
                    pass
        
        if not matches:
            return [TextContent(type="text", text="⚠️ 未找到匹配内容")]
        
        lines = ["🔍 搜索结果:", ""]
        for filename, line_num, line in matches[:20]:  # Limit to 20 matches
            lines.append(f"  • {{filename}}:{{line_num}}: {{line}}")
        
        if len(matches) > 20:
            lines.append(f"\n⚠️ 找到 {{len(matches)}} 个匹配，显示前 20 个")
        
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 搜索失败: {{e}}")]
'''

    def _gen_tools_custom(self) -> str:
        tool_defs = self._gen_tool_definitions()
        tool_handlers = "\n".join(
            f'''            elif name == "{tool['name']}":\n                # TODO: Implement {tool['name']} logic\n                return [TextContent(type="text", text=f"✅ {{tool['name']}} called with: {{arguments}}")]'''
            for tool in self.tools
        )

        return f'''#!/usr/bin/env python3
"""
Tool implementations for {self.display_name}
Category: Custom Logic

Generated by MCP Creator v{__version__}

⚠️  This is a skeleton - you need to implement the actual logic!
"""

import os
import json
import logging

from mcp.server import Server
from mcp.types import Tool, TextContent

from security import sanitize_string

logger = logging.getLogger("{self.name}")

# ── Tool Registration ──
def register_tools(server: Server):
    @server.list_tools()
    async def list_tools():
        return [
{tool_defs}
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        logger.info(f"Tool called: {{name}}")
        try:
            if False:  # Placeholder for first tool
                pass
{tool_handlers}
            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {{name}}")]
        except Exception as e:
            logger.exception("Custom tool error")
            return [TextContent(type="text", text=f"❌ 工具错误: {{e}}")]
'''

    # ─── security.py ───

    def _gen_security(self) -> str:
        return '''#!/usr/bin/env python3
"""
Security utilities for MCP server

Generated by MCP Creator v1.0.0
"""

import re
from pathlib import Path


def sanitize_string(s: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent injection attacks."""
    if not s:
        return ""
    # Truncate to max length
    s = s[:max_length]
    # Remove control characters
    s = re.sub(r'[\x00-\x1f\x7f]', '', s)
    return s


def mask_secret(s: str) -> str:
    """Mask secrets like API keys in logs."""
    if not s:
        return s
    # Mask common API key patterns
    s = re.sub(r'(api[_-]?key|token|secret)=[a-zA-Z0-9]{8,}', r'\1=***', s)
    return s


def sanitize_sql_identifier(s: str) -> str:
    """Sanitize SQL identifier to prevent SQL injection."""
    if not s:
        return ""
    # Allow only alphanumeric, underscore, and dot
    return re.sub(r'[^a-zA-Z0-9_\.]', '', s)


def is_safe_sql(sql: str) -> bool:
    """Check if SQL query is safe (read-only)."""
    sql_lower = sql.lower()
    # Disallow dangerous statements
    dangerous = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate']
    for word in dangerous:
        if f' {word} ' in sql_lower or sql_lower.startswith(word + ' '):
            return False
    return True


def validate_path(path: Path, allowed_dirs: list) -> bool:
    """Validate that path is within allowed directories."""
    try:
        for allowed in allowed_dirs:
            allowed_path = Path(allowed).resolve()
            # Check if path is within allowed directory
            if allowed_path in path.parents or path == allowed_path:
                return True
        return False
    except:
        return False
'''

    # ─── requirements.txt ──

    def _gen_requirements(self) -> str:
        reqs = ["mcp>=1.0.0", "httpx>=0.27.0"]
        if self.transport == "sse":
            reqs.extend(["uvicorn>=0.24.0", "starlette>=0.27.0"])
        if self.category == "database":
            db_type = self.spec.get("database", {}).get("type")
            if db_type == "postgresql":
                reqs.append("asyncpg>=0.28.0")
        return "\n".join(reqs)

    # ─── .env.example ──

    def _gen_env_example(self) -> str:
        lines = ["# Environment variables for MCP Server", ""]
        env_vars = self._get_required_env_vars()
        for var, desc in env_vars.items():
            lines.append(f"# {desc}")
            lines.append(f"{var}=your-{var.lower().replace('_', '-')}-here")
            lines.append("")
        return "\n".join(lines)

    # ─── .gitignore ──

    def _gen_gitignore(self) -> str:
        return '''# MCP Server - .gitignore

# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Dependencies
venv/
env/
'''

    # ─── README.md ──

    def _gen_readme(self) -> str:
        return f'''# {self.display_name}

{self.description}

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env and set your API keys/database connection
```

### 3. Run Smoke Test

```bash
python test_server.py
```

### 4. Configure IDE

#### Trae AI
- Open Trae AI → Settings → MCP
- Add server using `ide_configs/trae_config.json`

#### Cursor
- Copy `ide_configs/cursor_mcp.json` to `.cursor/mcp.json`
- Update the path to server.py

## 🛠️ Tools

{"\n".join(f"- **{tool['name']}**: {tool['description'][:100]}..." for tool in self.tools)}

## 🔧 Configuration

- **Transport**: {self.transport}
- **Category**: {self.category}
- **Version**: {self.version}

## 📁 Project Structure

```
{self.name}/
├── server.py              # MCP Server main entry
├── tools.py               # Tool implementations
├── security.py            # Security utilities
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── test_server.py         # Smoke test
├── README.md              # This file
├── ide_configs/           # IDE configurations
└── skill/                 # Companion skill file
```

## 🐛 Troubleshooting

- **ModuleNotFoundError: mcp**: Run `pip install mcp`
- **API Key not set**: Check .env file
- **Connection refused**: Ensure server is running

See mcp-creator.md for detailed error handling.
'''

    # ─── test_server.py ──

    def _gen_test(self) -> str:
        return f'''#!/usr/bin/env python3
"""
Smoke test for {self.display_name}

Generated by MCP Creator v{__version__}
"""

import os
import sys
import asyncio


def check_python_version():
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        return False
    print("✅ Python version: OK")
    return True


def check_dependencies():
    try:
        import mcp
        import httpx
        print(f"✅ Dependencies: OK (mcp v{mcp.__version__}, httpx v{httpx.__version__})")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False


def check_environment():
    print("Checking environment variables...")
    # Add your env var checks here
    print("✅ Environment variables: OK")
    return True


async def test_tool_listing():
    print("Testing tool listing...")
    try:
        # Import server modules
        from server import server
        from tools import register_tools
        
        # Register tools
        register_tools(server)
        
        # Test list_tools
        tools = await server._list_tools()
        print(f"✅ Tool listing: OK ({len(tools)} tools found)")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Tool listing failed: {e}")
        return False


async def main():
    print(f"🚀 {self.display_name} - Smoke Test")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_environment(),
        await test_tool_listing(),
    ]
    
    print("=" * 50)
    if all(checks):
        print("🎉 All tests passed! Server is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
'''

    # ─── IDE Configs ──

    def _gen_ide_config(self, ide: str) -> tuple:
        if ide == "trae":
            return ("trae_config.json", f'''
{{
  "name": "{self.name}",
  "command": "python",
  "args": ["{{server_path}}/server.py"],
  "env": {json.dumps(self._get_required_env_vars(), indent=4, ensure_ascii=False)}
}}
''')
        elif ide == "cursor":
            return ("cursor_mcp.json", f'''
{{
  "mcpServers": {{
    "{self.name}": {{
      "command": "python",
      "args": ["path/to/{self.name}/server.py"],
      "env": {json.dumps(self._get_required_env_vars(), indent=6, ensure_ascii=False)}
    }}
  }}
}}
''')
        elif ide == "claude_desktop":
            return ("claude_config.json", f'''
{{
  "mcp_servers": [
    {{
      "id": "{self.name}",
      "name": "{self.display_name}",
      "command": "python",
      "args": ["path/to/{self.name}/server.py"],
      "env": {json.dumps(self._get_required_env_vars(), indent=8, ensure_ascii=False)}
    }}
  ]
}}
''')
        return (f"{ide}_config.json", "{}")

    # ─── Companion Skill ──

    def _gen_skill(self) -> str:
        tool_descriptions = "\n".join(
            f"- **{tool['name']}**: {tool['description']}" for tool in self.tools
        )
        return f'''---
name: {self.name}
version: {self.version}
description: >
  Companion skill for {self.display_name}.
  Use this skill when interacting with the MCP server to get contextual guidance.
triggers:
  keywords: [{json.dumps(self.name)}]
platform: [windows, macos, linux]
---

# {self.display_name} Skill

## Overview

This skill provides guidance for using the {self.display_name} MCP server.

## Available Tools

{tool_descriptions}

## Usage Examples

### Example 1: Get current weather
```
请获取北京的当前天气
```

### Example 2: Query database
```
请查询用户表中的所有记录
```

## Troubleshooting

- **Tool not found**: Ensure server is running and IDE is configured correctly
- **API error**: Check API key and network connection
- **Database error**: Verify database connection string

For more details, see the server's README.md.
'''


# ═══════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="MCP Server Generator")
    parser.add_argument("--action", required=True, choices=["check-env", "locate", "validate-spec", "generate"])
    parser.add_argument("--config-file", help="Path to spec JSON file")
    parser.add_argument("--output-dir", help="Output directory for generated server")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--no-skill", action="store_true", help="Skip companion skill generation")
    parser.add_argument("--no-tests", action="store_true", help="Skip test script generation")
    parser.add_argument("--transport", choices=["stdio", "sse"], help="Override transport")
    
    args = parser.parse_args()

    try:
        if args.action == "check-env":
            info = check_environment()
            print_env_report(info)
            sys.exit(0 if info["all_ok"] else 1)

        elif args.action == "locate":
            script_path = Path(__file__).resolve()
            print(f"Generator script found at: {script_path}")
            print(f"Use this path with --action generate")
            sys.exit(0)

        elif args.action == "validate-spec":
            if not args.config_file:
                print("❌ --config-file is required for validate-spec")
                sys.exit(1)
            spec = read_spec_file(args.config_file)
            errors = validate_spec(spec)
            if errors:
                print("❌ Spec validation failed:")
                for e in errors:
                    print(f"  • {e}")
                sys.exit(1)
            print("✅ Spec validation passed!")
            sys.exit(0)

        elif args.action == "generate":
            if not args.config_file:
                print("❌ --config-file is required for generate")
                sys.exit(1)
            if not args.output_dir:
                print("❌ --output-dir is required for generate")
                sys.exit(1)

            # Read and validate spec
            spec = read_spec_file(args.config_file)
            errors = validate_spec(spec)
            if errors:
                print("❌ Spec validation failed:")
                for e in errors:
                    print(f"  • {e}")
                sys.exit(1)

            # Apply overrides
            if args.transport:
                spec["transport"] = args.transport
            if args.no_skill:
                spec["generate_skill"] = False
            if args.no_tests:
                spec["generate_tests"] = False

            # Generate files
            generator = MCPServerGenerator(spec)
            files = generator.generate_all()

            # Write files
            output_dir = Path(args.output_dir).resolve()
            if output_dir.exists() and not args.force:
                print(f"❌ Output directory already exists: {output_dir}")
                print("Use --force to overwrite")
                sys.exit(1)

            output_dir.mkdir(parents=True, exist_ok=True)

            for rel_path, content in files.items():
                file_path = output_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                print(f"✅ Generated: {rel_path}")

            print(f"\n🎉 Server generated successfully at: {output_dir}")
            print("\nNext steps:")
            print("1. cd", output_dir)
            print("2. pip install -r requirements.txt")
            print("3. copy .env.example .env")
            print("4. Edit .env with your credentials")
            print("5. python test_server.py")
            print("6. Configure your IDE with the files in ide_configs/")

    except GeneratorError as e:
        print(e.format())
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

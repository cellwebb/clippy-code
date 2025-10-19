# PLAN: Integrate MCP (Model Context Protocol) servers into code-with-clippy

Status: Draft
Owner: TBD
Target: vNext (incremental milestones below)

## Goals

- Let Clippy discover and call tools exposed by one or more MCP servers.
- Preserve current OpenAI-native tool-calling flow and safety model.
- Make MCP usage optional and zero-impact when not configured.
- Provide REPL and Document mode affordances to list servers/tools, approve calls, and view results.

## Non-Goals

- Building an MCP server in this repo.
- Replacing existing built-in tools (filesystem, grep, etc.).
- Full cross-provider MCP streaming semantics in initial milestone.

## Background (why MCP)

MCP standardizes how agents discover tools/resources from external services. Clippy already uses OpenAI-format tools. MCP servers expose JSON-Schema tool definitions that map well to OpenAI "function" tools, enabling dynamic tool catalogs without shipping code in the client.

## High-level design

- Introduce an mcp/ package that connects to configured MCP servers, lists tools, and executes tool calls.
- Add a tiny tools/catalog.py to merge built-in tools with MCP-derived tools at runtime.
- Extend permissions with explicit MCP action types and per-server approval controls.
- Keep the agent loop unchanged in spirit, but feed it a dynamic tool list each turn.
- Route tool calls whose names are MCP-qualified to the MCP manager.
- CLI/UI: provide commands to manage servers, list tools, and control approvals.

## Architecture changes

1) New package: src/clippy/mcp/
   - __init__.py: public API exports (Manager, Config, etc.)
   - manager.py: Manager class handling connection, listing tools, execution.
   - config.py: load mcp.json, env expansion, validation.
   - transports.py: stdio now; websocket/http later.
   - schema.py: map MCP JSON Schema to OpenAI tool schema.
   - trust.py: per-server trust store (session, optional persistence).
   - naming.py: helpers for mcp:{server}:{tool} parsing/formatting.
   - errors.py: MCP-specific exceptions.
   - types.py: dataclasses/pydantic models.
   - Optional third-party dependency: `mcp` (model-context-protocol client). ImportError should degrade gracefully.

2) New module: src/clippy/tools/catalog.py
   - API:
     - get_builtin_tools() -> list[dict]
     - get_mcp_tools(mgr: Manager) -> list[dict]
     - get_all_tools(mgr: Manager | None) -> list[dict]
   - Merges built-in tools with MCP tool schemas; leaves built-in __init__.py unchanged.

3) Modify agent loop to use catalog instead of static TOOLS
   - src/clippy/agent/loop.py:
     - from ..tools import catalog as tool_catalog
     - tools = tool_catalog.get_all_tools(mcp_manager)
     - Pass that list to provider.create_message(..., tools=tools)

4) Executor routing additions
   - src/clippy/executor.py: detect mcp: qualified names, route via mcp_manager.execute(...).

5) Permissions
   - src/clippy/permissions.py:
     - New ActionType entries:
       - MCP_LIST_TOOLS (auto-approve)
       - MCP_TOOL_CALL (require_approval by default)
       - MCP_CONNECT (require_approval once per session per server)
     - Ensure PermissionManager supports per-action updates at runtime.

6) Tool naming and routing
   - Use a qualified naming convention to avoid collisions:
     - function name: "mcp:{server_id}:{tool_name}"
   - Description: "MCP tool from {server_id}: {original_description}"
   - Parameters: pass-through JSON Schema from MCP
   - Routing rule:
     - if function name startswith("mcp:"), route to mcp_manager
     - else use builtin executor

7) CLI/UI integration
   - src/clippy/cli/commands.py: add /mcp commands
     - /mcp list        -> list servers and connection status
     - /mcp tools [srv] -> list tools per server
     - /mcp refresh     -> refresh tool catalogs
     - /mcp allow <srv> -> mark server as trusted for this session (sets server trust; see scoping below)
     - /mcp revoke <srv> -> revoke trust for the session
     - /mcp add/remove  -> optional, if we want to edit mcp.json from CLI (nice-to-have)
   - Document mode: reuse existing approval_callback; show server + tool in the prompt and logs.

8) Configuration (JSON only)
   - File name and search path:
     - Repo root: ./mcp.json (optional)
     - User: ~/.clippy/mcp.json (optional)
     - Env: CLIPPY_MCP_CONFIG (absolute or relative path to a JSON file)
   - JSON schema (map style):
     {
       "mcpServers": {
         "<server_id>": {
           "command": "string",
           "args": ["string", ...],
           "env": { "KEY": "VALUE" },          // optional
           "cwd": "string",                      // optional
           "timeout_s": 30                        // optional
         },
         ...
       }
     }
   - Notes:
     - This shape defaults to stdio transport for each server (spawned process via command/args).
     - Support environment variable placeholders in args/env values (e.g., "${PERPLEXITY_API_KEY}").
     - YAML is not supported.

9) Safety model
   - Approvals
     - First connect to an unknown server requires approval (MCP_CONNECT)
     - Listing tools is auto-approved (MCP_LIST_TOOLS)
     - Each tool call requires approval by default (MCP_TOOL_CALL)
     - User can mark a server as trusted for the session via /mcp allow <srv>
   - Visibility: Display server, tool, and arguments prior to execution (like existing tools). Show result previews if textual.
   - Timeouts and size caps on responses; truncate in UI with "view more" hint.
   - Secret hygiene: Recommend env placeholders and never commit raw secrets. Resolve ${VAR} at runtime.

10) Error handling & resilience
   - Connection retries with backoff (reuse tenacity patterns like providers.py)
   - Graceful degradation if a server is down: drop its tools from catalog with a warning
   - Map MCP errors into user-friendly messages

## Detailed implementation plan (by milestone)

M0 — Scaffolding and dynamic tool catalog
- [x] Add mcp/ package skeleton with stubbed Manager.
- [x] Add tools/catalog.py and unit tests.
- [x] Update agent/loop.py to use catalog.
- [x] Keep executor behavior unchanged for now.
- [x] Docs: PLAN.md (this), config skeleton (mcp.json), README notes.

M1 — Single server, list + call happy path
- [x] Implement Manager connect/list/execute for stdio transport.
- [x] Map MCP tool schema -> OpenAI tool schema.
- [x] Add ActionType.MCP_LIST_TOOLS, MCP_TOOL_CALL, MCP_CONNECT.
- [x] Update executor to route mcp:* calls.
- [x] Update tool_handler to show server/tool and use existing approval flow.
- [x] CLI: /mcp list, /mcp tools, /mcp refresh.
- [x] Tests: mock MCP client, end-to-end single call.

M2 — Multi-server and per-server approvals
- [x] Naming: mcp:{server}:{tool}
- [x] PermissionManager: lightweight per-server session state
      - Keep global ActionType but gate approval in Manager by server trust
- [x] CLI: /mcp allow <srv>, /mcp revoke <srv>
- [x] Tests: per-server approval logic.

M3 — UI/document mode enhancements
- [ ] Display diffs/previews when MCP tool affects files through clippy.
- [ ] Approval dialog shows server and arguments, with truncation + expand.
- [ ] Better error panels for MCP failures.

M4 — Additional transports and quality
- [ ] Add websocket/http transport support if available in mcp client.
- [ ] Connection pooling and background refresh.
- [ ] Telemetry/logging improvements with Rich panels.
- [ ] Robust timeouts and cancellation support (propagate InterruptedExceptionError).

## Code changes (files & signatures)

New: src/clippy/mcp/
- __init__.py: public exports (Manager, Config, naming helpers)
- manager.py:
  - class Manager:
    - __init__(config: Config, console: Console | None)
    - start() -> None
    - stop() -> None
    - list_servers() -> list[ServerInfo]
    - list_tools(server_id: str | None = None) -> list[TargetTool]
    - get_all_tools_openai() -> list[dict[str, Any]]  # mapped schemas
    - execute(server_id: str, tool: str, args: dict[str, Any]) -> tuple[bool, str, Any]
    - is_trusted(server_id: str) -> bool
    - set_trusted(server_id: str, trusted: bool) -> None
- config.py:
  - class Config: represents mcp.json; env expansion; validation.
  - load_config(path: str | None = None) -> Config
- transports.py:
  - BaseTransport, StdioTransport; future: WebSocketTransport.
- schema.py:
  - map_mcp_to_openai(mcp_tool: dict) -> dict
- trust.py:
  - in-memory trust store per session; optional persistence helpers.
- naming.py:
  - is_mcp_tool(name: str) -> bool
  - parse_mcp_qualified_name(name: str) -> tuple[str, str]  # server_id, tool
  - format_mcp_tool_name(server_id: str, tool_name: str) -> str
- errors.py:
  - MCP-specific exception hierarchy.
- types.py:
  - Dataclasses for ServerConfig, ServerInfo, TargetTool.

New: src/clippy/tools/catalog.py
- def get_builtin_tools() -> list[dict[str, Any]]
- def get_mcp_tools(mgr: Manager | None) -> list[dict[str, Any]]
- def get_all_tools(mgr: Manager | None) -> list[dict[str, Any]]
- def is_mcp_tool(name: str) -> bool (wrapper; may delegate to mcp.naming)

Modified: src/clippy/agent/loop.py
- Replace `from ..tools import TOOLS` with:
  - from ..tools import catalog as tool_catalog
  - tools = tool_catalog.get_all_tools(mcp_manager)
  - response = provider.create_message(messages=conversation_history, tools=tools, model=model)

Modified: src/clippy/executor.py
- Add branch:
  if tool_name.startswith("mcp:"):
      srv, tool = mcp.naming.parse_mcp_qualified_name(tool_name)
      return mcp_manager.execute(srv, tool, tool_input)

Modified: src/clippy/permissions.py
- Add ActionType.MCP_LIST_TOOLS, MCP_TOOL_CALL, MCP_CONNECT
- Update PermissionConfig defaults: LIST_TOOLS -> AUTO_APPROVE, TOOL_CALL/CONNECT -> REQUIRE_APPROVAL

Modified: src/clippy/agent/tool_handler.py
- Display server/tool for MCP calls
- Approval prompt includes server and arguments
- Use same add_tool_result() pathway

Modified: src/clippy/cli/commands.py
- Add handle_mcp_command(...): list/tools/refresh/allow/revoke
- Wire in handle_command()

Config: mcp.json (search path)
- Repo root: ./mcp.json (optional)
- User: ~/.clippy/mcp.json (optional)
- Env: CLIPPY_MCP_CONFIG (absolute/relative path)

## Schema mapping (MCP -> OpenAI tool)

Given an MCP tool:
- name: "search_docs"
- description: "Search documentation"
- input_schema: JSON Schema

Map to OpenAI tool:
- {
    "type": "function",
    "function": {
      "name": "mcp:{server_id}:search_docs",
      "description": "[MCP {server_id}] Search documentation",
      "parameters": input_schema
    }
  }

## Example mcp.json

{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    },
    "perplexity-ask": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}

## Security considerations

- Server trust model: unknown servers require explicit approval to connect/call.
- Argument echoing: show full arguments in approval prompts; redact values matching secret-like keys (token, password) heuristically.
- Timeouts: default 30s; configurable per server.
- Result size: cap and truncate; keep full in memory only if necessary.
- Sandboxing: MCP servers may perform actions outside clippy. Clarify that approvals govern only the client-side call; servers should be trusted by operator.

## Testing strategy

- Unit tests
  - tools/catalog: merging and naming
  - mcp/*: config loading, env expansion, transport stubs, schema mapping, trust toggles
- Integration tests (mock MCP client)
  - connect/list/tools
  - single tool call success/failure
  - approval flow: denied/allowed/auto-approve
- CLI tests
  - /mcp list/tools/allow/revoke/refresh

## Rollout & migration

- All MCP features disabled by default; if no mcp.json and no dependency, nothing changes.
- Backward compatible: built-in tools and flows unchanged.
- Add README section: "Using MCP servers with Clippy" with quickstart.

## Open questions

- Transport support breadth in initial release (stdio only vs websocket too?).
- How to persist per-server trust beyond session? (Possible: ~/.clippy/mcp_trust.json)
- Should we allow server-level tool filtering (allowlist) in config?

## Acceptance criteria

- With an MCP server configured and running, `clippy -i` can:
  - /mcp list and /mcp tools show available items
  - On user request, the model can select an MCP tool based on the dynamic tool list
  - User sees approval prompt that names the server/tool and arguments
  - On approval, the tool call goes through, returns output, and shows in the conversation
- When no MCP is configured or dependency missing, behavior is identical to today.
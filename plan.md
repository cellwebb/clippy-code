# Clippy Refactoring Plan

High-priority fixes and low-hanging fruit based on code review.

**Status: ✅ All tasks completed** (1092 tests passing)

---

## Critical: Fix Immediately

### 1. Lock vs RLock Bug ✅
**File:** `src/clippy/models.py:404`

**Problem:** Code uses `threading.Lock()` but makes reentrant calls.

**Solution:** Changed to `threading.RLock()`

---

## High Priority

### 2. Narrow Exception Handling ✅
**Files:**
- `src/clippy/agent/core.py:304` - `save_conversation()` → catches `(OSError, IOError, TypeError)`
- `src/clippy/agent/core.py:347` - `load_conversation()` → catches `(OSError, IOError, json.JSONDecodeError)`
- `src/clippy/mcp/config.py` - catches `(OSError, IOError, json.JSONDecodeError, ValueError)`

---

### 3. Consolidate Duplicated `_is_reasoner_model()` ✅
**Solution:** Moved to `src/clippy/llm/utils.py` to avoid circular imports.
- `providers.py` imports from `llm.utils`
- `llm/openai.py` imports from `.utils`

---

## Medium Priority (High Value)

### 4. Create `ToolResult` Dataclass ✅
**File:** `src/clippy/tools/result.py`

Includes helper methods `success_result()` and `failure_result()`.

---

### 5. Replace If-Elif Chain with Dispatch Table ✅
**File:** `src/clippy/executor.py`

Individual handler functions (`_handle_read_file`, `_handle_write_file`, etc.) with `_TOOL_HANDLERS` dispatch table.

---

### 6. Create `AgentLoopConfig` Dataclass ✅
**File:** `src/clippy/agent/loop.py`

**Updated callers:**
- `src/clippy/agent/core.py` - `_run_agent_loop()`
- `src/clippy/agent/subagent.py` - `_run_agent_loop()`

**Updated tests:**
- `tests/agent/test_loop.py` (21 tests)
- `tests/agent/test_multi_tool_sequences.py` (8 tests)
- `tests/agent/test_subagent.py`
- `tests/integration/test_subagent_workflow.py`
- `tests/agent/test_conversation_persistence.py` (exception types)

---

## Tracking

| Task | Status |
|------|--------|
| 1. Lock → RLock | ✅ |
| 2. Narrow exceptions | ✅ |
| 3. Consolidate `_is_reasoner_model` | ✅ |
| 4. `ToolResult` dataclass | ✅ |
| 5. Dispatch table | ✅ |
| 6. `AgentLoopConfig` dataclass | ✅ |

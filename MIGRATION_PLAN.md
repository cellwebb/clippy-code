# Migration Plan: Standardize on OpenAI Format

## Overview

Migrate clippy-code's internal format from Anthropic-style to OpenAI-style for better ecosystem compatibility.

## Current Format (Anthropic-based)

### Tool Definition

```python
{
    "name": "read_file",
    "description": "Read the contents of a file",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "The path to the file"}
        },
        "required": ["path"]
    }
}
```

### Messages (Content Blocks)

```python
# User message
{"role": "user", "content": "Read the file"}

# Assistant with tool use
{
    "role": "assistant",
    "content": [
        {"type": "text", "text": "I'll read that file"},
        {"type": "tool_use", "name": "read_file", "input": {"path": "foo.txt"}, "id": "call_123"}
    ]
}

# Tool result
{
    "role": "user",
    "content": [
        {"type": "tool_result", "tool_use_id": "call_123", "content": "file contents", "is_error": false}
    ]
}
```

### System Prompt

Separate `system` parameter in `create_message()`

---

## Target Format (OpenAI-native)

### Tool Definition

```python
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file"}
            },
            "required": ["path"]
        }
    }
}
```

### Messages (OpenAI Format)

```python
# System message
{"role": "system", "content": "You are a helpful assistant..."}

# User message
{"role": "user", "content": "Read the file"}

# Assistant with tool call
{
    "role": "assistant",
    "content": "I'll read that file",
    "tool_calls": [
        {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": '{"path": "foo.txt"}'  # JSON string!
            }
        }
    ]
}

# Tool result
{"role": "tool", "tool_call_id": "call_123", "content": "file contents"}
```

---

## Migration Steps

### Phase 1: Update Tool Definitions

**File:** `src/clippy/tools.py`

**Change:**

```python
# FROM (Anthropic format):
{
    "name": "read_file",
    "description": "...",
    "input_schema": {...}
}

# TO (OpenAI format):
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "...",
        "parameters": {...}  # Same as input_schema
    }
}
```

**Impact:** All tool definitions (8 tools total)

---

### Phase 2: Update Provider Interface

**File:** `src/clippy/providers.py`

#### 2.1 Update `LLMProvider` abstract class

**Current:**

```python
def create_message(
    self,
    messages: list[dict[str, Any]],  # Anthropic format
    system: str,  # Separate parameter
    tools: list[dict[str, Any]],  # Anthropic format
    ...
) -> LLMResponse
```

**Target:**

```python
def create_message(
    self,
    messages: list[dict[str, Any]],  # OpenAI format (includes system)
    tools: list[dict[str, Any]],  # OpenAI format
    ...
) -> LLMResponse  # Returns OpenAI-native response
```

#### 2.2 Remove intermediate formats

**Remove:**

- `ContentBlockType` enum
- `ContentBlock` dataclass
- `LLMResponse` dataclass (or simplify to just return dict)

**Use:** Native OpenAI response structure directly

---

### Phase 3: Simplify OpenAIProvider

**File:** `src/clippy/providers.py`

**Before:**

```python
class OpenAIProvider(LLMProvider):
    def create_message(self, messages, system, tools, ...):
        # Convert from Anthropic to OpenAI
        openai_messages = self.convert_messages_to_provider_format(messages)
        openai_messages = [{"role": "system", "content": system}] + openai_messages
        openai_tools = self.convert_tools_to_provider_format(tools)

        response = self.client.chat.completions.create(...)

        # Convert response back to Anthropic-style ContentBlocks
        content_blocks = []
        ...
        return LLMResponse(content=content_blocks, ...)
```

**After:**

```python
class OpenAIProvider(LLMProvider):
    def create_message(self, messages, tools, ...):
        # Messages and tools already in OpenAI format - no conversion!
        response = self.client.chat.completions.create(
            messages=messages,
            tools=tools,
            ...
        )

        # Return native OpenAI response (or minimal wrapper)
        return response.choices[0].message
```

**Remove:**

- `convert_messages_to_provider_format()`
- `convert_tools_to_provider_format()`
- All conversion logic

---

### Phase 4: Update AnthropicProvider

**File:** `src/clippy/providers.py`

Now Anthropic becomes the "special case" that needs conversion.

```python
class AnthropicProvider(LLMProvider):
    def create_message(self, messages, tools, ...):
        # Convert FROM OpenAI TO Anthropic format
        anthropic_messages = self._openai_to_anthropic_messages(messages)
        system_prompt = self._extract_system_message(messages)
        anthropic_tools = self._openai_to_anthropic_tools(tools)

        response = self.client.messages.create(
            system=system_prompt,
            messages=anthropic_messages,
            tools=anthropic_tools,
            ...
        )

        # Convert response FROM Anthropic TO OpenAI format
        return self._anthropic_to_openai_response(response)

    def _openai_to_anthropic_messages(self, messages):
        """Convert OpenAI messages to Anthropic content blocks."""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                continue  # Handled separately
            elif msg["role"] == "tool":
                # Convert to tool_result content block
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"]
                    }]
                })
            elif msg.get("tool_calls"):
                # Convert tool_calls to tool_use content blocks
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"])
                    })
                anthropic_messages.append({"role": "assistant", "content": content})
            else:
                # Simple message
                anthropic_messages.append(msg)
        return anthropic_messages

    def _openai_to_anthropic_tools(self, tools):
        """Convert OpenAI tools to Anthropic format."""
        return [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            }
            for tool in tools
        ]

    def _anthropic_to_openai_response(self, response):
        """Convert Anthropic response to OpenAI format."""
        # Build OpenAI-style message
        message = {"role": "assistant"}

        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })

        if text_parts:
            message["content"] = "\n".join(text_parts)
        if tool_calls:
            message["tool_calls"] = tool_calls

        return message
```

---

### Phase 5: Update ClippyAgent

**File:** `src/clippy/agent.py`

#### 5.1 Update conversation history format

```python
# Current (Anthropic content blocks):
self.conversation_history.append({
    "role": "assistant",
    "content": [
        {"type": "text", "text": block.text},
        {"type": "tool_use", "name": block.name, ...}
    ]
})

# Target (OpenAI format):
self.conversation_history.append({
    "role": "assistant",
    "content": "I'll read that file",
    "tool_calls": [{
        "id": "call_123",
        "type": "function",
        "function": {"name": "read_file", "arguments": '{"path": "foo.txt"}'}
    }]
})
```

#### 5.2 Update system prompt handling

```python
# Current:
response = self.provider.create_message(
    messages=self.conversation_history,
    system=self._create_system_prompt(),  # Separate parameter
    tools=TOOLS,
    ...
)

# Target:
# Add system message at start of conversation if not present
if not self.conversation_history or self.conversation_history[0]["role"] != "system":
    self.conversation_history.insert(0, {
        "role": "system",
        "content": self._create_system_prompt()
    })

response = self.provider.create_message(
    messages=self.conversation_history,  # Includes system message
    tools=TOOLS,
    ...
)
```

#### 5.3 Update response processing

```python
# Current (ContentBlock objects):
for block in response.content:
    if block.type == ContentBlockType.TEXT:
        text_response += block.text
    elif block.type == ContentBlockType.TOOL_USE:
        self._handle_tool_use(block.name, block.input, block.id, ...)

# Target (OpenAI message dict):
message = response  # Already a dict

# Handle text content
if message.get("content"):
    self.console.print(message["content"])

# Handle tool calls
if message.get("tool_calls"):
    for tool_call in message["tool_calls"]:
        self._handle_tool_use(
            tool_call["function"]["name"],
            json.loads(tool_call["function"]["arguments"]),  # Parse JSON!
            tool_call["id"],
            ...
        )
```

#### 5.4 Update tool result handling

```python
# Current (Anthropic content block):
self.conversation_history.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": not success
    }]
})

# Target (OpenAI tool message):
self.conversation_history.append({
    "role": "tool",
    "tool_call_id": tool_use_id,
    "content": content
    # Note: OpenAI doesn't have is_error flag, include error in content
})
```

---

### Phase 6: Update Tests

**Files:** `tests/test_*.py`

- Update mock responses to use OpenAI format
- Update assertions to check OpenAI message structure
- Test Anthropic conversion logic thoroughly

---

## Key Considerations

### 1. Tool Arguments as JSON Strings

OpenAI uses JSON strings for tool arguments, need `json.loads()`:

```python
# Before (Anthropic - dict):
tool_input = block.input  # Already a dict

# After (OpenAI - JSON string):
tool_input = json.loads(tool_call["function"]["arguments"])
```

### 2. System Message Handling

- OpenAI: System message in messages array
- Need to inject/maintain at conversation start

### 3. Tool Results

- OpenAI: Separate message with `role: "tool"`
- No built-in error flag (include in content)

### 4. Assistant Messages

- OpenAI: `content` and `tool_calls` are separate fields
- Both can be present in same message

### 5. Stop Reasons

- Map Anthropic's `stop_reason` to OpenAI's `finish_reason`

---

## Benefits After Migration

1. **Simpler codebase**: OpenAIProvider has minimal/no conversion logic
2. **Easier to add providers**: New OpenAI-compatible providers work out-of-box
3. **Better debugging**: Internal format matches most provider docs
4. **Future-proof**: Industry is converging on OpenAI format
5. **Local LLM support**: Easier integration with Ollama, llama.cpp, etc.

---

## Risks & Mitigations

### Risk: Breaking changes

**Mitigation:** Keep existing tests, add new ones for format validation

### Risk: Anthropic conversion bugs

**Mitigation:** Thorough testing of bidirectional conversion, especially tool calls

### Risk: JSON parsing errors

**Mitigation:** Add try/except around `json.loads()` with helpful error messages

### Risk: Lost functionality (e.g., is_error flag)

**Mitigation:** Encode error state in content string format

---

## Testing Strategy

1. **Unit tests**: Test each conversion function independently
2. **Integration tests**: Test full conversation flows with both providers
3. **Format validation**: Ensure messages match OpenAI schema
4. **Error cases**: Test malformed JSON, missing fields, etc.
5. **Backward compatibility**: Ensure existing functionality still works

---

## Implementation Order

1. ✅ Create this migration plan
2. Update tool definitions (`tools.py`)
3. Create new Anthropic conversion functions
4. Update OpenAIProvider (simplify)
5. Update AnthropicProvider (add conversions)
6. Update ClippyAgent (message handling)
7. Update tests
8. Manual testing with both providers
9. Update documentation

---

## Estimated Effort

- **Phase 1 (Tools):** 30 minutes
- **Phase 2-3 (OpenAI):** 1 hour
- **Phase 4 (Anthropic):** 2-3 hours (most complex)
- **Phase 5 (Agent):** 2 hours
- **Phase 6 (Tests):** 2 hours
- **Total:** ~8 hours

---

## Open Questions

1. Should we keep `LLMResponse` wrapper or return raw OpenAI message dict?
2. How to handle provider-specific features (e.g., Anthropic's thinking blocks)?
3. Should we version this change or make it atomic?
4. Do we need migration guide for users with custom providers?

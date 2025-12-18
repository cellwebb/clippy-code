# Changelog

## [2025-12-18] - v0.1.0

### What's New

- You can now pick which AI service (like Anthropic or OpenAI) powers the assistant.

### Improvements

- Added a simple --provider option and CLIPPY_PROVIDER setting so you can switch AI services from the command line or your config file.
- Updated the setup guide and example configuration to show how to configure each AI service and its keys.
- Optional install option lets you add OpenAI support only when you need it, keeping the core light.

---

## [2025-12-18] - v0.2.0

### What's New

- Now works with OpenAI-compatible services (e.g., Azure, Ollama, Cerebras) letting you choose different AI models

### Improvements

- Simplified setup: only one access key is needed, removing extra options
- Help messages are clearer, showing exactly what you need to enter
- Documentation updated with step‑by‑step guides for the new model services

### Bug Fixes

- Fixed a crash that could happen when the tool received malformed data
- Improved handling of unexpected errors during tool actions, so the app no longer freezes
- Removed old files that could cause confusion, keeping only current guides

---

## [2025-12-18] - v0.3.0

### What's New

- Responses now appear live as they’re generated, so you see the answer building in real time.
- Press Escape twice to stop a reply that’s taking too long.
- Switch between different AI services and their presets instantly with simple /model commands, each using its own access key.

### Improvements

- Overall speed and reliability have been improved for a smoother experience.

---

## [2025-12-18] - v0.4.0

### What's New

- New /status feature shows your current token usage and how much of the conversation space is used
- New /compact feature summarizes older chat history to keep conversations short and focused

### Improvements

- Removed the hard‑coded answer length limit, so you receive full responses even for large files
- Added automatic retries for temporary network issues, reducing crashes and improving reliability
- Simplified configuration by dropping the optional length setting and using the service’s default limits

---

## [2025-12-18] - v1.0.0



---

## [2025-12-18] - v1.1.0

### What's New

- New file editor lets you add, replace, delete, or append lines in a file
- A thinking indicator shows when the system is processing so you know it’s working

### Improvements

- Searches now run faster by using a quicker engine when available
- Folder listings clearly mark directories with a trailing slash
- Error messages are clearer and file details now tell you if an item is a folder

### Bug Fixes

- Fixed a security issue that could let the system access unintended folders

---

## [2025-12-18] - v1.1.1

### What's New

- You can now edit files directly within the app

### Improvements

- Search (grep) works more reliably
- Documentation headings are now displayed consistently

### Bug Fixes

- Fixed a crash that could happen when saving conversations due to a missing line break

---

## [2025-12-18] - v1.2.0

### What's New

- New AI options from ZAI, including GLM 4.6 and GLM 4.5 Air, are now available for use

### Improvements

- You can now use the same search options you’re used to from grep, with faster performance
- Wildcard patterns in file paths work more reliably during searches

### Bug Fixes

- Error messages no longer include an extra blank line

---

## [2025-12-18] - v1.3.0

### What's New

- Added a new “/compact” command that summarizes long conversations to save token usage
- Introduced auto‑approval management commands (/auto list, revoke, clear) so you can automatically approve trusted actions
- Added a visual diff preview in the approval dialog, showing exactly what file changes will be made before you confirm

### Improvements

- Redesigned the document interface with a Microsoft‑Word‑style ribbon and a cleaner toolbar layout for easier navigation
- Enhanced the status bar to show a token‑usage bar and a detailed breakdown of messages by type (system, user, assistant, tool)
- Updated the help system with organized sections, keyboard shortcuts, and clearer explanations of commands and toolbar buttons

### Bug Fixes

- Fixed a visual glitch where the paperclip icon could appear on a separate line in document mode
- Made file editing more reliable by adding validation that rolls back changes if an edit fails and enforcing exact pattern matches
- Corrected occasional crashes caused by improper file writing, ensuring files are saved correctly

---

## [2025-12-18] - v1.4.0



---

## [2025-12-18] - v1.4.1

### Improvements

- Conversation view now has a new scrollbar style for a cleaner look

---

## [2025-12-18] - v1.5.0

### What's New

- New block and pattern-based editing options let you replace or delete multiple lines in a file

### Improvements

- File edits now preserve original line breaks and handle tricky cases smoothly
- Tool results are now presented cleanly, showing just the important information
- Setup guides now include more server examples and clearer step‑by‑step instructions

---

## [2025-12-18] - v1.5.1

### What's New

- Trusted users can now run MCP tools without needing to set up server trust, thanks to a new option to skip the verification step

---

## [2025-12-18] - v1.5.2

### Improvements

- Long messages in the console are now formatted for easier reading

### Bug Fixes

- Error messages are now properly escaped to prevent display issues

---

## [2025-12-18] - v1.5.3

### Improvements

- The command-line tool is now called Clippy Code, matching the new branding in help messages and documentation

---

## [2025-12-18] - v1.6.0

### Improvements

- When the system reaches its step limit, you’ll see a clear message with a simple ‘continue’ option.
- Approval prompts now only accept yes, no, or allow, shown clearly, and guide you if you type something else.
- Underlying components have been updated, making the app feel faster and more reliable.

### Bug Fixes

- Fixed a crash that could occur if you entered an invalid response or pressed Ctrl+C during an approval prompt.

---

## [2025-12-18] - v1.7.0

### What's New

- Now shows the folder you’re working in at the top of each document, with long paths shortened for easy reading

### Improvements

- The app keeps a detailed activity record, providing clearer information if something goes wrong

---

## [2025-12-18] - v1.8.0

### What's New

- A spinning icon now shows while the assistant is thinking, so you know it’s working.
- You can now add, remove, and set a default AI model right from the app, plus see which models are available.

### Bug Fixes

- Fixed a problem where special characters could break the chat view, keeping the display clean and safe.

---

## [2025-12-18] - v1.8.1

### Improvements

- Error messages are now hidden from the screen and saved in a log, keeping the terminal tidy
- Helpful guide added to show where to find the hidden error logs for easier troubleshooting
- The app now cleans up its error‑logging resources automatically when it shuts down

---

## [2025-12-18] - v1.8.2

### Improvements

- You now pick a model directly, so the app works exactly the way you expect.
- Setup is simpler with fewer hidden settings to worry about.
- Help guides and example files have been updated to match the new setup process.

---

## [2025-12-18] - v1.9.0

### What's New

- Clippy can now split work among specialized helper agents, offering faster and more focused assistance for tasks like code review, testing, and refactoring
- Multiple helper agents can work at the same time, speeding up large jobs
- You can choose which AI model each helper agent uses and have those preferences saved for future sessions

### Improvements

- Clearer messages show when a helper agent starts, finishes, or runs into a problem, making it easier to follow progress
- Better handling of multi‑line text edits so patterns that end with blank lines are now processed correctly
- Edit tools now support advanced pattern options like start/end markers and regex for more precise changes

### Bug Fixes

- Fixed a crash that could happen when saving files with certain patterns
- Removed unnecessary background processing steps that could cause errors during updates
- Deleted old planning documents and ignored unused folders to keep things clean

---

## [2025-12-18] - v2.0.0

### Improvements

- Find‑and‑replace now works with exact text and a smart matching option that handles minor typos, so edits are more reliable.
- Editing multiple lines at once now removes the entire selected block and keeps the file’s spacing and line endings neat.
- Switching between AI models is now case‑insensitive, rejects empty names, and shows helpful suggestions if a model isn’t found.

### Bug Fixes

- Fixed an issue where deleting multi‑line sections could leave stray blank lines or break the file’s line endings.
- Improved error messages when a pattern appears many times or is written incorrectly, making it clearer what went wrong.

---

## [2025-12-18] - v2.1.0

### What's New

- Automatic conversation summarization when token usage exceeds a configurable threshold, keeping chats fast and affordable

### Improvements

- Directory listings now respect .gitignore files, so hidden folders and files are omitted automatically
- Model switching commands are case‑insensitive and validate names, giving clearer errors if a model isn’t available
- The UI now shows detailed status information, including token counts and current model, with an improved help panel

### Bug Fixes

- Fixed duplicate user messages appearing in interactive mode
- Corrected edit‑file tool to handle multi‑line patterns and trailing newlines reliably
- Escaped special characters in error messages to prevent Rich markup issues

---

## [2025-12-18] - v2.1.1

### Improvements

- Token usage now shows exact limits and where the numbers come from for clearer insight
- Model lookup works even if you use different capitalisation or model IDs, ensuring correct settings are applied
- Status view tells you whether usage is based on a specific threshold or a default estimate

---

## [2025-12-18] - v3.0.1

### What's New

- Tab completion now suggests commands and options as you type
- New Chutes.ai service you can select for tasks
- Start the tool with the new command “clippy-code”

### Improvements

- Tasks can now run up to 100 steps, allowing more complex work
- Provider names are shorter, making them easier to read and pick
- Interactive mode starts automatically when no prompt is given

### Bug Fixes

- Fixed a freeze when using the search tool by correcting recursive flag handling

---

## [2025-12-18] - v3.1.0

### What's New

- You can now use the MiniMax service for additional capabilities directly from the app

### Improvements

- File suggestions are smarter: they appear automatically as you type and you can also press @ to pick recent files, with the list sorted by the most recent changes
- Help now mentions the new @ shortcut, making it easier to discover and use file suggestions

### Bug Fixes

- Fixed garbled characters that sometimes appeared when tool results were shown, so everything displays cleanly

---

## [2025-12-18] - v3.2.0

### What's New

- You can now automatically save your chats and later resume them, with an easy list of past conversations to pick from

### Improvements

- Resuming a chat without a name now shows a simple list so you can choose the right one
- Saved chats are labeled with date and time, making them easy to identify
- Diff results are cleaner, showing only the important changes without extra blank lines

### Bug Fixes

- Fixed a crash that occurred when error messages contained special formatting tags

---

## [2025-12-18] - v3.4.0

### What's New

- Set custom time limit for tasks, with default now five minutes and option for no limit
- Turn MCP servers on or off directly from the command line
- Load a model using a simple “/model load <name>” command

### Improvements

- Commands only appear when relevant, so MCP options show up only if servers are configured
- Command suggestions now understand subcommands and show available models and providers
- Error messages now include the exact timeout value for clearer feedback

### Bug Fixes

- Fixed search when a pattern starts with a dash so it’s treated as text, not a flag
- Fixed occasional markup errors that could cause the display to crash
- Fixed duplicate command handling and improved server cleanup to prevent hangs

---

## [2025-12-18] - v3.5.0

### What's New

- The app now automatically checks the contents of code and data files for errors before saving, covering many common formats
- It can now recognize binary files like images or PDFs and avoid trying to check them, with clear guidance on how to proceed

### Improvements

- You can now choose to skip the file check for large files over 1 MB, making big saves faster
- Error messages are now more detailed and give specific steps to fix problems
- The file‑saving tool’s interface has been tidied up for smoother use

### Bug Fixes

- Fixed a rare crash that could happen when an error occurred during a write operation
- Improved the way the app handles unexpected issues so it won’t leak internal details
- Corrected handling of file‑system errors to prevent confusing prompts

---

## [2025-12-18] - v3.6.0

### What's New

- New collection of real‑world examples showing how to use the tool for web, data science, command‑line, DevOps and more
- New file commands – move, copy and find‑replace – let you manage files directly from the tool
- New project analysis command that scans your code for security issues, dependencies and overall quality

### Improvements

- Model selection panel now displays clearer status and highlights different providers
- Interactive mode now shows progress spinners and provides smarter auto‑completion suggestions
- REPL welcome screen now shows the current model and offers helpful usage tips

### Bug Fixes

- Fixed a problem where the tool always started in interactive mode, allowing it to run correctly in automated scripts

---

## [2025-12-18] - v3.7.0

### What's New

- Find and replace across multiple files with a preview and backup option
- Copy and move files or folders with safety checks and progress view
- New /truncate command to trim conversation history, keeping recent messages

### Improvements

- Tools are now grouped into categories with suggestions, making it easier to discover what you can do
- Help screen reorganized with clearer sections and concise descriptions, placing most used commands first
- Simplified truncate options to just keep recent or keep older messages for a more straightforward experience

---

## [2025-12-18] - v3.7.1

### What's New

- When you enter an unknown command, the app now suggests similar commands to help you find the right one

---

## [2025-12-18] - v4.0.0

### Improvements

- You can now set how much of the conversation the assistant remembers and limit the length of its replies
- The AI integration has been updated for smoother performance and fewer hiccups
- All existing features that use the assistant continue to work just as before

---

## [2025-12-18] - v4.1.0

### What's New

- You can now choose AI from Anthropic or Google Gemini
- HuggingFace AI models are now available

### Improvements

- Choosing AI models with special labels (like “hf:”) works more reliably
- Your custom OpenAI settings (like your own key or URL) are correctly applied to all compatible AI services
- Clearer messages appear when a selected AI model cannot be loaded

### Bug Fixes

- Fixed a problem where AI models with special labels ignored your custom OpenAI settings

---

## [2025-12-18] - v4.2.0

### What's New

- New /init command creates or updates AGENTS.md documentation, with options to refine, force overwrite, and automatically back up existing files

### Bug Fixes

- Removed unwanted blank lines at the start of assistant messages for cleaner display

---

## [2025-12-18] - v4.3.0

### What's New

- New YOLO mode automatically approves actions, letting you work faster without manual confirmations

---

## [2025-12-18] - v4.4.0

### What's New

- New think tool lets the assistant organize its thoughts and plan steps without performing any actions

---

## [2025-12-18] - v4.4.1

### What's New

- A fun ASCII art banner now greets you with a friendly “It looks like you're trying to code!” message.

### Improvements

- The welcome help screen is now shorter and focuses on the most important commands, making it easier for new users.

---

## [2025-12-18] - v4.4.2

### What's New

- Added support for Anthropic service with easy key setup

### Improvements

- Quick start guide moved to the top and simplified for faster onboarding
- Installation steps now show only two clear options, reducing confusion
- New paperclip‑style welcome banner looks cleaner and more friendly

---

## [2025-12-18] - v4.4.3

### Improvements

- Updated to version 4.4.3 with security and stability improvements

---

## [2025-12-18] - v4.6.0



---

## [2025-12-18] - v4.7.0

### What's New

- You can now pull information from web pages directly into the app
- Press Ctrl+J to write multi-line commands in interactive mode

### Improvements

- Agents can now run without a set step limit, letting them finish tasks without interruption

### Bug Fixes

- Safety fix: directory browsing no longer goes into subfolders unexpectedly

---

## [2025-12-18] - v4.8.0



---

## [2025-12-18] - v4.9.0

### What's New

- Added automatic detection and recovery for stuck subagents during parallel tasks, keeping work safe and giving clear reports

### Improvements

- Simplified command options by removing the unused dream mode flag
- Faster and more reliable display of messages with smoother start‑up greetings
- Restored the ability to browse folders recursively when listing files

### Bug Fixes

- Fixed errors that stopped conversations when using the ZAI model after automatic shortening
- Corrected missing settings in the stuck‑subagent detection presets
- Resolved memory problems that could cause the app to slow down or freeze during long chats

---

## [2025-12-18] - v4.9.1

### Improvements

- Simplified the interface by removing the vaporwave theme and related visual effects for a cleaner, more focused experience

---

## [2025-12-18] - v4.9.2

### Improvements

- You can now set a maximum number of attempts for parallel helpers, with the ability to adjust it for each helper individually.

### Bug Fixes

- Fixed a problem that could cause the app to freeze during parallel operations.

---

## [2025-12-18] - v4.10.0

### What's New

- Added automatic shortening of overly long results with clear warnings, so you won’t see overwhelming output.

### Improvements

- Summaries are now formatted with clearer markers, making them easier to read.
- Documentation now offers a quick‑start guide and separate details for advanced integrations, helping you get started faster.

---

## [2025-12-18] - v4.11.0

### What's New

- You can now create custom shortcuts and automations with a new custom command system
- A new read_lines tool lets you quickly view specific line ranges in any file

### Improvements

- The help screen now lists your custom shortcuts and gives clearer guidance
- Command handling is organized into separate sections, making the app more reliable and faster
- Model manager now lets you switch models easily and see a full list of available models

---

## [2025-12-18] - v4.12.0

### What's New

- Subagents can now automatically approve certain tools, so they can act without waiting for manual permission.

### Improvements

- Dangerous command patterns are blocked and file edits now require verification, keeping your work safer.
- Tool descriptions have been shortened and clarified, making it quicker to understand what each tool does.
- The system’s internal prompt has been trimmed, helping the app respond faster.

---

## [2025-12-18] - v4.13.0



---

## [2025-12-18] - v4.14.0

### What's New

- New first‑time setup wizard that walks you through picking an AI service, entering your access key and selecting a model.

### Improvements

- The app now starts without a preset model, so you’ll be guided to choose the one you want.
- Error messages now direct you to the new setup wizard when no models are configured.

---

## [2025-12-18] - v4.15.0

### What's New

- Added DeepSeek as a new AI provider option
- Introduced a read‑lines tool for extracting specific lines from files

### Improvements

- Model switching now works per session with a simple “/model <name>” shortcut and clearer help
- Provider commands are now consistent (use “/provider list”) and help texts updated
- Model list now shows a tidy table with icons for the current and default models

### Bug Fixes

- Fixed the misaligned ASCII art in the welcome screen of the interactive console

---

## [2025-12-18] - v4.16.0



---

## [2025-12-18] - v4.17.0

### What's New

- Added support for four new AI services (Groq, Mistral AI, Together AI, Minimax AI) so you can choose from more providers

### Improvements

- Auto‑complete now suggests model names for all model commands, making it easier to pick the right model
- Command execution is now safer with built‑in checks that block dangerous actions and a five‑minute timeout
- The app runs more smoothly when multiple tasks run at once, thanks to better handling of shared resources and faster look‑ups

### Bug Fixes

- Clearer messages when a provider is missing, guiding you to add it with a simple command
- Fixed occasional freezes by ensuring background tasks shut down cleanly with proper time limits
- Fixed crashes caused by unsafe command handling and improved error messages for connection and timeout problems

---

## [2025-12-18] - v4.17.1

### What's New

- New option to hide or show command output, giving you control over what you see
- New settings let you set command timeout and limit the length of tool results

### Improvements

- More reliable command behavior thanks to extensive testing of the new settings

---

## [2025-12-18] - v4.17.2

### Improvements

- Shutdown is now more reliable with a configurable timeout, reducing chances of hanging when the app closes

---

## [2025-12-18] - v4.17.3

### What's New

- Assistant replies now appear in the chat with clear formatting and a friendly emoji indicator

### Improvements

- Unwanted blank lines are removed from responses for cleaner reading
- Assistant messages are highlighted with a colored emoji for quick identification

---

## [2025-12-18] - v4.17.4

### Improvements

- Better stability when the same operation runs repeatedly, preventing occasional hangs.
- More precise error handling when saving or loading conversations and settings, reducing unexpected crashes.
- Clearer success or failure messages from built-in tools, helping you understand what happened.

### Bug Fixes

- Fixed a rare issue that could cause the app to stop responding during complex tasks.
- Resolved occasional errors when loading configuration files that were slightly malformed.
- Prevented rare deadlock situations that could freeze the app when multiple actions overlapped.

---

## [2025-12-18] - v4.18.0

### What's New

- New quick‑start command sets up default models automatically, so you can start working right away

### Improvements

- Model list now clearly shows which models are built‑in and which you added yourself
- Tool results are displayed more clearly, and error messages are easier to understand
- Saving and loading conversations handles file problems more smoothly, reducing unexpected stops

### Bug Fixes

- Fixed a crash that could happen when loading a saved conversation with bad data
- Fixed occasional freezing when the app tried to process certain tool actions
- Improved handling of missing or malformed configuration files to prevent startup errors

---

## [2025-12-18] - v4.18.1

### What's New

- A new column now shows the built‑in indicator separately, making it easier to see at a glance.

### Improvements

- Help messages for model commands are clearer and better organized.
- When typing, the app now suggests model names for the remove and threshold actions, speeding up work.
- The shortcut for viewing services has been renamed and the command list reordered for quicker navigation.

### Bug Fixes

- File searches now handle all path formats correctly, preventing missed or failed results.

---

## [2025-12-18] - v4.19.0

### What's New

- AI‑powered safety assistant that automatically blocks risky commands before they run

### Improvements

- Safety checks work automatically whenever the app can use AI
- More reliable handling of commands in different folders

---

## [2025-12-18] - v4.19.1

### What's New

- Safety checks now use a cache, so they respond faster
- You can turn the safety cache on or off and set its size and how long it remembers results

### Improvements

- Cache performance stats let you see how often safety checks are saved
- Added a simple demo and clear instructions on how to use the safety cache

---

## [2025-12-18] - v4.19.2

### Improvements

- Safety checks are now more forgiving: common development tools (ruff, pytest, make, etc.) are allowed even if a safety warning occurs, and you can enable or disable the safety checker with a simple setting.
- First‑time setup automatically loads model information from a configuration file, so the correct AI model is selected without extra steps.
- The default AI model has been updated to the newer gpt‑5‑mini, providing quicker and more accurate responses.

### Bug Fixes

- Fixed an issue where requesting lines outside the file’s range caused a crash; now you receive a clear error message instead.

---

## [2025-12-18] - v4.19.3

### What's New

- You can now choose which AI model is used for safety checks, giving you more control over the results

### Improvements

- Safety checks update instantly when you change the model, so you always get current advice
- Old safety decisions are cleared automatically when you switch models, preventing outdated warnings

---

## [2025-12-18] - v4.19.4

### What's New

- New safety command lets you turn safety checks on or off, view the current status, and get help directly in the tool

### Improvements

- Added extensive new guides for migration, performance tuning, advanced setup, best practices, troubleshooting, and use‑case recipes, all linked from the main help page

---

## [2025-12-18] - 4.19.4

### What's New

- You can now turn the safety checker on or off and choose which AI model it uses
- A new /safety command lets you quickly enable, disable, or view the status of safety checks
- Safety checks are now remembered, making responses faster and reducing unnecessary work

### Improvements

- Reading files now gives clearer error messages if you request a line range that doesn’t exist
- Safety checks now allow common development tools even when a rule is triggered, so your workflow isn’t stopped unexpectedly

### Bug Fixes

- Fixed a crash that could happen when trying to read lines beyond the end of a file

---

## [2025-12-18] - v4.20.0

### What's New

- New 'grepper' assistant that can scan code and files for patterns without making any changes

### Improvements

- Agents can now run up to 100 steps, allowing more complex tasks without hitting limits
- Stuck task detection is more reliable, reducing chances of the app freezing
- Provider setup guide is clearer, making it easier to connect to services like DeepSeek and Google Gemini

### Bug Fixes

- Fixed issue where requesting lines beyond a file’s length caused crashes; now returns available lines or a clear error

---

## [2025-12-18] - v4.20.1

### Bug Fixes

- Fixed issues where selecting line ranges could give incorrect results, especially with negative numbers or ranges that go beyond the file

---

## [2025-12-18] - v4.20.2

### What's New

- Six new specialist assistants (architect, debugger, security, performance, integrator, researcher) let you get focused help for specific tasks
- Status screen now shows how many tokens have been used and an estimate of cost, so you can track usage

### Improvements

- You can now choose the model you want for assistants, giving you more control
- Assistant command now shows a clear table and easier navigation
- File deletion command is safer, preventing accidental removal of important files

### Bug Fixes

- Fixed a bug that counted token usage twice, giving more accurate usage stats
- Fixed a crash when using the assistant command without arguments
- Corrected token tracking to only count new usage per request

---

## [2025-12-18] - v4.21.0

### Improvements

- All replies are now streamed instantly, giving you real‑time responses as they’re generated
- No extra settings needed – streaming works automatically without extra configuration
- Live updates are more reliable thanks to stronger error handling

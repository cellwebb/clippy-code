# Changelog

## [4.19.4] - 2025-12-09

### What's New

- New safety control commands to turn checks on/off and view status
- Quickly toggle safety checks while the app is running

### Improvements

- Comprehensive documentation including best practices, troubleshooting, and migration guides
- Better test coverage for safety integration features

## [4.19.3] - 2025-12-09

### What's New

- Choose which AI model checks command safety for more control

### Improvements

- Safety checks now use configurable models for better flexibility
- Command cache clears automatically when switching safety models

## [4.19.2] - 2025-12-09

### Improvements

- Updated default AI model to gpt-5-mini for better performance
- Enhanced command safety checker to be smarter about development workflows
- Improved first-time setup to use model configurations dynamically
- Better error handling when reading file lines with invalid ranges

### Bug Fixes

- Fixed crashes when requesting lines outside file boundaries

## [4.19.1] - 2025-12-09

### Improvements

- Command safety checks now use caching for faster performance
- Safety cache settings can be configured to reduce unnecessary checks
- Added example scripts showing cache performance benefits

## [4.19.0] - 2025-12-09

### What's New

- New intelligent safety agent protects you from dangerous commands by analyzing them before execution

### Improvements

- Better protection against harmful commands with automatic safety checking when AI provider is available
- Enhanced security documentation with detailed examples and troubleshooting guides

## [4.18.1] - 2025-12-09

### Added

- New command completion for /model remove and /model threshold commands

### Changed

- Improve model command help text formatting and organization
- Separate built-in indicator into dedicated column in model list display
- Update provider reference from /providers to /provider list
- Streamline version bumping process with git tag automation and pre-bump validation

### Fixed

- Resolve path handling issues in find_replace tool for absolute and relative glob patterns

## [4.18.0] - 2025-12-09

### What's New

- /model init command helps new users get started with default models
- Built-in model configurations for all providers

### Improvements

- Better code organization and reliability
- Cleaner model management with built-in and user-defined models
- Improved error handling for file operations

### Bug Fixes

- Fixed JSON loading error handling
- Removed redundant error handling in file operations

## [4.17.4] - 2025-12-09

### Improvements

- Better reliability with improved threading for complex operations
- More organized code structure for better performance and stability
- Enhanced error handling with specific exceptions for file operations
- Cleaner tool management with improved result handling
- Better model detection with shared utility functions

## [4.17.3] - 2025-12-07

### Improvements

- Assistant responses now display with better formatting and visual indicators
- Cleaner text display by removing extra blank lines from responses

## [4.17.2] - 2025-12-07

### Improvements

- App now shuts down more reliably with configurable cleanup timing
- Tests run significantly faster while maintaining accuracy

### Bug Fixes

- More reliable monitoring and cleanup of background tasks

## [4.17.1] - 2025-12-07

### Improvements

- Control command output visibility with new settings option
- Set custom timeouts for command execution
- Better test coverage with multiple report formats
- Comprehensive changelog documenting complete project history

## [4.17.0] - 2025-12-06

### What's New

- Added support for Groq, Mistral AI, Together AI, and Minimax AI providers

### Improvements

- Enhanced model command completion for better tab suggestions
- Better error messages when provider configuration is missing
- More reliable app performance with improved thread safety
- Enhanced security with protection against dangerous commands

### Bug Fixes

- Fixed security vulnerability preventing shell injection attacks
- Improved command execution reliability with better timeout handling

## [4.16.0] - 2025-12-02

### What's New

- Enhanced security with path validation for file operations

### Improvements

- Better error handling for external integrations
- Improved conversation management with automatic compaction
- Cleaner model management by removing temporary commands
- Faster and more reliable AI provider connections

### Bug Fixes

- Fixed conversation history not updating after auto-compaction
- Prevented crashes from external tool connection issues

## [4.15.0] - 2025-12-02

### What's New

- DeepSeek provider now available as an AI option with reasoner model support
- Read specific line ranges from files with new read_lines tool

### Improvements

- Better organized model list display with visual indicators and clearer formatting
- Quick model switching with '/model <name>' shortcut command
- Automatic re-authentication for Claude Code OAuth sessions
- Standardized provider commands for better consistency

### Bug Fixes

- Fixed ASCII art alignment in the welcome message display
- Fixed provider command interface inconsistency
- Fixed model threshold command parsing with multi-part arguments

## [4.14.0] - 2025-12-02

### What's New

- Interactive setup wizard guides you through AI provider configuration on first run

### Improvements

- Cleaner first-time experience without forcing a default model selection
- Better error messages guide you to setup instead of mentioning default models

## [4.13.0] - 2025-12-01

### What's New

- Create custom commands with interactive step-by-step wizards
- Use project-level custom commands that override global settings for team collaboration
- Configure AI models with an interactive 5-step setup wizard

### Improvements

- Manage AI providers more easily with optional API key support
- Better tab completion now includes your custom commands
- Cleaner provider list focusing on actively supported services

## [4.12.0] - 2025-11-27

### What's New

- Subagents can now auto-approve specific tools without manual confirmation

### Improvements

- Simplified system prompt for faster and more focused responses
- Enhanced tool descriptions for better clarity and understanding
- Added safety features to prevent execution of dangerous commands
- Streamlined file editing with centralized usage guidelines

### Bug Fixes

- Fixed circular import issues in tool handling
- Resolved trailing whitespace problems in parallel task execution

## [4.11.0] - 2025-11-23

### What's New

- Create your own custom slash commands for automation
- Read specific line ranges from files with new read_lines tool
- Get started quickly with custom commands quickstart guide

### Improvements

- Better organized command system for improved reliability
- Enhanced model management with easier switching between AI models
- More comprehensive help system with custom commands integration

## [4.10.0] - 2025-11-23

### Improvements

- Better conversation management with intelligent token tracking
- Automatic truncation of oversized tool results to keep responses manageable
- Streamlined documentation with improved structure and easier navigation
- Enhanced test reliability and code quality improvements

### Bug Fixes

- Fixed OAuth authentication issues with proper test environment setup
- Resolved trailing whitespace problems in parallel task execution
- Fixed test isolation by clearing conflicting environment variables

## [4.9.2] - 2025-11-23

### Improvements

- Better support for parallel task execution with improved iteration limits
- More reliable subagent coordination during complex multi-task operations

## [4.9.1] - 2025-11-23

### Improvements

- Cleaned up code structure for better reliability

## [4.9.0] - 2025-11-23

### What's New

- Automatic recovery system for stuck subagents during parallel tasks

### Improvements

- Better ZAI provider compatibility with conversation summaries
- Streamlined command structure and improved type checking
- Enhanced OAuth token handling and error management

### Bug Fixes

- Fixed recursive directory listing functionality
- Resolved OAuth test environment interference
- Fixed conversation compaction issues with ZAI GLM-4.6 model

## [4.8.0] - 2025-11-23

### What's New

- Sign in with Claude Code subscription using OAuth authentication
- New vaporwave dream mode with retro 90s-themed interface and animations

### Improvements

- Better organization with clear tool names in results
- Safer directory browsing without automatic recursion
- AI can now complete tasks without step limits

### Bug Fixes

- Fixed issue where tool results didn't show which tool was used

## [4.7.0] - 2025-11-23

### What's New

- Fetch web pages directly for research and documentation
- Press Ctrl+J to easily create multi-line inputs
- AI can now complete complex tasks without step limits

### Improvements

- Better performance for file operations

### Bug Fixes

- Fixed directory listing to prevent unintended file access

## [4.6.0] - 2025-11-22

### What's New

- Fetch content from web pages for research and documentation
- Press Ctrl+J to easily create multi-line inputs

### Improvements

- Better help commands with detailed guidance for models and servers
- Cleaner welcome screen with improved centering and layout
- Enhanced notifications show conversation space savings when auto-compacted
- Updated token usage threshold takes effect immediately without restart

### Bug Fixes

- Fixed model threshold cache not updating when changed during session

## [4.4.3] - 2025-11-18

### Improvements

- Added support for Hugging Face models and AI providers

## [4.4.2] - 2025-11-18

### Improvements

- New paperclip ASCII art banner for better appearance
- Streamlined documentation for easier onboarding
- Updated provider list and Anthropic API key configuration
- Cleaner example configuration files

## [4.4.1] - 2025-11-16

### Improvements

- Simplified welcome message to focus on essential information for new users
- Added a fun ASCII art welcome banner with Clippy's classic greeting

## [4.4.0] - 2025-11-12

### What's New

- New think tool helps AI organize thoughts before taking action

### Improvements

- AI can now plan internally before executing tasks
- Better reasoning process for more accurate results

## [4.3.0] - 2025-11-09

### What's New

- New YOLO mode for auto-approving all actions

### Improvements

- Streamlined workflow with automatic approvals

## [4.2.0] - 2025-11-09

### What's New

- New /init command automatically creates project documentation files
- Enhance existing documentation with project-specific insights using --refine flag

### Improvements

- Cleaner AI responses by removing extra blank lines at the start
- Better project analysis detects structure, dependencies, and development commands

## [4.1.0] - 2025-11-06

### What's New

- Support for Anthropic and Google Gemini AI providers
- HuggingFace model integration for more AI options

### Improvements

- Better handling of custom AI providers with OpenAI-compatible settings
- More flexible provider system with improved model identification

### Bug Fixes

- Fixed issue with prefixed models not using correct provider settings

## [4.0.0] - 2025-11-06

### Improvements

- Better AI model management with improved configuration options
- More reliable tool calling with enhanced compatibility
- Enhanced performance and stability for all AI interactions

## [3.7.1] - 2025-11-06

### Improvements

- Get helpful suggestions when you type an incorrect slash command
- Better error messages for unknown commands in both interactive and quick modes

## [3.7.0] - 2025-11-05

### What's New

- New /truncate command to manage conversation length
- Copy and move files with validation and progress tracking
- Find and replace text across multiple files with preview mode

### Improvements

- Better tool organization with categories and smart suggestions
- Help commands grouped by category for easier navigation
- Reduced tool catalog with more powerful capabilities

## [3.6.0] - 2025-11-03

### What's New

- New project analysis tool for security scanning and code quality assessment
- Real-world examples and development scenarios added to documentation

### Improvements

- Enhanced interactive mode with progress indicators and smart file completion
- Better model management UI with detailed status panels
- Streamlined file operations using familiar shell commands
- Improved error recovery with contextual suggestions

### Bug Fixes

- Fixed automated execution issues in CI pipelines by removing interactive flag

## [3.5.0] - 2025-11-01

### What's New

- Automatic file validation checks for common formats like Python, JSON, and YAML when writing files
- Binary file detection prevents errors when working with images, documents, and other non-text files

### Improvements

- Better error messages with actionable guidance when file operations fail
- File validation can be skipped for large files over 1MB to keep things fast

### Bug Fixes

- Fixed issue with error handling that could cause problems with external tool connections

## [3.4.0] - 2025-11-01

### What's New

- Mistral AI now available as a provider option
- Enable and disable MCP servers for better control
- /model load command makes switching AI models faster

### Improvements

- Better tab completion for model commands with context-aware suggestions
- Command timeout increased to 5 minutes with configurable options
- Cleaner documentation with restructured features section

### Bug Fixes

- Fixed search patterns starting with dash being misinterpreted as flags
- Prevented special formatting characters from causing display errors
- Fixed duplicate commands in MCP manager

## [3.2.0] - 2025-10-27

### What's New

- Save and resume conversations automatically
- Interactive conversation picker when resuming

### Improvements

- Better file change previews with cleaner formatting
- Auto-generates timestamps for saved conversations
- Shows conversation history when loading saves

### Bug Fixes

- Fixed crash when messages contain special formatting characters
- Prevented display errors with mismatched text formatting

## [3.1.0] - 2025-10-27

### What's New

- MiniMax provider now available as an AI option
- Smart file completion suggests files without typing @ symbol

### Improvements

- Better tab completion for file references with @ symbol
- Enhanced file detection by analyzing paths and extensions

### Bug Fixes

- Fixed display issues when tool outputs contain special characters
- Prevented rendering artifacts in diff content

## [3.0.1] - 2025-10-27

### What's New

- Tab completion for slash commands makes typing faster
- New 'clippy-code' command as an alternative way to start the app

### Improvements

- Auto-enters interactive mode when no task provided
- Can handle more complex tasks with increased limit to 100 operations
- Added Chutes.ai as a new AI provider option
- Simplified provider names for cleaner display
- Better search behavior with ripgrep's automatic recursive search

### Bug Fixes

- Fixed search tool flag handling for more reliable results

## [2.1.1] - 2025-10-25

### Improvements

- Better token usage tracking with model-specific limits
- Status command now shows how usage is calculated
- Model names and IDs are now case-insensitive for easier matching

## [2.1.0] - 2025-10-25

### What's New

- Conversations automatically summarize when they get too long to save space
- Clippy now has a fun personality with paperclip-themed jokes and puns

### Improvements

- Model management commands now work better in document mode
- File editing is more reliable with exact string matching instead of patterns
- Switching between AI models works better with validation and case-insensitive matching
- Document mode header now shows your current working directory

### Bug Fixes

- Fixed multi-line pattern deletion in file edits
- Fixed issues with trailing newlines when deleting text patterns

## [2.0.0] - 2025-10-21

### What's New

- Switch between AI models more easily with case-insensitive matching
- Edit files with simpler exact string matching instead of complex patterns

### Improvements

- Better error messages when model switching fails
- More reliable multi-line pattern deletion
- Smarter fuzzy matching finds similar text when exact match isn't found

### Bug Fixes

- Fixed issues with trailing newlines when deleting multi-line patterns
- Fixed pattern matching that counted wrong number of occurrences

## [1.9.0] - 2025-10-20

### What's New

- New subagent system for delegating complex tasks to specialized AI agents
- Set custom models for different subagent types with /subagent commands

### Improvements

- Better multi-line pattern handling for file edits
- Enhanced approval dialogs with improved error handling
- Clear visual indicators show which subagent is working

### Bug Fixes

- Fixed file editing issues with patterns ending in newlines
- Fixed potential runtime errors with external tool connections

## [1.8.2] - 2025-10-19

### Improvements

- Simplified configuration by removing environment variable fallbacks
- Better model selection with explicit model names and IDs
- Cleaner setup process with updated documentation and examples

## [1.8.1] - 2025-10-19

### Improvements

- Cleaner terminal output when connecting to external tools
- Better error messages for troubleshooting connection issues

## [1.8.0] - 2025-10-19

### What's New

- Manage your own AI models and providers with new commands like /model add/remove/default

### Improvements

- Better visual feedback with a spinner while AI is thinking
- More flexible model system with separate provider and user configurations

### Bug Fixes

- Fixed security issue preventing text markup from breaking the UI

## [1.7.0] - 2025-10-19

### Improvements

- Added detailed logging to help track what the app is doing
- Current working directory now displayed in the document header for easier navigation
- Better error tracking with detailed logs when something goes wrong

## [1.6.0] - 2025-10-19

### Improvements

- Simplified approval system with clearer yes/no/allow options
- Better approval prompt validation with helpful error messages
- App now asks if you want to continue when reaching task limits
- Switched to faster dependency management for quicker updates

## [1.5.3] - 2025-10-19

### Improvements

- Project renamed to 'clippy-code' for clearer branding and consistency
- Added automated publishing workflow for smoother updates
- Enhanced type checking for better reliability

## [1.5.2] - 2025-10-19

### Improvements

- Better console message formatting for improved readability

### Bug Fixes

- Fixed security issue with error message display to prevent markup injection

## [1.5.1] - 2025-10-19

### Improvements

- You can now approve MCP tools on-the-fly without pre-configuring trust settings

## [1.5.0] - 2025-10-19

### What's New

- New block editing operations for replacing and deleting multi-line text sections
- Advanced regex replacement with support for capture groups and flags

### Improvements

- Enhanced file editing with more precise block-based operations
- Better MCP tool compatibility and result formatting
- Expanded documentation with comprehensive MCP integration guides and examples

## [1.4.1] - 2025-10-18

### Improvements

- Customized scrollbar appearance for better conversation viewing

## [1.4.0] - 2025-10-18

### What's New

- Connect to external tools through Model Context Protocol (MCP) servers
- New MCP commands: list, tools, refresh, allow, and revoke
- Enhanced approval dialog with expandable details and better error messages

### Improvements

- Manually trust MCP servers for better security control
- Better error handling with contextual suggestions when things go wrong
- Improved grep tool now accepts both 'path' and 'paths' for flexibility

### Bug Fixes

- Fixed UI display issues in document mode
- Resolved connection reliability problems with external servers

## [1.3.0] - 2025-10-17

### What's New

- Edit tool now supports multi-line patterns for complex file changes
- Manage auto-approvals with new /auto command (list, revoke, clear)

### Improvements

- Approval dialog redesigned with modern Windows-style security interface
- Can handle longer tasks with increased limit from 25 to 50 operations
- Better code organization for improved reliability and performance
- File edits are more reliable with strict pattern matching and validation

### Bug Fixes

- Fixed paperclip icon splitting in document mode
- Improved edit tool reliability with better error handling and validation

## [1.2.0] - 2025-10-14

### What's New

- Support for ZAI provider with GLM models

### Improvements

- Better search with familiar grep flags and glob patterns
- Improved file search handling with proper glob expansion

## [1.1.1] - 2025-10-14

### Improvements

- File search and editing tools now work properly

### Bug Fixes

- Fixed conversation compaction error when missing newlines
- Improved documentation formatting consistency

## [1.1.0] - 2025-10-14

### What's New

- Visual indicator shows when AI is thinking
- New edit tool for precise line-based file modifications

### Improvements

- Better search using ripgrep when available
- Directory listings now show folders with trailing slash

### Bug Fixes

- Fixed security issue preventing directory traversal
- Improved error messages and reliability

## [1.0.0] - 2025-10-13

### What's New

- New grep tool for searching patterns across files
- Read multiple files at once with read_files tool
- Document mode now shows conversation like a chat interface

### Improvements

- Better error messages when something goes wrong
- Directory listings now respect .gitignore rules
- Auto-loads project documentation when available
- Cleaner document interface with modern conversation display
- Improved approval UI for tool actions

### Bug Fixes

- Fixed duplicate messages in interactive mode
- Fixed Enter key submission issues in document mode
- Fixed output display and text formatting in document UI

## [0.4.0] - 2025-10-12

### What's New

- Use /compact to summarize long conversations and save space
- Check your token usage with /status command

### Improvements

- Better reliability with automatic retries for failed connections
- No more response length limits - let AI determine the best response size

## [0.3.0] - 2025-10-12

### What's New

- Switch between different AI models during conversations using /model commands
- See responses appear in real-time as they're being written

### Improvements

- Better support for multiple AI providers with separate API keys
- Press ESC twice to quickly interrupt long responses
- Improved reliability for model switching and configuration

## [0.2.0] - 2025-10-12

### What's New

- Works with any OpenAI-compatible service (OpenAI, Cerebras, Ollama, and more)

### Improvements

- Simplified setup with OpenAI as the default provider
- Cleaner code structure for better reliability and performance
- Updated guides and examples to help you get started faster

## [0.1.0] - 2025-10-12

### What's New

- Choose your preferred AI provider - now supporting both Anthropic and OpenAI models
- Interactive chat mode for longer conversations, plus quick command mode for single tasks
- Safety system that automatically approves safe operations while asking for confirmation on risky ones

### Improvements

- Better documentation with comprehensive guides and examples
- New development tools for easier testing and code quality checks
- Improved configuration system with clear setup instructions


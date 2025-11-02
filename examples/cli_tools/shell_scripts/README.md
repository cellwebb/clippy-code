# Shell Scripts Example

## 🎯 Quick Overview

This directory contains practical shell script examples for common development tasks. For comprehensive automation scripts with error handling, monitoring, and deployment utilities, see `../shell_automation.md`.

## 📁 Script Examples

### Essential Scripts
- `git_helpers.sh`         - Git workflow automation
- `file_operations.sh`      - File management utilities  
- `backup_util.sh`          - Simple backup utility
- `log_analyzer.sh`         - Log file analysis

### Quick Start Commands

```bash
# Create collection of useful shell scripts
clippy "Create a collection of practical shell scripts for Git management, file operations, backup automation, and log analysis"

# Or create individual scripts
clippy "Create Git automation script with branch management and commit helpers"
clippy "Create file management script with batch operations and safety checks"
clippy "Create simple backup script with compression and rotation"
```

## 🚀 Example Git Helpers Script

### Quick Generation
```bash
clippy "Create git_helpers.sh with functions for branch switching, commit automation, and git status summaries"

# Example output:
✅ Created git_helpers.sh with:
- smart_switch()     - Switch branches safely
- quick_commit()     - Commit with auto-generated messages
- git_summary()      - Show repository overview
- clean_branches()   - Remove merged branches
- sync_repos()       - Sync with remote
```

### Usage Examples
```bash
source git_helpers.sh

# Smart branch switching
smart_switch feature/new-api  # Safely switch with stash handling

# Quick commit with current directory as message
quick_commit "Added authentication module"

# Show repository summary
git_summary  # Shows status, recent commits, branches

# Clean up merged branches
clean_branches  # Removes merged local branches
```

## 🔧 File Operations Script

### Quick Generation
```bash
clippy "Create file_operations.sh with batch renaming, backup creation, and file organization utilities"

# Features:
- batch_rename()     - Rename multiple files with patterns
- smart_backup()     - Create timestamped backups
- organize_files()   - Sort files into directory by type
- find_duplicates()  - Find and remove duplicate files
```

### Usage Examples
```bash
source file_operations.sh

# Batch rename (replace spaces with underscores)
batch_rename "*" "s/ /_/g"

# Create backup with rotation
smart_backup important_project/  # Creates project_20240115_143022.tar.gz

# Organize downloads folder
organize_files ~/Downloads --by-type --move

# Find duplicates in current directory
find_duplicates --delete --interactive
```

## 📊 Log Analyzer Script

### Quick Generation
```bash
clippy "Create log_analyzer.sh with error detection, statistics, and pattern matching"

# Features:
- error_summary()    - Count errors by type
- traffic_stats()    - Generate traffic statistics  
- search_patterns()  - Find specific patterns in logs
- generate_report()  - Create daily/weekly reports
```

### Usage Examples
```bash
source log_analyzer.sh

# Summarize errors in log file
error_summary /var/log/app.log --by-hour --top-10

# Generate traffic statistics
traffic_stats /var/log/nginx/access.log --json output.json

# Search for specific patterns
search_patterns /var/log/auth.log "failed.*login" --count --context 2

# Generate daily report
generate_report /var/log/ --output report_$(date +%Y%m%d).html
```

## 🔗 Related Examples

For more comprehensive automation examples, see:
- **Shell Automation**: `../shell_automation.md` - Complete production automation
- **Python CLI Tools**: `../python_cli/README.md` - Professional CLI development
- **Docker Projects**: `../../devops/docker_projects/README.md` - Container automation

## 💡 Quick Tips for Shell Scripts

### Error Handling
```bash
set -euo pipefail  # Exit on error, treat unset variables as error

# Custom error handling
handle_error() {
    echo "Error occurred in script at line $1"
    exit 1
}
trap 'handle_error $LINENO' ERR
```

### Input Validation
```bash
validate_input() {
    local input="$1"
    local pattern="$2"
    
    if [[ ! "$input" =~ $pattern ]]; then
        echo "Invalid input: $input"
        exit 1
    fi
}
```

### Colored Output
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
```

## 📝 Quick Script Generation Patterns

Use clippy-code to rapidly create scripts for common tasks:

```bash
# AWS automation
clippy "Create AWS automation script for EC2 instance management and deployment"

# Database utilities
clippy "Create database maintenance script with backup, cleanup, and monitoring"

# Monitoring script
clippy "Create monitoring script with email alerts and system health checks"

# Deployment helper
clippy "Create deployment helper script with staging and production support"
```

These scripts provide building blocks for more complex automation workflows! 🚀📎
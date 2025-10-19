"""CSS styles for the document UI."""

# Main CSS for DocumentApp
DOCUMENT_APP_CSS = """
Screen {
    background: #f0f0f0;
}
#top-bar {
    dock: top;
    height: auto;
}
#header {
    height: 3;
    background: #2b579a;
    color: white;
    padding: 0 1;
    text-align: center;
    content-align: center middle;
}
#ribbon {
    height: 3;
    background: #f5f5f5;
    border-bottom: solid #d0d0d0;
    padding: 0;
    margin: 0;
}
.ribbon-tabs {
    height: 1;
    background: #f5f5f5;
    color: #555555;
    padding: 0 1;
    text-align: left;
}
.ribbon-content {
    height: 3;
    background: white;
    padding: 0 1;
    margin: 0;
}
.ribbon-group {
    width: auto;
    height: 1fr;
    border-right: solid #e0e0e0;
    padding: 0 1;
    margin: 0 1 0 0;
}
.ribbon-item {
    width: auto;
    height: 1;
    color: #333333;
    text-align: left;
    padding: 0 1;
}
.ribbon-group-label {
    width: auto;
    height: 1;
    color: #666666;
    text-align: center;
    text-style: italic;
}
#toolbar {
    height: 1;
    background: #f0f0f0;
    padding: 0 1;
    margin: 0;
}
#toolbar Button {
    margin: 0 1;
    width: 12;
    height: 1fr;
    background: #f0f0f0;
    color: #333333;
    border: none;
    text-style: bold;
    content-align: center middle;
}
#toolbar Button:hover {
    background: #e6e6e6;
}
#document-container {
    layout: vertical;
    background: white;
    color: #000000;
    border: solid #d0d0d0;
    margin: 1 2;
    padding: 2 4;
    height: 1fr;
    width: 1fr;
    overflow-y: auto;
    scrollbar-background: white;
    scrollbar-color: white;
    scrollbar-color-hover: #f0f0f0;
    scrollbar-color-active: #e0e0e0;
}
#conversation-log {
    height: auto;
    background: white;
    color: #000000;
    border: none;
    padding: 0;
    scrollbar-size: 0 0;
}
#thinking-indicator {
    display: none;
    height: auto;
    background: white;
    color: #999999;
    padding: 1 0 0 0;
    text-style: italic;
}
#thinking-indicator.visible {
    display: block;
}
#input-container {
    height: auto;
    background: white;
    border: none;
    padding: 1 0 0 0;
}
#input-prompt {
    width: auto;
    height: 1;
    background: white;
    color: #000000;
    padding: 0;
    margin: 0;
}
#user-input {
    width: 1fr;
    background: white;
    color: #000000;
    border: none;
    height: 1;
    padding: 0;
    margin: 0;
}
DocumentStatusBar {
    dock: bottom;
    height: 1;
    background: #1e3c72;
    color: white;
    text-align: center;
}
ApprovalBackdrop {
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    layer: overlay;
    align: center middle;
}
#approval-dialog {
    width: 85%;
    height: auto;
    max-height: 70%;
    max-width: 120;
    background: #f0f0f0;
    border: solid #003c74;
    border-title-align: left;
    border-title-color: white;
    border-title-background: #003c74;
    border-title-style: bold;
    padding: 0;
    margin: 2 4;
}
#approval-title {
    width: 100%;
    height: auto;
    background: #0078d4;
    color: white;
    text-align: left;
    text-style: bold;
    padding: 1 2;
    margin: 0;
}
#approval-content {
    width: 100%;
    height: auto;
    max-height: 25;
    overflow-y: auto;
    background: white;
    padding: 2 3;
}
#approval-main-message {
    color: #003c74;
    text-style: bold;
    padding: 0 0 2 0;
}
#approval-tool-name {
    color: #505050;
    text-style: bold;
    padding: 0 0 1 0;
}
#approval-tool-input {
    color: #505050;
    padding: 0 0 1 0;
    background: #f5f5f5;
    border: solid #d0d0d0;
    margin: 0 0 1 0;
}
#diff-preview-header {
    color: #0078d4;
    text-style: bold;
    padding: 1 0 0 0;
}
#diff-no-changes {
    color: #707070;
    text-style: italic;
    padding: 0 0 1 0;
    background: #f9f9f9;
    border: solid #e0e0e0;
    margin: 0 0 1 0;
}
#diff-preview-unavailable {
    color: #707070;
    text-style: italic;
    padding: 0 0 1 0;
}
#diff-display {
    height: auto;
    max-height: 12;
    border: solid #d0d0d0;
    background: #1e1e1e;
    padding: 0;
    margin: 0 0 1 0;
}
#approval-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 2 3;
    background: #f0f0f0;
    border-top: solid #d0d0d0;
}
#approval-buttons Button {
    margin: 0 1;
    min-width: 16;
    height: 3;
}
#approval-yes {
    background: #0078d4;
    color: white;
    text-style: bold;
    border: solid #003c74;
}
#approval-yes:hover {
    background: #005a9e;
}
#approval-allow {
    background: #107c10;
    color: white;
    text-style: bold;
    border: solid #0e6b0e;
}
#approval-allow:hover {
    background: #0d5e0d;
}
#approval-no {
    background: #e1e1e1;
    color: #000000;
    border: solid #adadad;
}
#approval-no:hover {
    background: #d0d0d0;
}
#approval-stop {
    background: #d13438;
    color: white;
    text-style: bold;
    border: solid #a02c2f;
}
#approval-stop:hover {
    background: #a92326;
}

/* Truncated hint styles */
.truncated-hint {
    color: #666666;
    text-style: italic;
    padding: 0 0 1 0;
}

/* Error panel styles */
#error-panel {
    width: 85%;
    height: auto;
    max-height: 70%;
    max-width: 120;
    background: #fff5f5;
    border: solid #d13438;
    border-title-align: left;
    border-title-color: white;
    border-title-background: #d13438;
    border-title-style: bold;
    padding: 0;
    margin: 2 4;
}
#error-title {
    width: 100%;
    height: auto;
    background: #d13438;
    color: white;
    text-align: left;
    text-style: bold;
    padding: 1 2;
    margin: 0;
}
#error-content {
    width: 100%;
    height: auto;
    max-height: 20;
    overflow-y: auto;
    background: white;
    padding: 2 3;
}
#error-main-message {
    color: #d13438;
    text-style: bold;
    padding: 0 0 2 0;
}
#error-details-header {
    color: #333333;
    text-style: bold;
    padding: 1 0 1 0;
}
#error-details {
    color: #505050;
    padding: 0 0 1 0;
    background: #f5f5f5;
    border: solid #e0e0e0;
    margin: 0 0 1 0;
}
#suggestions-header {
    color: #0078d4;
    text-style: bold;
    padding: 1 0 0 0;
}
.suggestion {
    color: #505050;
    padding: 0 0 0 1;
}
#error-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 2 3;
    background: #f0f0f0;
    border-top: solid #d0d0d0;
}
#error-ok {
    background: #0078d4;
    color: white;
    text-style: bold;
    border: solid #003c74;
}
#error-ok:hover {
    background: #005a9e;
}
#error-retry {
    background: #107c10;
    color: white;
    text-style: bold;
    border: solid #0e6b0e;
}
#error-retry:hover {
    background: #0d5e0d;
}

/* Input section headers */
#input-section-header {
    color: #0078d4;
    text-style: bold;
    padding: 1 0 1 0;
}

/* Diff section headers */
#diff-section-header {
    color: #0078d4;
    text-style: bold;
    padding: 1 0 1 0;
}

/* MCP preview unavailable */
#mcp-preview-unavailable {
    color: #707070;
    text-style: italic;
    padding: 0 0 1 0;
    background: #fff9e6;
    border: solid #e0e0e0;
    margin: 0 0 1 0;
}
"""

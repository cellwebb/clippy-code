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
    background: rgba(0, 0, 0, 0.5);
    layer: overlay;
    align: center middle;
}
#approval-dialog {
    width: 85%;
    height: auto;
    max-height: 70%;
    max-width: 120;
    background: #fffef0;
    border: thick #ff9500;
    padding: 0 2 1 2;
    margin: 2 4;
}
#approval-title {
    width: 100%;
    height: auto;
    background: #ff9500;
    color: #000000;
    text-align: center;
    text-style: bold;
    padding: 1 0;
    margin: 0;
}
#approval-content {
    width: 100%;
    height: auto;
    max-height: 25;
    overflow-y: auto;
    padding: 1 0;
}
#approval-tool-name {
    color: #0066cc;
    text-style: bold;
    padding: 0 0 1 0;
}
#approval-tool-input {
    color: #666666;
    padding: 0 0 1 0;
}
#diff-preview-header {
    color: #ff9500;
    text-style: bold;
    padding: 1 0 0 0;
}
#diff-display {
    height: auto;
    max-height: 12;
    border: solid #cccccc;
    background: #1e1e1e;
    padding: 0;
    margin: 0 0 1 0;
}
#approval-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1 0 0 0;
    background: #fffef0;
}
#approval-buttons Button {
    margin: 0 1;
    min-width: 14;
    height: 3;
}
"""

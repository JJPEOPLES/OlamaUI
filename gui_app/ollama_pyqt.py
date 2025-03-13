#!/usr/bin/env python3
"""
Ollama Chat GUI Application using PyQt
A modern graphical UI for chatting with Ollama models with code spaces and file handling
"""

import os
import sys
import json
import time
import threading
import requests
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QSplitter, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, 
                           QListWidget, QTabWidget, QFileDialog, QMessageBox, QSlider, 
                           QScrollArea, QFrame, QToolBar, QAction, QMenu, QSizePolicy,
                           QToolButton, QSpinBox, QCheckBox, QProgressBar, QStatusBar)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QRegExp

# Configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api')
APP_VERSION = "1.0.0"

# Color scheme - Dark charcoal theme
COLORS = {
    'background': "#312f2e",
    'sidebar': "#212020",
    'input_bg': "#413e3d",
    'text': "#ffffff",
    'muted_text': "#cccccc",
    'accent': "#4a86e8",
    'success': "#28a745",
    'warning': "#ffc107",
    'error': "#dc3545",
    'code_bg': "#1e1e1e",
    'user_msg_bg': "#312f2e",
    'assistant_msg_bg': "#413e3d"
}

# Syntax highlighting for code blocks
class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "\\bclass\\b", "\\bdef\\b", "\\bif\\b", "\\belif\\b", "\\belse\\b",
            "\\bfor\\b", "\\bwhile\\b", "\\breturn\\b", "\\bimport\\b", "\\bfrom\\b",
            "\\btry\\b", "\\bexcept\\b", "\\bfinally\\b", "\\braise\\b", "\\bwith\\b",
            "\\bas\\b", "\\bpass\\b", "\\bbreak\\b", "\\bcontinue\\b", "\\bin\\b",
            "\\bis\\b", "\\bnot\\b", "\\band\\b", "\\bor\\b", "\\bTrue\\b", "\\bFalse\\b",
            "\\bNone\\b", "\\blambda\\b", "\\bglobal\\b", "\\bnonlocal\\b", "\\bassert\\b"
        ]
        for pattern in keywords:
            self.highlighting_rules.append((QRegExp(pattern), keyword_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("'.*'"), string_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\b"), number_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.highlighting_rules.append((QRegExp("#[^\n]*"), comment_format))
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"), function_format))
        
        # Class names
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))
        self.highlighting_rules.append((QRegExp("\\bclass\\s+[A-Za-z0-9_]+"), class_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

# Message widget for chat
class MessageWidget(QFrame):
    def __init__(self, text, role, parent=None):
        super().__init__(parent)
        self.role = role
        
        # Set background color based on role
        if role == "user":
            self.setStyleSheet(f"background-color: {COLORS['user_msg_bg']}; border-radius: 5px;")
        elif role == "assistant":
            self.setStyleSheet(f"background-color: {COLORS['assistant_msg_bg']}; border-radius: 5px;")
        else:  # system
            self.setStyleSheet(f"background-color: {COLORS['sidebar']}; border-radius: 5px;")
        
        layout = QVBoxLayout(self)
        
        # Header with role indicator
        header_layout = QHBoxLayout()
        
        # Icon/avatar
        icon_text = "👤" if role == "user" else "🤖" if role == "assistant" else "ℹ️"
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 16px;")
        header_layout.addWidget(icon_label)
        
        # Role label
        role_label = QLabel(role.capitalize())
        role_label.setStyleSheet(f"color: {COLORS['muted_text']}; font-size: 12px;")
        header_layout.addWidget(role_label)
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_label = QLabel(timestamp)
        time_label.setStyleSheet(f"color: {COLORS['muted_text']}; font-size: 10px;")
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Process text for code blocks
        self.process_text(text, layout)
    
    def process_text(self, text, layout):
        # Split by code blocks
        parts = []
        current_text = ""
        in_code_block = False
        code_block_content = ""
        
        for line in text.split('\n'):
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if current_text:
                        parts.append(('text', current_text))
                        current_text = ""
                    parts.append(('code', code_block_content))
                    code_block_content = ""
                    in_code_block = False
                else:
                    # Start of code block
                    if current_text:
                        parts.append(('text', current_text))
                        current_text = ""
                    in_code_block = True
            elif in_code_block:
                code_block_content += line + '\n'
            else:
                current_text += line + '\n'
        
        # Add any remaining text
        if current_text:
            parts.append(('text', current_text))
        
        # Create widgets for each part
        for part_type, content in parts:
            if part_type == 'text':
                text_label = QLabel(content)
                text_label.setWordWrap(True)
                text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                text_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px;")
                layout.addWidget(text_label)
            else:  # code
                code_frame = QFrame()
                code_frame.setStyleSheet(f"background-color: {COLORS['code_bg']}; border-radius: 3px;")
                code_layout = QVBoxLayout(code_frame)
                
                # Code editor with syntax highlighting
                code_edit = QTextEdit()
                code_edit.setReadOnly(True)
                code_edit.setPlainText(content)
                code_edit.setStyleSheet(f"""
                    background-color: {COLORS['code_bg']};
                    color: {COLORS['text']};
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                    border: none;
                """)
                
                # Apply syntax highlighting
                highlighter = CodeHighlighter(code_edit.document())
                
                # Add copy button
                copy_btn = QPushButton("Copy")
                copy_btn.setStyleSheet(f"""
                    background-color: {COLORS['accent']};
                    color: {COLORS['text']};
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                """)
                copy_btn.clicked.connect(lambda _, text=content: QApplication.clipboard().setText(text))
                
                # Add save button
                save_btn = QPushButton("Save as File")
                save_btn.setStyleSheet(f"""
                    background-color: {COLORS['sidebar']};
                    color: {COLORS['text']};
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                """)
                save_btn.clicked.connect(lambda _, text=content: self.save_code_to_file(text))
                
                # Add buttons to a horizontal layout
                btn_layout = QHBoxLayout()
                btn_layout.addWidget(copy_btn)
                btn_layout.addWidget(save_btn)
                btn_layout.addStretch()
                
                code_layout.addWidget(code_edit)
                code_layout.addLayout(btn_layout)
                
                layout.addWidget(code_frame)
    
    def save_code_to_file(self, code):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Code", "", "All Files (*);;Python Files (*.py);;Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                QMessageBox.information(self, "Success", f"Code saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

# Thread for API calls
class ApiThread(QThread):
    response_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, url, payload, parent=None):
        super().__init__(parent)
        self.url = url
        self.payload = payload
    
    def run(self):
        try:
            response = requests.post(self.url, json=self.payload)
            if response.status_code == 200:
                self.response_received.emit(response.json())
            else:
                self.error_occurred.emit(f"API Error: {response.status_code}")
        except Exception as e:
            self.error_occurred.emit(f"Connection Error: {str(e)}")

# Main application window
class OllamaChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama Chat")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Variables
        self.models = []
        self.selected_model = ""
        self.temperature = 0.7
        self.max_tokens = 1024
        self.system_prompt = "You are a helpful assistant."
        self.chat_history = []
        self.is_generating = False
        self.current_chats = []
        self.ollama_api_url = OLLAMA_API_URL
        self.connection_status = "Not Connected"
        self.attached_files = []
        
        # Set up the UI
        self.setup_ui()
        
        # Fetch models
        self.fetch_models()
    
    def setup_ui(self):
        # Set application style
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
            QSplitter::handle {{
                background-color: {COLORS['sidebar']};
            }}
            QScrollArea {{
                border: none;
            }}
            QComboBox, QLineEdit, QTextEdit, QSpinBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['sidebar']};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['text']};
                border: none;
                padding: 8px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: #5a96f8;
            }}
            QPushButton:pressed {{
                background-color: #3a76d8;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['sidebar']};
                background-color: {COLORS['background']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['sidebar']};
                color: {COLORS['text']};
                padding: 8px 12px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['background']};
            }}
            QListWidget {{
                background-color: {COLORS['sidebar']};
                color: {COLORS['text']};
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
            }}
            QStatusBar {{
                background-color: {COLORS['sidebar']};
                color: {COLORS['text']};
            }}
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(250)
        self.sidebar.setMaximumWidth(350)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # App title and version
        title_layout = QHBoxLayout()
        app_title = QLabel("Ollama Chat")
        app_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(app_title)
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"color: {COLORS['muted_text']}; font-size: 12px;")
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        
        sidebar_layout.addLayout(title_layout)
        sidebar_layout.addSpacing(10)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(new_chat_btn)
        
        sidebar_layout.addSpacing(10)
        
        # Chat history list
        history_label = QLabel("Chat History")
        history_label.setStyleSheet("font-weight: bold;")
        sidebar_layout.addWidget(history_label)
        
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_selected_chat)
        sidebar_layout.addWidget(self.chat_list)
        
        # Settings section
        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-weight: bold;")
        sidebar_layout.addWidget(settings_label)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_selected)
        model_layout.addWidget(self.model_combo)
        sidebar_layout.addLayout(model_layout)
        
        # Temperature slider
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temp_label = QLabel(f"{self.temperature:.1f}")
        temp_layout.addWidget(self.temp_label)
        sidebar_layout.addLayout(temp_layout)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        self.temp_slider.setValue(int(self.temperature * 100))
        self.temp_slider.valueChanged.connect(self.update_temperature)
        sidebar_layout.addWidget(self.temp_slider)
        
        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Max Tokens:"))
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setMinimum(10)
        self.tokens_spin.setMaximum(4096)
        self.tokens_spin.setValue(self.max_tokens)
        self.tokens_spin.valueChanged.connect(self.update_max_tokens)
        tokens_layout.addWidget(self.tokens_spin)
        sidebar_layout.addLayout(tokens_layout)
        
        # System prompt
        sidebar_layout.addWidget(QLabel("System Prompt:"))
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlainText(self.system_prompt)
        self.system_prompt_edit.setMaximumHeight(100)
        sidebar_layout.addWidget(self.system_prompt_edit)
        
        # API URL
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API URL:"))
        self.api_url_edit = QLineEdit(self.ollama_api_url)
        api_layout.addWidget(self.api_url_edit)
        test_conn_btn = QPushButton("Test")
        test_conn_btn.setMaximumWidth(60)
        test_conn_btn.clicked.connect(self.test_connection)
        api_layout.addWidget(test_conn_btn)
        sidebar_layout.addLayout(api_layout)
        
        # Connection status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_indicator = QLabel("⚫")  # Will be colored based on status
        self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
        status_layout.addWidget(self.status_indicator)
        self.status_label = QLabel(self.connection_status)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        sidebar_layout.addLayout(status_layout)
        
        # Add sidebar to splitter
        splitter.addWidget(self.sidebar)
        
        # Right content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Chat area with tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Create initial chat tab
        self.new_chat()
        
        content_layout.addWidget(self.tabs)
        
        # Add content area to splitter
        splitter.addWidget(content_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 900])
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def create_chat_tab(self, title="New Chat"):
        """Create a new chat tab with all necessary widgets"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        # Chat messages area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(10)
        
        scroll_area.setWidget(messages_widget)
        chat_layout.addWidget(scroll_area)
        
        # Add welcome message
        self.add_system_message("Welcome to Ollama Chat! Select a model to start chatting.")
        
        # File attachments area
        files_widget = QWidget()
        files_widget.setMaximumHeight(100)
        files_widget.setVisible(False)  # Hidden initially
        files_layout = QVBoxLayout(files_widget)
        
        files_header = QHBoxLayout()
        files_header.addWidget(QLabel("Attached Files:"))
        clear_btn = QPushButton("Clear All")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self.clear_attachments)
        files_header.addWidget(clear_btn)
        files_layout.addLayout(files_header)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(60)
        files_layout.addWidget(self.files_list)
        
        chat_layout.addWidget(files_widget)
        self.files_widget = files_widget
        
        # Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar for input options
        toolbar = QHBoxLayout()
        
        # Attach file button
        attach_btn = QPushButton("📎 Attach File")
        attach_btn.clicked.connect(self.attach_file)
        toolbar.addWidget(attach_btn)
        
        # Code snippet button
        code_btn = QPushButton("💻 Code Snippet")
        code_btn.clicked.connect(self.insert_code_snippet)
        toolbar.addWidget(code_btn)
        
        # Reasoning toggle
        self.reasoning_check = QCheckBox("Include reasoning")
        self.reasoning_check.setChecked(False)
        toolbar.addWidget(self.reasoning_check)
        
        toolbar.addStretch()
        input_layout.addLayout(toolbar)
        
        # Text input
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Type your message here...")
        self.input_edit.setMinimumHeight(100)
        input_layout.addWidget(self.input_edit)
        
        # Send button
        send_layout = QHBoxLayout()
        send_layout.addStretch()
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        send_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(send_layout)
        
        chat_layout.addWidget(input_widget)
        
        # Set layout ratios
        chat_layout.setStretch(0, 7)  # Messages area
        chat_layout.setStretch(1, 1)  # Files area
        chat_layout.setStretch(2, 2)  # Input area
        
        # Add tab
        tab_index = self.tabs.addTab(chat_widget, title)
        self.tabs.setCurrentIndex(tab_index)
        
        # Add to chat list
        self.chat_list.addItem(title)
        self.current_chats.append({"title": title, "history": []})
    
    def close_tab(self, index):
        """Close a chat tab"""
        if self.tabs.count() > 1:  # Keep at least one tab open
            self.tabs.removeTab(index)
            # Also remove from chat list and history
            self.chat_list.takeItem(index)
            if index < len(self.current_chats):
                self.current_chats.pop(index)
    
    def new_chat(self):
        """Create a new chat tab"""
        chat_count = self.tabs.count() + 1
        self.create_chat_tab(f"Chat {chat_count}")
    
    def load_selected_chat(self, item):
        """Load a chat when selected from the list"""
        # Find the index of the selected chat
        for i in range(self.chat_list.count()):
            if self.chat_list.item(i).text() == item.text():
                self.tabs.setCurrentIndex(i)
                break
    
    def on_model_selected(self, model_name):
        """Handle model selection"""
        if model_name and model_name != self.selected_model:
            self.selected_model = model_name
            self.statusBar.showMessage(f"Model '{model_name}' selected")
    
    def update_temperature(self, value):
        """Update temperature value from slider"""
        self.temperature = value / 100.0
        self.temp_label.setText(f"{self.temperature:.1f}")
    
    def update_max_tokens(self, value):
        """Update max tokens value from spinner"""
        self.max_tokens = value
    
    def test_connection(self):
        """Test connection to Ollama API"""
        api_url = self.api_url_edit.text()
        
        # Update status indicator to yellow (testing)
        self.status_indicator.setStyleSheet(f"color: {COLORS['warning']}; font-size: 16px;")
        self.status_label.setText("Testing...")
        
        def test():
            try:
                response = requests.get(f"{api_url}/tags", timeout=5)
                if response.status_code == 200:
                    # Connection successful
                    self.status_indicator.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px;")
                    self.status_label.setText("Connected")
                    self.ollama_api_url = api_url
                    
                    # Update models
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    self.update_models(models)
                    
                    QMessageBox.information(self, "Connection Successful", 
                                          f"Successfully connected to Ollama API at {api_url}")
                else:
                    # API returned an error
                    self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
                    self.status_label.setText("Error")
                    QMessageBox.critical(self, "API Error", 
                                       f"Error connecting to API: Server returned {response.status_code}")
            except requests.exceptions.Timeout:
                # Connection timed out
                self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
                self.status_label.setText("Timeout")
                QMessageBox.critical(self, "Connection Timeout", 
                                   f"Connection to {api_url} timed out.\n\nPlease check if the server is running and accessible.")
            except Exception as e:
                # Other connection error
                self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
                self.status_label.setText("Error")
                QMessageBox.critical(self, "Connection Error", 
                                   f"Could not connect to Ollama API at {api_url}.\n\nError: {str(e)}")
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=test, daemon=True).start()
    
    def fetch_models(self):
        """Fetch available models from Ollama API"""
        # Update status indicator
        self.status_indicator.setStyleSheet(f"color: {COLORS['warning']}; font-size: 16px;")
        self.status_label.setText("Connecting...")
        
        def fetch():
            try:
                response = requests.get(f"{self.ollama_api_url}/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    # Update UI in the main thread
                    self.update_models(models)
                    
                    # Update connection status
                    self.status_indicator.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px;")
                    self.status_label.setText("Connected")
                else:
                    self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
                    self.status_label.setText("Error")
                    QMessageBox.critical(self, "API Error", 
                                       f"Error fetching models: API returned {response.status_code}")
            except Exception as e:
                self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
                self.status_label.setText("Error")
                QMessageBox.critical(self, "Connection Error", 
                                   f"Could not connect to Ollama API at {self.ollama_api_url}.\n\n"
                                   f"Make sure Ollama is running and try again.\n\nError: {str(e)}")
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_models(self, models):
        """Update the model dropdown with fetched models"""
        self.models = models
        
        # Clear and repopulate the combo box
        self.model_combo.clear()
        
        if models:
            self.model_combo.addItems(models)
            self.selected_model = models[0]
            self.statusBar.showMessage(f"Found {len(models)} models")
        else:
            self.statusBar.showMessage("No models found")
            QMessageBox.warning(self, "No Models Found", 
                              "No models were found in your Ollama installation.\n\n"
                              "Please install at least one model using 'ollama pull <model>'")
    
    def attach_file(self):
        """Attach a file to the current chat"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach File", "", "All Files (*)")
        if file_path:
            # Check file size (limit to 10MB for example)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                QMessageBox.warning(self, "File Too Large", 
                                  "The selected file is too large. Please select a file smaller than 10MB.")
                return
            
            # Add to attached files list
            file_name = os.path.basename(file_path)
            self.files_list.addItem(file_name)
            self.attached_files.append({"path": file_path, "name": file_name})
            
            # Show the files widget if it was hidden
            self.files_widget.setVisible(True)
            
            # Update status
            self.statusBar.showMessage(f"File attached: {file_name}")
    
    def clear_attachments(self):
        """Clear all attached files"""
        self.files_list.clear()
        self.attached_files = []
        self.files_widget.setVisible(False)
        self.statusBar.showMessage("Attachments cleared")
    
    def insert_code_snippet(self):
        """Insert a code snippet template into the input field"""
        cursor = self.input_edit.textCursor()
        cursor.insertText("```python\n# Your code here\n```")
        self.input_edit.setFocus()
    
    def add_system_message(self, text):
        """Add a system message to the chat"""
        message_widget = MessageWidget(text, "system")
        self.messages_layout.addWidget(message_widget)
    
    def add_user_message(self, text):
        """Add a user message to the chat"""
        message_widget = MessageWidget(text, "user")
        self.messages_layout.addWidget(message_widget)
        
        # Add to chat history
        current_tab = self.tabs.currentIndex()
        if current_tab < len(self.current_chats):
            self.current_chats[current_tab]["history"].append({
                "role": "user",
                "content": text
            })
    
    def add_assistant_message(self, text):
        """Add an assistant message to the chat"""
        message_widget = MessageWidget(text, "assistant")
        self.messages_layout.addWidget(message_widget)
        
        # Add to chat history
        current_tab = self.tabs.currentIndex()
        if current_tab < len(self.current_chats):
            self.current_chats[current_tab]["history"].append({
                "role": "assistant",
                "content": text
            })
    
    def send_message(self):
        """Send a message to the Ollama API"""
        if self.is_generating:
            return
        
        message = self.input_edit.toPlainText().strip()
        if not message:
            return
        
        if not self.selected_model:
            QMessageBox.warning(self, "No Model Selected", "Please select a model first.")
            return
        
        # Add user message to chat
        self.add_user_message(message)
        
        # Clear input
        self.input_edit.clear()
        
        # Prepare messages array
        messages = []
        
        # Add system message
        system_prompt = self.system_prompt_edit.toPlainText().strip()
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add reasoning instruction if checked
        if self.reasoning_check.isChecked():
            reasoning_prompt = {
                "role": "system",
                "content": "Please think step by step and show your reasoning before providing the final answer."
            }
            messages.append(reasoning_prompt)
        
        # Add file content if any files are attached
        if self.attached_files:
            file_contents = []
            for file_info in self.attached_files:
                try:
                    with open(file_info["path"], 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_contents.append(f"File: {file_info['name']}\n\n{content}\n\n")
                except Exception as e:
                    file_contents.append(f"Error reading file {file_info['name']}: {str(e)}")
            
            if file_contents:
                file_message = {
                    "role": "user",
                    "content": "I'm attaching the following files for reference:\n\n" + "\n".join(file_contents)
                }
                messages.append(file_message)
        
        # Add chat history from current tab
        current_tab = self.tabs.currentIndex()
        if current_tab < len(self.current_chats):
            messages.extend(self.current_chats[current_tab]["history"])
        
        # Send to API
        self.is_generating = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Generating...")
        self.statusBar.showMessage("Generating response...")
        
        # Create a progress indicator
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        
        progress_label = QLabel("Ollama is thinking...")
        progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_layout.addWidget(progress_bar)
        
        self.messages_layout.addWidget(progress_widget)
        
        # Prepare API payload
        payload = {
            "model": self.selected_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        # Create and start API thread
        self.api_thread = ApiThread(f"{self.ollama_api_url}/chat", payload)
        self.api_thread.response_received.connect(lambda data: self.handle_response(data, progress_widget))
        self.api_thread.error_occurred.connect(lambda error: self.handle_error(error, progress_widget))
        self.api_thread.start()
    
    def handle_response(self, data, progress_widget):
        """Handle successful API response"""
        # Remove progress indicator
        progress_widget.setParent(None)
        
        # Process response
        if data.get("message") and data["message"].get("content"):
            content = data["message"]["content"]
            self.add_assistant_message(content)
        else:
            self.add_system_message("Error: Received empty response from model.")
        
        # Reset state
        self.is_generating = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        self.statusBar.showMessage("Response received")
    
    def handle_error(self, error, progress_widget):
        """Handle API error"""
        # Remove progress indicator
        progress_widget.setParent(None)
        
        # Show error message
        self.add_system_message(f"Error: {error}")
        
        # Reset state
        self.is_generating = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        self.statusBar.showMessage("Error occurred")

def main():
    # Set up command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Ollama Chat - PyQt GUI')
    parser.add_argument('--api-url', type=str, help='Ollama API URL')
    args = parser.parse_args()
    
    # Set API URL from args if provided
    global OLLAMA_API_URL
    if args.api_url:
        OLLAMA_API_URL = args.api_url
    
    # Create and run the application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
    
    window = OllamaChatApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
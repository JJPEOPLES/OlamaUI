# Ollama Chat UI

This repository contains six implementations of a chat UI for Ollama:

1. A Ruby implementation using Sinatra with Tailwind CSS
2. A Python implementation using Flask with Tailwind CSS
3. A terminal-based implementation using Python curses
4. A GUI implementation using Python and Tkinter
5. A ChatGPT-style UI with dark charcoal theme using Python and Tkinter
6. A modern PyQt-based UI with code spaces and file handling

All implementations provide interfaces to interact with Ollama's API, allowing you to chat with any model you have installed in Ollama.

## Requirements

- Ollama installed and running on your machine (https://ollama.com/download)
- Python 3.7+ (for Python, GUI, and terminal implementations)
- Ruby 3.0+ (for Ruby implementation)
- Tkinter (usually included with Python, required for GUI implementation)
- PyQt5 (required for PyQt UI implementation)
- Docker and Docker Compose (optional, for containerized setup)

### PyQt Installation

For the PyQt-based UI, you'll need to install PyQt5:

```bash
pip install PyQt5
```

## Quick Start

### Using the Universal Launcher

The `ollama-chat` script provides a unified way to launch any of the implementations:

```bash
# Make the script executable
chmod +x ollama-chat

# Launch terminal UI
./ollama-chat

# Launch terminal UI with a specific model
./ollama-chat --model llama3

# Launch GUI application
./ollama-chat --gui

# Launch ChatGPT-style UI with dark charcoal theme
./ollama-chat --chatgpt

# Launch PyQt-based UI with code spaces and file handling
./ollama-chat --pyqt

# Launch Python web UI
./ollama-chat --web

# Launch Ruby web UI
./ollama-chat --web --ruby
```

### Using Docker Compose

```bash
docker-compose up -d
```

This will start both web applications:
- Ruby app at http://localhost:4567
- Python app at http://localhost:5000

## Features

### Web UI Features
- Select from available Ollama models
- Adjust temperature and other generation parameters
- Chat with the selected model
- Markdown-like formatting in responses
- Responsive design for mobile and desktop
- System prompt support
- Tailwind CSS styling

### GUI Features
- Native desktop application using Tkinter
- Clean, user-friendly interface
- Model selection and parameter adjustment
- Save and load chat histories
- Copy responses to clipboard
- Code block formatting
- Keyboard shortcuts

### ChatGPT-Style UI Features
- Dark charcoal theme (#312f2e) for a sleek look
- Custom chat titles with rename option
- Friend invitation system
- Pen icon for new chats
- Save and load chat histories to/from files
- Rename and delete chats
- Download Ollama models directly from the UI
- System prompt customization
- Connect to local or remote Ollama instances
- Connection status monitoring

### PyQt UI Features
- Modern, responsive interface with PyQt5
- Dark charcoal theme for a professional look
- Tabbed interface for multiple conversations
- Code spaces with syntax highlighting
- File attachment support for context
- Code block detection and formatting
- Save code snippets directly to files
- Step-by-step reasoning toggle
- Connection status monitoring
- Remote Ollama instance support

### Terminal UI Features
- Interactive terminal interface with curses
- Model selection
- Temperature adjustment
- Command system for controlling the chat
- Keyboard shortcuts

## Commands and Shortcuts

### Terminal Commands
While in the terminal chat interface, you can use the following commands:
- `/exit` or `/quit` - Exit the application
- `/temp [value]` - Set temperature (0-1)
- `/clear` - Clear chat history
- `/help` - Show help

### GUI Keyboard Shortcuts
- `Ctrl+Enter`: Send message
- `Ctrl+S`: Save chat
- `Ctrl+O`: Load chat
- `Ctrl+N`: New chat

## Environment Variables

All implementations support the following environment variables:

- `OLLAMA_API_URL`: URL of the Ollama API (default: http://localhost:11434/api)

## Troubleshooting

- Make sure Ollama is running on your machine
- Check that you have at least one model downloaded in Ollama
- If using Docker, ensure that host.docker.internal resolves to your host machine
- For GUI issues, ensure Tkinter is properly installed with your Python distribution

## License

MIT
# Ollama Chat UI

This repository contains four implementations of a chat UI for Ollama:

1. A Ruby implementation using Sinatra with Tailwind CSS
2. A Python implementation using Flask with Tailwind CSS
3. A terminal-based implementation using Python curses
4. A GUI implementation using Python and Tkinter

All implementations provide interfaces to interact with Ollama's API, allowing you to chat with any model you have installed in Ollama.

## Requirements

- Ollama installed and running on your machine (https://ollama.com/download)
- Python 3.7+ (for Python, GUI, and terminal implementations)
- Ruby 3.0+ (for Ruby implementation)
- Tkinter (usually included with Python, required for GUI implementation)
- Docker and Docker Compose (optional, for containerized setup)

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
# Ollama Chat Terminal

A terminal-based UI for chatting with Ollama models.

## Features

- Interactive terminal UI with curses
- Model selection from available Ollama models
- Adjustable temperature
- Command system for controlling the chat
- Keyboard shortcuts

## Requirements

- Python 3.7+
- Ollama running on your machine
- `requests` Python package

## Installation

```bash
# Install required packages
pip install requests

# Make the script executable
chmod +x ollama_chat.py
```

## Usage

```bash
# Basic usage
./ollama_chat.py

# Specify a model directly
./ollama_chat.py --model llama3

# Set temperature
./ollama_chat.py --temp 0.5

# Set maximum tokens
./ollama_chat.py --max-tokens 2048

# Specify custom API URL
./ollama_chat.py --api-url http://custom-ollama-server:11434/api
```

## Commands

While in the chat interface, you can use the following commands:

- `/exit` or `/quit` - Exit the application
- `/temp [value]` - Set temperature (0-1)
- `/clear` - Clear chat history
- `/help` - Show help

## Keyboard Shortcuts

- `Ctrl+C` - Exit the application
- `Ctrl+G` - Submit message (when in input box)

## Troubleshooting

- Make sure Ollama is running on your machine
- Check that you have at least one model downloaded in Ollama
- If you see display issues, try resizing your terminal window
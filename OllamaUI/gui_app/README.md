# Ollama Chat GUI

A graphical user interface for chatting with Ollama models using Python and Tkinter.

## Features

- Clean, native GUI interface using Tkinter
- Select from available Ollama models
- Adjust temperature and max tokens
- System prompt support
- Save and load chat histories
- Copy responses to clipboard
- Code block formatting
- Keyboard shortcuts

## Requirements

- Python 3.7+
- Tkinter (usually included with Python)
- Ollama running on your machine

## Usage

```bash
# Basic usage
python ollama_gui.py

# Specify custom API URL
python ollama_gui.py --api-url http://custom-ollama-server:11434/api
```

## Keyboard Shortcuts

- `Ctrl+Enter`: Send message
- `Ctrl+S`: Save chat
- `Ctrl+O`: Load chat
- `Ctrl+N`: New chat

## Customization

You can customize the appearance by:

1. Creating a `theme.json` file in the same directory
2. Using a different Tkinter theme (clam, vista, etc.)
3. Modifying the font sizes in the code

## Troubleshooting

- Make sure Ollama is running on your machine
- Check that you have at least one model downloaded in Ollama
- If you encounter display issues, try adjusting your system's DPI settings
#!/usr/bin/env python3
"""
Ollama Chat Terminal Application
A simple terminal-based UI for chatting with Ollama models
"""

import os
import sys
import json
import time
import signal
import requests
import argparse
from typing import List, Dict, Any, Optional
import curses
from curses import textpad
import textwrap

# Configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api')

# Terminal colors and styles
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class OllamaChat:
    def __init__(self):
        self.models = []
        self.current_model = None
        self.chat_history = []
        self.temperature = 0.7
        self.max_tokens = 1024
        self.stdscr = None
        self.input_box = None
        self.chat_win = None
        self.status_win = None
        self.max_y = 0
        self.max_x = 0
        self.input_start_y = 0
        self.chat_height = 0
        self.prompt = "You: "
        self.response_prefix = "AI: "
        self.exit_requested = False

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from Ollama API"""
        try:
            response = requests.get(f"{OLLAMA_API_URL}/tags")
            if response.status_code == 200:
                return response.json().get('models', [])
            else:
                return []
        except Exception as e:
            print(f"{Colors.RED}Error fetching models: {str(e)}{Colors.ENDC}")
            return []

    def select_model(self) -> Optional[str]:
        """Display a menu to select a model"""
        self.models = self.fetch_models()
        
        if not self.models:
            print(f"{Colors.RED}No models available. Make sure Ollama is running.{Colors.ENDC}")
            return None
        
        print(f"{Colors.HEADER}{Colors.BOLD}Available Models:{Colors.ENDC}")
        for i, model in enumerate(self.models):
            print(f"{Colors.BLUE}[{i+1}]{Colors.ENDC} {model['name']}")
        
        while True:
            try:
                choice = input(f"{Colors.GREEN}Select a model (1-{len(self.models)}): {Colors.ENDC}")
                idx = int(choice) - 1
                if 0 <= idx < len(self.models):
                    return self.models[idx]['name']
                else:
                    print(f"{Colors.YELLOW}Invalid choice. Please try again.{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.YELLOW}Please enter a number.{Colors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.RED}Model selection cancelled.{Colors.ENDC}")
                return None

    def send_message(self, message: str) -> Optional[str]:
        """Send a message to the Ollama API and get a response"""
        if not self.current_model:
            return "No model selected."
        
        # Add user message to history
        self.chat_history.append({"role": "user", "content": message})
        
        try:
            payload = {
                "model": self.current_model,
                "messages": self.chat_history,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            response = requests.post(f"{OLLAMA_API_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') and data['message'].get('content'):
                    content = data['message']['content']
                    # Add assistant response to history
                    self.chat_history.append({"role": "assistant", "content": content})
                    return content
                else:
                    return "Error: Received empty response from model."
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    def init_curses(self, stdscr):
        """Initialize the curses interface"""
        self.stdscr = stdscr
        curses.curs_set(1)  # Show cursor
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # User
        curses.init_pair(2, curses.COLOR_BLUE, -1)   # AI
        curses.init_pair(3, curses.COLOR_RED, -1)    # Error/System
        curses.init_pair(4, curses.COLOR_YELLOW, -1) # Status
        
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.input_start_y = self.max_y - 5
        self.chat_height = self.input_start_y - 2
        
        # Create windows
        self.create_windows()
        
        # Set up signal handler for resize
        signal.signal(signal.SIGWINCH, self.handle_resize)

    def create_windows(self):
        """Create the UI windows"""
        # Status window (top line)
        self.status_win = curses.newwin(1, self.max_x, 0, 0)
        self.status_win.attron(curses.color_pair(4))
        status_text = f" Model: {self.current_model} | Temp: {self.temperature} | Press Ctrl+C to exit"
        self.status_win.addstr(0, 0, status_text[:self.max_x-1])
        self.status_win.attroff(curses.color_pair(4))
        self.status_win.refresh()
        
        # Chat window
        self.chat_win = curses.newwin(self.chat_height, self.max_x, 1, 0)
        self.chat_win.scrollok(True)
        self.chat_win.refresh()
        
        # Input window
        input_win = curses.newwin(3, self.max_x, self.input_start_y, 0)
        input_win.attron(curses.color_pair(1))
        input_win.addstr(0, 0, self.prompt)
        input_win.attroff(curses.color_pair(1))
        input_win.box()
        input_win.refresh()
        
        # Input textbox
        self.input_box = textpad.Textbox(
            curses.newwin(1, self.max_x - len(self.prompt) - 2, self.input_start_y, len(self.prompt))
        )

    def handle_resize(self, signum, frame):
        """Handle terminal resize event"""
        curses.endwin()
        self.stdscr.refresh()
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.input_start_y = self.max_y - 5
        self.chat_height = self.input_start_y - 2
        self.create_windows()
        self.redraw_chat()

    def redraw_chat(self):
        """Redraw the chat history"""
        self.chat_win.clear()
        y_pos = 0
        
        for msg in self.chat_history:
            role = msg["role"]
            content = msg["content"]
            
            if role == "user":
                prefix = "You: "
                color_pair = 1
            elif role == "assistant":
                prefix = "AI: "
                color_pair = 2
            else:
                prefix = "System: "
                color_pair = 3
            
            # Wrap text to fit window width
            wrapped_lines = textwrap.wrap(content, self.max_x - len(prefix) - 2)
            
            self.chat_win.attron(curses.color_pair(color_pair))
            self.chat_win.addstr(y_pos, 0, prefix)
            self.chat_win.attroff(curses.color_pair(color_pair))
            
            for i, line in enumerate(wrapped_lines):
                if i == 0:
                    self.chat_win.addstr(y_pos, len(prefix), line)
                else:
                    y_pos += 1
                    self.chat_win.addstr(y_pos, len(prefix), line)
            
            y_pos += 2  # Add space between messages
            
            # If we've filled the window, stop drawing
            if y_pos >= self.chat_height:
                break
        
        self.chat_win.refresh()

    def run_curses_ui(self, stdscr):
        """Main curses UI loop"""
        self.init_curses(stdscr)
        
        # Initial welcome message
        self.chat_history.append({
            "role": "system", 
            "content": f"Welcome to Ollama Chat Terminal! You are chatting with {self.current_model}."
        })
        self.redraw_chat()
        
        while not self.exit_requested:
            try:
                # Get user input
                user_input = self.input_box.edit().strip()
                
                # Clear input area
                input_win = curses.newwin(3, self.max_x, self.input_start_y, 0)
                input_win.attron(curses.color_pair(1))
                input_win.addstr(0, 0, self.prompt)
                input_win.attroff(curses.color_pair(1))
                input_win.box()
                input_win.refresh()
                
                # Process special commands
                if user_input.lower() in ['/exit', '/quit']:
                    self.exit_requested = True
                    break
                elif user_input.lower().startswith('/temp '):
                    try:
                        new_temp = float(user_input.split(' ')[1])
                        if 0 <= new_temp <= 1:
                            self.temperature = new_temp
                            self.chat_history.append({
                                "role": "system", 
                                "content": f"Temperature set to {self.temperature}"
                            })
                        else:
                            self.chat_history.append({
                                "role": "system", 
                                "content": "Temperature must be between 0 and 1"
                            })
                    except:
                        self.chat_history.append({
                            "role": "system", 
                            "content": "Invalid temperature format. Use /temp 0.7"
                        })
                    self.redraw_chat()
                    continue
                elif user_input.lower() == '/clear':
                    self.chat_history = []
                    self.chat_history.append({
                        "role": "system", 
                        "content": "Chat history cleared."
                    })
                    self.redraw_chat()
                    continue
                elif user_input.lower() == '/help':
                    help_text = (
                        "Commands:\n"
                        "/exit or /quit - Exit the application\n"
                        "/temp [value] - Set temperature (0-1)\n"
                        "/clear - Clear chat history\n"
                        "/help - Show this help"
                    )
                    self.chat_history.append({
                        "role": "system", 
                        "content": help_text
                    })
                    self.redraw_chat()
                    continue
                elif not user_input:
                    continue
                
                # Add user message to UI
                self.redraw_chat()
                
                # Show "thinking" indicator
                self.status_win.clear()
                self.status_win.attron(curses.color_pair(4))
                status_text = f" Model: {self.current_model} | Temp: {self.temperature} | Thinking..."
                self.status_win.addstr(0, 0, status_text[:self.max_x-1])
                self.status_win.attroff(curses.color_pair(4))
                self.status_win.refresh()
                
                # Get AI response
                response = self.send_message(user_input)
                
                # Update status
                self.status_win.clear()
                self.status_win.attron(curses.color_pair(4))
                status_text = f" Model: {self.current_model} | Temp: {self.temperature} | Press Ctrl+C to exit"
                self.status_win.addstr(0, 0, status_text[:self.max_x-1])
                self.status_win.attroff(curses.color_pair(4))
                self.status_win.refresh()
                
                # Redraw chat with new messages
                self.redraw_chat()
                
            except KeyboardInterrupt:
                self.exit_requested = True
                break
            except Exception as e:
                self.chat_history.append({
                    "role": "system", 
                    "content": f"Error: {str(e)}"
                })
                self.redraw_chat()

    def run(self):
        """Main application entry point"""
        print(f"{Colors.HEADER}{Colors.BOLD}Ollama Chat Terminal{Colors.ENDC}")
        print(f"{Colors.BLUE}A simple terminal UI for chatting with Ollama models{Colors.ENDC}")
        print()
        
        # Select model
        self.current_model = self.select_model()
        if not self.current_model:
            print(f"{Colors.RED}No model selected. Exiting.{Colors.ENDC}")
            return
        
        print(f"{Colors.GREEN}Starting chat with {self.current_model}...{Colors.ENDC}")
        time.sleep(1)
        
        # Start curses UI
        try:
            curses.wrapper(self.run_curses_ui)
        except Exception as e:
            print(f"{Colors.RED}Error in curses UI: {str(e)}{Colors.ENDC}")
        
        print(f"{Colors.GREEN}Chat session ended.{Colors.ENDC}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Ollama Chat Terminal')
    parser.add_argument('--model', type=str, help='Model to use (skips selection)')
    parser.add_argument('--temp', type=float, default=0.7, help='Temperature (0-1)')
    parser.add_argument('--max-tokens', type=int, default=1024, help='Maximum tokens to generate')
    parser.add_argument('--api-url', type=str, help='Ollama API URL')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Set API URL from args if provided
    if args.api_url:
        OLLAMA_API_URL = args.api_url
    
    chat = OllamaChat()
    chat.temperature = args.temp
    chat.max_tokens = args.max_tokens
    
    # If model is provided, skip selection
    if args.model:
        models = chat.fetch_models()
        model_names = [m['name'] for m in models]
        if args.model in model_names:
            chat.current_model = args.model
            chat.run()
        else:
            print(f"{Colors.RED}Model '{args.model}' not found.{Colors.ENDC}")
            print(f"{Colors.YELLOW}Available models: {', '.join(model_names)}{Colors.ENDC}")
    else:
        chat.run()
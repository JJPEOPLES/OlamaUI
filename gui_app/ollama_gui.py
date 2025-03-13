#!/usr/bin/env python3
"""
Ollama Chat GUI Application
A simple graphical UI for chatting with Ollama models
"""

import os
import sys
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
from datetime import datetime

# Configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api')
APP_VERSION = "1.0.0"

class OllamaChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat GUI")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set app icon if available
        try:
            self.root.iconbitmap("icon.ico")  # Windows
        except:
            try:
                img = tk.PhotoImage(file="icon.png")
                self.root.tk.call('wm', 'iconphoto', self.root._w, img)  # Linux/Mac
            except:
                pass  # No icon available
        
        # Variables
        self.models = []
        self.selected_model = tk.StringVar()
        self.temperature = tk.DoubleVar(value=0.7)
        self.max_tokens = tk.IntVar(value=1024)
        self.system_prompt = tk.StringVar()
        self.chat_history = []
        self.is_generating = False
        
        # Create UI
        self.create_menu()
        self.create_ui()
        
        # Fetch models
        self.fetch_models()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-s>", lambda e: self.save_chat())
        self.root.bind("<Control-o>", lambda e: self.load_chat())
        self.root.bind("<Control-n>", lambda e: self.new_chat())
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Chat", command=self.new_chat, accelerator="Ctrl+N")
        file_menu.add_command(label="Save Chat", command=self.save_chat, accelerator="Ctrl+S")
        file_menu.add_command(label="Load Chat", command=self.load_chat, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy Selected", command=self.copy_selected)
        edit_menu.add_command(label="Copy Last Response", command=self.copy_last_response)
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear Chat", command=self.clear_chat)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Model menu
        model_menu = tk.Menu(menubar, tearoff=0)
        model_menu.add_command(label="Refresh Models", command=self.fetch_models)
        menubar.add_cascade(label="Model", menu=model_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_ui(self):
        """Create the main UI elements"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a PanedWindow for resizable sections
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (settings)
        left_frame = ttk.Frame(paned, padding="5")
        paned.add(left_frame, weight=1)
        
        # Right panel (chat)
        right_frame = ttk.Frame(paned, padding="5")
        paned.add(right_frame, weight=3)
        
        # Configure the settings panel
        self.setup_settings_panel(left_frame)
        
        # Configure the chat panel
        self.setup_chat_panel(right_frame)
    
    def setup_settings_panel(self, parent):
        """Set up the settings panel"""
        # Model selection
        ttk.Label(parent, text="Model:").pack(anchor=tk.W, pady=(0, 5))
        self.model_combobox = ttk.Combobox(parent, textvariable=self.selected_model, state="readonly")
        self.model_combobox.pack(fill=tk.X, pady=(0, 10))
        self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_selected)
        
        # Temperature
        ttk.Label(parent, text=f"Temperature: {self.temperature.get():.1f}").pack(anchor=tk.W, pady=(0, 5))
        temp_scale = ttk.Scale(parent, from_=0.0, to=1.0, variable=self.temperature, command=self.update_temp_label)
        temp_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Max tokens
        ttk.Label(parent, text="Max Tokens:").pack(anchor=tk.W, pady=(0, 5))
        tokens_frame = ttk.Frame(parent)
        tokens_frame.pack(fill=tk.X, pady=(0, 10))
        
        tokens_entry = ttk.Entry(tokens_frame, textvariable=self.max_tokens, width=8)
        tokens_entry.pack(side=tk.LEFT)
        
        tokens_scale = ttk.Scale(tokens_frame, from_=10, to=4096, variable=self.max_tokens)
        tokens_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # System prompt
        ttk.Label(parent, text="System Prompt:").pack(anchor=tk.W, pady=(0, 5))
        self.system_prompt_text = scrolledtext.ScrolledText(parent, height=8, wrap=tk.WORD)
        self.system_prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Action buttons
        ttk.Button(parent, text="New Chat", command=self.new_chat).pack(fill=tk.X, pady=2)
        ttk.Button(parent, text="Save Chat", command=self.save_chat).pack(fill=tk.X, pady=2)
        ttk.Button(parent, text="Load Chat", command=self.load_chat).pack(fill=tk.X, pady=2)
        ttk.Button(parent, text="Clear Chat", command=self.clear_chat).pack(fill=tk.X, pady=2)
        
        # Status
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT)
        
        self.version_label = ttk.Label(status_frame, text=f"v{APP_VERSION}", anchor=tk.E)
        self.version_label.pack(side=tk.RIGHT)
    
    def setup_chat_panel(self, parent):
        """Set up the chat panel"""
        # Chat display area
        chat_frame = ttk.Frame(parent)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat history display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.tag_configure("user", foreground="#0066cc", font=("TkDefaultFont", 10, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#006633")
        self.chat_display.tag_configure("system", foreground="#666666", justify="center")
        self.chat_display.tag_configure("code", background="#f0f0f0", font=("Courier", 9))
        
        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.user_input = scrolledtext.ScrolledText(input_frame, height=4, wrap=tk.WORD)
        self.user_input.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.user_input.bind("<Control-Return>", self.send_message)
        
        send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Hint label
        hint_label = ttk.Label(parent, text="Press Ctrl+Enter to send", foreground="#999999")
        hint_label.pack(anchor=tk.E)
        
        # Add initial system message
        self.add_to_chat("Welcome to Ollama Chat! Select a model to start chatting.", "system")
    
    def update_temp_label(self, value):
        """Update the temperature label when the slider changes"""
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label) and "Temperature:" in child.cget("text"):
                        child.configure(text=f"Temperature: {float(value):.1f}")
                        break
    
    def fetch_models(self):
        """Fetch available models from Ollama API"""
        self.status_label.config(text="Fetching models...")
        
        def fetch():
            try:
                response = requests.get(f"{OLLAMA_API_URL}/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    # Update UI in the main thread
                    self.root.after(0, lambda: self.update_models(models))
                else:
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Error: API returned {response.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Error connecting to Ollama API: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Connection Error", 
                    f"Could not connect to Ollama API at {OLLAMA_API_URL}.\n\n"
                    f"Make sure Ollama is running and try again.\n\nError: {str(e)}"
                ))
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_models(self, models):
        """Update the model dropdown with fetched models"""
        self.models = models
        self.model_combobox["values"] = models
        
        if models:
            self.status_label.config(text=f"Found {len(models)} models")
        else:
            self.status_label.config(text="No models found")
            messagebox.showwarning(
                "No Models Found", 
                "No models were found in your Ollama installation.\n\n"
                "Please install at least one model using 'ollama pull <model>'"
            )
    
    def on_model_selected(self, event):
        """Handle model selection"""
        model = self.selected_model.get()
        if model:
            self.clear_chat()
            self.add_to_chat(f"Model '{model}' selected. Start chatting!", "system")
    
    def add_to_chat(self, message, role):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp and role prefix
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if role == "user":
            prefix = f"[{timestamp}] You: "
            self.chat_display.insert(tk.END, prefix, "user")
        elif role == "assistant":
            prefix = f"[{timestamp}] AI: "
            self.chat_display.insert(tk.END, prefix, "assistant")
        else:  # system
            self.chat_display.insert(tk.END, f"\n--- {message} ---\n\n", "system")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            return
        
        # Process message for code blocks and formatting
        remaining_text = message
        while "```" in remaining_text:
            # Find the start of the code block
            start_idx = remaining_text.find("```")
            # Add the text before the code block
            if start_idx > 0:
                self.chat_display.insert(tk.END, remaining_text[:start_idx])
            
            # Find the end of the code block
            end_idx = remaining_text.find("```", start_idx + 3)
            if end_idx == -1:  # No closing backticks
                self.chat_display.insert(tk.END, remaining_text[start_idx:])
                break
            
            # Extract and add the code block
            code_block = remaining_text[start_idx+3:end_idx].strip()
            self.chat_display.insert(tk.END, "\n")
            self.chat_display.insert(tk.END, code_block, "code")
            self.chat_display.insert(tk.END, "\n")
            
            # Continue with the rest of the text
            remaining_text = remaining_text[end_idx+3:]
        
        # Add any remaining text
        if remaining_text:
            # Process inline code
            while "`" in remaining_text:
                start_idx = remaining_text.find("`")
                end_idx = remaining_text.find("`", start_idx + 1)
                
                if end_idx == -1:  # No closing backtick
                    self.chat_display.insert(tk.END, remaining_text)
                    break
                
                # Add text before the inline code
                if start_idx > 0:
                    self.chat_display.insert(tk.END, remaining_text[:start_idx])
                
                # Add the inline code
                inline_code = remaining_text[start_idx+1:end_idx]
                self.chat_display.insert(tk.END, inline_code, "code")
                
                # Continue with the rest of the text
                remaining_text = remaining_text[end_idx+1:]
            
            # Add any final remaining text
            if remaining_text:
                self.chat_display.insert(tk.END, remaining_text)
        
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        """Send a message to the Ollama API"""
        if self.is_generating:
            return
        
        message = self.user_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        model = self.selected_model.get()
        if not model:
            messagebox.showwarning("No Model Selected", "Please select a model first.")
            return
        
        # Add user message to chat
        self.add_to_chat(message, "user")
        
        # Clear input
        self.user_input.delete("1.0", tk.END)
        
        # Add to chat history
        self.chat_history.append({
            "role": "user",
            "content": message
        })
        
        # Prepare messages array
        messages = []
        
        # Add system message if provided
        system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add chat history
        messages.extend(self.chat_history)
        
        # Send to API
        self.is_generating = True
        self.status_label.config(text="Generating response...")
        
        def generate():
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature.get(),
                        "num_predict": self.max_tokens.get()
                    }
                }
                
                response = requests.post(f"{OLLAMA_API_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("message") and data["message"].get("content"):
                        content = data["message"]["content"]
                        
                        # Add to chat history
                        self.chat_history.append({
                            "role": "assistant",
                            "content": content
                        })
                        
                        # Update UI in the main thread
                        self.root.after(0, lambda: self.add_to_chat(content, "assistant"))
                        self.root.after(0, lambda: self.status_label.config(text="Ready"))
                    else:
                        self.root.after(0, lambda: self.add_to_chat(
                            "Error: Received empty response from model.", "system"))
                        self.root.after(0, lambda: self.status_label.config(text="Error"))
                else:
                    error_msg = f"Error: API returned {response.status_code}"
                    try:
                        error_data = response.json()
                        if error_data.get("error"):
                            error_msg = f"Error: {error_data['error']}"
                    except:
                        pass
                    
                    self.root.after(0, lambda: self.add_to_chat(error_msg, "system"))
                    self.root.after(0, lambda: self.status_label.config(text="Error"))
            except Exception as e:
                self.root.after(0, lambda: self.add_to_chat(
                    f"Error: {str(e)}", "system"))
                self.root.after(0, lambda: self.status_label.config(text="Error"))
            finally:
                self.root.after(0, lambda: setattr(self, 'is_generating', False))
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=generate, daemon=True).start()
    
    def new_chat(self):
        """Start a new chat"""
        if self.chat_history and messagebox.askyesno(
            "New Chat", "This will clear the current chat. Continue?"):
            self.clear_chat()
        elif not self.chat_history:
            self.clear_chat()
    
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_history = []
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        model = self.selected_model.get()
        if model:
            self.add_to_chat(f"Model '{model}' selected. Start chatting!", "system")
        else:
            self.add_to_chat("Welcome to Ollama Chat! Select a model to start chatting.", "system")
    
    def save_chat(self):
        """Save the chat history to a file"""
        if not self.chat_history:
            messagebox.showinfo("Info", "No chat to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Chat History"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "model": self.selected_model.get(),
                    "system_prompt": self.system_prompt_text.get("1.0", tk.END).strip(),
                    "temperature": self.temperature.get(),
                    "max_tokens": self.max_tokens.get(),
                    "history": self.chat_history,
                    "timestamp": datetime.now().isoformat(),
                    "app_version": APP_VERSION
                }, f, indent=2)
            
            self.status_label.config(text=f"Chat saved to {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save chat: {str(e)}")
    
    def load_chat(self):
        """Load chat history from a file"""
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Chat History"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load settings
            if data.get("model") in self.models:
                self.selected_model.set(data["model"])
            
            if "system_prompt" in data:
                self.system_prompt_text.delete("1.0", tk.END)
                self.system_prompt_text.insert("1.0", data["system_prompt"])
            
            if "temperature" in data:
                self.temperature.set(data["temperature"])
            
            if "max_tokens" in data:
                self.max_tokens.set(data["max_tokens"])
            
            # Load chat history
            self.chat_history = data.get("history", [])
            
            # Update chat display
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            
            # Add loaded messages to display
            self.add_to_chat(f"Chat loaded from {os.path.basename(file_path)}", "system")
            for msg in self.chat_history:
                self.add_to_chat(msg["content"], msg["role"])
            
            self.chat_display.config(state=tk.DISABLED)
            self.status_label.config(text=f"Chat loaded from {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load chat: {str(e)}")
    
    def copy_selected(self):
        """Copy selected text to clipboard"""
        try:
            selected_text = self.chat_display.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.status_label.config(text="Text copied to clipboard")
        except:
            self.status_label.config(text="No text selected")
    
    def copy_last_response(self):
        """Copy the last assistant response to clipboard"""
        for msg in reversed(self.chat_history):
            if msg["role"] == "assistant":
                self.root.clipboard_clear()
                self.root.clipboard_append(msg["content"])
                self.status_label.config(text="Last response copied to clipboard")
                return
        
        self.status_label.config(text="No assistant response to copy")
    
    def show_about(self):
        """Show the about dialog"""
        about_text = f"""Ollama Chat GUI v{APP_VERSION}

A simple graphical interface for chatting with Ollama models.

• API URL: {OLLAMA_API_URL}
• Python: {sys.version.split()[0]}
• Tkinter: {tk.TkVersion}

This application allows you to interact with any model
installed in your Ollama instance.
"""
        messagebox.showinfo("About Ollama Chat GUI", about_text)
    
    def on_close(self):
        """Handle window close event"""
        if self.is_generating:
            if not messagebox.askyesno(
                "Generating in Progress", 
                "A response is currently being generated. Are you sure you want to exit?"
            ):
                return
        
        if self.chat_history and not messagebox.askyesno(
            "Exit", "Do you want to exit? Any unsaved chat will be lost."
        ):
            return
        
        self.root.destroy()

def main():
    # Set up command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Ollama Chat GUI')
    parser.add_argument('--api-url', type=str, help='Ollama API URL')
    args = parser.parse_args()
    
    # Set API URL from args if provided
    global OLLAMA_API_URL
    if args.api_url:
        OLLAMA_API_URL = args.api_url
    
    # Create and run the GUI
    root = tk.Tk()
    app = OllamaChatGUI(root)
    
    # Apply a theme if available
    try:
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes:
            style.theme_use('vista')
    except:
        pass  # Use default theme if custom themes fail
    
    root.mainloop()

if __name__ == "__main__":
    main()
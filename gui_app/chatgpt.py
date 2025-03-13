#!/usr/bin/env python3
"""
ChatGPT-style UI for Ollama
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
OLLAMA_API_URLRSION = "1.0.0"

class ChatGPTStyle(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ollama Chat - ChatGPT Style")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.configure(bg="#312f2e")  # Dark charcoal/slate background
        
        # Variables
        self.models = []
        self.selected_model = tk.StringVar()
        self.temperature = tk.DoubleVar(value=0.7)
        self.max_tokens = tk.IntVar(value=1024)
        self.system_prompt = tk.StringVar(value="You are a helpful assistant.")
        self.chat_history = []
        self.is_generating = False
        self.current_chats = []  # List of chat titles for sidebar
        self.dark_mode = True

        # Ollama connection settings
        self.ollama_api_url = tk.StringVar(value=OLLAMA_API_URL)
        self.connection_status = tk.StringVar(value="Not Connected")
        
        # Create UI
        self.create_ui()
        
        # Fetch models
        self.fetch_models()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-n>", lambda e: self.new_chat())

    def create_ui(self):
        """Create the main UI elements in ChatGPT style"""
        # Configure styles for dark theme
        self.configure_styles()
        
        # Main layout - 3 panels: sidebar, chat area, settings panel
        self.sidebar_frame = tk.Frame(self, bg="#212020", width=250)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)  # Don't shrink

        self.chat_frame = tk.Frame(self, bg="#312f2e")
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Create sidebar
        self.setup_sidebar()
        
        # Create chat area
        self.setup_chat_area()

    def configure_styles(self):
        """Configure ttk styles for dark theme"""
        self.style = ttk.Style()
        
        # Configure dark charcoal theme colors
        self.style.configure("TFrame", background="#312f2e")
        self.style.configure("TButton",
                            background="#413e3d",
                            foreground="#ffffff",
                            borderwidth=0,
                            focuscolor="#413e3d",
                            lightcolor="#413e3d",
                            darkcolor="#413e3d")
        self.style.map("TButton",
                      background=[("active", "#514e4d"), ("pressed", "#212020")])

        self.style.configure("Sidebar.TButton",
                            background="#212020",
                            foreground="#ffffff",
                            borderwidth=0)
        self.style.map("Sidebar.TButton",
                      background=[("active", "#413e3d"), ("pressed", "#111111")])

        self.style.configure("TLabel",
                            background="#312f2e",
                            foreground="#ffffff")

        self.style.configure("Sidebar.TLabel",
                            background="#212020",
                            foreground="#ffffff")

        self.style.configure("TEntry",
                            fieldbackground="#413e3d",
                            foreground="#ffffff",
                            insertcolor="#ffffff")

        self.style.configure("TCombobox",
                            fieldbackground="#413e3d",
                            background="#413e3d",
                            foreground="#ffffff",
                            arrowcolor="#ffffff")

        self.style.map("TCombobox",
                      fieldbackground=[("readonly", "#413e3d")])

        self.style.configure("Horizontal.TScale",
                            background="#312f2e",
                            troughcolor="#413e3d")

    def setup_sidebar(self):
        """Set up the sidebar with new chat button and chat history"""
        # New chat button with pen icon
        new_chat_frame = tk.Frame(self.sidebar_frame, bg="#212020")
        new_chat_frame.pack(fill=tk.X, padx=10, pady=10)

        # Pen icon (using Unicode character)
        pen_icon = tk.Label(new_chat_frame, text="✏️", bg="#212020", fg="#ffffff", font=("Segoe UI", 14))
        pen_icon.pack(side=tk.LEFT, padx=(0, 5))

        new_chat_btn = ttk.Button(new_chat_frame,
                                 text="New chat",
                                 style="Sidebar.TButton",
                                 command=self.new_chat)
        new_chat_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Separator
        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # Chat history list (scrollable)
        chat_list_container = tk.Frame(self.sidebar_frame, bg="#212020")
        chat_list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add a scrollbar
        chat_list_scrollbar = ttk.Scrollbar(chat_list_container)
        chat_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a canvas for scrolling
        chat_list_canvas = tk.Canvas(chat_list_container, bg="#212020",
                                   highlightthickness=0, bd=0,
                                   yscrollcommand=chat_list_scrollbar.set)
        chat_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        chat_list_scrollbar.config(command=chat_list_canvas.yview)

        # Create a frame inside the canvas for chat buttons
        self.chat_list_frame = tk.Frame(chat_list_canvas, bg="#212020")
        chat_list_canvas.create_window((0, 0), window=self.chat_list_frame, anchor="nw", width=chat_list_canvas.winfo_width())

        # Configure the canvas to resize with the frame
        self.chat_list_frame.bind("<Configure>",
                                lambda e: chat_list_canvas.configure(scrollregion=chat_list_canvas.bbox("all")))

        # Add some example chats
        self.add_chat_to_sidebar("Welcome to Ollama Chat")
        self.add_chat_to_sidebar("My first conversation")
        
        # Bottom section with settings
        bottom_frame = tk.Frame(self.sidebar_frame, bg="#212020")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        # Model selector
        ttk.Label(bottom_frame, text="Model:", style="Sidebar.TLabel").pack(anchor=tk.W, pady=(0, 5))
        self.model_combobox = ttk.Combobox(bottom_frame, 
                                          textvariable=self.selected_model, 
                                          state="readonly",
                                          style="TCombobox")
        self.model_combobox.pack(fill=tk.X, pady=(0, 10))
        self.model_combobox["values"] = ["Loading models..."]
        self.model_combobox.current(0)
        self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_selected)
        
        # Settings button
        settings_btn = ttk.Button(bottom_frame,
                                 text="Settings",
                                 style="Sidebar.TButton",
                                 command=self.show_settings)
        settings_btn.pack(fill=tk.X, pady=5)

        # Save Chat button
        save_btn = ttk.Button(bottom_frame,
                             text="Save Chat",
                             style="Sidebar.TButton",
                             command=self.save_chat_to_file)
        save_btn.pack(fill=tk.X, pady=5)

        # Load Chat button
        load_btn = ttk.Button(bottom_frame,
                             text="Load Chat",
                             style="Sidebar.TButton",
                             command=self.load_chat_from_file)
        load_btn.pack(fill=tk.X, pady=5)

    def setup_chat_area(self):
        """Set up the main chat area"""
        # Chat messages area (scrollable)
        self.chat_display_frame = tk.Frame(self.chat_frame, bg="#312f2e")
        self.chat_display_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Create a canvas for scrolling
        self.chat_canvas = tk.Canvas(self.chat_display_frame, bg="#312f2e",
                                    highlightthickness=0, bd=0)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.chat_display_frame, orient=tk.VERTICAL,
                                 command=self.chat_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame inside the canvas for messages
        self.messages_frame = tk.Frame(self.chat_canvas, bg="#312f2e")
        self.messages_frame.bind("<Configure>",
                               lambda e: self.chat_canvas.configure(
                                   scrollregion=self.chat_canvas.bbox("all")))
        
        # Create window in canvas
        self.canvas_frame = self.chat_canvas.create_window((0, 0), 
                                                         window=self.messages_frame, 
                                                         anchor="nw")
        
        # Bind canvas resize to adjust the inner frame
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Input area at bottom
        input_frame = tk.Frame(self.chat_frame, bg="#413e3d", height=120)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        input_frame.pack_propagate(False)  # Don't shrink

        # Text input with rounded corners (using a frame trick)
        input_container = tk.Frame(input_frame, bg="#413e3d", padx=10, pady=10)
        input_container.pack(fill=tk.BOTH, expand=True)

        self.user_input = tk.Text(input_container, bg="#413e3d", fg="#ffffff",
                                 font=("Segoe UI", 11), height=3, bd=1,
                                 relief=tk.FLAT, padx=10, pady=10,
                                 insertbackground="#ffffff", wrap=tk.WORD)
        self.user_input.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.user_input.bind("<Control-Return>", self.send_message)
        
        # Placeholder text
        self.user_input.insert("1.0", "Message Ollama...")
        self.user_input.bind("<FocusIn>", self.clear_placeholder)
        self.user_input.bind("<FocusOut>", self.add_placeholder)
        
        # Send button
        send_btn = ttk.Button(input_container, text="Send", command=self.send_message)
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add initial welcome message
        self.add_system_message("Welcome to Ollama Chat! Select a model to start chatting.")

    def on_canvas_configure(self, event):
        """Handle canvas resize"""
        # Update the width of the frame to fill the canvas
        self.chat_canvas.itemconfig(self.canvas_frame, width=event.width)

    def add_chat_to_sidebar(self, title):
        """Add a chat to the sidebar with options to rename and share"""
        chat_frame = tk.Frame(self.chat_list_frame, bg="#212020")
        chat_frame.pack(fill=tk.X, padx=5, pady=2)

        # Chat button with title
        chat_btn = ttk.Button(chat_frame,
                             text=title,
                             style="Sidebar.TButton")
        chat_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Options menu (three dots)
        options_btn = ttk.Button(chat_frame,
                                text="⋮",
                                style="Sidebar.TButton",
                                width=2,
                                command=lambda t=title: self.show_chat_options(t, chat_frame))
        options_btn.pack(side=tk.RIGHT)

        self.current_chats.append(title)

    def show_chat_options(self, title, parent_frame):
        """Show options for a chat (rename, share, delete)"""
        # Create a popup menu
        options_menu = tk.Menu(self, tearoff=0, bg="#312f2e", fg="#ffffff",
                              activebackground="#413e3d", activeforeground="#ffffff",
                              bd=0)

        # Add menu items
        options_menu.add_command(label="Rename chat",
                                command=lambda: self.rename_chat(title, parent_frame))
        options_menu.add_command(label="Invite friends",
                                command=lambda: self.invite_friends(title))
        options_menu.add_separator()
        options_menu.add_command(label="Delete chat",
                                command=lambda: self.delete_chat(title, parent_frame))

        # Display the menu
        try:
            options_menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            options_menu.grab_release()

    def rename_chat(self, old_title, parent_frame):
        """Rename a chat"""
        # Create a dialog for renaming
        dialog = tk.Toplevel(self)
        dialog.title("Rename Chat")
        dialog.geometry("300x120")
        dialog.configure(bg="#FFFFFF")
        dialog.grab_set()  # Make modal

        # Center the dialog
        dialog.geometry(f"+{self.winfo_rootx() + 50}+{self.winfo_rooty() + 50}")

        # Dialog content
        frame = tk.Frame(dialog, bg="#FFFFFF", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="New chat name:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))

        entry = ttk.Entry(frame)
        entry.pack(fill=tk.X, pady=(0, 10))
        entry.insert(0, old_title)
        entry.select_range(0, tk.END)
        entry.focus_set()

        # Buttons
        button_frame = tk.Frame(frame, bg="#1E1E1E")
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel",
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        def save_rename():
            new_title = entry.get().strip()
            if new_title and new_title != old_title:
                # Update the button text
                for child in parent_frame.winfo_children():
                    if isinstance(child, ttk.Button) and child.cget("text") == old_title:
                        child.config(text=new_title)
                        break

                # Update the list
                idx = self.current_chats.index(old_title)
                self.current_chats[idx] = new_title

            dialog.destroy()

        ttk.Button(button_frame, text="Save",
                  command=save_rename).pack(side=tk.RIGHT, padx=5)

    def invite_friends(self, title):
        """Invite friends to a chat"""
        # Create a dialog for inviting friends
        dialog = tk.Toplevel(self)
        dialog.title("Invite Friends")
        dialog.geometry("400x300")
        dialog.configure(bg="#FFFFFF")
        dialog.grab_set()  # Make modal

        # Center the dialog
        dialog.geometry(f"+{self.winfo_rootx() + 50}+{self.winfo_rooty() + 50}")

        # Dialog content
        frame = tk.Frame(dialog, bg="#FFFFFF", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Invite friends to join '{title}'", style="TLabel").pack(anchor=tk.W, pady=(0, 10))

        # Email input
        ttk.Label(frame, text="Enter email addresses (comma separated):", style="TLabel").pack(anchor=tk.W, pady=(0, 5))

        email_entry = ttk.Entry(frame)
        email_entry.pack(fill=tk.X, pady=(0, 15))
        email_entry.focus_set()

        # Message input
        ttk.Label(frame, text="Add a message (optional):", style="TLabel").pack(anchor=tk.W, pady=(0, 5))

        message_text = tk.Text(frame, bg="#F7F7F8", fg="#333333", height=5,
                             font=("Segoe UI", 10), padx=10, pady=10,
                             insertbackground="#333333", wrap=tk.WORD)
        message_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        message_text.insert("1.0", f"I'd like to share my Ollama chat '{title}' with you!")

        # Buttons
        button_frame = tk.Frame(frame, bg="#FFFFFF")
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel",
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        def send_invites():
            emails = email_entry.get().strip()
            message = message_text.get("1.0", "end-1c")

            if emails:
                # In a real app, this would send actual invitations
                # For now, just show a confirmation
                messagebox.showinfo("Invitations Sent",
                                   f"Invitations to '{title}' have been sent to: {emails}")
                dialog.destroy()
            else:
                messagebox.showwarning("No Recipients",
                                      "Please enter at least one email address.")

        ttk.Button(button_frame, text="Send Invitations",
                  command=send_invites).pack(side=tk.RIGHT, padx=5)

    def delete_chat(self, title, parent_frame):
        """Delete a chat"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}'?"):
            # Remove from UI
            parent_frame.destroy()

            # Remove from list
            if title in self.current_chats:
                self.current_chats.remove(title)

    def add_system_message(self, text):
        """Add a system message to the chat"""
        message_frame = tk.Frame(self.messages_frame, bg="#413e3d", padx=20, pady=10)
        message_frame.pack(fill=tk.X, padx=0, pady=5)

        message_label = tk.Label(message_frame, text=text, bg="#413e3d", fg="#cccccc",
                               font=("Segoe UI", 11), justify=tk.LEFT, wraplength=700)
        message_label.pack(anchor=tk.W)

    def add_user_message(self, text):
        """Add a user message to the chat"""
        message_frame = tk.Frame(self.messages_frame, bg="#312f2e", padx=20, pady=10)
        message_frame.pack(fill=tk.X, padx=0, pady=0)

        # User icon
        icon_label = tk.Label(message_frame, text="👤", bg="#312f2e", fg="#ffffff",
                            font=("Segoe UI", 14))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Message content
        message_label = tk.Label(message_frame, text=text, bg="#312f2e", fg="#ffffff",
                               font=("Segoe UI", 11), justify=tk.LEFT, wraplength=700)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scroll to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def add_assistant_message(self, text):
        """Add an assistant message to the chat"""
        message_frame = tk.Frame(self.messages_frame, bg="#413e3d", padx=20, pady=10)
        message_frame.pack(fill=tk.X, padx=0, pady=0)

        # Assistant icon
        icon_label = tk.Label(message_frame, text="🤖", bg="#413e3d", fg="#ffffff",
                            font=("Segoe UI", 14))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Process markdown-like formatting
        formatted_text = self.format_markdown(text)

        # Message content
        message_label = tk.Label(message_frame, text=formatted_text, bg="#413e3d", fg="#ffffff",
                               font=("Segoe UI", 11), justify=tk.LEFT, wraplength=700)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scroll to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def format_markdown(self, text):
        """Simple markdown formatting for display"""
        # This is a simplified version - in a real app, you'd use a proper markdown parser
        # or rich text widget instead of a Label
        return text

    def clear_placeholder(self, event):
        """Clear placeholder text when input is focused"""
        if self.user_input.get("1.0", "end-1c") == "Message Ollama...":
            self.user_input.delete("1.0", tk.END)
            self.user_input.config(fg="white")

    def add_placeholder(self, event):
        """Add placeholder text when input loses focus and is empty"""
        if not self.user_input.get("1.0", "end-1c").strip():
            self.user_input.delete("1.0", tk.END)
            self.user_input.config(fg="gray")
            self.user_input.insert("1.0", "Message Ollama...")

    def test_connection(self):
        """Test the connection to the Ollama API"""
        api_url = self.ollama_api_url.get()

        # Update status indicator to yellow (testing)
        self.status_indicator.itemconfig("status_light", fill="yellow")
        self.connection_status.set("Testing...")

        def test():
            try:
                response = requests.get(f"{api_url}/tags", timeout=5)
                if response.status_code == 200:
                    # Connection successful
                    self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="green"))
                    self.after(0, lambda: self.connection_status.set("Connected"))
                    self.after(0, lambda: messagebox.showinfo(
                        "Connection Successful",
                        f"Successfully connected to Ollama API at {api_url}"))
                else:
                    # API returned an error
                    self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="red"))
                    self.after(0, lambda: self.connection_status.set("Error"))
                    self.after(0, lambda: messagebox.showerror(
                        "API Error",
                        f"Error connecting to API: Server returned {response.status_code}"))
            except requests.exceptions.Timeout:
                # Connection timed out
                self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="red"))
                self.after(0, lambda: self.connection_status.set("Timeout"))
                self.after(0, lambda: messagebox.showerror(
                    "Connection Timeout",
                    f"Connection to {api_url} timed out.\n\nPlease check if the server is running and accessible."))
            except Exception as e:
                # Other connection error
                self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="red"))
                self.after(0, lambda: self.connection_status.set("Error"))
                self.after(0, lambda: messagebox.showerror(
                    "Connection Error",
                    f"Could not connect to Ollama API at {api_url}.\n\n"
                    f"Error: {str(e)}"))

        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=test, daemon=True).start()

    def fetch_models_for_listbox(self, listbox):
        """Fetch models and update the listbox"""
        # Clear the listbox
        listbox.delete(0, tk.END)
        listbox.insert(tk.END, "Fetching models...")

        def fetch():
            try:
                response = requests.get(f"{self.ollama_api_url.get()}/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]

                    # Update listbox in the main thread
                    self.after(0, lambda: listbox.delete(0, tk.END))
                    for model in models:
                        self.after(0, lambda m=model: listbox.insert(tk.END, m))
                else:
                    self.after(0, lambda: listbox.delete(0, tk.END))
                    self.after(0, lambda: listbox.insert(tk.END, f"Error: API returned {response.status_code}"))
            except Exception as e:
                self.after(0, lambda: listbox.delete(0, tk.END))
                self.after(0, lambda: listbox.insert(tk.END, f"Error: {str(e)}"))

        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=fetch, daemon=True).start()

    def fetch_models(self):
        """Fetch available models from Ollama API"""
        # Update connection status
        if hasattr(self, 'status_indicator'):
            self.status_indicator.itemconfig("status_light", fill="yellow")
            self.connection_status.set("Connecting...")

        def fetch():
            try:
                response = requests.get(f"{self.ollama_api_url.get()}/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]

                    # Update UI in the main thread
                    self.after(0, lambda: self.update_models(models))

                    # Update connection status if indicator exists
                    if hasattr(self, 'status_indicator'):
                        self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="green"))
                        self.after(0, lambda: self.connection_status.set("Connected"))
                else:
                    if hasattr(self, 'status_indicator'):
                        self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="red"))
                        self.after(0, lambda: self.connection_status.set("Error"))

                    self.after(0, lambda: messagebox.showerror(
                        "API Error",
                        f"Error fetching models: API returned {response.status_code}"))
            except Exception as e:
                if hasattr(self, 'status_indicator'):
                    self.after(0, lambda: self.status_indicator.itemconfig("status_light", fill="red"))
                    self.after(0, lambda: self.connection_status.set("Error"))

                self.after(0, lambda: messagebox.showerror(
                    "Connection Error",
                    f"Could not connect to Ollama API at {self.ollama_api_url.get()}.\n\n"
                    f"Make sure Ollama is running and try again.\n\nError: {str(e)}"))

        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=fetch, daemon=True).start()

    def update_models(self, models):
        """Update the model dropdown with fetched models"""
        self.models = models
        
        if models:
            self.model_combobox["values"] = models
            self.model_combobox.current(0)  # Select first model
            self.selected_model.set(models[0])
            self.add_system_message(f"Model '{models[0]}' selected. Start chatting!")
        else:
            self.model_combobox["values"] = ["No models available"]
            self.model_combobox.current(0)
            messagebox.showwarning(
                "No Models Found", 
                "No models were found in your Ollama installation.\n\n"
                "Please install at least one model using 'ollama pull <model>'")

    def on_model_selected(self, event):
        """Handle model selection"""
        model = self.selected_model.get()
        if model and model != "Loading models..." and model != "No models available":
            self.new_chat()
            self.add_system_message(f"Model '{model}' selected. Start chatting!")

    def send_message(self, event=None):
        """Send a message to the Ollama API"""
        if self.is_generating:
            return
        
        # Get message text, handling placeholder
        message_text = self.user_input.get("1.0", tk.END).strip()
        if not message_text or message_text == "Message Ollama...":
            return
        
        model = self.selected_model.get()
        if not model or model == "Loading models..." or model == "No models available":
            messagebox.showwarning("No Model Selected", "Please select a model first.")
            return
        
        # Add user message to chat
        self.add_user_message(message_text)
        
        # Clear input
        self.user_input.delete("1.0", tk.END)
        self.user_input.config(fg="white")  # Reset color in case it was gray
        
        # Add to chat history
        self.chat_history.append({
            "role": "user",
            "content": message_text
        })
        
        # Prepare messages array
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": self.system_prompt.get()
        })
        
        # Add chat history
        messages.extend(self.chat_history)
        
        # Send to API
        self.is_generating = True
        
        # Add a temporary "thinking" message
        thinking_frame = tk.Frame(self.messages_frame, bg="#444654", padx=20, pady=10)
        thinking_frame.pack(fill=tk.X, padx=0, pady=0)
        
        icon_label = tk.Label(thinking_frame, text="🤖", bg="#444654", fg="white",
                            font=("Segoe UI", 14))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        thinking_label = tk.Label(thinking_frame, text="Thinking...", bg="#444654", fg="#ECECF1",
                                font=("Segoe UI", 11, "italic"))
        thinking_label.pack(side=tk.LEFT)
        
        # Scroll to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        
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
                
                response = requests.post(f"{self.ollama_api_url.get()}/chat", json=payload)
                
                # Remove thinking message
                self.after(0, lambda: thinking_frame.destroy())
                
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
                        self.after(0, lambda: self.add_assistant_message(content))
                    else:
                        self.after(0, lambda: self.add_system_message(
                            "Error: Received empty response from model."))
                else:
                    error_msg = f"Error: API returned {response.status_code}"
                    try:
                        error_data = response.json()
                        if error_data.get("error"):
                            error_msg = f"Error: {error_data['error']}"
                    except:
                        pass
                    
                    self.after(0, lambda: self.add_system_message(error_msg))
            except Exception as e:
                self.after(0, lambda: thinking_frame.destroy())
                self.after(0, lambda: self.add_system_message(f"Error: {str(e)}"))
            finally:
                self.after(0, lambda: setattr(self, 'is_generating', False))
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=generate, daemon=True).start()

    def new_chat(self, prompt_for_title=True):
        """Start a new chat"""
        # Clear chat history
        self.chat_history = []

        # Clear chat display
        for widget in self.messages_frame.winfo_children():
            widget.destroy()

        # Add welcome message
        model = self.selected_model.get()
        if model and model != "Loading models..." and model != "No models available":
            self.add_system_message(f"Model '{model}' selected. Start chatting!")
        else:
            self.add_system_message("Welcome to Ollama Chat! Select a model to start chatting.")

        # Prompt for chat title if requested
        if prompt_for_title:
            self.prompt_for_chat_title()

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("600x500")
        settings_window.configure(bg="#312f2e")
        settings_window.grab_set()  # Make modal

        # Create a notebook with tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # General settings tab
        general_frame = tk.Frame(notebook, bg="#312f2e", padx=20, pady=20)
        notebook.add(general_frame, text="General")

        # System prompt
        ttk.Label(general_frame, text="System Prompt:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))
        system_prompt_text = tk.Text(general_frame, bg="#413e3d", fg="white", height=5,
                                   font=("Segoe UI", 11), padx=10, pady=10,
                                   insertbackground="white", wrap=tk.WORD)
        system_prompt_text.pack(fill=tk.X, pady=(0, 15))
        system_prompt_text.insert("1.0", self.system_prompt.get())

        # Temperature
        ttk.Label(general_frame, text=f"Temperature: {self.temperature.get():.1f}", style="TLabel").pack(anchor=tk.W, pady=(0, 5))
        temp_scale = ttk.Scale(general_frame, from_=0.0, to=1.0, variable=self.temperature,
                              orient=tk.HORIZONTAL, length=200)
        temp_scale.pack(fill=tk.X, pady=(0, 15))

        # Max tokens
        ttk.Label(general_frame, text="Max Tokens:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))
        max_tokens_entry = ttk.Entry(general_frame, textvariable=self.max_tokens)
        max_tokens_entry.pack(fill=tk.X, pady=(0, 15))

        # Connection settings tab
        connection_frame = tk.Frame(notebook, bg="#312f2e", padx=20, pady=20)
        notebook.add(connection_frame, text="Connection")

        # Ollama API URL
        ttk.Label(connection_frame, text="Ollama API URL:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))
        api_url_frame = tk.Frame(connection_frame, bg="#312f2e")
        api_url_frame.pack(fill=tk.X, pady=(0, 10))

        api_url_entry = ttk.Entry(api_url_frame, textvariable=self.ollama_api_url)
        api_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        test_conn_btn = ttk.Button(api_url_frame, text="Test Connection",
                                  command=self.test_connection)
        test_conn_btn.pack(side=tk.RIGHT)

        # Connection status
        status_frame = tk.Frame(connection_frame, bg="#312f2e", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=10)

        ttk.Label(status_frame, text="Status:", style="TLabel").pack(side=tk.LEFT, padx=(0, 10))

        self.status_indicator = tk.Canvas(status_frame, width=15, height=15, bg="#312f2e", highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.status_indicator.create_oval(2, 2, 13, 13, fill="red", tags="status_light")

        status_label = ttk.Label(status_frame, textvariable=self.connection_status, style="TLabel")
        status_label.pack(side=tk.LEFT)

        # Connection instructions
        instruction_text = "You can connect to a local or remote Ollama instance.\n\n" + \
                          "Local: http://localhost:11434/api\n" + \
                          "Remote: http://server-ip:11434/api\n\n" + \
                          "Note: For remote connections, ensure the Ollama server allows remote access."

        instruction_label = ttk.Label(connection_frame, text=instruction_text, style="TLabel",
                                    wraplength=400, justify=tk.LEFT)
        instruction_label.pack(anchor=tk.W, pady=20)

        # Models tab
        models_frame = tk.Frame(notebook, bg="#312f2e", padx=20, pady=20)
        notebook.add(models_frame, text="Models")

        # Download models section
        ttk.Label(models_frame, text="Download New Models:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))

        model_frame = tk.Frame(models_frame, bg="#312f2e")
        model_frame.pack(fill=tk.X, pady=(0, 15))

        model_entry = ttk.Entry(model_frame)
        model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        model_entry.insert(0, "llama3")

        download_btn = ttk.Button(model_frame, text="Download",
                                 command=lambda: self.download_model(model_entry.get()))
        download_btn.pack(side=tk.RIGHT)

        # Available models list
        ttk.Label(models_frame, text="Available Models:", style="TLabel").pack(anchor=tk.W, pady=(10, 5))

        models_list_frame = tk.Frame(models_frame, bg="#413e3d", bd=1, relief=tk.SUNKEN)
        models_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        models_listbox = tk.Listbox(models_list_frame, bg="#413e3d", fg="white",
                                  selectbackground="#514e4d", bd=0, highlightthickness=0)
        models_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        models_scrollbar = ttk.Scrollbar(models_list_frame, orient=tk.VERTICAL, command=models_listbox.yview)
        models_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        models_listbox.config(yscrollcommand=models_scrollbar.set)

        # Populate models list
        for model in self.models:
            models_listbox.insert(tk.END, model)

        refresh_btn = ttk.Button(models_frame, text="Refresh Models",
                               command=lambda: self.fetch_models_for_listbox(models_listbox))
        refresh_btn.pack(anchor=tk.E, pady=(5, 0))

        # Buttons at the bottom of the window
        button_frame = tk.Frame(settings_window, bg="#312f2e")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Save",
                  command=lambda: self.save_settings(system_prompt_text.get("1.0", "end-1c"),
                                                   api_url_entry.get(),
                                                   settings_window)).pack(side=tk.RIGHT, padx=5)

        ttk.Button(button_frame, text="Cancel",
                  command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)

    def save_settings(self, system_prompt, api_url, window):
        """Save settings and close dialog"""
        self.system_prompt.set(system_prompt)

        # Update API URL if changed
        if api_url != self.ollama_api_url.get():
            self.ollama_api_url.set(api_url)
            global OLLAMA_API_URL
            OLLAMA_API_URL = api_url
            # Refresh models with new API URL
            self.fetch_models()

        window.destroy()

    def download_model(self, model_name):
        """Download a model from Ollama"""
        if not model_name:
            messagebox.showwarning("Error", "Please enter a model name")
            return
        
        # Create progress window
        progress_window = tk.Toplevel(self)
        progress_window.title(f"Downloading {model_name}")
        progress_window.geometry("400x150")
        progress_window.configure(bg="#343541")
        progress_window.grab_set()  # Make modal
        
        frame = tk.Frame(progress_window, bg="#343541", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Downloading {model_name}...", style="TLabel").pack(pady=(0, 10))
        
        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=300, mode='indeterminate')
        progress.pack(fill=tk.X, pady=10)
        progress.start()
        
        status_label = ttk.Label(frame, text="Starting download...", style="TLabel")
        status_label.pack(pady=10)
        
        def download():
            try:
                # Start the download
                response = requests.post(
                    f"{self.ollama_api_url.get()}/pull",
                    json={"name": model_name},
                    stream=True
                )
                
                if response.status_code != 200:
                    self.after(0, lambda: status_label.config(
                        text=f"Error: API returned {response.status_code}"))
                    return
                
                # Process the streaming response
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get('status', '')
                        self.after(0, lambda s=status: status_label.config(text=s))
                
                # Download complete
                self.after(0, lambda: progress.stop())
                self.after(0, lambda: status_label.config(text="Download complete!"))
                self.after(0, lambda: progress_window.title(f"{model_name} Downloaded"))
                
                # Refresh models list
                self.after(1000, self.fetch_models)
                self.after(2000, progress_window.destroy)
                
            except Exception as e:
                self.after(0, lambda: progress.stop())
                self.after(0, lambda: status_label.config(text=f"Error: {str(e)}"))
        
        # Run in a separate thread
        threading.Thread(target=download, daemon=True).start()

    def load_chat_from_file(self):
        """Load a chat from a file"""
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Load Chat"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Load chat data from file
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)

            # Check if it's a valid chat file
            if "messages" not in chat_data:
                messagebox.showerror("Invalid Chat File", "The selected file does not contain valid chat data.")
                return

            # Start a new chat
            self.new_chat(False)  # Don't prompt for title

            # Set the chat title if available
            if "title" in chat_data:
                self.add_chat_to_sidebar(chat_data["title"])
            else:
                self.add_chat_to_sidebar(f"Loaded Chat {len(self.current_chats) + 1}")

            # Set model if available and exists
            if "model" in chat_data and chat_data["model"] in self.models:
                self.selected_model.set(chat_data["model"])
                self.model_combobox.set(chat_data["model"])

            # Set system prompt if available
            if "system_prompt" in chat_data:
                self.system_prompt.set(chat_data["system_prompt"])

            # Load messages
            self.chat_history = chat_data["messages"]

            # Display messages
            self.add_system_message(f"Chat loaded from {os.path.basename(file_path)}")
            for msg in self.chat_history:
                if msg["role"] == "user":
                    self.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    self.add_assistant_message(msg["content"])

            messagebox.showinfo("Chat Loaded", f"Chat has been loaded from:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error Loading Chat", f"An error occurred while loading the chat:\n{str(e)}")

    def save_chat_to_file(self):
        """Save the current chat to a file"""
        if not self.chat_history:
            messagebox.showinfo("No Chat to Save", "There is no chat content to save.")
            return

        # Get current timestamp for default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"ollama_chat_{timestamp}.json"

        # Ask user for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Save Chat"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Prepare chat data
            chat_data = {
                "title": self.current_chats[-1] if self.current_chats else "Untitled Chat",
                "model": self.selected_model.get(),
                "timestamp": datetime.now().isoformat(),
                "system_prompt": self.system_prompt.get(),
                "messages": self.chat_history,
                "app_version": APP_VERSION
            }

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Chat Saved", f"Chat has been saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving Chat", f"An error occurred while saving the chat:\n{str(e)}")

    def prompt_for_chat_title(self):
        """Prompt the user for a chat title"""
        # Create a dialog for chat title
        dialog = tk.Toplevel(self)
        dialog.title("New Chat")
        dialog.geometry("300x150")
        dialog.configure(bg="#312f2e")
        dialog.grab_set()  # Make modal

        # Center the dialog
        dialog.geometry(f"+{self.winfo_rootx() + 50}+{self.winfo_rooty() + 50}")

        # Dialog content
        frame = tk.Frame(dialog, bg="#312f2e", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Enter a title for your chat:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))

        entry = ttk.Entry(frame)
        entry.pack(fill=tk.X, pady=(0, 10))
        entry.insert(0, f"Chat {len(self.current_chats) + 1}")
        entry.select_range(0, tk.END)
        entry.focus_set()

        # Buttons
        button_frame = tk.Frame(frame, bg="#312f2e")
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel",
                  command=lambda: self.finish_new_chat(f"Chat {len(self.current_chats) + 1}", dialog)).pack(side=tk.RIGHT, padx=5)

        def save_title():
            title = entry.get().strip()
            if not title:
                title = f"Chat {len(self.current_chats) + 1}"
            self.finish_new_chat(title, dialog)

        ttk.Button(button_frame, text="Create",
                  command=save_title).pack(side=tk.RIGHT, padx=5)

        # Bind Enter key to save
        entry.bind("<Return>", lambda e: save_title())

    def finish_new_chat(self, title, dialog=None):
        """Finish creating a new chat with the given title"""
        # Add to sidebar
        self.add_chat_to_sidebar(title)

        # Close dialog if open
        if dialog:
            dialog.destroy()

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

        self.destroy()

def main():
    # Set up command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Ollama Chat - ChatGPT Style')
    parser.add_argument('--api-url', type=str, help='Ollama API URL')
    args = parser.parse_args()

    # Set API URL from args if provided
    global OLLAMA_API_URL
    if args.api_url:
        OLLAMA_API_URL = args.api_url

    # Create and run the GUI
    app = ChatGPTStyle()

    # Set the API URL from command line if provided
    if args.api_url:
        app.ollama_api_url.set(args.api_url)

    app.mainloop()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
PromptForge V2.5 - Enhanced UI Framework
Multi-pane layout with integrated AI communication
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
import json
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class UIState(Enum):
    IDLE = "idle"
    AI_THINKING = "ai_thinking"
    EXECUTING_SCENARIO = "executing_scenario"
    ERROR = "error"

@dataclass
class AIMessage:
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    attachments: Optional[list] = None

class V25MainWindow:
    """Enhanced PromptForge V2.5 UI with 3-pane integrated AI bridge"""
    
    def __init__(self, root):
        self.root = root
        self.setup_main_window()
        self.state = UIState.IDLE
        self.ai_conversation = []
        self.current_channel_a_json = None
        self.project_root = None
        
        # Create the three-pane layout
        self.create_panes()
        self.create_ai_chat_pane()
        self.create_scenario_execution_pane()
        self.create_terminal_output_pane()
        
        # Status bar
        self.create_status_bar()
        
        # Initialize state
        self.update_ui_state(UIState.IDLE)
    
    def setup_main_window(self):
        """Configure main window properties"""
        self.root.title("PromptForge V2.5 - Integrated AI Bridge")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 600)
        
        # Configure theme colors (Blue theme for V2.5)
        style = ttk.Style()
        style.theme_use('clam')
        
        # V2.5 Blue theme colors
        self.colors = {
            'primary': '#004499',
            'secondary': '#0066CC', 
            'accent': '#3388FF',
            'success': '#00AA44',
            'warning': '#FF8800',
            'error': '#CC2244',
            'background': '#F8F9FA',
            'surface': '#FFFFFF'
        }
    
    def create_panes(self):
        """Create the main 3-pane layout structure"""
        # Main horizontal paned window
        self.main_paned = ttk.PanedWindow(self.root, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Left pane: AI Chat Interface
        self.ai_frame = ttk.LabelFrame(self.main_paned, text="AI Chat Interface", padding="8")
        self.main_paned.add(self.ai_frame, weight=2, minsize=350)
        
        # Center pane: Scenario Execution  
        self.scenario_frame = ttk.LabelFrame(self.main_paned, text="Scenario Execution", padding="8")
        self.main_paned.add(self.scenario_frame, weight=2, minsize=350)
        
        # Right pane: Terminal Output
        self.terminal_frame = ttk.LabelFrame(self.main_paned, text="Terminal Output", padding="8")
        self.main_paned.add(self.terminal_frame, weight=1, minsize=300)
    
    def create_ai_chat_pane(self):
        """Create AI chat interface components"""
        # Chat history area
        history_frame = ttk.Frame(self.ai_frame)
        history_frame.pack(fill='both', expand=True, pady=(0, 8))
        
        ttk.Label(history_frame, text="Chat History:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.chat_history = scrolledtext.ScrolledText(
            history_frame, 
            height=20, 
            width=50,
            wrap='word',
            state='disabled',
            font=('Consolas', 9)
        )
        self.chat_history.pack(fill='both', expand=True)
        
        # Prompt input area
        prompt_frame = ttk.Frame(self.ai_frame)
        prompt_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(prompt_frame, text="AI Prompt:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.prompt_text = scrolledtext.ScrolledText(
            prompt_frame,
            height=6,
            width=50,
            wrap='word',
            font=('Consolas', 10)
        )
        self.prompt_text.pack(fill='x', pady=(4, 0))
        
        # File attachment area
        attach_frame = ttk.Frame(self.ai_frame)
        attach_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(attach_frame, text="Attachments:", font=('Segoe UI', 9)).pack(anchor='w')
        
        attach_buttons_frame = ttk.Frame(attach_frame)
        attach_buttons_frame.pack(fill='x', pady=(4, 0))
        
        self.attach_file_btn = ttk.Button(
            attach_buttons_frame, 
            text="📎 Attach File", 
            command=self.attach_file
        )
        self.attach_file_btn.pack(side='left', padx=(0, 4))
        
        self.attach_screenshot_btn = ttk.Button(
            attach_buttons_frame,
            text="📷 Screenshot",
            command=self.attach_screenshot
        )
        self.attach_screenshot_btn.pack(side='left')
        
        self.attachments_list = tk.Listbox(attach_frame, height=3)
        self.attachments_list.pack(fill='x', pady=(4, 0))
        
        # Submit button
        self.submit_btn = ttk.Button(
            self.ai_frame,
            text="🚀 Submit to AI",
            command=self.submit_ai_prompt,
            style='Accent.TButton'
        )
        self.submit_btn.pack(fill='x', pady=(0, 4))
        
        # Provider selection
        provider_frame = ttk.Frame(self.ai_frame)
        provider_frame.pack(fill='x')
        
        ttk.Label(provider_frame, text="AI Provider:").pack(side='left')
        self.provider_var = tk.StringVar(value="Anthropic")
        self.provider_combo = ttk.Combobox(
            provider_frame, 
            textvariable=self.provider_var,
            values=["Anthropic", "OpenAI", "Mock (Testing)"],
            state='readonly',
            width=15
        )
        self.provider_combo.pack(side='right')
    
    def create_scenario_execution_pane(self):
        """Create scenario execution interface"""
        # Channel-A JSON preview area
        json_frame = ttk.Frame(self.scenario_frame)
        json_frame.pack(fill='both', expand=True, pady=(0, 8))
        
        json_header = ttk.Frame(json_frame)
        json_header.pack(fill='x', pady=(0, 4))
        
        ttk.Label(json_header, text="Channel-A JSON:", font=('Segoe UI', 9, 'bold')).pack(side='left')
        
        self.validate_json_btn = ttk.Button(
            json_header,
            text="✓ Validate",
            command=self.validate_channel_a_json
        )
        self.validate_json_btn.pack(side='right')
        
        self.channel_a_display = scrolledtext.ScrolledText(
            json_frame,
            height=15,
            width=50,
            wrap='word',
            font=('Consolas', 9)
        )
        self.channel_a_display.pack(fill='both', expand=True)
        
        # Scenario selection and execution
        execution_frame = ttk.Frame(self.scenario_frame)
        execution_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(execution_frame, text="Scenario:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        scenario_select_frame = ttk.Frame(execution_frame)
        scenario_select_frame.pack(fill='x', pady=(4, 0))
        
        self.scenario_var = tk.StringVar()
        self.scenario_combo = ttk.Combobox(
            scenario_select_frame,
            textvariable=self.scenario_var,
            values=["apply_freeform_paste", "git_publish", "app_selfcheck"],  # Will be loaded from registry
            state='readonly',
            width=25
        )
        self.scenario_combo.pack(side='left', fill='x', expand=True, padx=(0, 4))
        
        self.execute_btn = ttk.Button(
            scenario_select_frame,
            text="▶ Execute",
            command=self.execute_scenario,
            style='Success.TButton'
        )
        self.execute_btn.pack(side='right')
        
        # Execution status
        self.status_frame = ttk.Frame(execution_frame)
        self.status_frame.pack(fill='x', pady=(8, 0))
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Ready", 
            foreground=self.colors['success'],
            font=('Segoe UI', 9)
        )
        self.status_label.pack(side='left')
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(side='right')
    
    def create_terminal_output_pane(self):
        """Create terminal output display"""
        # Output tabs
        self.output_notebook = ttk.Notebook(self.terminal_frame)
        self.output_notebook.pack(fill='both', expand=True)
        
        # Command output tab
        self.cmd_output_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.cmd_output_frame, text="Command Output")
        
        self.cmd_output = scrolledtext.ScrolledText(
            self.cmd_output_frame,
            height=25,
            width=40,
            wrap='word',
            font=('Consolas', 9),
            state='disabled'
        )
        self.cmd_output.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Error log tab
        self.error_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.error_frame, text="Error Log")
        
        self.error_log = scrolledtext.ScrolledText(
            self.error_frame,
            height=25,
            width=40,
            wrap='word',
            font=('Consolas', 9),
            state='disabled',
            foreground=self.colors['error']
        )
        self.error_log.pack(fill='both', expand=True, padx=4, pady=4)
        
        # AI Analysis tab (for AI-suggested next steps)
        self.ai_analysis_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.ai_analysis_frame, text="AI Analysis")
        
        self.ai_analysis = scrolledtext.ScrolledText(
            self.ai_analysis_frame,
            height=25,
            width=40,
            wrap='word',
            font=('Consolas', 9),
            state='disabled'
        )
        self.ai_analysis.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Clear output button
        clear_frame = ttk.Frame(self.terminal_frame)
        clear_frame.pack(fill='x', pady=(4, 0))
        
        self.clear_output_btn = ttk.Button(
            clear_frame,
            text="🗑 Clear Output",
            command=self.clear_terminal_output
        )
        self.clear_output_btn.pack(side='right')
    
    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x', padx=4, pady=2)
        
        # Project info
        self.project_label = ttk.Label(
            self.status_bar, 
            text="Project: PromptForge_V2.5",
            font=('Segoe UI', 8)
        )
        self.project_label.pack(side='left')
        
        # Version info
        self.version_label = ttk.Label(
            self.status_bar,
            text="V2.5-dev",
            font=('Segoe UI', 8, 'bold'),
            foreground=self.colors['primary']
        )
        self.version_label.pack(side='right')
    
    # Event handlers and methods
    
    def update_ui_state(self, new_state: UIState):
        """Update UI state and enable/disable controls accordingly"""
        self.state = new_state
        
        if new_state == UIState.AI_THINKING:
            self.submit_btn.configure(state='disabled', text="🤔 AI Thinking...")
            self.progress_bar.start()
        elif new_state == UIState.EXECUTING_SCENARIO:
            self.execute_btn.configure(state='disabled', text="⚙ Executing...")
            self.progress_bar.start()
        elif new_state == UIState.ERROR:
            self.status_label.configure(text="Error", foreground=self.colors['error'])
            self.progress_bar.stop()
        else:  # IDLE
            self.submit_btn.configure(state='normal', text="🚀 Submit to AI")
            self.execute_btn.configure(state='normal', text="▶ Execute")
            self.status_label.configure(text="Ready", foreground=self.colors['success'])
            self.progress_bar.stop()
    
    def add_chat_message(self, message: AIMessage):
        """Add a message to chat history"""
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, f"\n[{message.timestamp}] {message.role.title()}:\n")
        self.chat_history.insert(tk.END, f"{message.content}\n")
        self.chat_history.configure(state='disabled')
        self.chat_history.see(tk.END)
    
    def attach_file(self):
        """Handle file attachment"""
        file_path = filedialog.askopenfilename(
            title="Select file to attach",
            filetypes=[
                ("Text files", "*.txt *.md *.py *.js *.json"),
                ("Images", "*.png *.jpg *.jpeg *.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.attachments_list.insert(tk.END, f"📎 {Path(file_path).name}")
    
    def attach_screenshot(self):
        """Handle screenshot attachment (placeholder)"""
        messagebox.showinfo("Screenshot", "Screenshot functionality will be implemented in next iteration")
    
    def submit_ai_prompt(self):
        """Submit prompt to AI service"""
        prompt_text = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt_text:
            messagebox.showwarning("Empty Prompt", "Please enter a prompt before submitting")
            return
        
        self.update_ui_state(UIState.AI_THINKING)
        
        # Add user message to chat
        user_message = AIMessage(
            role="user",
            content=prompt_text,
            timestamp="2025-09-23 12:00:00"  # Will be actual timestamp
        )
        self.add_chat_message(user_message)
        
        # Clear prompt text
        self.prompt_text.delete(1.0, tk.END)
        
        # Start AI processing in background thread
        threading.Thread(target=self.process_ai_request, args=(prompt_text,), daemon=True).start()
    
    def process_ai_request(self, prompt: str):
        """Process AI request in background thread"""
        try:
            # This will be replaced with actual AI API calls
            import time
            time.sleep(2)  # Simulate AI processing
            
            # Mock response with Channel-A JSON
            mock_response = """Here's the code you requested:

```json
{
  "files": [
    {
      "path": "src/example.py",
      "language": "python", 
      "contents": "print('Hello from AI!')\n"
    }
  ]
}
```

This creates a simple Python file that prints a greeting."""
            
            # Schedule UI update on main thread
            self.root.after(0, self.handle_ai_response, mock_response)
            
        except Exception as e:
            self.root.after(0, self.handle_ai_error, str(e))
    
    def handle_ai_response(self, response: str):
        """Handle AI response on main thread"""
        # Add AI message to chat
        ai_message = AIMessage(
            role="assistant",
            content=response,
            timestamp="2025-09-23 12:00:02"
        )
        self.add_chat_message(ai_message)
        
        # Extract Channel-A JSON
        json_content = self.extract_channel_a_json(response)
        if json_content:
            self.channel_a_display.delete(1.0, tk.END)
            self.channel_a_display.insert(1.0, json_content)
            self.current_channel_a_json = json_content
            self.status_label.configure(text="Channel-A JSON detected", foreground=self.colors['success'])
        
        self.update_ui_state(UIState.IDLE)
    
    def handle_ai_error(self, error: str):
        """Handle AI error on main thread"""
        self.error_log.configure(state='normal')
        self.error_log.insert(tk.END, f"\n[ERROR] AI Request failed: {error}\n")
        self.error_log.configure(state='disabled')
        self.update_ui_state(UIState.ERROR)
    
    def extract_channel_a_json(self, text: str) -> Optional[str]:
        """Extract Channel-A JSON from AI response"""
        import re
        
        # Look for JSON code blocks
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            try:
                # Validate JSON structure
                json_obj = json.loads(matches[0])
                if 'files' in json_obj:
                    return json.dumps(json_obj, indent=2)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def validate_channel_a_json(self):
        """Validate Channel-A JSON format"""
        json_text = self.channel_a_display.get(1.0, tk.END).strip()
        if not json_text:
            messagebox.showwarning("No JSON", "No Channel-A JSON to validate")
            return
        
        try:
            json_obj = json.loads(json_text)
            
            # Basic Channel-A validation
            if 'files' not in json_obj:
                raise ValueError("Missing 'files' array")
            
            for i, file_obj in enumerate(json_obj['files']):
                required_fields = ['path', 'language', 'contents']
                for field in required_fields:
                    if field not in file_obj:
                        raise ValueError(f"File {i}: Missing required field '{field}'")
            
            self.status_label.configure(text="JSON Valid", foreground=self.colors['success'])
            messagebox.showinfo("Validation", "Channel-A JSON is valid!")
            
        except (json.JSONDecodeError, ValueError) as e:
            self.status_label.configure(text="JSON Invalid", foreground=self.colors['error'])
            messagebox.showerror("Validation Error", f"Invalid Channel-A JSON:\n{e}")
    
    def execute_scenario(self):
        """Execute selected scenario with current Channel-A JSON"""
        scenario = self.scenario_var.get()
        if not scenario:
            messagebox.showwarning("No Scenario", "Please select a scenario to execute")
            return
        
        if not self.current_channel_a_json:
            messagebox.showwarning("No JSON", "No Channel-A JSON to execute")
            return
        
        self.update_ui_state(UIState.EXECUTING_SCENARIO)
        
        # Start scenario execution in background
        threading.Thread(target=self.execute_scenario_background, args=(scenario,), daemon=True).start()
    
    def execute_scenario_background(self, scenario: str):
        """Execute scenario in background thread"""
        try:
            # Mock scenario execution
            import time
            time.sleep(3)
            
            mock_output = f"Executing scenario: {scenario}\nProcessing Channel-A JSON...\nCreated files:\n  src/example.py\nExecution completed successfully!"
            
            self.root.after(0, self.handle_scenario_success, mock_output)
            
        except Exception as e:
            self.root.after(0, self.handle_scenario_error, str(e))
    
    def handle_scenario_success(self, output: str):
        """Handle successful scenario execution"""
        self.cmd_output.configure(state='normal')
        self.cmd_output.insert(tk.END, f"\n{output}\n")
        self.cmd_output.configure(state='disabled')
        self.cmd_output.see(tk.END)
        
        self.update_ui_state(UIState.IDLE)
        
        # Trigger AI analysis of results
        self.analyze_execution_results(output)
    
    def handle_scenario_error(self, error: str):
        """Handle scenario execution error"""
        self.error_log.configure(state='normal')
        self.error_log.insert(tk.END, f"\n[ERROR] Scenario execution failed: {error}\n")
        self.error_log.configure(state='disabled')
        self.update_ui_state(UIState.ERROR)
    
    def analyze_execution_results(self, output: str):
        """AI analysis of execution results (mock implementation)"""
        # Mock AI analysis
        analysis = f"""AI Analysis of Execution Results:

✅ Execution Status: SUCCESS
📁 Files Created: 1
⏱ Execution Time: ~3 seconds

Suggested Next Steps:
1. Review the created file: src/example.py
2. Test the functionality
3. Consider adding error handling
4. Run git_publish to commit changes

The execution completed successfully. The file was created as expected."""

        self.ai_analysis.configure(state='normal')
        self.ai_analysis.delete(1.0, tk.END)
        self.ai_analysis.insert(1.0, analysis)
        self.ai_analysis.configure(state='disabled')
        
        # Switch to AI Analysis tab
        self.output_notebook.select(self.ai_analysis_frame)
    
    def clear_terminal_output(self):
        """Clear all terminal output"""
        for widget in [self.cmd_output, self.error_log, self.ai_analysis]:
            widget.configure(state='normal')
            widget.delete(1.0, tk.END)
            widget.configure(state='disabled')

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = V25MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

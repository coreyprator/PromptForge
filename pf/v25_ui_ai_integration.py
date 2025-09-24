#!/usr/bin/env python3
"""
PromptForge V2.5 - UI-AI Integration Layer
Connects the enhanced UI with AI infrastructure and scenario execution
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import json
import subprocess
import sys

# Import our AI integration components
from v25_ai_integration import (
    AIIntegrationManager, AIRequest, AIProvider, AIAttachment,
    ChannelAParser
)

class AsyncTaskManager:
    """Manages async tasks in tkinter synchronous environment"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.loop = None
        self.thread = None
        self._start_async_thread()
    
    def _start_async_thread(self):
        """Start async event loop in separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
    
    def run_async(self, coro, callback: Optional[Callable] = None):
        """Run async coroutine and schedule callback on main thread"""
        def done_callback(task):
            if callback:
                result = None
                error = None
                try:
                    result = task.result()
                except Exception as e:
                    error = e
                
                # Schedule callback on main thread
                self.root.after(0, lambda: callback(result, error))
        
        # Schedule coroutine on async thread
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(done_callback)

class EnhancedV25UI:
    """Enhanced V2.5 UI with full AI integration"""
    
    def __init__(self, root, project_root: Optional[Path] = None):
        self.root = root
        self.project_root = project_root or Path.cwd()
        
        # Initialize AI integration
        self.ai_manager = AIIntegrationManager(self.project_root / '.pf' / 'ai_config.json')
        self.async_manager = AsyncTaskManager(root)
        
        # State management
        self.current_conversation = []
        self.current_channel_a_json = None
        self.scenario_registry = None
        
        # Setup UI
        self.setup_main_window()
        self.create_layout()
        self.load_scenario_registry()
        self.update_provider_list()
        
        # Initialize state
        self.set_status("Ready")
    
    def setup_main_window(self):
        """Configure main window"""
        self.root.title(f"PromptForge V2.5 - {self.project_root.name}")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 600)
        
        # V2.5 Blue theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Success.TButton', foreground='#00AA44')
        style.configure('Warning.TButton', foreground='#FF8800')
        style.configure('Error.TLabel', foreground='#CC2244')
    
    def create_layout(self):
        """Create the main 3-pane layout"""
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Create the three panes
        self.create_ai_pane()
        self.create_scenario_pane() 
        self.create_terminal_pane()
        
        # Status bar
        self.create_status_bar()
    
    def create_ai_pane(self):
        """Create AI chat pane"""
        self.ai_frame = ttk.LabelFrame(self.main_paned, text="AI Communication", padding="8")
        self.main_paned.add(self.ai_frame, weight=2, minsize=350)
        
        # Chat history
        history_frame = ttk.Frame(self.ai_frame)
        history_frame.pack(fill='both', expand=True, pady=(0, 8))
        
        ttk.Label(history_frame, text="Conversation History", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.chat_display = scrolledtext.ScrolledText(
            history_frame,
            height=15,
            wrap='word',
            state='disabled',
            font=('Consolas', 9)
        )
        self.chat_display.pack(fill='both', expand=True, pady=(4, 0))
        
        # Prompt input
        prompt_frame = ttk.Frame(self.ai_frame)
        prompt_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(prompt_frame, text="Your Prompt", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.prompt_input = scrolledtext.ScrolledText(
            prompt_frame,
            height=6,
            wrap='word',
            font=('Consolas', 10)
        )
        self.prompt_input.pack(fill='x', pady=(4, 0))
        
        # File attachments
        attach_frame = ttk.Frame(self.ai_frame)
        attach_frame.pack(fill='x', pady=(0, 8))
        
        attach_header = ttk.Frame(attach_frame)
        attach_header.pack(fill='x')
        
        ttk.Label(attach_header, text="Attachments", font=('Segoe UI', 9, 'bold')).pack(side='left')
        
        ttk.Button(attach_header, text="+ File", command=self.attach_file, width=8).pack(side='right', padx=(4, 0))
        ttk.Button(attach_header, text="+ Image", command=self.attach_image, width=8).pack(side='right')
        
        self.attachments_list = tk.Listbox(attach_frame, height=3)
        self.attachments_list.pack(fill='x', pady=(4, 0))
        self.attachments_list.bind('<Button-3>', self.show_attachment_menu)
        
        # Provider and submit
        control_frame = ttk.Frame(self.ai_frame)
        control_frame.pack(fill='x')
        
        provider_frame = ttk.Frame(control_frame)
        provider_frame.pack(fill='x', pady=(0, 4))
        
        ttk.Label(provider_frame, text="Provider:").pack(side='left')
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(
            provider_frame,
            textvariable=self.provider_var,
            state='readonly',
            width=20
        )
        self.provider_combo.pack(side='right')
        
        self.submit_btn = ttk.Button(
            control_frame,
            text="Submit to AI",
            command=self.submit_ai_request,
            style='Success.TButton'
        )
        self.submit_btn.pack(fill='x')
    
    def create_scenario_pane(self):
        """Create scenario execution pane"""
        self.scenario_frame = ttk.LabelFrame(self.main_paned, text="Scenario Execution", padding="8")
        self.main_paned.add(self.scenario_frame, weight=2, minsize=350)
        
        # Channel-A JSON display
        json_frame = ttk.Frame(self.scenario_frame)
        json_frame.pack(fill='both', expand=True, pady=(0, 8))
        
        json_header = ttk.Frame(json_frame)
        json_header.pack(fill='x', pady=(0, 4))
        
        ttk.Label(json_header, text="Channel-A JSON", font=('Segoe UI', 9, 'bold')).pack(side='left')
        
        ttk.Button(json_header, text="Validate", command=self.validate_json).pack(side='right', padx=(4, 0))
        ttk.Button(json_header, text="Clear", command=self.clear_json).pack(side='right')
        
        self.json_display = scrolledtext.ScrolledText(
            json_frame,
            height=12,
            wrap='word',
            font=('Consolas', 9)
        )
        self.json_display.pack(fill='both', expand=True)
        
        # Scenario selection and execution
        exec_frame = ttk.Frame(self.scenario_frame)
        exec_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(exec_frame, text="Select Scenario", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        scenario_control = ttk.Frame(exec_frame)
        scenario_control.pack(fill='x', pady=(4, 0))
        
        self.scenario_var = tk.StringVar()
        self.scenario_combo = ttk.Combobox(
            scenario_control,
            textvariable=self.scenario_var,
            state='readonly',
            width=25
        )
        self.scenario_combo.pack(side='left', fill='x', expand=True, padx=(0, 4))
        
        self.execute_btn = ttk.Button(
            scenario_control,
            text="Execute",
            command=self.execute_scenario,
            style='Success.TButton'
        )
        self.execute_btn.pack(side='right')
        
        # Auto-execute toggle
        self.auto_execute_var = tk.BooleanVar()
        ttk.Checkbutton(
            exec_frame,
            text="Auto-execute when Channel-A JSON detected",
            variable=self.auto_execute_var
        ).pack(anchor='w', pady=(4, 0))
    
    def create_terminal_pane(self):
        """Create terminal output pane"""
        self.terminal_frame = ttk.LabelFrame(self.main_paned, text="Output & Analysis", padding="8")
        self.main_paned.add(self.terminal_frame, weight=1, minsize=300)
        
        # Tabbed output display
        self.output_notebook = ttk.Notebook(self.terminal_frame)
        self.output_notebook.pack(fill='both', expand=True)
        
        # Command output
        self.cmd_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.cmd_frame, text="Command Output")
        
        self.cmd_output = scrolledtext.ScrolledText(
            self.cmd_frame,
            wrap='word',
            font=('Consolas', 9),
            state='disabled'
        )
        self.cmd_output.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Error log
        self.error_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.error_frame, text="Errors")
        
        self.error_output = scrolledtext.ScrolledText(
            self.error_frame,
            wrap='word',
            font=('Consolas', 9),
            state='disabled',
            foreground='#CC2244'
        )
        self.error_output.pack(fill='both', expand=True, padx=4, pady=4)
        
        # AI Analysis
        self.analysis_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.analysis_frame, text="AI Analysis")
        
        self.analysis_output = scrolledtext.ScrolledText(
            self.analysis_frame,
            wrap='word',
            font=('Consolas', 9),
            state='disabled'
        )
        self.analysis_output.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Clear button
        ttk.Button(
            self.terminal_frame,
            text="Clear All Output",
            command=self.clear_all_output
        ).pack(anchor='e', pady=(4, 0))
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x', padx=4, pady=2)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side='left')
        
        ttk.Label(
            self.status_bar, 
            text=f"V2.5-dev | {self.project_root.name}",
            font=('Segoe UI', 8, 'bold')
        ).pack(side='right')
    
    # Event handlers and core functionality
    
    def set_status(self, message: str, error: bool = False):
        """Update status bar"""
        self.status_label.configure(
            text=message,
            foreground='#CC2244' if error else '#000000'
        )
    
    def append_to_output(self, widget: scrolledtext.ScrolledText, text: str):
        """Append text to output widget"""
        widget.configure(state='normal')
        widget.insert(tk.END, f"\n{text}")
        widget.configure(state='disabled')
        widget.see(tk.END)
    
    def add_chat_message(self, role: str, content: str):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"\n[{timestamp}] {role.upper()}:\n")
        self.chat_display.insert(tk.END, f"{content}\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)
        
        # Store in conversation history
        self.current_conversation.append({
            'role': role,
            'content': content,
            'timestamp': timestamp
        })
    
    def load_scenario_registry(self):
        """Load scenario registry"""
        registry_path = self.project_root / '.pf' / 'scenario_registry.json'
        if registry_path.exists():
            try:
                with open(registry_path) as f:
                    self.scenario_registry = json.load(f)
                
                # Populate scenario dropdown
                scenarios = []
                for category in ['core', 'untested']:
                    for scenario in self.scenario_registry.get('scenarios', {}).get(category, []):
                        scenarios.append(scenario['display_name'])
                
                self.scenario_combo['values'] = scenarios
                if scenarios:
                    self.scenario_combo.current(0)
                    
            except Exception as e:
                self.set_status(f"Failed to load scenarios: {e}", error=True)
    
    def update_provider_list(self):
        """Update AI provider list"""
        providers = self.ai_manager.get_available_providers()
        self.provider_combo['values'] = providers
        if providers:
            self.provider_combo.current(0)
    
    def attach_file(self):
        """Attach a file"""
        file_path = filedialog.askopenfilename(
            title="Select file to attach",
            filetypes=[
                ("Text files", "*.txt *.md *.py *.js *.json *.xml *.yaml"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            file_path = Path(file_path)
            self.attachments_list.insert(tk.END, f"📎 {file_path.name}")
    
    def attach_image(self):
        """Attach an image"""
        file_path = filedialog.askopenfilename(
            title="Select image to attach",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            file_path = Path(file_path)
            self.attachments_list.insert(tk.END, f"🖼 {file_path.name}")
    
    def show_attachment_menu(self, event):
        """Show attachment context menu"""
        if self.attachments_list.curselection():
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Remove", command=self.remove_attachment)
            menu.tk_popup(event.x_root, event.y_root)
    
    def remove_attachment(self):
        """Remove selected attachment"""
        selection = self.attachments_list.curselection()
        if selection:
            self.attachments_list.delete(selection[0])
    
    def submit_ai_request(self):
        """Submit request to AI"""
        prompt_text = self.prompt_input.get(1.0, tk.END).strip()
        if not prompt_text:
            messagebox.showwarning("Empty Prompt", "Please enter a prompt")
            return
        
        # Disable submit button
        self.submit_btn.configure(state='disabled', text="AI Thinking...")
        self.set_status("Sending request to AI...")
        
        # Add user message to chat
        self.add_chat_message("user", prompt_text)
        
        # Clear prompt
        self.prompt_input.delete(1.0, tk.END)
        
        # Get selected provider
        provider_name = self.provider_var.get()
        if "Anthropic" in provider_name:
            provider = AIProvider.ANTHROPIC
        elif "OpenAI" in provider_name:
            provider = AIProvider.OPENAI
        else:
            provider = AIProvider.MOCK
        
        # Prepare attachments
        attachments = []
        for i in range(self.attachments_list.size()):
            item_text = self.attachments_list.get(i)
            # This would need to load actual file content
            # Simplified for now
            attachments.append(AIAttachment(
                name=item_text.split(' ', 1)[1],
                content="",
                mime_type="text/plain",
                attachment_type="file"
            ))
        
        # Create AI request
        request = AIRequest(
            prompt=prompt_text,
            provider=provider,
            attachments=attachments
        )
        
        # Send request asynchronously
        self.async_manager.run_async(
            self.ai_manager.send_request(request),
            self.handle_ai_response
        )
    
    def handle_ai_response(self, response, error):
        """Handle AI response"""
        # Re-enable submit button
        self.submit_btn.configure(state='normal', text="Submit to AI")
        
        if error:
            self.set_status(f"AI request failed: {error}", error=True)
            self.append_to_output(self.error_output, f"AI Error: {error}")
            return
        
        if not response.success:
            self.set_status(f"AI request failed: {response.error_message}", error=True)
            self.append_to_output(self.error_output, f"AI Error: {response.error_message}")
            return
        
        # Add AI response to chat
        self.add_chat_message("assistant", response.content)
        
        # Handle Channel-A JSON if found
        if response.channel_a_json:
            self.json_display.delete(1.0, tk.END)
            self.json_display.insert(1.0, response.channel_a_json)
            self.current_channel_a_json = response.channel_a_json
            
            self.set_status("Channel-A JSON detected")
            
            # Auto-execute if enabled
            if self.auto_execute_var.get():
                self.root.after(1000, self.execute_scenario)  # Small delay for user to see
        else:
            self.set_status("AI response received (no Channel-A JSON)")
    
    def validate_json(self):
        """Validate Channel-A JSON"""
        json_text = self.json_display.get(1.0, tk.END).strip()
        if not json_text:
            messagebox.showwarning("No JSON", "No JSON to validate")
            return
        
        try:
            json_obj = json.loads(json_text)
            is_valid, message = ChannelAParser.validate_channel_a_structure(json_obj)
            
            if is_valid:
                messagebox.showinfo("Valid JSON", "Channel-A JSON structure is valid!")
                self.set_status("JSON validated successfully")
            else:
                messagebox.showerror("Invalid JSON", f"Validation failed:\n{message}")
                self.set_status("JSON validation failed", error=True)
                
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{e}")
            self.set_status("JSON format error", error=True)
    
    def clear_json(self):
        """Clear JSON display"""
        self.json_display.delete(1.0, tk.END)
        self.current_channel_a_json = None
    
    def execute_scenario(self):
        """Execute selected scenario"""
        scenario_name = self.scenario_var.get()
        if not scenario_name:
            messagebox.showwarning("No Scenario", "Please select a scenario")
            return
        
        json_text = self.json_display.get(1.0, tk.END).strip()
        if not json_text:
            messagebox.showwarning("No JSON", "No Channel-A JSON to execute")
            return
        
        # Disable execute button
        self.execute_btn.configure(state='disabled', text="Executing...")
        self.set_status("Executing scenario...")
        
        # Execute in background thread
        threading.Thread(
            target=self.execute_scenario_background,
            args=(scenario_name, json_text),
            daemon=True
        ).start()
    
    def execute_scenario_background(self, scenario_name: str, json_text: str):
        """Execute scenario in background"""
        try:
            # Write JSON to clipboard (simulate the current V2.4 process)
            # This is a simplified version - real implementation would use proper scenario execution
            
            # For now, simulate execution
            import time
            time.sleep(2)
            
            output = f"Executing scenario: {scenario_name}\nProcessing Channel-A JSON...\nSimulated execution completed!"
            
            self.root.after(0, self.handle_execution_success, output)
            
        except Exception as e:
            self.root.after(0, self.handle_execution_error, str(e))
    
    def handle_execution_success(self, output: str):
        """Handle successful execution"""
        self.execute_btn.configure(state='normal', text="Execute")
        self.set_status("Execution completed successfully")
        
        self.append_to_output(self.cmd_output, output)
        
        # Switch to command output tab
        self.output_notebook.select(0)
        
        # Request AI analysis of results
        self.request_ai_analysis(output)
    
    def handle_execution_error(self, error: str):
        """Handle execution error"""
        self.execute_btn.configure(state='normal', text="Execute")
        self.set_status("Execution failed", error=True)
        
        self.append_to_output(self.error_output, f"Execution Error: {error}")
        
        # Switch to error tab
        self.output_notebook.select(1)
    
    def request_ai_analysis(self, execution_output: str):
        """Request AI analysis of execution results"""
        analysis_prompt = f"""Please analyze the following scenario execution output and provide:

1. Summary of what was accomplished
2. Any issues or warnings to note
3. Suggested next steps
4. Recommendations for improvement

Execution Output:
```
{execution_output}
```

Provide a concise but helpful analysis."""

        # Create analysis request
        request = AIRequest(
            prompt=analysis_prompt,
            provider=AIProvider.MOCK,  # Use mock for now
            system_prompt="You are a helpful assistant analyzing PromptForge scenario execution results. Be concise and practical."
        )
        
        # Send analysis request
        self.async_manager.run_async(
            self.ai_manager.send_request(request),
            self.handle_analysis_response
        )
    
    def handle_analysis_response(self, response, error):
        """Handle AI analysis response"""
        if error or not response.success:
            self.append_to_output(self.analysis_output, f"Analysis failed: {error or response.error_message}")
            return
        
        # Display analysis
        self.analysis_output.configure(state='normal')
        self.analysis_output.delete(1.0, tk.END)
        self.analysis_output.insert(1.0, response.content)
        self.analysis_output.configure(state='disabled')
        
        # Switch to analysis tab
        self.output_notebook.select(2)
    
    def clear_all_output(self):
        """Clear all output displays"""
        for widget in [self.cmd_output, self.error_output, self.analysis_output]:
            widget.configure(state='normal')
            widget.delete(1.0, tk.END)
            widget.configure(state='disabled')

def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Get project root (could be passed as argument)
    project_root = Path.cwd()
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    
    app = EnhancedV25UI(root, project_root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted")
    finally:
        # Clean up async thread
        if hasattr(app, 'async_manager') and app.async_manager.loop:
            app.async_manager.loop.call_soon_threadsafe(app.async_manager.loop.stop)

if __name__ == "__main__":
    main()

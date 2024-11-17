import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
import threading
import time
import requests
import os

from src.generators.code_generator import SmartCodeGenerator
from src.config.analyzer_config import AnalyzerConfig
from src.generators.entity_analyzer import EntityAnalyzer

class APIGeneratorGUI:
    """GUI for Next.js API Generator"""
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.root.title("Next.js API Generator")
        self.root.geometry("1200x800")
        
        # Initialize config and generators
        self.config = AnalyzerConfig()
        self.entity_analyzer = EntityAnalyzer()
        self.code_generator = SmartCodeGenerator(self.config)
        
        # Initialize variables
        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.ollama_url = tk.StringVar(value=self.config.OLLAMA_BASE_URL)
        self.ollama_model = tk.StringVar(value=self.config.OLLAMA_MODEL)
        self.is_connected = False
        self.is_generating = False
        
        # Initialize logging
        self.setup_logging()
        
        # Create GUI elements
        self.create_widgets()
        
        # Log application start
        self.logger.info("Application started")

    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('APIGenerator')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # File handler
        log_file = f'logs/generator_{time.strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Stream handler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_formatter = logging.Formatter('%(levelname)s - %(message)s')
        stream_handler.setFormatter(stream_formatter)
        self.logger.addHandler(stream_handler)

    def create_widgets(self):
        """Create all GUI widgets"""
        # Create main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")

        # Ollama Connection Frame
        connection_frame = ttk.LabelFrame(main_container, text="Ollama Connection", padding="10")
        connection_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(connection_frame, text="Ollama URL:").grid(row=0, column=0, padx=5)
        ttk.Entry(connection_frame, textvariable=self.ollama_url, width=40).grid(row=0, column=1, padx=5)
        
        ttk.Label(connection_frame, text="Model:").grid(row=0, column=2, padx=5)
        ttk.Entry(connection_frame, textvariable=self.ollama_model, width=20).grid(row=0, column=3, padx=5)
        
        self.connect_button = ttk.Button(
            connection_frame, 
            text="Connect",
            command=self.connect_to_ollama
        )
        self.connect_button.grid(row=0, column=4, padx=5)

        # Project Paths Frame
        paths_frame = ttk.LabelFrame(main_container, text="Project Paths", padding="10")
        paths_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(paths_frame, text="Source Path:").grid(row=0, column=0, padx=5)
        ttk.Entry(paths_frame, textvariable=self.source_path, width=60).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(paths_frame, text="Browse", command=self.browse_source).grid(row=0, column=2, padx=5)

        ttk.Label(paths_frame, text="Output Path:").grid(row=1, column=0, padx=5)
        ttk.Entry(paths_frame, textvariable=self.output_path, width=60).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(paths_frame, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5)

        paths_frame.grid_columnconfigure(1, weight=1)

        # Entity List Frame
        entity_frame = ttk.LabelFrame(main_container, text="Detected Entities", padding="10")
        entity_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Create scrollable entity list
        self.entity_canvas = tk.Canvas(entity_frame)
        entity_scrollbar = ttk.Scrollbar(entity_frame, orient="vertical", command=self.entity_canvas.yview)
        self.scrollable_entity_frame = ttk.Frame(self.entity_canvas)

        self.scrollable_entity_frame.bind(
            "<Configure>",
            lambda e: self.entity_canvas.configure(scrollregion=self.entity_canvas.bbox("all"))
        )

        self.entity_canvas.create_window((0, 0), window=self.scrollable_entity_frame, anchor="nw")
        self.entity_canvas.configure(yscrollcommand=entity_scrollbar.set)

        self.entity_canvas.pack(side="left", fill="both", expand=True)
        entity_scrollbar.pack(side="right", fill="y")

        # Generation Options Frame
        options_frame = ttk.LabelFrame(main_container, text="Generation Options", padding="10")
        options_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # Checkboxes for different components
        self.gen_services = tk.BooleanVar(value=True)
        self.gen_dtos = tk.BooleanVar(value=True)
        self.gen_controllers = tk.BooleanVar(value=True)
        self.gen_swagger = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Services", variable=self.gen_services).grid(row=0, column=0, padx=5)
        ttk.Checkbutton(options_frame, text="DTOs", variable=self.gen_dtos).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(options_frame, text="Controllers", variable=self.gen_controllers).grid(row=0, column=2, padx=5)
        ttk.Checkbutton(options_frame, text="Swagger", variable=self.gen_swagger).grid(row=0, column=3, padx=5)

        # Console Output
        console_frame = ttk.LabelFrame(main_container, text="Console Output", padding="10")
        console_frame.grid(row=4, column=0, padx=10, pady=5, sticky="nsew")

        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            height=10,
            background="black",
            foreground="light green"
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)

        # Progress Bar
        progress_frame = ttk.Frame(main_container)
        progress_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, expand=True)

        # Generate Button
        self.generate_button = ttk.Button(
            main_container,
            text="Generate API Files",
            command=self.start_generation,
            state="disabled"
        )
        self.generate_button.grid(row=6, column=0, pady=10)

        # Configure weights
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(4, weight=1)
        
        # Configure root window weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def connect_to_ollama(self):
        """Test connection to Ollama server"""
        self.log_message("Testing connection to Ollama...")
        try:
            base_url = self.ollama_url.get().rstrip('/')
            model = self.ollama_model.get()
            
            try:
                # Check server status
                response = requests.get(
                    f"{base_url}/api/version",
                    timeout=10
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise Exception(
                    f"Ollama server is not running at {base_url}. "
                    "Please make sure Ollama is started using 'ollama serve'"
                )

            # Test model availability
            try:
                response = requests.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": "test connection",
                        "stream": False
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                if response.status_code == 200:
                    self.is_connected = True
                    self.generate_button.config(state="normal")
                    self.log_message("Successfully connected to Ollama!")
                    messagebox.showinfo(
                        "Success", 
                        f"Connected to Ollama successfully!\nModel: {model}"
                    )
                else:
                    raise Exception(f"Unexpected response: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                raise Exception(
                    f"Model '{model}' not found or not loaded. "
                    f"Try running: ollama pull {model}"
                )
                    
        except Exception as e:
            self.is_connected = False
            self.generate_button.config(state="disabled")
            self.log_message(f"Connection error: {str(e)}")
            messagebox.showerror(
                "Connection Error", 
                f"Failed to connect to Ollama:\n\n{str(e)}\n\n"
                "Please ensure:\n"
                "1. Ollama is running (ollama serve)\n"
                "2. The URL is correct\n"
                "3. The model is installed (ollama pull MODEL)"
            )

    def browse_source(self):
        """Browse for source project directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.source_path.set(directory)
            self.scan_entities()

    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_path.set(directory)

    def scan_entities(self):
        """Scan source directory for entity files"""
        try:
            # Clear previous entities
            for widget in self.scrollable_entity_frame.winfo_children():
                widget.destroy()

            source_path = Path(self.source_path.get())
            self.log_message(f"Scanning for entities in {source_path}")

            self.entity_vars = {}
            entity_files = []

            # Scan for entity files
            for root, _, files in os.walk(source_path):
                for file in files:
                    if file.endswith('.entity.ts'):
                        rel_path = os.path.relpath(os.path.join(root, file), source_path)
                        if not any(ignore in rel_path for ignore in self.config.IGNORE_DIRS):
                            entity_files.append(rel_path)

            # Create checkboxes for each entity
            for file_path in sorted(entity_files):
                var = tk.BooleanVar(value=True)
                self.entity_vars[file_path] = var
                
                frame = ttk.Frame(self.scrollable_entity_frame)
                frame.pack(fill=tk.X, padx=5, pady=2)
                
                cb = ttk.Checkbutton(
                    frame,
                    text=file_path,
                    variable=var
                )
                cb.pack(side=tk.LEFT)
                
                # Add preview button
                preview_btn = ttk.Button(
                    frame,
                    text="Preview",
                    command=lambda p=file_path: self.preview_entity(p)
                )
                preview_btn.pack(side=tk.RIGHT)

            self.log_message(f"Found {len(entity_files)} entities")

        except Exception as e:
            self.log_message(f"Error scanning entities: {str(e)}")
            messagebox.showerror("Error", f"Failed to scan entities: {str(e)}")

    def preview_entity(self, entity_path: str):
        """Show preview of what will be generated for an entity"""
        try:
            source_path = Path(self.source_path.get())
            entity_file = source_path / entity_path
            
            with open(entity_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create preview window
            preview = tk.Toplevel(self.root)
            preview.title(f"Preview: {entity_path}")
            preview.geometry("800x600")
            
            # Add tabs for different generations
            notebook = ttk.Notebook(preview)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Generate previews
            for gen_type in ['dto', 'service', 'controller']:
                if getattr(self.config, f'GENERATE_{gen_type.upper()}S', True):
                    try:
                        code = self.code_generator.generate_code_with_ollama(
                            entity_path,
                            content,
                            gen_type
                        )
                        
                        frame = ttk.Frame(notebook)
                        notebook.add(frame, text=gen_type.capitalize())
                        
                        text = scrolledtext.ScrolledText(frame)
                        text.pack(fill=tk.BOTH, expand=True)
                        text.insert('1.0', code)
                        text.config(state='disabled')
                        
                    except Exception as e:
                        self.log_message(f"Error generating preview for {gen_type}: {str(e)}")
            
        except Exception as e:
            self.log_message(f"Error creating preview: {str(e)}")
            messagebox.showerror("Error", f"Failed to create preview: {str(e)}")

    def start_generation(self):
        """Start the generation process in a separate thread"""
        if not self.is_connected:
            messagebox.showerror("Error", "Please connect to Ollama first")
            return

        if not self.source_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Please select both source and output paths")
            return

        selected_entities = [path for path, var in self.entity_vars.items() if var.get()]
        if not selected_entities:
            messagebox.showwarning("Warning", "No entities selected")
            return

        try:
            # Update config based on UI selections
            self.config.GENERATE_SERVICES = self.gen_services.get()
            self.config.GENERATE_DTOS = self.gen_dtos.get()
            self.config.GENERATE_CONTROLLERS = self.gen_controllers.get()
            self.config.GENERATE_SWAGGER = self.gen_swagger.get()

            # Analyze project structure first
            source_path = Path(self.source_path.get())
            self.log_message("Analyzing project structure...")
            self.code_generator.analyze_project_structure(source_path)
            self.log_message("Project analysis completed")

            # Start generation in a separate thread
            self.is_generating = True
            self.generate_button.config(state="disabled")
            thread = threading.Thread(target=self.generate_files, args=(selected_entities,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.log_message(f"Error starting generation: {str(e)}")
            messagebox.showerror("Error", f"Failed to start generation: {str(e)}")
            self.generate_button.config(state="normal")

    def generate_files(self, selected_entities: List[str]):
        """Generate API files for selected entities"""
        try:
            source_path = Path(self.source_path.get())
            output_path = Path(self.output_path.get())

            total_entities = len(selected_entities)
            for i, entity_path in enumerate(selected_entities, 1):
                if not self.is_generating:
                    break

                self.log_message(f"Processing {entity_path} ({i}/{total_entities})")
                
                try:
                    # Read entity file
                    full_path = source_path / entity_path
                    with open(full_path, 'r', encoding='utf-8') as f:
                        entity_content = f.read()

                    # Generate each type
                    for gen_type in ['dto', 'service', 'controller']:
                        if getattr(self.config, f'GENERATE_{gen_type.upper()}S', True):
                            try:
                                self.log_message(f"Generating {gen_type} for {entity_path}")
                                code = self.code_generator.generate_code_with_ollama(
                                    entity_path,
                                    entity_content,
                                    gen_type
                                )
                                
                                if code:
                                    # Save generated code
                                    entity_name = Path(entity_path).stem.replace('.entity', '')
                                    output_file = output_path / f'{gen_type}s' / f'{entity_name}.{gen_type}.ts'
                                    output_file.parent.mkdir(parents=True, exist_ok=True)
                                    
                                    with open(output_file, 'w', encoding='utf-8') as f:
                                        f.write(code)
                                    
                                    self.log_message(f"Generated {gen_type} for {entity_name}")
                                else:
                                    self.log_message(f"No {gen_type} code generated for {entity_path}")
                                
                            except Exception as e:
                                self.log_message(f"Error generating {gen_type}: {str(e)}")
                                if not messagebox.askyesno("Error", 
                                    f"Error generating {gen_type}. Continue with remaining files?"):
                                    raise
                    
                    # Update progress
                    progress = (i / total_entities) * 100
                    self.progress_var.set(progress)
                    self.root.update_idletasks()
                    
                except Exception as e:
                    self.log_message(f"Error processing {entity_path}: {str(e)}")
                    if not messagebox.askyesno("Error", 
                        f"Error processing {entity_path}. Continue with remaining entities?"):
                        break

            if self.is_generating:
                self.log_message("Generation completed successfully!")
                messagebox.showinfo("Success", "API files generated successfully!")

        except Exception as e:
            self.log_message(f"Error generating files: {str(e)}")
            messagebox.showerror("Error", f"Generation failed: {str(e)}")

        finally:
            self.is_generating = False
            self.generate_button.config(state="normal")
            self.progress_var.set(0)

    def log_message(self, message: str):
        """Add message to console output"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.console_text.insert(tk.END, formatted_message)
        self.console_text.see(tk.END)
        self.logger.info(message)

    def on_closing(self):
        """Handle application closing"""
        if self.is_generating:
            if messagebox.askokcancel("Quit", "Generation is in progress. Do you want to stop and quit?"):
                self.is_generating = False
                time.sleep(0.5)  # Give time for threads to clean up
                self.root.destroy()
        else:
            self.root.destroy()
            
    def validate_paths(self) -> bool:
        """Validate source and output paths"""
        source_path = Path(self.source_path.get())
        output_path = Path(self.output_path.get())
        
        if not source_path.exists():
            messagebox.showerror("Error", "Source path does not exist")
            return False
            
        if not source_path.is_dir():
            messagebox.showerror("Error", "Source path must be a directory")
            return False
            
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create output directory: {str(e)}")
            return False
            
        return True

    def clear_console(self):
        """Clear the console output"""
        self.console_text.delete(1.0, tk.END)
        
    def save_logs(self):
        """Save console logs to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "Logs saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {str(e)}")

    def check_generation_status(self):
        """Check if generation can proceed"""
        if not self.is_connected:
            messagebox.showerror("Error", "Please connect to Ollama first")
            return False
            
        if not self.validate_paths():
            return False
            
        if not self.entity_vars:
            messagebox.showerror("Error", "No entities detected. Please select a valid source directory")
            return False
            
        if not any(var.get() for var in self.entity_vars.values()):
            messagebox.showerror("Error", "No entities selected for generation")
            return False
            
        if not any([
            self.gen_services.get(),
            self.gen_dtos.get(),
            self.gen_controllers.get(),
            self.gen_swagger.get()
        ]):
            messagebox.showerror("Error", "Please select at least one generation option")
            return False
            
        return True
    def add_menu_bar(self):
        """Add menu bar to the window"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Logs", command=self.save_logs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clear Console", command=self.clear_console)
        tools_menu.add_command(label="Refresh Entities", command=self.scan_entities)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def show_about(self):
        """Show about dialog"""
        about_text = """Next.js API Generator

A tool for automatically generating API endpoints, services, 
and DTOs for Next.js projects using Ollama.

Features:
- Automatic code generation
- Project structure analysis
- Swagger documentation
- TypeScript support
- Customizable templates

Version: 1.0.0"""
        
        messagebox.showinfo("About", about_text)
        
    def show_status_bar(self):
        """Add status bar to the window"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=99, column=0, sticky="ew", padx=5, pady=2)
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Ready"
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.connection_indicator = ttk.Label(
            self.status_frame,
            text="⚫ Disconnected",
            foreground="red"
        )
        self.connection_indicator.pack(side=tk.RIGHT)
        
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.config(text=message)
        
    def update_connection_status(self):
        """Update connection indicator"""
        if self.is_connected:
            self.connection_indicator.config(
                text="🟢 Connected",
                foreground="green"
            )
        else:
            self.connection_indicator.config(
                text="⚫ Disconnected",
                foreground="red"
            )
            
    def show_error_dialog(self, title: str, message: str):
        """Show error dialog with detailed information"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")
        
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert('1.0', message)
        text.config(state='disabled')
        
        ttk.Button(
            dialog, 
            text="Close", 
            command=dialog.destroy
        ).pack(pady=5)
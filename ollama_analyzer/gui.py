import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
import json

from config import AnalyzerConfig
from cache_manager import CacheManager
from dependency_analyzer import DependencyAnalyzer
from utils import get_project_files, analyze_project_structure, format_size

class ConsoleHandler(logging.Handler):
    def __init__(self, console_widget):
        logging.Handler.__init__(self)
        self.console_widget = console_widget

    def emit(self, record):
        msg = self.format(record)
        self.console_widget.insert(tk.END, f"{msg}\n")
        self.console_widget.see(tk.END)
        self.console_widget.update_idletasks()

class OllamaAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Next.js Project Analyzer")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.config = AnalyzerConfig()
        self.setup_logging()
        self.init_variables()
        self.create_widgets()
        
        self.logger.info("Application started")

    def setup_logging(self):
        self.logger = logging.getLogger('OllamaAnalyzer')
        self.logger.setLevel(logging.DEBUG)
        
        Path('logs').mkdir(exist_ok=True)
        
        log_file = f'logs/analyzer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def init_variables(self):
        self.project_path = tk.StringVar()
        self.model_name = tk.StringVar(value=self.config.DEFAULT_MODEL)
        self.base_url = tk.StringVar(value="http://localhost:11434")
        self.is_analyzing = False
        self.is_connected = False

    def create_widgets(self):
        # Project settings frame
        settings_frame = ttk.LabelFrame(self.root, text="Project Settings", padding="10")
        settings_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Project path selection
        ttk.Label(settings_frame, text="Project Path:").grid(row=0, column=0, padx=5, pady=5)
        path_entry = ttk.Entry(settings_frame, textvariable=self.project_path, width=50)
        path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(settings_frame, text="Browse", command=self.browse_project).grid(row=0, column=2, padx=5)

        # Model settings
        ttk.Label(settings_frame, text="Model:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.model_name).grid(row=1, column=1, sticky="ew", padx=5)

        ttk.Label(settings_frame, text="Ollama URL:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.base_url).grid(row=2, column=1, sticky="ew", padx=5)

        # Connection status and test button
        self.connection_status = ttk.Label(settings_frame, text="⚠️ Not Connected", foreground="red")
        self.connection_status.grid(row=2, column=2, padx=5)
        ttk.Button(settings_frame, text="Connect to Ollama", command=self.connect_to_ollama).grid(row=2, column=3, padx=5)

        settings_frame.grid_columnconfigure(1, weight=1)

        # Query frame
        query_frame = ttk.LabelFrame(self.root, text="Query", padding="10")
        query_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.query_text = scrolledtext.ScrolledText(query_frame, height=3)
        self.query_text.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.query_text.insert("1.0", "Enter your question about the project here...")
        self.query_text.bind("<FocusIn>", lambda e: self.on_query_focus_in())
        self.query_text.bind("<FocusOut>", lambda e: self.on_query_focus_out())

        # Analysis controls
        button_frame = ttk.Frame(query_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.analyze_button = ttk.Button(
            button_frame, 
            text="Analyze", 
            command=self.start_analysis,
            state="disabled"
        )
        self.analyze_button.pack(side=tk.LEFT, pady=5)

        self.progress_bar = ttk.Progressbar(button_frame, mode='determinate', length=400)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        query_frame.grid_columnconfigure(0, weight=1)

        # Create notebook for different views
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Console output tab
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="Console")

        # Console toolbar
        console_toolbar = ttk.Frame(console_frame)
        console_toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(
            console_toolbar,
            text="Clear Console",
            command=lambda: self.console_text.delete(1.0, tk.END)
        ).pack(side=tk.LEFT)

        # Console text area
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            height=20,
            background='black',
            foreground='light green'
        )
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add console handler to logger
        console_handler = ConsoleHandler(self.console_text)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

        # Analysis results tab
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Analysis Results")

        # Results toolbar
        results_toolbar = ttk.Frame(results_frame)
        results_toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(
            results_toolbar,
            text="Clear Results",
            command=lambda: self.results_text.delete(1.0, tk.END)
        ).pack(side=tk.LEFT)

        ttk.Button(
            results_toolbar,
            text="Save Results",
            command=self.save_results
        ).pack(side=tk.LEFT, padx=5)

        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            height=20
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Project files tab
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Project Files")

        # Files text area
        self.file_list_text = scrolledtext.ScrolledText(
            files_frame,
            wrap=tk.WORD,
            height=20
        )
        self.file_list_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure grid weights
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def on_query_focus_in(self):
        if self.query_text.get("1.0", "end-1c") == "Enter your question about the project here...":
            self.query_text.delete("1.0", tk.END)
            self.query_text.config(foreground='black')

    def on_query_focus_out(self):
        if not self.query_text.get("1.0", "end-1c").strip():
            self.query_text.insert("1.0", "Enter your question about the project here...")
            self.query_text.config(foreground='grey')

    def browse_project(self):
        directory = filedialog.askdirectory()
        if directory:
            self.project_path.set(directory)
            self.logger.info(f"Selected project directory: {directory}")
            self.scan_project_files()

    def connect_to_ollama(self):
        self.logger.info("Attempting to connect to Ollama...")
        try:
            response = requests.get(f"{self.base_url.get()}/api/version")
            if response.status_code == 200:
                model_response = requests.post(
                    f"{self.base_url.get()}/api/generate",
                    json={"model": self.model_name.get(), "prompt": "test", "stream": False}
                )
                
                if model_response.status_code == 200:
                    self.is_connected = True
                    self.connection_status.config(text="✅ Connected", foreground="green")
                    self.analyze_button.config(state="normal")
                    self.logger.info("Successfully connected to Ollama")
                    messagebox.showinfo("Success", "Successfully connected to Ollama!")
                else:
                    raise Exception(f"Model '{self.model_name.get()}' not found")
            else:
                raise Exception("Ollama service not responding")
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            self.is_connected = False
            self.connection_status.config(text="❌ Error", foreground="red")
            self.analyze_button.config(state="disabled")
            messagebox.showerror("Error", f"Connection failed: {str(e)}")

    def scan_project_files(self):
        if self.project_path.get():
            try:
                project_path = Path(self.project_path.get())
                self.logger.info(f"Scanning project at: {project_path}")
                
                # Clear previous content
                self.file_list_text.delete(1.0, tk.END)
                
                # Analyze project
                analysis = analyze_project_structure(project_path, self.config)
                
                # Display results
                self.file_list_text.insert(tk.END, "Project Structure:\n\n")
                
                # Statistics
                self.file_list_text.insert(tk.END, "Statistics:\n")
                self.file_list_text.insert(tk.END, f"Total Files: {analysis['stats']['total_files']}\n")
                self.file_list_text.insert(tk.END, f"Total Directories: {analysis['stats']['total_dirs']}\n")
                self.file_list_text.insert(tk.END, f"Total Size: {format_size(analysis['stats']['total_size'])}\n\n")
                
                # Files
                self.file_list_text.insert(tk.END, "Files:\n")
                for file in sorted(analysis['files']):
                    self.file_list_text.insert(tk.END, f"{file}\n")
                    
                # Log results
                self.logger.info(f"Found {len(analysis['files'])} files")
                self.logger.info("Files by extension:")
                for ext, count in analysis['stats']['by_extension'].items():
                    self.logger.info(f"  {ext}: {count} files")
                
            except Exception as e:
                self.logger.error(f"Error scanning project files: {str(e)}")
                messagebox.showerror("Error", f"Error scanning project: {str(e)}")

    def start_analysis(self):
        if self.is_analyzing:
            self.is_analyzing = False
            self.analyze_button.config(text="Analyze")
            self.logger.info("Analysis stopped by user")
        else:
            self.analyze_button.config(text="Stop")
            thread = threading.Thread(target=self.analyze_project)
            thread.daemon = True
            thread.start()

    def analyze_project(self):
        if not self.is_connected:
            self.logger.error("Cannot start analysis - not connected to Ollama")
            messagebox.showerror("Error", "Please connect to Ollama first")
            return

        project_path = self.project_path.get()
        if not project_path:
            self.logger.error("Cannot start analysis - no project path selected")
            messagebox.showerror("Error", "Please select a project directory")
            return

        self.console_text.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.is_analyzing = True

        try:
            project_path = Path(project_path)
            cache = CacheManager(project_path / '.cache')
            analyzer = DependencyAnalyzer(project_path)

            files = get_project_files(project_path, self.config)
            total_files = len(files)
            self.progress_bar["maximum"] = total_files

            self.logger.info(f"Found {total_files} files to analyze")
            question = self.query_text.get(1.0, tk.END).strip()

            results = {}
            for i, file_path in enumerate(files, 1):
                if not self.is_analyzing:
                    break

                self.logger.info(f"Analyzing file {i}/{total_files}: {file_path}")
                try:
                    cached_response = cache.get_cached_analysis(
                        file_path, question, self.model_name.get()
                    )

                    if cached_response:
                        self.logger.info(f"Using cached response for {file_path}")
                        results[file_path] = cached_response
                    else:
                        abs_path = project_path / file_path
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        metadata = {
                            'last_modified': abs_path.stat().st_mtime,
                            'file_type': abs_path.suffix
                        }
                        cache.cache_file(file_path, content, metadata)

                        response = self.query_ollama(file_path, content, question)
                        if response and response != 'NOT_RELEVANT':
                            results[file_path] = response
                            cache.cache_analysis(
                                file_path, question, response, self.model_name.get()
                            )

                    if file_path in results:
                        self.results_text.insert(tk.END, f"\n=== {file_path} ===\n{results[file_path]}\n")
                        self.results_text.see(tk.END)

                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {str(e)}")

                self.progress_bar["value"] = i
                self.root.update_idletasks()
                time.sleep(0.5)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("analysis_results")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"analysis_{timestamp}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

            self.logger.info(f"Analysis completed. Results saved to: {output_file}")
            messagebox.showinfo("Complete", f"Analysis completed!\nResults saved to: {output_file}")

        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
        finally:
            self.is_analyzing = False
            self.progress_bar["value"] = 0
            self.analyze_button.config(text="Analyze")

    def query_ollama(self, file_path: str, content: str, question: str) -> str:
        """Query Ollama with file content and question"""
        url = f"{self.base_url.get()}/api/generate"

        system_prompt = f"""You are analyzing the file {file_path} from a Next.js project.
Focus on providing specific, actionable insights related to the question.
If the file is not relevant to the question, respond with 'NOT_RELEVANT'."""

        prompt = f"""
File: {file_path}

Content:
{content}

Question: {question}

Please provide a detailed analysis focusing specifically on this file and the question asked.
If this file is not relevant to the question, respond with 'NOT_RELEVANT'.

Consider:
1. The file's role in the Next.js project structure
2. Any dependencies or imports
3. Specific code sections relevant to the question
4. Potential impact of changes
5. Best practices and optimization opportunities
"""

        try:
            response = requests.post(url, json={
                "model": self.model_name.get(),
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }, timeout=30)

            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            self.logger.error(f"Error querying Ollama: {str(e)}")
            raise

    def save_results(self):
        """Save analysis results to a file"""
        if not self.results_text.get("1.0", tk.END).strip():
            messagebox.showwarning("No Results", "There are no results to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.get("1.0", tk.END))
                self.logger.info(f"Results saved to: {file_path}")
                messagebox.showinfo("Success", f"Results saved to:\n{file_path}")
            except Exception as e:
                self.logger.error(f"Error saving results: {str(e)}")
                messagebox.showerror("Error", f"Failed to save results: {str(e)}")

    def on_closing(self):
        """Handle application closing"""
        if self.is_analyzing:
            if messagebox.askokcancel("Quit", "Analysis is in progress. Do you want to stop and quit?"):
                self.is_analyzing = False
                time.sleep(1)  # Give time for threads to clean up
                self.root.destroy()
        else:
            self.root.destroy()
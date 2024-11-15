import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import json
import requests
from typing import Optional
import threading
import time

class OllamaAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Project Analyzer")
        self.root.geometry("1000x800")
        
        # Configure grid weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Variables
        self.project_path = tk.StringVar()
        self.model_name = tk.StringVar(value="llama2")
        self.base_url = tk.StringVar(value="http://localhost:11434")
        self.is_analyzing = False
        self.is_connected = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Project settings frame
        settings_frame = ttk.LabelFrame(self.root, text="Project Settings", padding="10")
        settings_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Project path selection
        ttk.Label(settings_frame, text="Project Path:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.project_path).grid(row=0, column=1, sticky="ew", padx=5)
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
        
        self.analyze_button = ttk.Button(query_frame, text="Analyze", command=self.start_analysis, state="disabled")
        self.analyze_button.grid(row=1, column=0, pady=5)
        self.progress_bar = ttk.Progressbar(query_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=1, sticky="ew", padx=5)
        
        query_frame.grid_columnconfigure(1, weight=1)
        
        # Results frame with notebook
        results_frame = ttk.LabelFrame(self.root, text="Results", padding="10")
        results_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Console output tab
        self.console_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD)
        self.notebook.add(self.console_text, text="Console")
        
        # Analysis results tab
        self.results_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD)
        self.notebook.add(self.results_text, text="Analysis Results")
        
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)

    def connect_to_ollama(self):
        try:
            # First check if Ollama service is running
            response = requests.get(f"{self.base_url.get()}/api/version")
            if response.status_code == 200:
                # Then check if the specified model is available
                model_response = requests.post(
                    f"{self.base_url.get()}/api/generate",
                    json={"model": self.model_name.get(), "prompt": "test", "stream": False}
                )
                if model_response.status_code == 200:
                    self.is_connected = True
                    self.connection_status.config(text="✅ Connected", foreground="green")
                    self.analyze_button.config(state="normal")
                    messagebox.showinfo("Success", "Successfully connected to Ollama!")
                else:
                    self.is_connected = False
                    self.connection_status.config(text="⚠️ Model Not Found", foreground="red")
                    self.analyze_button.config(state="disabled")
                    messagebox.showerror("Error", f"Model '{self.model_name.get()}' not found. Please check the model name.")
            else:
                raise Exception("Ollama service not responding")
        except requests.exceptions.ConnectionError:
            self.is_connected = False
            self.connection_status.config(text="❌ Connection Failed", foreground="red")
            self.analyze_button.config(state="disabled")
            messagebox.showerror("Error", "Cannot connect to Ollama. Please make sure:\n\n1. Ollama is installed\n2. Ollama service is running\n3. Run 'ollama serve' in terminal")
        except Exception as e:
            self.is_connected = False
            self.connection_status.config(text="❌ Error", foreground="red")
            self.analyze_button.config(state="disabled")
            messagebox.showerror("Error", f"Connection failed: {str(e)}")

    def browse_project(self):
        directory = filedialog.askdirectory()
        if directory:
            self.project_path.set(directory)
            
    def log_message(self, message):
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)
        
    def analyze_project(self):
        if not self.is_connected:
            messagebox.showerror("Error", "Please connect to Ollama first")
            return
            
        project_path = self.project_path.get()
        if not project_path:
            messagebox.showerror("Error", "Please select a project directory")
            return
            
        self.console_text.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.is_analyzing = True
        
        try:
            analyzer = OllamaProjectAnalyzer(
                project_path=project_path,
                model_name=self.model_name.get(),
                base_url=self.base_url.get()
            )
            
            files = analyzer.get_file_list()
            total_files = len(files)
            self.progress_bar["maximum"] = total_files
            
            self.log_message(f"Found {total_files} files to analyze...")
            question = self.query_text.get(1.0, tk.END).strip()
            
            results = {}
            for i, file_path in enumerate(files, 1):
                if not self.is_analyzing:
                    break
                    
                self.log_message(f"Analyzing file {i}/{total_files}: {file_path}")
                try:
                    if not self.verify_connection():
                        raise Exception("Lost connection to Ollama")
                    
                    analysis = analyzer.analyze_file(file_path, question)
                    if analysis:
                        results[file_path] = analysis
                        self.results_text.insert(tk.END, f"\n=== {file_path} ===\n{analysis}\n")
                        self.results_text.see(tk.END)
                except Exception as e:
                    self.log_message(f"Error analyzing {file_path}: {str(e)}")
                    # Try to reconnect
                    if not self.verify_connection():
                        if not messagebox.askyesno("Connection Lost", "Lost connection to Ollama. Try to reconnect?"):
                            break
                        self.connect_to_ollama()
                
                self.progress_bar["value"] = i
                self.root.update_idletasks()
                time.sleep(0.5)
                
            output_file = f"analysis_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            self.log_message(f"\nAnalysis saved to: {output_file}")
            
        except Exception as e:
            self.log_message(f"Error during analysis: {str(e)}")
        finally:
            self.is_analyzing = False
            self.progress_bar["value"] = 0
            
    def verify_connection(self):
        try:
            response = requests.get(f"{self.base_url.get()}/api/version")
            return response.status_code == 200
        except:
            return False
            
    def start_analysis(self):
        if self.is_analyzing:
            self.is_analyzing = False
            return
            
        thread = threading.Thread(target=self.analyze_project)
        thread.daemon = True
        thread.start()
        
class OllamaProjectAnalyzer:
    def __init__(self, project_path: str, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        self.project_path = os.path.abspath(project_path)
        self.model_name = model_name
        self.base_url = base_url
        
    def get_file_list(self):
        ignore_dirs = {
            'node_modules', '.next', '.git', 
            'public', 'out', 'build', 'dist'
        }
        ignore_extensions = {
            '.map', '.lock', '.log', '.env'
        }
        
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for filename in filenames:
                if any(filename.endswith(ext) for ext in ignore_extensions):
                    continue
                    
                if filename.endswith(('.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.json')):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, self.project_path)
                    files.append(relative_path)
        
        return files
        
    def read_file_content(self, file_path: str) -> str:
        full_path = os.path.join(self.project_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return ""
            
    def query_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            print(f"Error querying Ollama: {str(e)}")
            return ""
            
    def analyze_file(self, file_path: str, question: str) -> str:
        content = self.read_file_content(file_path)
        if not content:
            return ""
            
        system_prompt = f"You are analyzing the file {file_path} from a Next.js project. Focus on providing specific, actionable insights."
        
        prompt = f"""
File: {file_path}

Content:
{content}

Question: {question}

Please provide a detailed analysis focusing specifically on this file and the question asked.
"""
        
        return self.query_ollama(prompt, system_prompt)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaAnalyzerGUI(root)
    root.mainloop()
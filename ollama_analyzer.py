import os
import json
import requests
from typing import List, Dict, Optional
import time

class OllamaProjectAnalyzer:
    def __init__(self, project_path: str, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        """
        Initialize the analyzer with project path and Ollama settings.
        
        Args:
            project_path: Path to the Next.js project
            model_name: Name of the Ollama model to use
            base_url: Base URL for Ollama API
        """
        self.project_path = os.path.abspath(project_path)
        self.model_name = model_name
        self.base_url = base_url
        self.context = {}
        
    def get_file_list(self) -> List[str]:
        """Get all relevant files from the Next.js project."""
        ignore_dirs = {
            'node_modules', '.next', '.git', 
            'public', 'out', 'build', 'dist'
        }
        ignore_extensions = {
            '.map', '.lock', '.log', '.env'
        }
        
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            # Remove ignored directories
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
        """Read and return the content of a file."""
        full_path = os.path.join(self.project_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return ""

    def query_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a query to Ollama and get the response.
        
        Args:
            prompt: The user's question
            system_prompt: Optional system prompt to provide context
        """
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
        """Analyze a specific file with a question."""
        content = self.read_file_content(file_path)
        if not content:
            return f"Could not analyze {file_path}"
            
        system_prompt = f"You are analyzing the file {file_path} from a Next.js project. Focus on providing specific, actionable insights."
        
        prompt = f"""
File: {file_path}

Content:
{content}

Question: {question}

Please provide a detailed analysis focusing specifically on this file and the question asked.
"""
        
        return self.query_ollama(prompt, system_prompt)

    def analyze_project(self, question: str) -> Dict[str, str]:
        """
        Analyze the entire project with respect to a specific question.
        Returns a dictionary of file paths and their analysis results.
        """
        files = self.get_file_list()
        results = {}
        
        print(f"Found {len(files)} files to analyze...")
        
        for i, file_path in enumerate(files, 1):
            print(f"Analyzing file {i}/{len(files)}: {file_path}")
            analysis = self.analyze_file(file_path, question)
            results[file_path] = analysis
            # Add a small delay to avoid overwhelming Ollama
            time.sleep(0.5)
            
        return results

    def save_analysis(self, results: Dict[str, str], output_file: str):
        """Save analysis results to a JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
    def interactive_mode(self):
        """Run in interactive mode, allowing multiple questions about the project."""
        print(f"Analyzing Next.js project at: {self.project_path}")
        print("Enter your questions (type 'exit' to quit):")
        
        while True:
            question = input("\nYour question: ").strip()
            
            if question.lower() == 'exit':
                break
                
            results = self.analyze_project(question)
            output_file = f"analysis_{int(time.time())}.json"
            self.save_analysis(results, output_file)
            print(f"\nAnalysis saved to: {output_file}")

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze a Next.js project using Ollama")
    parser.add_argument("project_path", help="Path to the Next.js project")
    parser.add_argument("--model", default="llama2", help="Ollama model to use")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama API URL")
    
    args = parser.parse_args()
    
    analyzer = OllamaProjectAnalyzer(
        project_path=args.project_path,
        model_name=args.model,
        base_url=args.url
    )
    
    analyzer.interactive_mode()
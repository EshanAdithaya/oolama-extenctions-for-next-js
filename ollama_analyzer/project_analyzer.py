import logging
import requests
from pathlib import Path
from typing import Optional
from config import AnalyzerConfig
from utils import get_project_files

class ProjectAnalyzer:
    def __init__(self, project_path: Path, config: AnalyzerConfig):
        self.project_path = project_path
        self.config = config
        self.consolidated_content = ""
        self.file_map = {}
        self.current_index = 0

    def consolidate_project(self) -> str:
        """Consolidate all project files into a single string with file markers"""
        consolidated = []
        files = get_project_files(self.project_path, self.config)
        
        for file_path in files:
            abs_path = self.project_path / file_path
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Store file location for later reference
                self.file_map[self.current_index] = file_path
                
                # Add file marker and content
                consolidated.append(f"\n=== FILE_START_{self.current_index}: {file_path} ===\n")
                consolidated.append(content)
                consolidated.append(f"\n=== FILE_END_{self.current_index} ===\n")
                
                self.current_index += 1
                
            except Exception as e:
                logging.error(f"Error reading {file_path}: {str(e)}")
                
        self.consolidated_content = "\n".join(consolidated)
        return self.consolidated_content

    def query_ollama(self, base_url: str, model_name: str, question: str) -> str:
        """Query Ollama with the entire project context"""
        url = f"{base_url}/api/generate"
        
        system_prompt = """You are a Next.js expert analyzing an entire project.
Your task is to:
1. Find relevant files and code sections that answer the user's question
2. Provide specific file paths and line numbers where changes are needed
3. Give clear, actionable steps to implement the solution
4. Consider project structure and dependencies

When referencing code, always include the file path and specify exactly where changes should be made."""

        prompt = f"""
Project Structure:
{self.consolidated_content}

Question: {question}

Please provide a detailed answer that includes:
1. Which specific files need to be modified
2. Exact code changes needed
3. Step-by-step implementation instructions
4. Any dependencies or considerations
"""

        try:
            response = requests.post(url, json={
                "model": model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }, timeout=60)
            
            response.raise_for_status()
            return response.json()['response']
            
        except Exception as e:
            logging.error(f"Error querying Ollama: {str(e)}")
            raise

    def get_file_content(self, file_index: int) -> Optional[str]:
        """Retrieve original file content by index"""
        if file_index in self.file_map:
            file_path = self.project_path / self.file_map[file_index]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logging.error(f"Error reading file: {str(e)}")
        return None
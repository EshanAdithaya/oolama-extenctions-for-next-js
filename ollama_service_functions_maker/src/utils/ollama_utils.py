import subprocess
import platform
import requests
from typing import Tuple, Optional
import logging

logger = logging.getLogger('OllamaUtils')

def check_ollama_installation() -> Tuple[bool, str]:
    """Check if Ollama is installed and get its version"""
    try:
        # Check if ollama command exists
        if platform.system() == "Windows":
            # For Windows, check in WSL
            result = subprocess.run(
                ['wsl', 'ollama', '--version'], 
                capture_output=True, 
                text=True
            )
        else:
            result = subprocess.run(
                ['ollama', '--version'], 
                capture_output=True, 
                text=True
            )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, "Ollama not found"
            
    except subprocess.CalledProcessError:
        return False, "Error checking Ollama installation"
    except FileNotFoundError:
        return False, "Ollama command not found"

def start_ollama_server() -> Tuple[bool, str]:
    """Attempt to start the Ollama server"""
    try:
        if platform.system() == "Windows":
            # For Windows, start in WSL
            subprocess.Popen(
                ['wsl', 'ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        return True, "Ollama server started"
    except Exception as e:
        return False, f"Failed to start Ollama: {str(e)}"

def check_model_availability(base_url: str, model_name: str) -> Tuple[bool, str]:
    """Check if a model is available and pull if needed"""
    try:
        # Check if model exists
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model_name, "prompt": "test", "stream": False},
            timeout=5
        )
        
        if response.status_code == 200:
            return True, "Model ready"
            
        # If not found, try to pull it
        logger.info(f"Model {model_name} not found, attempting to pull...")
        
        if platform.system() == "Windows":
            result = subprocess.run(
                ['wsl', 'ollama', 'pull', model_name],
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True,
                text=True
            )
            
        if result.returncode == 0:
            return True, f"Model {model_name} pulled successfully"
        else:
            return False, f"Failed to pull model {model_name}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Error checking model: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"
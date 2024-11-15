To run the project:

1. Create a directory structure like this:
```
ollama_analyzer/
├── requirements.txt
├── __init__.py
├── main.py
├── config.py
├── cache_manager.py
├── dependency_analyzer.py
├── gui.py
└── utils.py
```

2. Copy each file's content into the corresponding file in your directory structure.

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure Ollama is running:
```bash
ollama serve
```

5. Run the analyzer:
```bash
python main.py
```

The application will:
- Create necessary directories (logs, .cache, analysis_results)
- Show the GUI interface
- Allow you to select a Next.js project
- Connect to Ollama
- Analyze files with caching
- Save results

Usage workflow:
1. Click "Browse" to select your Next.js project
2. Click "Connect to Ollama" to establish connection
3. Enter your question in the query box
4. Click "Analyze" to start analysis
5. Monitor progress in the console tab
6. View results in the Analysis Results tab
7. Find saved results in the analysis_results directory

The system will cache both file contents and analysis results for faster subsequent queries about the same files.
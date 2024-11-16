import json
import requests

class AnalysisSummarizer:
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url
        self.model_name = model_name
        
    def summarize_results(self, results_file: str = None, results_dict: dict = None, original_query: str = None) -> str:
        """
        Summarize analysis results and get final conclusion using LLM
        Args:
            results_file: Path to JSON results file
            results_dict: Dictionary containing analysis results
            original_query: Original user query
        """
        if results_file:
            with open(results_file, 'r') as f:
                results = json.load(f)
        else:
            results = results_dict

        # Create summarized content
        summary = self._create_summary(results)
        
        # Get final conclusion using LLM
        conclusion = self._get_conclusion(summary, original_query)
        
        return conclusion
    
    def _create_summary(self, results: dict) -> str:
        """Create a concise summary of analysis results"""
        summary = []
        
        # Group by file types
        file_groups = self._group_by_file_type(results)
        
        for file_type, files in file_groups.items():
            relevant_findings = []
            for file_path, content in files.items():
                if content and content != 'NOT_RELEVANT':
                    relevant_findings.append({
                        'file': file_path,
                        'content': content
                    })
            
            if relevant_findings:
                summary.append(f"\n=== {file_type} Files ===\n")
                for finding in relevant_findings:
                    summary.append(f"File: {finding['file']}\n{finding['content']}\n")
        
        return "\n".join(summary)
    
    def _group_by_file_type(self, results: dict) -> dict:
        """Group results by file type for better organization"""
        groups = {
            'Components': {},
            'Layouts': {},
            'Pages': {},
            'Styles': {},
            'Config': {},
            'Other': {}
        }
        
        for file_path, content in results.items():
            if any(x in file_path.lower() for x in ['component', 'components']):
                groups['Components'][file_path] = content
            elif any(x in file_path.lower() for x in ['layout', 'layouts']):
                groups['Layouts'][file_path] = content
            elif any(x in file_path.lower() for x in ['page', 'pages']):
                groups['Pages'][file_path] = content
            elif any(x in file_path.lower() for x in ['.css', '.scss', '.sass', 'styles']):
                groups['Styles'][file_path] = content
            elif any(x in file_path.lower() for x in ['config', 'settings']):
                groups['Config'][file_path] = content
            else:
                groups['Other'][file_path] = content
                
        return {k: v for k, v in groups.items() if v}
    
    def _get_conclusion(self, summary: str, query: str) -> str:
        """Get final conclusion using LLM"""
        system_prompt = """You are a Next.js expert analyzing project files.
Provide a clear, actionable conclusion based on the analysis results.
Focus on specifics: exact file paths, code snippets, and step-by-step instructions when relevant."""

        prompt = f"""
Analysis Summary:
{summary}

Original Question:
{query}

Please provide a clear, actionable conclusion that answers the original question.
Include:
1. Specific files that need to be modified
2. Exact code changes needed
3. Step-by-step instructions
4. Any potential impacts or considerations
"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                },
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()['response']
            
        except Exception as e:
            return f"Error getting conclusion: {str(e)}"
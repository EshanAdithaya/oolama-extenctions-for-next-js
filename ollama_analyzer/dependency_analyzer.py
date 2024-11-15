import os
import re
from typing import List, Set, Dict
from pathlib import Path
import networkx as nx
from dataclasses import dataclass

@dataclass
class DependencyInfo:
    imports: List[str]
    exports: List[str]
    components: List[str]
    hooks: List[str]
    styles: List[str]

class DependencyAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.graph = nx.DiGraph()

    def analyze_file(self, file_path: str, content: str) -> DependencyInfo:
        # Basic patterns for detection
        import_pattern = r'import\s+.+\s+from\s+[\'"]([^\'"]+)[\'"]'
        export_pattern = r'export\s+(?:default\s+)?(?:function|const|class)\s+([A-Za-z0-9_]+)'
        component_pattern = r'(?:function|const)\s+([A-Z][A-Za-z0-9_]*)'
        hook_pattern = r'use[A-Z][A-Za-z0-9_]*'
        style_pattern = r'import\s+[\'"](.+\.(?:css|scss|sass))[\'"]'

        imports = re.findall(import_pattern, content)
        exports = re.findall(export_pattern, content)
        components = re.findall(component_pattern, content)
        hooks = re.findall(hook_pattern, content)
        styles = re.findall(style_pattern, content)

        return DependencyInfo(
            imports=imports,
            exports=exports,
            components=components,
            hooks=hooks,
            styles=styles
        )

    def build_dependency_graph(self, files: Dict[str, str]):
        self.graph.clear()

        for file_path, content in files.items():
            self.graph.add_node(file_path)
            dep_info = self.analyze_file(file_path, content)

            # Add dependencies
            for imp in dep_info.imports:
                if imp.startswith('.'):
                    # Resolve relative import
                    resolved = self.resolve_import(file_path, imp)
                    if resolved in files:
                        self.graph.add_edge(file_path, resolved)

        return self.graph

    def resolve_import(self, source_file: str, import_path: str) -> str:
        source_dir = os.path.dirname(source_file)
        if import_path.startswith('.'):
            resolved = os.path.normpath(os.path.join(source_dir, import_path))
            # Add common extensions if none specified
            if not os.path.splitext(resolved)[1]:
                for ext in ['.js', '.jsx', '.ts', '.tsx']:
                    if os.path.exists(self.project_root / f"{resolved}{ext}"):
                        return f"{resolved}{ext}"
            return resolved
        return import_path

    def get_related_files(self, file_path: str, depth: int = 2) -> Set[str]:
        if file_path not in self.graph:
            return set()

        related = set()
        current_level = {file_path}

        for _ in range(depth):
            next_level = set()
            for current_file in current_level:
                next_level.update(self.graph.predecessors(current_file))
                next_level.update(self.graph.successors(current_file))
            related.update(current_level)
            current_level = next_level - related

        return related
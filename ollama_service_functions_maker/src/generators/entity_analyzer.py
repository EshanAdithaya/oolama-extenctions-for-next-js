import re
from typing import Dict, List, Optional
from pathlib import Path
import ast
import json
import logging

logger = logging.getLogger('EntityAnalyzer')

class EntityAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('EntityAnalyzer')
    
    def analyze_entity_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a TypeScript entity file and extract its structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract interface/class name
            name_match = re.search(r'(?:interface|class)\s+(\w+)', content)
            if not name_match:
                return None
                
            entity_name = name_match.group(1)
            
            # Extract properties
            properties = []
            prop_pattern = r'(\w+)(?:\?)?:\s*([\w\[\]<>|]+)'
            for match in re.finditer(prop_pattern, content):
                prop_name, prop_type = match.groups()
                properties.append({
                    'name': prop_name,
                    'type': prop_type,
                    'required': '?' not in match.group(0)
                })
            
            # Extract decorators if any
            decorators = []
            decorator_pattern = r'@(\w+)\((.*?)\)'
            for match in re.finditer(decorator_pattern, content):
                decorators.append({
                    'name': match.group(1),
                    'args': match.group(2)
                })
            
            return {
                'name': entity_name,
                'properties': properties,
                'decorators': decorators,
                'file_path': str(file_path),
                'imports': self.extract_imports(content)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing entity file {file_path}: {str(e)}")
            return None
    
    def extract_imports(self, content: str) -> List[Dict]:
        """Extract import statements from the file"""
        imports = []
        import_pattern = r'import\s+{([^}]+)}\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        for match in re.finditer(import_pattern, content):
            imports.append({
                'items': [item.strip() for item in match.group(1).split(',')],
                'from': match.group(2)
            })
        
        return imports
    
    def generate_prisma_schema(self, entity: Dict) -> str:
        """Generate Prisma schema from entity definition"""
        schema_lines = [f"model {entity['name']} {{"]
        
        # Add properties
        for prop in entity['properties']:
            type_mapping = {
                'string': 'String',
                'number': 'Int',
                'boolean': 'Boolean',
                'Date': 'DateTime',
            }
            
            prisma_type = type_mapping.get(prop['type'], 'String')
            required = '' if prop['required'] else '?'
            
            schema_lines.append(f"  {prop['name']} {prisma_type}{required}")
        
        schema_lines.append("}")
        return "\n".join(schema_lines)
    
    def generate_zod_schema(self, entity: Dict) -> str:
        """Generate Zod validation schema from entity definition"""
        schema_lines = [f"export const {entity['name']}Schema = z.object({{"]
        
        # Add properties
        for prop in entity['properties']:
            type_mapping = {
                'string': 'z.string()',
                'number': 'z.number()',
                'boolean': 'z.boolean()',
                'Date': 'z.date()',
            }
            
            zod_type = type_mapping.get(prop['type'], 'z.string()')
            if not prop['required']:
                zod_type += '.optional()'
                
            schema_lines.append(f"  {prop['name']}: {zod_type},")
        
        schema_lines.append("})")
        return "\n".join(schema_lines)
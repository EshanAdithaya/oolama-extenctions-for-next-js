from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from pathlib import Path
import logging
import json
import re
import requests
import time
from time import sleep
import os


@dataclass
class CodeGenerationConfig:
    """Configuration for code generation"""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama"  # Default to codellama for better code generation
    API_TIMEOUT: int = 120
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    TEMPLATE_DIR: Path = Path("templates")
    CACHE_DIR: Path = Path(".cache")
    
    def validate(self) -> bool:
        """Validate configuration"""
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Test connection to Ollama
            response = requests.get(f"{self.OLLAMA_BASE_URL}/api/version", timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Configuration validation failed: {str(e)}")
            return False

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, config: CodeGenerationConfig):
        self.config = config
        self.logger = logging.getLogger('OllamaClient')
        
    def generate_code(self, entity_path: str, entity_content: str, 
                     generation_type: str) -> str:
        """Generate code using Ollama"""
        try:
            # Prepare context
            context = self._prepare_context(entity_path, entity_content, generation_type)
            
            # Create prompts
            system_prompt = self._create_system_prompt(generation_type)
            user_prompt = self._create_user_prompt(context)
            
            # Combined prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate code
            generated_code = self.ollama.generate_code(full_prompt)
            
            # Clean and validate
            clean_code = self._clean_generated_code(generated_code)
            if not self._validate_code(clean_code, generation_type):
                raise ValueError("Generated code validation failed")
                
            return clean_code
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {str(e)}")
            raise
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code"""
        # Remove markdown if present
        code = re.sub(r'```typescript\n', '', code)
        code = re.sub(r'```\n?', '', code)
        return code.strip()
    
    def _validate_code(self, code: str, generation_type: str) -> bool:
        """Validate generated code"""
        if not code:
            return False
            
        # Basic validation
        if generation_type == 'dto':
            required = ['@ApiProperty', 'export class', '@IsOptional']
        elif generation_type == 'service':
            required = ['@Injectable', 'constructor', 'async']
        else:  # controller
            required = ['@Controller', '@Get', '@Post', '@ApiTags']
            
        return all(req in code for req in required)

    def _prepare_context(self, entity_path: str, entity_content: str, 
                        generation_type: str) -> Dict:
        """Prepare context for code generation"""
        
        # Basic context
        context = {
            'entity': {
                'path': entity_path,
                'content': entity_content,
                'name': Path(entity_path).stem.replace('.entity', '')
            },
            'generation_type': generation_type,
            'patterns': self.project_context.get('patterns', {}),
            'similar_files': []
        }

    def check_connection(self) -> Tuple[bool, str]:
        """Check connection to Ollama"""
        try:
            # Check version endpoint
            response = requests.get(
                f"{self.config.OLLAMA_BASE_URL}/api/version",
                timeout=5
            )
            response.raise_for_status()
            
            # Test model availability
            test_response = self.generate_code("// Test connection")
            if test_response:
                return True, "Connection successful"
                
        except Exception as e:
            return False, str(e)
            
        return False, "Unknown error"

class SmartCodeGenerator:
    """Main code generation orchestrator"""
    
    def __init__(self, config: CodeGenerationConfig):
        self.config = config
        self.logger = logging.getLogger('SmartCodeGenerator')
        self.ollama = OllamaClient(config)
        self.project_context = {}

    def _find_similar_files(self, target_path: str) -> List[Dict]:
        """Find similar files for context"""
        similar = []
        target_name = Path(target_path).stem.split('.')[0]
        
        for category in ['entities', 'dtos', 'services', 'controllers']:
            if category in self.project_context:
                for file in self.project_context[category]:
                    file_name = Path(file['path']).stem.split('.')[0]
                    if file_name != target_name and len(similar) < 3:
                        similar.append(file)
                
        return similar

    def generate_code_with_ollama(self, entity_path: str, entity_content: str, 
                            generation_type: str, retry_count: int = 0) -> str:
        """Generate code using Ollama with project context and retries"""
        try:
            context = self._prepare_generation_context(entity_path, entity_content, generation_type)
            
            system_prompt = self._create_system_prompt(generation_type)
            user_prompt = self._create_user_prompt(context)

            # Combine prompts for the generate endpoint
            combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"

            request_data = {
                "model": self.config.OLLAMA_MODEL,
                "prompt": combined_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stop": ["```"],
                    "num_predict": 2048,
                }
            }

            if not self._verify_json_serializable(request_data):
                raise ValueError("Request data is not JSON serializable")

            # Query Ollama using the generate endpoint
            self.logger.debug(f"Sending request to {self.config.OLLAMA_BASE_URL}/api/generate")
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json=request_data,
                timeout=120
            )
            
            response.raise_for_status()
            result = response.json()
            
            generated_code = result.get('response', '')
            clean_code = self._extract_code_from_response(generated_code)
            
            if not self._validate_generated_code(clean_code, generation_type):
                raise ValueError("Generated code validation failed")
                
            return clean_code

        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama server. Please ensure Ollama is running.")
            if retry_count < self.config.MAX_RETRIES:
                sleep(self.config.RETRY_DELAY * (retry_count + 1))
                return self.generate_code_with_ollama(
                    entity_path, entity_content, generation_type, retry_count + 1
                )
            raise
        except Exception as e:
            self.logger.error(f"Error generating {generation_type}: {str(e)}")
            if retry_count < self.config.MAX_RETRIES:
                sleep(self.config.RETRY_DELAY * (retry_count + 1))
                return self.generate_code_with_ollama(
                    entity_path, entity_content, generation_type, retry_count + 1
                )
            raise

    def _create_user_prompt(self, context: Dict) -> str:
        """Create user prompt with context"""
        return f"""Generate a {context['generation_type']} for the following entity:

File: {context['entity']['path']}

Content:
{context['entity']['content']}

Project Patterns:
{json.dumps(context.get('project_patterns', {}), indent=2)}

Similar Files:
{self._format_similar_files(context.get('similar_files', []))}

Requirements:
1. Follow the existing project patterns
2. Include all necessary imports
3. Add comprehensive documentation
4. Implement proper validation
5. Follow TypeScript best practices"""

    def _prepare_generation_context(self, entity_path: str, entity_content: str, 
                                generation_type: str) -> Dict:
        """Prepare context for code generation"""
        try:
            self.logger.debug("Starting context preparation")
            
            self.logger.debug("Extracting metadata")
            entity_metadata = self._extract_file_metadata(entity_content)
            
            self.logger.debug("Finding similar files")
            similar_files = self._find_similar_files(entity_path)
            
            self.logger.debug("Getting relationships")
            relationships = self.project_context.get('relationships', {}).get(entity_path, {})
            
            # Extract entity name
            entity_name = Path(entity_path).stem.replace('.entity', '')
            
            # Build context dictionary
            context = {
                'entity': {
                    'name': entity_name,
                    'path': str(entity_path),
                    'content': entity_content,
                    'metadata': self._make_json_serializable(entity_metadata)
                },
                'similar_files': self._make_json_serializable(similar_files),
                'relationships': self._make_json_serializable(relationships),
                'project_patterns': self._make_json_serializable(
                    self.project_context.get('patterns', {})
                ),
                'generation_type': generation_type
            }
            
            return context
                
        except Exception as e:
            self.logger.error(f"Error preparing context: {str(e)}")
            raise
        
    def analyze_project(self, source_path: Path) -> None:
        """Analyze project structure"""
        try:
            self.logger.info(f"Analyzing project at {source_path}")
            
            # Reset context
            self.project_context = {
                'entities': [],
                'services': [],
                'controllers': [],
                'dtos': [],
                'common': [],
                'patterns': {},
                'relationships': {}
            }
            
            # Scan project files
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = Path(root) / file
                    if self._should_process_file(file_path):
                        content = self._read_file(file_path)
                        if content:
                            self._process_file(file_path, content)
                            
            # Analyze patterns
            self._analyze_patterns()
            self.logger.info("Project analysis completed")
            
        except Exception as e:
            self.logger.error(f"Project analysis failed: {str(e)}")
            raise

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        if any(ignore in str(file_path) for ignore in ['node_modules', '.git', 'dist']):
            return False
            
        return file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']
        
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Error reading {file_path}: {str(e)}")
            return None
            
    def _process_file(self, file_path: Path, content: str) -> None:
        """Process individual file"""
        try:
            # Extract metadata
            metadata = self._extract_metadata(content)
            
            # Categorize file
            file_info = {
                'path': str(file_path),
                'content': content,
                'metadata': metadata
            }
            
            if 'entity' in file_path.name:
                self.project_context['entities'].append(file_info)
            elif 'service' in file_path.name:
                self.project_context['services'].append(file_info)
            elif 'controller' in file_path.name:
                self.project_context['controllers'].append(file_info)
            elif 'dto' in file_path.name:
                self.project_context['dtos'].append(file_info)
            else:
                self.project_context['common'].append(file_info)
                
        except Exception as e:
            self.logger.warning(f"Error processing {file_path}: {str(e)}")
            
    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from file content"""
        metadata = {
            'imports': [],
            'exports': [],
            'classes': [],
            'interfaces': [],
            'decorators': []
        }
        
        # Extract patterns
        import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
        class_pattern = r'class\s+(\w+)'
        interface_pattern = r'interface\s+(\w+)'
        decorator_pattern = r'@(\w+)'
        
        metadata['imports'] = re.findall(import_pattern, content)
        metadata['classes'] = re.findall(class_pattern, content)
        metadata['interfaces'] = re.findall(interface_pattern, content)
        metadata['decorators'] = re.findall(decorator_pattern, content)
        
        return metadata

    def _analyze_patterns(self) -> None:
        """Analyze project patterns and conventions"""
        try:
            patterns = {
                'naming': self._analyze_naming_patterns(),
                'decorators': self._analyze_decorator_patterns(),
                'file_structure': self._analyze_file_structure(),
                'validation': self._analyze_validation_patterns(),
                'error_handling': self._analyze_error_patterns(),
                'relationships': self._analyze_relationships()
            }
            
            self.project_context['patterns'] = patterns
            self.logger.info("Pattern analysis completed")
            
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {str(e)}")
            raise

    def _analyze_naming_patterns(self) -> Dict:
        """Analyze naming conventions"""
        patterns = {
            'entities': {},
            'dtos': {},
            'services': {},
            'controllers': {},
            'file_naming': {},
            'class_naming': {},
            'method_naming': {}
        }
        
        try:
            # Analyze file naming patterns
            for category in ['entities', 'dtos', 'services', 'controllers']:
                if category in self.project_context:
                    for file_info in self.project_context[category]:
                        file_path = Path(file_info['path'])
                        
                        # Extract file naming pattern
                        name_parts = file_path.stem.split('.')
                        if len(name_parts) > 1:
                            pattern = '.'.join(name_parts[:-1])  # Everything before last part
                            patterns['file_naming'][pattern] = patterns['file_naming'].get(pattern, 0) + 1
                        
                        # Extract class naming pattern
                        for class_name in file_info['metadata'].get('classes', []):
                            if class_name.endswith('DTO'):
                                patterns['class_naming']['dto'] = 'PascalCase + DTO'
                            elif class_name.endswith('Entity'):
                                patterns['class_naming']['entity'] = 'PascalCase + Entity'
                            elif class_name.endswith('Service'):
                                patterns['class_naming']['service'] = 'PascalCase + Service'
                            elif class_name.endswith('Controller'):
                                patterns['class_naming']['controller'] = 'PascalCase + Controller'
                                
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing naming patterns: {str(e)}")
            return patterns

    def _analyze_decorator_patterns(self) -> Dict:
        """Analyze decorator usage patterns"""
        patterns = {
            'entities': set(),
            'dtos': set(),
            'controllers': set(),
            'services': set(),
            'validation': set(),
            'swagger': set()
        }
        
        try:
            # Analyze decorator usage across different file types
            for file_type, files in self.project_context.items():
                if isinstance(files, list):
                    for file_info in files:
                        for decorator in file_info['metadata'].get('decorators', []):
                            # Categorize decorators
                            if decorator.startswith(('Is', 'Min', 'Max', 'Length')):
                                patterns['validation'].add(decorator)
                            elif decorator.startswith('Api'):
                                patterns['swagger'].add(decorator)
                            elif decorator in ['Entity', 'Column', 'PrimaryColumn']:
                                patterns['entities'].add(decorator)
                            elif decorator in ['Injectable', 'Service']:
                                patterns['services'].add(decorator)
                            elif decorator in ['Controller', 'Get', 'Post', 'Put', 'Delete']:
                                patterns['controllers'].add(decorator)
                                
            # Convert sets to lists for JSON serialization
            return {k: list(v) for k, v in patterns.items()}
            
        except Exception as e:
            self.logger.error(f"Error analyzing decorator patterns: {str(e)}")
            return {k: list(v) for k, v in patterns.items()}

    def _analyze_file_structure(self) -> Dict:
        """Analyze project file structure patterns"""
        patterns = {
            'module_structure': {},
            'feature_structure': {},
            'common_folders': set(),
            'test_structure': {}
        }
        
        try:
            # Analyze common project structure patterns
            all_paths = []
            for category in self.project_context:
                if isinstance(self.project_context[category], list):
                    for file_info in self.project_context[category]:
                        all_paths.append(Path(file_info['path']))
                        
            # Analyze module/feature structure
            for path in all_paths:
                parts = path.parts
                if len(parts) > 2:
                    feature_folder = parts[-3] if len(parts) > 3 else parts[-2]
                    if any(x in feature_folder for x in ['module', 'feature', 'domain']):
                        structure = {
                            'has_entity': any(p.endswith('.entity.ts') for p in all_paths if feature_folder in p.parts),
                            'has_service': any(p.endswith('.service.ts') for p in all_paths if feature_folder in p.parts),
                            'has_controller': any(p.endswith('.controller.ts') for p in all_paths if feature_folder in p.parts),
                            'has_dto': any(p.endswith('.dto.ts') for p in all_paths if feature_folder in p.parts),
                            'has_interface': any(p.endswith('.interface.ts') for p in all_paths if feature_folder in p.parts)
                        }
                        patterns['module_structure'][feature_folder] = structure
                        
            # Identify common folders
            for path in all_paths:
                common_folders = ['common', 'shared', 'utils', 'helpers', 'config']
                patterns['common_folders'].update(
                    folder for folder in path.parts 
                    if folder.lower() in common_folders
                )
                
            # Convert sets to lists for JSON serialization
            patterns['common_folders'] = list(patterns['common_folders'])
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing file structure: {str(e)}")
            return patterns

    def _analyze_validation_patterns(self) -> Dict:
        """Analyze validation patterns"""
        patterns = {
            'class_validators': set(),
            'custom_validators': set(),
            'validation_pipes': set(),
            'common_rules': {}
        }
        
        try:
            # Analyze validation patterns in DTOs
            if 'dtos' in self.project_context:
                for file_info in self.project_context['dtos']:
                    content = file_info['content']
                    
                    # Extract class-validator decorators
                    validator_pattern = r'@(\w+(?:Max|Min|Length|Contains|Matches|IsString|IsNumber|IsDate|IsBoolean|IsEmail|IsOptional|ValidateNested)\w*)'
                    validators = re.findall(validator_pattern, content)
                    patterns['class_validators'].update(validators)
                    
                    # Extract custom validators
                    custom_pattern = r'class\s+(\w+(?:Validator|Guard|Pipe))\s+'
                    custom = re.findall(custom_pattern, content)
                    patterns['custom_validators'].update(custom)
                    
                    # Extract validation pipes
                    pipe_pattern = r'@UsePipes\((\w+)\)'
                    pipes = re.findall(pipe_pattern, content)
                    patterns['validation_pipes'].update(pipes)
            
            # Convert sets to lists for JSON serialization
            return {
                'class_validators': list(patterns['class_validators']),
                'custom_validators': list(patterns['custom_validators']),
                'validation_pipes': list(patterns['validation_pipes']),
                'common_rules': patterns['common_rules']
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing validation patterns: {str(e)}")
            return {k: list(v) if isinstance(v, set) else v for k, v in patterns.items()}

    def _analyze_error_patterns(self) -> Dict:
        """Analyze error handling patterns"""
        patterns = {
            'exceptions': set(),
            'error_handlers': set(),
            'common_errors': {},
            'error_filters': set()
        }
        
        try:
            for category in ['services', 'controllers']:
                if category in self.project_context:
                    for file_info in self.project_context[category]:
                        content = file_info['content']
                        
                        # Extract thrown exceptions
                        exception_pattern = r'throw\s+new\s+(\w+Error)'
                        exceptions = re.findall(exception_pattern, content)
                        patterns['exceptions'].update(exceptions)
                        
                        # Extract error handlers
                        handler_pattern = r'@Catch\((\w+)\)'
                        handlers = re.findall(handler_pattern, content)
                        patterns['error_handlers'].update(handlers)
                        
                        # Extract error filters
                        filter_pattern = r'class\s+(\w+Filter)\s+implements\s+ExceptionFilter'
                        filters = re.findall(filter_pattern, content)
                        patterns['error_filters'].update(filters)
                        
                        # Count common errors
                        for exc in exceptions:
                            patterns['common_errors'][exc] = patterns['common_errors'].get(exc, 0) + 1
            
            # Convert sets to lists for JSON serialization
            return {
                'exceptions': list(patterns['exceptions']),
                'error_handlers': list(patterns['error_handlers']),
                'error_filters': list(patterns['error_filters']),
                'common_errors': patterns['common_errors']
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing error patterns: {str(e)}")
            return {k: list(v) if isinstance(v, set) else v for k, v in patterns.items()}

    def _analyze_relationships(self) -> Dict:
        """Analyze entity relationships"""
        patterns = {
            'one_to_many': [],
            'many_to_one': [],
            'one_to_one': [],
            'many_to_many': [],
            'dependencies': {}
        }
        
        try:
            if 'entities' in self.project_context:
                for file_info in self.project_context['entities']:
                    content = file_info['content']
                    file_path = file_info['path']
                    
                    # Extract relationships from decorators
                    relationships = {
                        'one_to_many': re.findall(r'@OneToMany\(\)\s+(\w+):', content),
                        'many_to_one': re.findall(r'@ManyToOne\(\)\s+(\w+):', content),
                        'one_to_one': re.findall(r'@OneToOne\(\)\s+(\w+):', content),
                        'many_to_many': re.findall(r'@ManyToMany\(\)\s+(\w+):', content)
                    }
                    
                    if any(rel for rel in relationships.values()):
                        patterns['dependencies'][file_path] = relationships
                        
                    # Add to overall patterns
                    for rel_type, rels in relationships.items():
                        patterns[rel_type].extend(rels)
                        
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing relationships: {str(e)}")
            return patterns

    def _deep_serialize(self, obj: Any, path: str = "root") -> Union[dict, list, str, int, float, bool, None]:
        """Deep serialize any object to JSON-compatible format"""
        try:
            self.logger.debug(f"Serializing {path}: {type(obj)}")
            
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (set, frozenset)):
                return list(obj)
            elif isinstance(obj, list):
                return [self._deep_serialize(item, f"{path}[{i}]") 
                       for i, item in enumerate(obj)]
            elif isinstance(obj, dict):
                return {
                    str(k): self._deep_serialize(v, f"{path}.{k}")
                    for k, v in obj.items()
                }
            elif isinstance(obj, Path):
                return str(obj)
            else:
                return str(obj)
        except Exception as e:
            self.logger.error(f"Serialization error at {path}: {str(e)}")
            return str(obj)

    def _verify_json_serializable(self, data: Any, path: str = "root") -> bool:
        """Verify if data can be JSON serialized"""
        try:
            json.dumps(data)
            return True
        except Exception as e:
            self.logger.error(f"JSON serialization failed at {path}: {str(e)}")
            return False

    def _create_system_prompt(self, generation_type: str) -> str:
        """Create detailed system prompt based on project analysis"""
        try:
            # Get patterns and serialize them
            patterns = self._deep_serialize(self.project_context.get('patterns', {}))
            
            base_prompt = f"""You are an expert NestJS/TypeScript developer specializing in API development.
Your task is to generate a {generation_type} following the project's patterns and best practices.

Project Patterns:
{json.dumps(patterns, indent=2)}

Requirements:
1. Follow existing project patterns exactly
2. Include all necessary imports
3. Add comprehensive documentation
4. Implement proper error handling
5. Follow TypeScript best practices
6. Add complete Swagger documentation
7. Include proper validation
8. Return only the generated code, no explanations"""

            type_specific = {
                'dto': """
- Use class-validator decorators
- Include example values in Swagger decorators
- Add comprehensive property descriptions
- Handle nested DTOs properly
- Include proper type definitions""",

                'service': """
- Implement complete CRUD operations
- Use proper transaction handling
- Include comprehensive error handling
- Add proper logging
- Handle relationships correctly
- Implement proper data validation""",

                'controller': """
- Follow RESTful principles
- Add complete Swagger documentation
- Implement proper validation pipes
- Handle all HTTP methods
- Add proper response types
- Include security decorators
- Implement proper error responses"""
            }

            return f"{base_prompt}\n{type_specific.get(generation_type, '')}"
            
        except Exception as e:
            self.logger.error(f"Error creating system prompt: {str(e)}")
            raise

    def _create_user_prompt(self, context: Dict) -> str:
        """Create user prompt with context"""
        return f"""Generate a {context['generation_type']} for the following entity:

File: {context['entity']['path']}

Content:
{context['entity']['content']}

Project Patterns:
{json.dumps(context['patterns'], indent=2)}

Similar Files:
{self._format_similar_files(context['similar_files'])}

Requirements:
1. Follow the existing project patterns
2. Include all necessary imports
3. Add comprehensive documentation
4. Implement proper validation
5. Follow TypeScript best practices"""




    def _format_similar_files(self, files: List[Dict]) -> str:
        """Format similar files for prompt"""
        formatted = []
        for file in files:
            formatted.append(f"File: {file['path']}\n")
            formatted.append(file['content'])
            formatted.append("\n---\n")
        return "\n".join(formatted)
    

    def _make_json_serializable(self, obj, path="root"):
        """Convert any object to a JSON serializable format with detailed logging"""
        try:
            self.logger.debug(f"Serializing {path}: type={type(obj)}")
            
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (set, frozenset)):
                self.logger.debug(f"Converting set at {path} to list")
                return list(obj)
            elif isinstance(obj, list):
                self.logger.debug(f"Processing list at {path}")
                return [self._make_json_serializable(item, f"{path}[{i}]") 
                        for i, item in enumerate(obj)]
            elif isinstance(obj, dict):
                self.logger.debug(f"Processing dict at {path}")
                return {
                    str(k): self._make_json_serializable(v, f"{path}.{k}")
                    for k, v in obj.items()
                }
            elif isinstance(obj, Path):
                return str(obj)
            else:
                self.logger.debug(f"Converting unknown type {type(obj)} to string at {path}")
                return str(obj)
                
        except Exception as e:
            self.logger.error(f"Error serializing at {path}: {str(e)}, type={type(obj)}")
            raise
        
    def _serialize_context(self, context):
        """Serialize context with detailed logging"""
        try:
            self.logger.debug("Starting context serialization")
            serialized = {}
            
            for key, value in context.items():
                try:
                    serialized[key] = self._make_json_serializable(value)
                    self.logger.debug(f"Serialized key {key} successfully")
                except Exception as e:
                    self.logger.error(f"Error serializing key {key}: {str(e)}")
                    serialized[key] = str(value)
            
            return serialized
        except Exception as e:
            self.logger.error(f"Error in _serialize_context: {str(e)}")
            raise

    def verify_ollama_connection(self) -> Tuple[bool, str]:
        """Verify Ollama connection and model availability"""
        try:
            # Check if Ollama is running and model exists
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/v1/generate",
                json={
                    "model": self.config.OLLAMA_MODEL,
                    "prompt": "test",
                    "stream": False
                },
                timeout=10
            )
            response.raise_for_status()
            return True, "Connection successful"

        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama server. Please ensure Ollama is running with: ollama serve"
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "404" in error_msg:
                available_models = self._get_available_models()
                return False, f"Model not found. Available models: {', '.join(available_models)}"
            return False, error_msg

    def _get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/v1/tags")
            response.raise_for_status()
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except Exception:
            return []

    def _extract_file_metadata(self, content: str) -> Dict:
        """Extract metadata from file content"""
        try:
            metadata = {
                'imports': [],
                'decorators': [],
                'classes': [],
                'functions': [],
                'interfaces': []
            }
            
            # Extract imports
            import_pattern = r'^import\s+.*?;|^import\s+{.*?}\s+from\s+.*?;'
            metadata['imports'] = re.findall(import_pattern, content, re.MULTILINE)
            
            # Extract decorators
            decorator_pattern = r'@\w+(?:\(.*?\))?'
            metadata['decorators'] = re.findall(decorator_pattern, content)
            
            # Extract classes
            class_pattern = r'class\s+(\w+)'
            metadata['classes'] = re.findall(class_pattern, content)
            
            # Extract interfaces
            interface_pattern = r'interface\s+(\w+)'
            metadata['interfaces'] = re.findall(interface_pattern, content)
            
            # Extract functions
            function_pattern = r'(?:async\s+)?function\s+(\w+)'
            metadata['functions'] = re.findall(function_pattern, content)
            
            return metadata
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {str(e)}")
            return {}

    def _analyze_naming_patterns(self) -> Dict:
        """Analyze naming patterns in the project"""
        patterns = {
            'file_naming': {},
            'class_naming': {},
            'interface_naming': {},
            'function_naming': {},
            'variable_naming': {}
        }
        
        try:
            # Analyze file naming
            file_patterns = {}
            for file_type, files in self.project_context.items():
                if isinstance(files, list):
                    for file in files:
                        name = Path(file['path']).stem
                        parts = re.split(r'[.-]', name)
                        if len(parts) > 1:
                            pattern = '-'.join(parts[:-1])
                            file_patterns[pattern] = file_patterns.get(pattern, 0) + 1
            
            patterns['file_naming'] = file_patterns

            # Analyze class/interface naming
            for file_type, files in self.project_context.items():
                if isinstance(files, list):
                    for file in files:
                        metadata = file.get('metadata', {})
                        
                        # Class naming
                        for class_name in metadata.get('classes', []):
                            if class_name.endswith('DTO'):
                                patterns['class_naming']['dto'] = 'PascalCase + DTO'
                            elif class_name.endswith('Entity'):
                                patterns['class_naming']['entity'] = 'PascalCase + Entity'
                            elif class_name.endswith('Service'):
                                patterns['class_naming']['service'] = 'PascalCase + Service'
                            elif class_name.endswith('Controller'):
                                patterns['class_naming']['controller'] = 'PascalCase + Controller'

            return patterns
            
        except Exception as e:
            self.logger.warning(f"Error analyzing naming patterns: {str(e)}")
            return patterns

    def _analyze_decorator_patterns(self) -> Dict:
        """Analyze decorator usage patterns"""
        patterns = {
            'entity': [],
            'dto': [],
            'controller': [],
            'service': []
        }
        
        try:
            for file_type, files in self.project_context.items():
                if isinstance(files, list):
                    for file in files:
                        metadata = file.get('metadata', {})
                        decorators = metadata.get('decorators', [])
                        
                        if file['path'].endswith('.entity.ts'):
                            patterns['entity'].extend(decorators)
                        elif file['path'].endswith('.dto.ts'):
                            patterns['dto'].extend(decorators)
                        elif file['path'].endswith('.controller.ts'):
                            patterns['controller'].extend(decorators)
                        elif file['path'].endswith('.service.ts'):
                            patterns['service'].extend(decorators)
            
            # Count occurrences and get most common
            for key in patterns:
                if patterns[key]:
                    counter = {}
                    for dec in patterns[key]:
                        counter[dec] = counter.get(dec, 0) + 1
                    patterns[key] = [k for k, v in sorted(counter.items(), key=lambda x: x[1], reverse=True)]
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Error analyzing decorator patterns: {str(e)}")
            return patterns

    def _analyze_error_patterns(self) -> Dict:
        """Analyze error handling patterns"""
        patterns = {
            'exceptions': [],
            'error_handling': {},
            'common_errors': set()
        }
        
        try:
            error_pattern = r'throw\s+new\s+(\w+Error)'
            catch_pattern = r'catch\s*\((\w+)\)'
            
            for file_type, files in self.project_context.items():
                if isinstance(files, list):
                    for file in files:
                        content = file['content']
                        
                        # Find thrown exceptions
                        exceptions = re.findall(error_pattern, content)
                        patterns['exceptions'].extend(exceptions)
                        
                        # Find catch blocks
                        catches = re.findall(catch_pattern, content)
                        for catch in catches:
                            patterns['error_handling'][catch] = patterns['error_handling'].get(catch, 0) + 1
            
            # Get most common patterns
            patterns['exceptions'] = list(set(patterns['exceptions']))
            patterns['common_errors'] = {k for k, v in patterns['error_handling'].items() if v > 1}
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Error analyzing error patterns: {str(e)}")
            return patterns

    def _analyze_validation_patterns(self) -> Dict:
            """Analyze validation patterns"""
            patterns = {
                'decorators': set(),
                'pipes': set(),
                'custom_validators': set()
            }
            
            try:
                validation_decorator_pattern = r'@(\w+(?:Max|Min|Length|Contains|Matches|IsString|IsNumber|IsDate|IsBoolean|IsEmail|IsOptional|ValidateNested)\w*)'
                pipe_pattern = r'@UsePipes\((\w+)\)'
                custom_validator_pattern = r'class\s+(\w+(?:Validator|Guard|Pipe))\s+'
                
                for file_type, files in self.project_context.items():
                    if isinstance(files, list):
                        for file in files:
                            content = file['content']
                            
                            # Find validation decorators
                            decorators = re.findall(validation_decorator_pattern, content)
                            patterns['decorators'].update(decorators)
                            
                            # Find pipes
                            pipes = re.findall(pipe_pattern, content)
                            patterns['pipes'].update(pipes)
                            
                            # Find custom validators
                            custom = re.findall(custom_validator_pattern, content)
                            patterns['custom_validators'].update(custom)
                
                # Convert sets to lists for JSON serialization
                return {k: list(v) for k, v in patterns.items()}
                
            except Exception as e:
                self.logger.warning(f"Error analyzing validation patterns: {str(e)}")
                return {k: list(v) for k, v in patterns.items()}

    

    

    def _filter_source_files(self, file_path: str) -> bool:
        """Filter function for source files"""
        # Skip binary and git files
        if '.git/' in file_path:
            return False
            
        # Skip common binary file extensions
        binary_extensions = {'.jpg', '.png', '.gif', '.pdf', '.zip', '.exe'}
        if any(file_path.endswith(ext) for ext in binary_extensions):
            return False
            
        # Skip node_modules
        if 'node_modules' in file_path:
            return False
            
        # Only include TypeScript files and config files
        allowed_extensions = {'.ts', '.json', '.js'}
        return any(file_path.endswith(ext) for ext in allowed_extensions)

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with proper error handling"""
        try:
            if not self._filter_source_files(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return content
        except UnicodeDecodeError:
            self.logger.debug(f"Skipping binary file: {file_path}")
            return None
        except Exception as e:
            self.logger.warning(f"Error reading file {file_path}: {str(e)}")
            return None

    def analyze_project_structure(self, source_path: Path):
        """Analyze entire project structure to understand patterns and relationships"""
        self.logger.info(f"Analyzing project structure at {source_path}")
        
        try:
            # Reset project context
            self.project_context = {
                'configs': [],    
                'entities': [],   
                'dtos': [],      
                'services': [],   
                'controllers': [], 
                'common': [],     
                'relationships': {},
                'patterns': {}
            }
            
            # Scan project recursively
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(source_path)
                    
                    content = self._read_file_content(str(file_path))
                    if content is None:
                        continue
                        
                    try:
                        file_info = {
                            'path': str(relative_path),
                            'content': content,
                            'metadata': self._extract_file_metadata(content)
                        }
                        
                        # Categorize file
                        if file in ['package.json', 'tsconfig.json', 'nest-cli.json']:
                            self.project_context['configs'].append(file_info)
                        elif file.endswith('.entity.ts'):
                            self.project_context['entities'].append(file_info)
                            self._analyze_entity_relationships(file_info)
                        elif file.endswith('.dto.ts'):
                            self.project_context['dtos'].append(file_info)
                        elif file.endswith('.service.ts'):
                            self.project_context['services'].append(file_info)
                        elif file.endswith('.controller.ts'):
                            self.project_context['controllers'].append(file_info)
                        elif file.endswith(('.util.ts', '.helper.ts', '.constant.ts')):
                            self.project_context['common'].append(file_info)
                                
                    except Exception as e:
                        self.logger.warning(f"Error processing file {file_path}: {str(e)}")
                        continue

            # Analyze patterns
            self.project_context['patterns'] = {
                'naming': self._analyze_naming_patterns(),
                'decorators': self._analyze_decorator_patterns(),
                'error_handling': self._analyze_error_patterns(),
                'validation': self._analyze_validation_patterns()
            }
            
            self.logger.info("Project analysis completed")
                
        except Exception as e:
            self.logger.error(f"Error analyzing project: {str(e)}")
            raise

    def _analyze_entity_relationships(self, file_info: Dict):
        """Analyze entity relationships from file"""
        try:
            content = file_info['content']
            path = file_info['path']
            
            # Extract relationships from decorators
            relationships = {
                'oneToMany': re.findall(r'@OneToMany\(\)\s+(\w+):', content),
                'manyToOne': re.findall(r'@ManyToOne\(\)\s+(\w+):', content),
                'oneToOne': re.findall(r'@OneToOne\(\)\s+(\w+):', content),
                'manyToMany': re.findall(r'@ManyToMany\(\)\s+(\w+):', content)
            }
            
            # Extract referenced entities
            referenced_entities = re.findall(r'import.*?{(.*?)}.*?from', content)
            referenced_entities = [e.strip() for ref in referenced_entities for e in ref.split(',')]
            
            self.project_context['relationships'][path] = {
                'relationships': relationships,
                'referenced_entities': referenced_entities
            }
            
        except Exception as e:
            self.logger.warning(f"Error analyzing relationships: {str(e)}")



    def _validate_generated_code(self, code: str, generation_type: str) -> bool:
        """Validate generated code for completeness and correctness"""
        try:
            # Check for basic structure
            if not code.strip():
                return False

            # Check for required elements based on type
            required_elements = {
                'dto': [
                    '@ApiProperty',
                    'class',
                    'export class',
                    'IsOptional',
                    'validator'
                ],
                'service': [
                    '@Injectable',
                    'constructor',
                    'private readonly',
                    'async',
                    'return'
                ],
                'controller': [
                    '@Controller',
                    '@Get',
                    '@Post',
                    '@ApiTags',
                    '@ApiResponse'
                ]
            }

            type_elements = required_elements.get(generation_type, [])
            missing_elements = [elem for elem in type_elements if elem not in code]

            if missing_elements:
                self.logger.warning(f"Missing required elements: {missing_elements}")
                return False

            # Check for imports
            if 'import' not in code:
                self.logger.warning("Missing imports")
                return False

            # Check for TypeScript types
            if not re.search(r':\s*\w+[\[\]{}]*', code):
                self.logger.warning("Missing TypeScript types")
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Code validation error: {str(e)}")
            return False

    def _extract_code_from_response(self, response: str) -> str:
        """Clean and format the generated code"""
        try:
            # Remove markdown code blocks if present
            code = re.sub(r'```typescript\n', '', response)
            code = re.sub(r'```\n?', '', code)
            
            # Strip whitespace
            code = code.strip()
            
            # Ensure proper imports
            if 'import' not in code.split('\n')[0]:
                imports = self._generate_imports(code)
                code = f"{imports}\n\n{code}"
            
            return code
            
        except Exception as e:
            self.logger.warning(f"Error extracting code: {str(e)}")
            return response

    def _generate_imports(self, code: str) -> str:
        """Generate necessary imports based on code content"""
        imports = set()
        
        # Add common imports based on content
        import_patterns = {
            '@ApiProperty': 'import { ApiProperty } from "@nestjs/swagger";',
            '@Injectable': 'import { Injectable } from "@nestjs/common";',
            '@Controller': 'import { Controller } from "@nestjs/common";',
            '@Get': 'import { Get } from "@nestjs/common";',
            '@Post': 'import { Post } from "@nestjs/common";',
            '@Put': 'import { Put } from "@nestjs/common";',
            '@Delete': 'import { Delete } from "@nestjs/common";',
            '@Body': 'import { Body } from "@nestjs/common";',
            '@Param': 'import { Param } from "@nestjs/common";',
            '@IsString': 'import { IsString } from "class-validator";',
            '@IsNumber': 'import { IsNumber } from "class-validator";',
            '@IsOptional': 'import { IsOptional } from "class-validator";',
            'PrismaService': 'import { PrismaService } from "../prisma.service";'
        }
        
        for pattern, import_stmt in import_patterns.items():
            if pattern in code:
                imports.add(import_stmt)
        
        return '\n'.join(sorted(imports))

    def process_entity(self, entity_path: str, output_path: Path):
        """Process a single entity and generate all related files"""
        try:
            self.logger.info(f"Processing entity: {entity_path}")
            
            # Read entity file
            with open(entity_path, 'r', encoding='utf-8') as f:
                entity_content = f.read()

            # Extract entity name
            entity_name = Path(entity_path).stem.replace('.entity', '')
            self.logger.debug(f"Processing entity: {entity_name}")

            # Generate each type of file
            generation_types = ['dto', 'service', 'controller']
            
            for gen_type in generation_types:
                if getattr(self.config, f'GENERATE_{gen_type.upper()}S', True):
                    try:
                        self.logger.info(f"Generating {gen_type} for {entity_path}")
                        code = self.generate_code_with_ollama(
                            entity_path, 
                            entity_content, 
                            gen_type
                        )
                        
                        if not code:
                            self.logger.error(f"No code generated for {gen_type}")
                            continue
                        
                        # Save generated code
                        output_file = output_path / f'{gen_type}s' / f'{entity_name}.{gen_type}.ts'
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(code)
                        
                        self.logger.info(f"Generated {gen_type} for {entity_name}")
                        
                    except Exception as e:
                        self.logger.error(f"Error generating {gen_type} for {entity_name}: {str(e)}")
                        continue

        except Exception as e:
            self.logger.error(f"Error processing entity {entity_path}: {str(e)}")
            raise

    def generate_all(self, source_path: Path, output_path: Path):
        """Generate code for all entities with parallel processing"""
        try:
            # First analyze project structure
            self.analyze_project_structure(source_path)
            
            # Process entities in parallel
            with ThreadPoolExecutor() as executor:
                futures = []
                for entity in self.project_context['entities']:
                    futures.append(
                        executor.submit(
                            self.process_entity,
                            entity['path'],
                            output_path
                        )
                    )
                
                # Wait for all generations to complete
                failed = []
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        failed.append(str(e))
                
                if failed:
                    raise Exception(f"Generation completed with {len(failed)} errors: {', '.join(failed)}")
                    
            self.logger.info("Code generation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating code: {str(e)}")
            raise
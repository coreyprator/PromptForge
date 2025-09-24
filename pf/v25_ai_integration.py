#!/usr/bin/env python3
"""
PromptForge V2.5 - AI Integration Infrastructure
Provider abstraction layer with Channel-A JSON parsing
"""

import json
import asyncio
import aiohttp
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import logging
from pathlib import Path
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    MOCK = "mock"

@dataclass
class AIAttachment:
    """Represents a file or image attachment"""
    name: str
    content: Union[str, bytes]
    mime_type: str
    attachment_type: str  # 'file', 'image', 'text'

@dataclass
class AIRequest:
    """Structured AI request"""
    prompt: str
    attachments: List[AIAttachment] = field(default_factory=list)
    provider: AIProvider = AIProvider.ANTHROPIC
    temperature: float = 0.7
    max_tokens: int = 4000
    system_prompt: Optional[str] = None

@dataclass
class AIResponse:
    """Structured AI response"""
    content: str
    provider: AIProvider
    success: bool
    error_message: Optional[str] = None
    usage_info: Dict[str, Any] = field(default_factory=dict)
    channel_a_json: Optional[str] = None

class ChannelAParser:
    """Robust Channel-A JSON extraction and validation"""
    
    @staticmethod
    def extract_json_blocks(text: str) -> List[str]:
        """Extract all JSON code blocks from text"""
        # Pattern for JSON code blocks with optional language specifier
        patterns = [
            r'```json\s*(\{.*?\})\s*```',  # ```json { ... } ```
            r'```\s*(\{.*?"files".*?\})\s*```',  # ``` { ... "files" ... } ```
            r'(\{[^{}]*"files"[^{}]*\{.*?\}[^{}]*\})'  # Raw JSON with "files" key
        ]
        
        json_blocks = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            json_blocks.extend(matches)
        
        return json_blocks
    
    @staticmethod
    def validate_channel_a_structure(json_obj: Dict[str, Any]) -> tuple[bool, str]:
        """Validate Channel-A JSON structure"""
        try:
            # Check for required 'files' key
            if 'files' not in json_obj:
                return False, "Missing required 'files' array"
            
            files = json_obj['files']
            if not isinstance(files, list):
                return False, "'files' must be an array"
            
            if len(files) == 0:
                return False, "'files' array cannot be empty"
            
            # Validate each file object
            required_fields = ['path', 'language', 'contents']
            for i, file_obj in enumerate(files):
                if not isinstance(file_obj, dict):
                    return False, f"File {i}: must be an object"
                
                for field in required_fields:
                    if field not in file_obj:
                        return False, f"File {i}: missing required field '{field}'"
                    
                    if not isinstance(file_obj[field], str):
                        return False, f"File {i}: field '{field}' must be a string"
                
                # Validate path format
                path = file_obj['path']
                if path.startswith('/') or ':' in path:
                    return False, f"File {i}: path must be relative (no absolute paths or drive letters)"
                
                # Validate language
                language = file_obj['language'].lower()
                supported_languages = {
                    'python', 'javascript', 'typescript', 'java', 'csharp', 'cpp', 'c',
                    'html', 'css', 'json', 'xml', 'yaml', 'markdown', 'text', 'bash', 'powershell'
                }
                if language not in supported_languages:
                    logger.warning(f"File {i}: unusual language '{language}' - proceeding anyway")
            
            return True, "Valid Channel-A JSON structure"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @classmethod
    def parse_response(cls, response_text: str) -> tuple[Optional[str], List[str]]:
        """Parse AI response for Channel-A JSON"""
        json_blocks = cls.extract_json_blocks(response_text)
        valid_json = None
        validation_errors = []
        
        for block in json_blocks:
            try:
                # Clean up the JSON block
                cleaned_json = block.strip()
                
                # Parse JSON
                json_obj = json.loads(cleaned_json)
                
                # Validate Channel-A structure
                is_valid, message = cls.validate_channel_a_structure(json_obj)
                
                if is_valid:
                    # Format nicely
                    valid_json = json.dumps(json_obj, indent=2)
                    logger.info("Successfully extracted and validated Channel-A JSON")
                    break
                else:
                    validation_errors.append(f"Structure validation failed: {message}")
                    
            except json.JSONDecodeError as e:
                validation_errors.append(f"JSON parse error: {str(e)}")
            except Exception as e:
                validation_errors.append(f"Unexpected error: {str(e)}")
        
        return valid_json, validation_errors

class AIProviderBase(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = None
    
    @abstractmethod
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Send request to AI provider"""
        pass
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for Channel-A JSON responses"""
        return """You are a helpful AI assistant that provides code and technical solutions. 

When providing code, structure your response as Channel-A JSON format:

```json
{
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "language": "python",
      "contents": "complete file contents here"
    }
  ]
}
```

Important guidelines:
- Use relative paths only (no absolute paths or drive letters)
- Provide complete file contents, not snippets
- Include proper language specification
- Ensure JSON is valid and properly formatted
- You can include explanatory text before or after the JSON block"""

class AnthropicProvider(AIProviderBase):
    """Anthropic Claude API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = AIProvider.ANTHROPIC
        self.api_key = config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = config.get('model', 'claude-3-sonnet-20240229')
    
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Send request to Anthropic API"""
        if not self.api_key:
            return AIResponse(
                content="",
                provider=self.provider_type,
                success=False,
                error_message="Anthropic API key not configured"
            )
        
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # Build messages
            messages = []
            
            # Handle attachments
            if request.attachments:
                content_parts = [{"type": "text", "text": request.prompt}]
                
                for attachment in request.attachments:
                    if attachment.attachment_type == 'image':
                        # Convert image to base64 if it's bytes
                        if isinstance(attachment.content, bytes):
                            image_data = base64.b64encode(attachment.content).decode()
                        else:
                            image_data = attachment.content
                        
                        content_parts.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": attachment.mime_type,
                                "data": image_data
                            }
                        })
                    elif attachment.attachment_type == 'file':
                        # Include file content in text
                        file_content = attachment.content
                        if isinstance(file_content, bytes):
                            file_content = file_content.decode('utf-8')
                        
                        content_parts.append({
                            "type": "text",
                            "text": f"\n\n--- File: {attachment.name} ---\n{file_content}\n--- End File ---\n"
                        })
                
                messages.append({
                    "role": "user",
                    "content": content_parts
                })
            else:
                messages.append({
                    "role": "user",
                    "content": request.prompt
                })
            
            # Build request payload
            payload = {
                "model": self.model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": messages
            }
            
            # Add system prompt if provided
            system_prompt = request.system_prompt or self._create_system_prompt()
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        content = response_data['content'][0]['text']
                        
                        # Parse for Channel-A JSON
                        channel_a_json, parse_errors = ChannelAParser.parse_response(content)
                        
                        return AIResponse(
                            content=content,
                            provider=self.provider_type,
                            success=True,
                            usage_info=response_data.get('usage', {}),
                            channel_a_json=channel_a_json
                        )
                    else:
                        error_msg = response_data.get('error', {}).get('message', f"HTTP {response.status}")
                        return AIResponse(
                            content="",
                            provider=self.provider_type,
                            success=False,
                            error_message=error_msg
                        )
        
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return AIResponse(
                content="",
                provider=self.provider_type,
                success=False,
                error_message=str(e)
            )

class OpenAIProvider(AIProviderBase):
    """OpenAI API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = AIProvider.OPENAI
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = config.get('model', 'gpt-4')
    
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Send request to OpenAI API"""
        if not self.api_key:
            return AIResponse(
                content="",
                provider=self.provider_type,
                success=False,
                error_message="OpenAI API key not configured"
            )
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Build messages
            messages = []
            
            # Add system message
            system_prompt = request.system_prompt or self._create_system_prompt()
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Handle attachments
            if request.attachments:
                content_parts = [{"type": "text", "text": request.prompt}]
                
                for attachment in request.attachments:
                    if attachment.attachment_type == 'image':
                        # OpenAI vision API format
                        if isinstance(attachment.content, bytes):
                            image_data = base64.b64encode(attachment.content).decode()
                            data_url = f"data:{attachment.mime_type};base64,{image_data}"
                        else:
                            data_url = attachment.content
                        
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": data_url}
                        })
                    elif attachment.attachment_type == 'file':
                        # Include file content in text
                        file_content = attachment.content
                        if isinstance(file_content, bytes):
                            file_content = file_content.decode('utf-8')
                        
                        content_parts[0]["text"] += f"\n\n--- File: {attachment.name} ---\n{file_content}\n--- End File ---\n"
                
                messages.append({
                    "role": "user",
                    "content": content_parts
                })
            else:
                messages.append({
                    "role": "user",
                    "content": request.prompt
                })
            
            # Build request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        content = response_data['choices'][0]['message']['content']
                        
                        # Parse for Channel-A JSON
                        channel_a_json, parse_errors = ChannelAParser.parse_response(content)
                        
                        return AIResponse(
                            content=content,
                            provider=self.provider_type,
                            success=True,
                            usage_info=response_data.get('usage', {}),
                            channel_a_json=channel_a_json
                        )
                    else:
                        error_msg = response_data.get('error', {}).get('message', f"HTTP {response.status}")
                        return AIResponse(
                            content="",
                            provider=self.provider_type,
                            success=False,
                            error_message=error_msg
                        )
        
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return AIResponse(
                content="",
                provider=self.provider_type,
                success=False,
                error_message=str(e)
            )

class MockProvider(AIProviderBase):
    """Mock provider for testing without API calls"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = AIProvider.MOCK
        self.responses = config.get('mock_responses', [])
        self.response_index = 0
    
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Send mock request"""
        # Simulate network delay
        await asyncio.sleep(1)
        
        if self.responses and self.response_index < len(self.responses):
            content = self.responses[self.response_index]
            self.response_index += 1
        else:
            # Default mock response with Channel-A JSON
            content = f"""I'll help you with that request: "{request.prompt[:50]}..."

Here's a solution:

```json
{{
  "files": [
    {{
      "path": "src/mock_example.py",
      "language": "python",
      "contents": "# Mock response generated by MockProvider\\nprint('Hello from mock AI!')\\n\\ndef main():\\n    print('Request: {request.prompt[:30]}...')\\n\\nif __name__ == '__main__':\\n    main()\\n"
    }}
  ]
}}
```

This creates a basic Python file that demonstrates the requested functionality."""
        
        # Parse for Channel-A JSON
        channel_a_json, parse_errors = ChannelAParser.parse_response(content)
        
        return AIResponse(
            content=content,
            provider=self.provider_type,
            success=True,
            usage_info={"mock": True},
            channel_a_json=channel_a_json
        )

class AIIntegrationManager:
    """Main AI integration manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.cwd() / '.pf' / 'ai_config.json'
        self.config = self._load_config()
        self.providers = self._initialize_providers()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load AI config: {e}")
        
        # Default configuration
        return {
            "default_provider": "mock",
            "providers": {
                "anthropic": {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4000,
                    "temperature": 0.7
                },
                "openai": {
                    "model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7
                },
                "mock": {
                    "mock_responses": []
                }
            }
        }
    
    def _initialize_providers(self) -> Dict[AIProvider, AIProviderBase]:
        """Initialize AI providers"""
        providers = {}
        
        provider_config = self.config.get('providers', {})
        
        providers[AIProvider.ANTHROPIC] = AnthropicProvider(provider_config.get('anthropic', {}))
        providers[AIProvider.OPENAI] = OpenAIProvider(provider_config.get('openai', {}))
        providers[AIProvider.MOCK] = MockProvider(provider_config.get('mock', {}))
        
        return providers
    
    def save_config(self):
        """Save current configuration"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, indent=2, fp=f)
        except Exception as e:
            logger.error(f"Failed to save AI config: {e}")
    
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Send request to appropriate provider"""
        provider = self.providers.get(request.provider)
        if not provider:
            return AIResponse(
                content="",
                provider=request.provider,
                success=False,
                error_message=f"Provider {request.provider.value} not available"
            )
        
        logger.info(f"Sending request to {request.provider.value} provider")
        response = await provider.send_request(request)
        
        # Log the response
        if response.success:
            logger.info(f"Request successful - Channel-A JSON: {'Found' if response.channel_a_json else 'Not found'}")
        else:
            logger.error(f"Request failed: {response.error_message}")
        
        return response
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        available = []
        for provider_type, provider in self.providers.items():
            if provider_type == AIProvider.MOCK:
                available.append("Mock (Testing)")
            elif provider_type == AIProvider.ANTHROPIC:
                if provider.api_key:
                    available.append("Anthropic")
                else:
                    available.append("Anthropic (No API Key)")
            elif provider_type == AIProvider.OPENAI:
                if provider.api_key:
                    available.append("OpenAI")
                else:
                    available.append("OpenAI (No API Key)")
        
        return available

# Example usage and testing
async def test_ai_integration():
    """Test the AI integration system"""
    manager = AIIntegrationManager()
    
    # Test with mock provider
    request = AIRequest(
        prompt="Create a simple Python hello world program",
        provider=AIProvider.MOCK
    )
    
    response = await manager.send_request(request)
    
    print(f"Response Success: {response.success}")
    print(f"Provider: {response.provider.value}")
    print(f"Content Length: {len(response.content)}")
    print(f"Channel-A JSON Found: {'Yes' if response.channel_a_json else 'No'}")
    
    if response.channel_a_json:
        print("\nExtracted Channel-A JSON:")
        print(response.channel_a_json[:200] + "..." if len(response.channel_a_json) > 200 else response.channel_a_json)

if __name__ == "__main__":
    asyncio.run(test_ai_integration())

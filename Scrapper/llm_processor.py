import logging
from typing import Dict, Any, Optional
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure
import json
import re

from config import Config

class LLMProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini API
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required in environment variables")
        
        configure(api_key=Config.GEMINI_API_KEY)
        self.model = GenerativeModel(Config.GEMINI_MODEL)
    
    async def process_content(self, content_data: Dict[str, Any], team_id: str, user_id: str = "") -> Optional[Dict[str, Any]]:
        """Process content through LLM to extract structured knowledge."""
        try:
            # First, convert content to markdown
            markdown_content = await self._convert_to_markdown(content_data)
            
            # Then extract structured knowledge
            knowledge_item = await self._extract_knowledge(content_data, markdown_content, team_id, user_id)
            
            return knowledge_item
            
        except Exception as e:
            self.logger.error(f"Error processing content with LLM: {e}")
            return None
    
    async def _convert_to_markdown(self, content_data: Dict[str, Any]) -> str:
        """Convert content to markdown format using LLM."""
        try:
            title = content_data.get('title', '')
            content = content_data.get('content', '')
            content_type = content_data.get('content_type', 'blog')
            
            prompt = f"""
            Convert the following content to well-formatted Markdown. 
            Preserve all important information, structure, and formatting.
            
            Title: {title}
            Content Type: {content_type}
            Content:
            {content[:8000]}  # Limit content length for API
            
            Please return only the markdown content without any additional text or explanations.
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                # Fallback: basic markdown conversion
                return self._basic_markdown_conversion(content_data)
                
        except Exception as e:
            self.logger.error(f"Error converting to markdown: {e}")
            return self._basic_markdown_conversion(content_data)
    
    def _basic_markdown_conversion(self, content_data: Dict[str, Any]) -> str:
        """Basic markdown conversion as fallback."""
        title = content_data.get('title', '')
        content = content_data.get('content', '')
        
        markdown = f"# {title}\n\n" if title else ""
        
        # Convert paragraphs
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                markdown += f"{paragraph.strip()}\n\n"
        
        return markdown.strip()
    
    async def _extract_knowledge(self, content_data: Dict[str, Any], markdown_content: str, team_id: str, user_id: str) -> Dict[str, Any]:
        """Extract structured knowledge from content."""
        try:
            title = content_data.get('title', '')
            content_type = content_data.get('content_type', 'blog')
            author = content_data.get('author', '')
            url = content_data.get('url', '')
            
            prompt = f"""
            Analyze the following content and extract technical knowledge in a structured format.
            
            Content Information:
            - Title: {title}
            - Content Type: {content_type}
            - Author: {author}
            - URL: {url}
            
            Content (Markdown):
            {markdown_content[:6000]}  # Limit content length
            
            Please extract and structure the technical knowledge, concepts, insights, and key information from this content.
            Focus on:
            1. Technical concepts and explanations
            2. Best practices and methodologies
            3. Code examples and technical solutions
            4. Industry insights and trends
            5. Practical tips and recommendations
            
            Return the knowledge in a clear, well-organized markdown format that would be valuable for a technical knowledge base.
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Clean and structure the response
                structured_content = self._clean_llm_response(response.text)
                
                return {
                    "team_id": team_id,
                    "items": [
                        {
                            "title": title,
                            "content": structured_content,
                            "content_type": content_type,
                            "source_url": url,
                            "author": author,
                            "user_id": user_id
                        }
                    ]
                }
            else:
                # Fallback: use original markdown content
                return {
                    "team_id": team_id,
                    "items": [
                        {
                            "title": title,
                            "content": markdown_content,
                            "content_type": content_type,
                            "source_url": url,
                            "author": author,
                            "user_id": user_id
                        }
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"Error extracting knowledge: {e}")
            # Return basic structure with original content
            return {
                "team_id": team_id,
                "items": [
                    {
                        "title": content_data.get('title', ''),
                        "content": markdown_content,
                        "content_type": content_data.get('content_type', 'blog'),
                        "source_url": content_data.get('url', ''),
                        "author": content_data.get('author', ''),
                        "user_id": user_id
                    }
                ]
            }
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean and format LLM response."""
        # Remove any markdown code blocks that might wrap the response
        response = re.sub(r'^```markdown\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        
        # Remove any JSON formatting if present
        response = re.sub(r'^```json\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        
        # Clean up excessive whitespace
        response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
        
        return response.strip()
    
    async def validate_content(self, content_data: Dict[str, Any]) -> bool:
        """Validate if content is worth processing."""
        try:
            content = content_data.get('content', '')
            title = content_data.get('title', '')
            
            # Skip if content is too short
            if len(content) < 100:
                return False
            
            # Skip if title is missing or too short
            if not title or len(title) < 5:
                return False
            
            # Check for technical keywords
            technical_keywords = [
                'api', 'code', 'programming', 'development', 'software', 'technology',
                'algorithm', 'database', 'framework', 'library', 'function', 'class',
                'method', 'variable', 'loop', 'condition', 'error', 'debug', 'test',
                'deploy', 'server', 'client', 'frontend', 'backend', 'database',
                'security', 'performance', 'optimization', 'architecture', 'design'
            ]
            
            content_lower = content.lower()
            has_technical_content = any(keyword in content_lower for keyword in technical_keywords)
            
            return has_technical_content
            
        except Exception as e:
            self.logger.error(f"Error validating content: {e}")
            return False 
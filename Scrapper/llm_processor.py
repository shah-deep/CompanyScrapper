import logging
from typing import Dict, Any, Optional
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure
import json
import re
import asyncio

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
            
            prompt = f"""
            Convert the following content to clean Markdown format. 
            IMPORTANT: Do not modify, shorten, or change any content. Only convert formatting to markdown.
            Preserve ALL original text, information, and structure exactly as provided.
            
            Title: {title}
            Content:
            {content}
            
            Return only the markdown-formatted content without any additional text or explanations.
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
    
    async def _extract_knowledge(self, content_data: Dict[str, Any], markdown_content: str, team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Extract structured knowledge from content."""
        try:
            title = content_data.get('title', '')
            content_type = content_data.get('content_type', 'blog')
            author = content_data.get('author', '')
            url = content_data.get('url', '')
            
            prompt = f"""
            Analyze the following content and perform these tasks:

            1. FIRST, determine if this is technical content worth processing:
               - Check if it contains technical concepts, code examples, programming topics, software development, APIs, algorithms, etc.
               - If it's just general information, terms of service, privacy policy, or non-technical content, respond with "NOT_TECHNICAL"
               - If it's technical content, proceed to step 2

            2. If technical, extract and enhance metadata:
               - Identify the content type (tutorial, documentation, blog post, case study, etc.)
               - Find author information if not already provided
               - Look for any technical expertise indicators

            3. Extract structured technical knowledge:
               - Technical concepts and explanations
               - Best practices and methodologies  
               - Code examples and technical solutions
               - Industry insights and trends
               - Practical tips and recommendations

            Content Information:
            - Title: {title}
            - Current Content Type: {content_type}
            - Current Author: {author}
            - URL: {url}

            Content (Markdown):
            {markdown_content}

            Please respond in this exact format:
            If NOT technical: "NOT_TECHNICAL"
            If technical: 
            "TECHNICAL|content_type|author|extracted_knowledge_markdown"
            
            Where:
            - content_type: the identified content type
            - author: the found authors (single author or comma separated list string or original or empty string)
            - extracted_knowledge_markdown: the structured technical knowledge
            """
            
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return None
            
            response_text = response.text.strip()
            
            # Check if content is not technical
            if response_text == "NOT_TECHNICAL":
                self.logger.info(f"Skipping non-technical content: {title}")
                return None
            
            # Parse technical response
            if response_text.startswith("TECHNICAL|"):
                try:
                    parts = response_text.split("|", 3)
                    if len(parts) == 4:
                        _, extracted_content_type, extracted_author, structured_content = parts
                        
                        # Use extracted values if they're more specific than original
                        final_content_type = extracted_content_type if extracted_content_type and extracted_content_type != 'blog' else content_type
                        final_author = extracted_author if extracted_author and extracted_author != 'Unknown' else author
                        
                        # Clean the structured content
                        cleaned_fullcontent = self._clean_llm_response(markdown_content)
                        cleaned_content = self._clean_llm_response(structured_content)
                        
                        return {
                            "team_id": team_id,
                            "items": [
                                {
                                    "title": title,
                                    "content": cleaned_content,
                                    "full_content": cleaned_fullcontent,
                                    "content_type": final_content_type,
                                    "source_url": url,
                                    "author": final_author
                                }
                            ]
                        }
                except Exception as e:
                    self.logger.error(f"Error parsing LLM response: {e}")
            
            # Fallback: use original content if parsing fails
            return {
                "team_id": team_id,
                "items": [
                    {
                        "title": title,
                        "content": markdown_content,
                        "content_type": content_type,
                        "source_url": url,
                        "author": author
                    }
                ]
            }
                
        except Exception as e:
            self.logger.error(f"Error extracting knowledge: {e}")
            return None
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
    
    def validate_content_sync(self, content_data: Dict[str, Any]) -> bool:
        """Synchronous version of validate_content for multiprocessing workers."""
        # Create a new event loop for this thread/process
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.validate_content(content_data))
        finally:
            if loop.is_running():
                loop.close()
    
    def process_content_sync(self, content_data: Dict[str, Any], team_id: str, user_id: str = "") -> Optional[Dict[str, Any]]:
        """Synchronous version of process_content for multiprocessing workers."""
        # Create a new event loop for this thread/process
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.process_content(content_data, team_id, user_id))
        finally:
            if loop.is_running():
                loop.close() 
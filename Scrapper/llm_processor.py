import logging
from typing import Dict, Any, Optional, List, Tuple
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
            # Check if content needs chunking
            content = content_data.get('content', '')
            if len(content) > Config.CHUNK_SIZE:
                self.logger.info(f"Content is large ({len(content)} chars), processing in chunks")
                return await self._process_content_in_chunks(content_data, team_id, user_id)
            else:
                # Process normally for smaller content
                markdown_content = await self._convert_to_markdown(content_data)
                knowledge_item = await self._extract_knowledge(content_data, markdown_content, team_id, user_id)
                return knowledge_item
            
        except Exception as e:
            self.logger.error(f"Error processing content with LLM: {e}")
            return None
    
    async def _process_content_in_chunks(self, content_data: Dict[str, Any], team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Process large content by breaking it into chunks and combining results."""
        try:
            content = content_data.get('content', '')
            title = content_data.get('title', '')
            url = content_data.get('url', '')
            content_type = content_data.get('content_type', '')
            author = content_data.get('author', '')

            # Create chunks
            chunks = self._create_content_chunks(content)
            self.logger.info(f"Created {len(chunks)} chunks for processing")
            
            # Process first chunk to get metadata (content_type, author)
            first_chunk_data = {
                **content_data,
                'content': chunks[0]
            }
            
            # Convert first chunk to markdown
            first_markdown = await self._convert_to_markdown(first_chunk_data)
            
            # Extract metadata from first chunk
            metadata_result = await self._extract_metadata_only(first_chunk_data, first_markdown)
            if not metadata_result:
                self.logger.warning("Failed to extract metadata from first chunk")
            else:
                content_type, author = metadata_result
            
            # Process all chunks for content extraction
            chunk_results = []
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                chunk_data = {
                    **content_data,
                    'content': chunk,
                    'content_type': content_type,  # Use consistent content_type
                    'author': author  # Use consistent author
                }
                
                # Convert chunk to markdown
                chunk_markdown = await self._convert_to_markdown(chunk_data)
                
                # Extract structured content from chunk
                chunk_structured = await self._extract_structured_content_only(chunk_data, chunk_markdown)
                if chunk_structured:
                    chunk_results.append({
                        'markdown': chunk_markdown,
                        'structured': chunk_structured
                    })
            
            if not chunk_results:
                self.logger.warning("No valid chunks processed")
                return None
            
            # Combine all chunks
            combined_markdown = self._combine_chunks([r['markdown'] for r in chunk_results])
            combined_structured = self._combine_chunks([r['structured'] for r in chunk_results])
            
            # Clean the combined content
            cleaned_fullcontent = self._clean_llm_response(combined_markdown)
            cleaned_content = self._clean_llm_response(combined_structured)
            
            return {
                "team_id": team_id,
                "items": [
                    {
                        "title": title,
                        "content": cleaned_content,
                        "full_content": cleaned_fullcontent,
                        "content_type": content_type,
                        "source_url": url,
                        "author": author
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing content in chunks: {e}")
            return None
    
    def _create_content_chunks(self, content: str) -> List[str]:
        """Create overlapping chunks from content."""
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + Config.CHUNK_SIZE
            
            # If this is not the last chunk, try to break at a sentence boundary
            if end < len(content):
                # Look for sentence endings within the last 200 characters of the chunk
                search_start = max(start + Config.CHUNK_SIZE - 200, start)
                search_end = min(end + 200, len(content))
                
                # Find the best break point (sentence ending)
                best_break = end
                for i in range(search_start, search_end):
                    if content[i] in '.!?':
                        # Check if it's followed by whitespace and uppercase letter (likely sentence end)
                        if i + 1 < len(content) and content[i + 1].isspace():
                            if i + 2 < len(content) and content[i + 2].isupper():
                                best_break = i + 1
                                break
                
                end = best_break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - Config.CHUNK_OVERLAP
            if start >= len(content):
                break
        
        return chunks
    
    async def _extract_metadata_only(self, content_data: Dict[str, Any], markdown_content: str) -> Optional[Tuple[str, str]]:
        """Extract only metadata (content_type, author) from the first chunk."""
        try:
            title = content_data.get('title', '')
            content_type = content_data.get('content_type', '')
            author = content_data.get('author', '')
            url = content_data.get('url', '')
            
            prompt = f"""
            Analyze the following content and extract ONLY the metadata:

            - Identify the content type (tutorial, documentation, blog post, case study, etc.)
            - Find author information if not already provided

            Content Information:
            - Title: {title}
            - Current Content Type: {content_type}
            - Current Authors: {author}
            - URL: {url}

            Content (Markdown):
            {markdown_content}

            "content_type|author"
            
            Where:
            - content_type: the identified content type
            - author: the found authors (single author or comma separated list string or original or empty string)
            """
            
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return None
            
            response_text = response.text.strip()
            
           
            try:
                parts = response_text.split("|", 2)
                if len(parts) == 3:
                    _, extracted_content_type, extracted_author = parts
                    
                    # Use extracted values if they're more specific than original
                    final_content_type = extracted_content_type if extracted_content_type and extracted_content_type != 'blog' else content_type
                    final_author = extracted_author if extracted_author and extracted_author != 'Unknown' else author
                    
                    return final_content_type, final_author
            except Exception as e:
                self.logger.error(f"Error parsing metadata response: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")
            return None
    
    async def _extract_structured_content_only(self, content_data: Dict[str, Any], markdown_content: str) -> Optional[str]:
        """Extract only structured content from a chunk."""
        try:
            title = content_data.get('title', '')
            content_type = content_data.get('content_type', '')
            
            prompt = f"""
            Extract structured technical knowledge from this content chunk:

            Content Information:
            - Title: {title}
            - Content Type: {content_type}

            Content Chunk (Markdown):
            {markdown_content}

            Extract and structure the technical knowledge from this chunk:
            - Technical concepts and explanations
            - Best practices and methodologies  
            - Code examples and technical solutions
            - Industry insights and trends
            - Practical tips and recommendations

            If this chunk does not contain technical information, return an empty string.
            Return only the structured technical knowledge in markdown format.
            Focus on the technical content present in this specific chunk.
            """
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting structured content from chunk: {e}")
            return None
    
    def _combine_chunks(self, chunks: List[str]) -> str:
        """Combine multiple chunks into a single coherent document."""
        if not chunks:
            return ""
        
        if len(chunks) == 1:
            return chunks[0]
        
        # Combine chunks with proper spacing
        combined = ""
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Add separator between chunks
                combined += "\n\n---\n\n"
            combined += chunk
        
        return combined
    
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
            content_type = content_data.get('content_type', '')
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
            content_type = content_data.get('content_type', '')
            
            # Skip if content is too short
            if len(content) < 100:
                return False
            
            # Check for technical keywords
            technical_keywords = [
                'api', 'code', 'programming', 'development', 'software', 'technology',
                'algorithm', 'database', 'framework', 'library', 'function', 'class',
                'method', 'variable', 'loop', 'condition', 'error', 'debug', 'test',
                'deploy', 'server', 'client', 'frontend', 'backend', 'database',
                'security', 'performance', 'optimization', 'architecture', 'design',
                'interview', 'coding', 'technical', 'computer', 'system', 'application',
                'data', 'analysis', 'machine', 'learning', 'artificial', 'intelligence',
                'web', 'mobile', 'cloud', 'network', 'protocol', 'interface'
            ]
            
            content_lower = content.lower()
            has_technical_content = any(keyword in content_lower for keyword in technical_keywords)
            
            # If we have technical content, accept it regardless of title
            if has_technical_content:
                return True
            
            # If no technical keywords found, check if it's a book or document type
            # Books and documents might not have obvious technical keywords but could be valuable
            if content_type in ['book', 'document', 'pdf', 'manual', 'guide'] and len(content) > 1000:
                return True
            
            # If title is missing but content is substantial, check for any technical indicators
            if not title or len(title) < 5:
                # Look for any technical indicators in the first 2000 characters
                sample_content = content[:2000].lower()
                technical_indicators = [
                    'chapter', 'section', 'problem', 'solution', 'example', 'implementation',
                    'design', 'pattern', 'structure', 'model', 'approach', 'methodology',
                    'practice', 'principle', 'concept', 'theory', 'framework', 'architecture'
                ]
                has_indicators = any(indicator in sample_content for indicator in technical_indicators)
                if has_indicators and len(content) > 2000:
                    return True
            
            return False
            
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
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
            if metadata_result:
                title, content_type, author = metadata_result
                self.logger.info(f"Metadata result: {metadata_result}")
            else:
                self.logger.warning("Failed to extract metadata from first chunk, using original values")
            
            # Process all chunks for content extraction
            chunk_results = []
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                chunk_data = {
                    **content_data,
                    'content': chunk,
                    'title': title,  # Use consistent title
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
            
            # Create item with conditional user_id
            item = {
                        "title": title,
                        "content": cleaned_content,
                        "full_content": cleaned_fullcontent,
                        "content_type": content_type,
                        "source_url": url,
                        "author": author,
                        "user_id": ""
                    }
            
            # Add user_id to item if provided and not empty
            if user_id and user_id.strip():
                item["user_id"] = user_id.strip()
            
            return {
                "team_id": team_id,
                "items": [item]
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
    
    async def _extract_metadata_only(self, content_data: Dict[str, Any], markdown_content: str) -> Optional[Tuple[str, str, str]]:
        """Extract metadata (title, content_type, author) from the first chunk."""
        try:
            title = content_data.get('title', '')
            content_type = content_data.get('content_type', '')
            author = content_data.get('author', '')
            
            prompt = f"""
            Analyze the following content and extract metadata. Extract what you can find, even if some information is missing:

            - Extract or generate a title if not provided
            - Identify the content type (tutorial, documentation, blog post, case study, etc.)
            - Find author information if not already provided

            Content Information:
            - Current Title: {title}
            - Possible Content Type: {content_type}
            - Possible Authors: {author}

            Content (Markdown):
            {markdown_content}

            Respond in this EXACT format: "title|content_type|author"
            
            Where:
            - title: extracted or generated title (find & use original if good, generate if missing/generic)
            - content_type: the identified content type (use original if given)
            - author: the found authors (or empty string)
            
            IMPORTANT: 
            - Use ONLY the pipe-separated format: "title|content_type|author"
            - Do NOT use JSON format
            - Do NOT add any additional text or explanations
            - If any field cannot be determined, use the original value or empty string. Do not fail completely.
            """
            
            response = self.model.generate_content(prompt)
            
            if not response.text:
                # Return original values if LLM fails
                return title, content_type, author
            
            response_text = response.text.strip()
            
            try:
                # First try to parse as pipe-separated format
                if "|" in response_text:
                    parts = response_text.split("|", 2)
                    if len(parts) == 3:
                        extracted_title, extracted_content_type, extracted_author = parts
                        
                        # Use extracted values if they're meaningful, otherwise fall back to originals
                        final_title = extracted_title if extracted_title and extracted_title.strip() and extracted_title.lower() not in ['unknown', 'untitled', 'no title'] else title
                        final_content_type = extracted_content_type if extracted_content_type and extracted_content_type.strip() and extracted_content_type.lower() != 'unknown' else content_type
                        final_author = extracted_author if extracted_author and extracted_author.strip() and extracted_author.lower() != 'unknown' else author
                        
                        return final_title, final_content_type, final_author
                
                # If pipe-separated format fails, try to parse JSON format as fallback
                import json
                try:
                    # Clean the response using existing function
                    cleaned_response = self._clean_llm_response(response_text)
                    
                    json_data = json.loads(cleaned_response)
                    
                    extracted_title = json_data.get('title', title)
                    extracted_content_type = json_data.get('content_type', content_type)
                    extracted_author = json_data.get('author', author)
                    
                    # Use extracted values if they're meaningful, otherwise fall back to originals
                    final_title = extracted_title if extracted_title and extracted_title.strip() and extracted_title.lower() not in ['unknown', 'untitled', 'no title'] else title
                    final_content_type = extracted_content_type if extracted_content_type and extracted_content_type.strip() and extracted_content_type.lower() != 'unknown' else content_type
                    final_author = extracted_author if extracted_author and extracted_author.strip() and extracted_author.lower() != 'unknown' else author
                    
                    self.logger.info(f"Successfully parsed JSON response for metadata")
                    return final_title, final_content_type, final_author
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse JSON response: {response_text}")
                
                # If both formats fail, return original values
                self.logger.warning(f"Unexpected metadata response format: {response_text}")
                return title, content_type, author
                
            except Exception as e:
                self.logger.error(f"Error parsing metadata response: {e}")
                # Return original values if parsing fails
                return title, content_type, author
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")
            # Return original values if extraction fails completely
            return content_data.get('title', ''), content_data.get('content_type', ''), content_data.get('author', '')
    
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
               - Extract or generate a title if not provided or if the current title is generic
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
            - Current Title: {title}
            - Possible Content Type: {content_type}
            - Possible Authors: {author}
            - URL: {url}

            Content (Markdown):
            {markdown_content}

            Please respond in this exact format:
            If NOT technical: "NOT_TECHNICAL"
            If technical: 
            "TECHNICAL|title|content_type|author|extracted_knowledge_markdown"
            
            Where:
            - title: extracted or generated title (find & use original if good, generate if missing/generic)
            - content_type: the identified content type (use original if given)
            - author: the found authors (or empty string)
            - extracted_knowledge_markdown: the structured technical knowledge
            
            IMPORTANT: 
            - Use ONLY the pipe-separated format: "TECHNICAL|title|content_type|author|extracted_knowledge_markdown"
            - Do NOT use JSON format
            - Do NOT add any additional text or explanations
            - If any metadata field cannot be determined, use the original value or empty string. Do not fail completely.
            """
            
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return None
            
            response_text = response.text.strip()
            
            # Check if content is not technical
            if response_text == "NOT_TECHNICAL":
                self.logger.info(f"Skipping non-technical content: {title}")
                return None
            
            # Parse technical response - try pipe-separated format first
            if response_text.startswith("TECHNICAL|"):
                try:
                    parts = response_text.split("|", 4)
                    if len(parts) == 5:
                        _, extracted_title, extracted_content_type, extracted_author, structured_content = parts
                        
                        # Use extracted values if they're more specific than original
                        final_title = extracted_title if extracted_title and extracted_title.strip() and extracted_title.lower() not in ['unknown', 'untitled', 'no title'] else title
                        final_content_type = extracted_content_type if extracted_content_type and extracted_content_type != 'blog' else content_type
                        final_author = extracted_author if extracted_author and extracted_author != 'Unknown' else author
                        
                        # Clean the structured content using existing function
                        cleaned_fullcontent = self._clean_llm_response(markdown_content)
                        cleaned_content = self._clean_llm_response(structured_content)
                        
                        # Create item with conditional user_id
                        item = {
                                    "title": final_title,
                                    "content": cleaned_content,
                                    "full_content": cleaned_fullcontent,
                                    "content_type": final_content_type,
                                    "source_url": url,
                                    "author": final_author,
                                    "user_id": ""
                                }
                        
                        # Add user_id to item if provided and not empty
                        if user_id and user_id.strip():
                            item["user_id"] = user_id
                        
                        return {
                            "team_id": team_id,
                            "items": [item]
                        }
                except Exception as e:
                    self.logger.error(f"Error parsing pipe-separated LLM response: {e}")
            
            # If pipe-separated format fails, try to parse JSON format as fallback
            try:
                # Clean the response using existing function
                cleaned_response = self._clean_llm_response(response_text)
                
                json_data = json.loads(cleaned_response)
                
                extracted_title = json_data.get('title', title)
                extracted_content_type = json_data.get('content_type', content_type)
                extracted_author = json_data.get('author', author)
                extracted_knowledge = json_data.get('knowledge', '') or json_data.get('content', '')
                
                # Use extracted values if they're meaningful, otherwise fall back to originals
                final_title = extracted_title if extracted_title and extracted_title.strip() and extracted_title.lower() not in ['unknown', 'untitled', 'no title'] else title
                final_content_type = extracted_content_type if extracted_content_type and extracted_content_type.strip() and extracted_content_type.lower() != 'unknown' else content_type
                final_author = extracted_author if extracted_author and extracted_author.strip() and extracted_author.lower() != 'unknown' else author
                
                # Clean the content using existing function
                cleaned_fullcontent = self._clean_llm_response(markdown_content)
                cleaned_content = self._clean_llm_response(extracted_knowledge) if extracted_knowledge else cleaned_fullcontent
                
                # Create item with conditional user_id
                item = {
                            "title": final_title,
                            "content": cleaned_content,
                            "full_content": cleaned_fullcontent,
                            "content_type": final_content_type,
                            "source_url": url,
                            "author": final_author
                        }
                
                # Add user_id to item if provided
                if user_id and user_id.strip():
                    item["user_id"] = user_id
                
                self.logger.info(f"Successfully parsed JSON response for knowledge extraction")
                return {
                    "team_id": team_id,
                    "items": [item]
                }
                
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON response: {response_text}")
            except Exception as e:
                self.logger.error(f"Error parsing JSON LLM response: {e}")
            
            # Fallback: use original content if parsing fails
            # Try to extract a basic title from content if none exists
            fallback_title = title
            if not fallback_title or len(fallback_title.strip()) < 3:
                # Try to extract title from first few lines of content
                content_lines = markdown_content.split('\n')
                for line in content_lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if line and len(line) > 5 and len(line) < 100:
                        # Remove markdown formatting
                        clean_line = re.sub(r'^#+\s*', '', line)
                        if clean_line and not clean_line.startswith('```'):
                            fallback_title = clean_line
                            break
            
            # Clean the content using existing function
            cleaned_fullcontent = self._clean_llm_response(markdown_content)
            
            # Create item with conditional user_id
            item = {
                        "title": fallback_title,
                        "content": cleaned_fullcontent,
                        "content_type": content_type,
                        "source_url": url,
                        "author": author
                    }
            
            # Add user_id to item if provided
            if user_id and user_id.strip():
                item["user_id"] = user_id
            
            return {
                "team_id": team_id,
                "items": [item]
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
                sample_content = content[:5000].lower()
                technical_indicators = [
                    'chapter', 'section', 'problem', 'solution', 'example', 'implementation',
                    'design', 'pattern', 'structure', 'model', 'approach', 'methodology',
                    'practice', 'principle', 'concept', 'theory', 'framework', 'architecture'
                ]
                has_indicators = any(indicator in sample_content for indicator in technical_indicators)
                if has_indicators and len(content) > 1000:
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
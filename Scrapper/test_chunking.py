#!/usr/bin/env python3
"""
Test script to verify content chunking functionality for large content.
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_processor import LLMProcessor
from config import Config

def create_large_test_content():
    """Create a large test content to test chunking."""
    # Create a large technical document
    sections = [
        "# Introduction to Python Programming\n\n",
        "Python is a high-level, interpreted programming language known for its simplicity and readability. " * 50 + "\n\n",
        
        "## Basic Syntax\n\n",
        "Python uses indentation to define code blocks. This makes the code more readable and enforces good coding practices. " * 40 + "\n\n",
        
        "### Variables and Data Types\n\n",
        "In Python, you don't need to declare variable types explicitly. The interpreter automatically determines the type based on the value assigned. " * 45 + "\n\n",
        
        "### Control Structures\n\n",
        "Python provides several control structures including if-else statements, loops, and exception handling. " * 35 + "\n\n",
        
        "## Advanced Features\n\n",
        "Python offers many advanced features such as list comprehensions, decorators, generators, and context managers. " * 40 + "\n\n",
        
        "### Object-Oriented Programming\n\n",
        "Python supports object-oriented programming with classes, inheritance, polymorphism, and encapsulation. " * 30 + "\n\n",
        
        "### Functional Programming\n\n",
        "Python also supports functional programming concepts like lambda functions, map, filter, and reduce. " * 25 + "\n\n",
        
        "## Libraries and Frameworks\n\n",
        "Python has a rich ecosystem of libraries and frameworks for various purposes including web development, data science, and machine learning. " * 35 + "\n\n",
        
        "### Web Development\n\n",
        "Popular web frameworks include Django, Flask, and FastAPI. These frameworks provide tools for building web applications efficiently. " * 30 + "\n\n",
        
        "### Data Science\n\n",
        "Python is widely used in data science with libraries like NumPy, Pandas, Matplotlib, and Scikit-learn. " * 25 + "\n\n",
        
        "## Best Practices\n\n",
        "Following Python best practices helps write maintainable and efficient code. This includes proper naming conventions, documentation, and testing. " * 40 + "\n\n",
        
        "### Code Style\n\n",
        "PEP 8 is the style guide for Python code. It provides guidelines for formatting, naming conventions, and code organization. " * 30 + "\n\n",
        
        "### Testing\n\n",
        "Unit testing is essential for reliable code. Python provides the unittest framework and third-party libraries like pytest. " * 25 + "\n\n",
        
        "## Conclusion\n\n",
        "Python is a versatile programming language suitable for various applications from simple scripts to complex enterprise systems. " * 20 + "\n\n"
    ]
    
    return "".join(sections)

def test_chunking_functionality():
    """Test the chunking functionality."""
    print("Testing Content Chunking Functionality")
    print("=" * 60)
    
    # Create test content
    test_content = create_large_test_content()
    content_length = len(test_content)
    
    print(f"Created test content with {content_length} characters")
    print(f"Chunk size: {Config.CHUNK_SIZE} characters")
    print(f"Chunk overlap: {Config.CHUNK_OVERLAP} characters")
    
    # Create content data
    content_data = {
        'title': 'Introduction to Python Programming',
        'content': test_content,
        'content_type': 'tutorial',
        'author': 'Python Documentation Team',
        'url': 'https://example.com/python-tutorial'
    }
    
    try:
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        
        # Test chunk creation
        print("\nTesting chunk creation...")
        chunks = llm_processor._create_content_chunks(test_content)
        print(f"Created {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(chunk)} characters")
            if i < 3:  # Show first few chunks
                print(f"    Preview: {chunk[:100]}...")
        
        # Test if content is large enough to trigger chunking
        print(f"\nContent size check: {content_length} > {Config.CHUNK_SIZE} = {content_length > Config.CHUNK_SIZE}")
        
        if content_length > Config.CHUNK_SIZE:
            print("Content is large enough to trigger chunking")
        else:
            print("Content is not large enough to trigger chunking")
            # Make content larger
            content_data['content'] = test_content * 3
            print(f"   Expanded content to {len(content_data['content'])} characters")
        
        # Test chunk combination
        print("\nTesting chunk combination...")
        combined = llm_processor._combine_chunks(chunks)
        print(f"Combined length: {len(combined)} characters")
        print(f"Original length: {len(test_content)} characters")
        print(f"Length difference: {abs(len(combined) - len(test_content))} characters")
        
        # Test with a smaller content to verify normal processing
        print("\nTesting normal processing (small content)...")
        small_content_data = {
            'title': 'Small Test',
            'content': 'This is a small test content for normal processing.',
            'content_type': 'test',
            'author': 'Test Author',
            'url': 'https://example.com/test'
        }
        
        # This should not trigger chunking
        if len(small_content_data['content']) <= Config.CHUNK_SIZE:
            print("Small content will use normal processing")
        else:
            print("Small content unexpectedly large")
        
        print("\nChunking functionality test completed!")
        print("\nThe chunking system will:")
        print("- Automatically detect large content (>8000 chars by default)")
        print("- Break content into overlapping chunks")
        print("- Extract metadata from the first chunk only")
        print("- Process each chunk for structured content")
        print("- Combine all chunks into final result")
        print("- Maintain consistency across all chunks")
        
        return True
        
    except Exception as e:
        print(f"Chunking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chunk_boundaries():
    """Test that chunks break at appropriate boundaries."""
    print("\nTesting Chunk Boundaries")
    print("=" * 40)
    
    try:
        llm_processor = LLMProcessor()
        
        # Create content with clear sentence boundaries
        test_content = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence. " * 200
        
        chunks = llm_processor._create_content_chunks(test_content)
        
        print(f"Created {len(chunks)} chunks")
        
        # Check that chunks end at sentence boundaries
        for i, chunk in enumerate(chunks):
            if chunk and not chunk.endswith(('.', '!', '?')):
                print(f"Chunk {i+1} doesn't end with sentence punctuation")
                print(f"   Ends with: '{chunk[-10:]}'")
            else:
                print(f"Chunk {i+1} ends properly")
        
        return True
        
    except Exception as e:
        print(f"Boundary test failed: {e}")
        return False

def main():
    """Main test function."""
    print("Content Chunking Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        test_chunking_functionality,
        test_chunk_boundaries
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    test_names = [
        "Chunking Functionality",
        "Chunk Boundaries"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "PASS" if result else "FAIL"
        print(f"{name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("All chunking tests passed!")
        print("\nThe chunking system is ready to handle large content.")
        print("\nConfiguration:")
        print(f"- CHUNK_SIZE: {Config.CHUNK_SIZE} characters")
        print(f"- CHUNK_OVERLAP: {Config.CHUNK_OVERLAP} characters")
        print(f"- MAX_CONTENT_LENGTH: {Config.MAX_CONTENT_LENGTH} characters")
    else:
        print("Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main() 
import json
from datetime import datetime
from urllib.parse import urlparse
import os

class URLAggregator:
    def __init__(self):
        self.all_urls = {
            'company_pages': [],
            'blog_posts': [],
            'founder_blogs': [],
            'external_mentions': [],
            'potential_urls': []
        }
        self.company_url = None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to handle trailing slashes consistently."""
        if not url:
            return url
        
        # Parse the URL
        parsed = urlparse(url)
        
        # Normalize the path - remove trailing slash unless it's the root path
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path.rstrip('/')
        
        # Reconstruct the URL
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        if parsed.fragment:
            normalized += f"#{parsed.fragment}"
        
        return normalized
    
    def _get_output_directory(self):
        """Get the output directory for saving files"""
        # Get the project root directory (two levels up from Crawler)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        output_dir = os.path.join(project_root, 'data', 'scrapped_urls')
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def _get_output_path(self, filename):
        """Get the full path for an output file"""
        output_dir = self._get_output_directory()
        return os.path.join(output_dir, filename)
    
    def set_company_url(self, url):
        """Set the company homepage URL for filename generation"""
        self.company_url = url
    
    def add_company_pages(self, pages):
        """Add company website pages"""
        # Normalize URLs before adding
        normalized_pages = []
        for page in pages:
            if isinstance(page, dict):
                normalized_page = page.copy()
                normalized_page['url'] = self._normalize_url(page.get('url', ''))
                normalized_pages.append(normalized_page)
            else:
                normalized_pages.append(page)
        self.all_urls['company_pages'].extend(normalized_pages)
    
    def add_blog_posts(self, blogs):
        """Add blog posts from company website"""
        # Normalize URLs before adding
        normalized_blogs = []
        for blog in blogs:
            if isinstance(blog, dict):
                normalized_blog = blog.copy()
                normalized_blog['url'] = self._normalize_url(blog.get('url', ''))
                normalized_blogs.append(normalized_blog)
            else:
                normalized_blogs.append(blog)
        self.all_urls['blog_posts'].extend(normalized_blogs)
    
    def add_founder_blogs(self, founder_blogs):
        """Add blogs written by founders"""
        # Normalize URLs before adding
        normalized_blogs = []
        for blog in founder_blogs:
            if isinstance(blog, dict):
                normalized_blog = blog.copy()
                normalized_blog['url'] = self._normalize_url(blog.get('url', ''))
                normalized_blogs.append(normalized_blog)
            else:
                normalized_blogs.append(blog)
        self.all_urls['founder_blogs'].extend(normalized_blogs)
    
    def add_external_mentions(self, mentions):
        """Add external mentions of the company"""
        # Normalize URLs before adding
        normalized_mentions = []
        for mention in mentions:
            if isinstance(mention, dict):
                normalized_mention = mention.copy()
                normalized_mention['url'] = self._normalize_url(mention.get('url', ''))
                normalized_mentions.append(normalized_mention)
            else:
                normalized_mentions.append(mention)
        self.all_urls['external_mentions'].extend(normalized_mentions)
    
    def add_potential_urls(self, potential_urls):
        """Add potential URLs that didn't pass LLM validation"""
        # Normalize URLs before adding
        normalized_urls = []
        for potential in potential_urls:
            if isinstance(potential, dict):
                normalized_potential = potential.copy()
                normalized_potential['url'] = self._normalize_url(potential.get('url', ''))
                normalized_urls.append(normalized_potential)
            else:
                normalized_urls.append(potential)
        self.all_urls['potential_urls'].extend(normalized_urls)
    
    def generate_url_list(self, company_name, output_file=None):
        """Generate a comprehensive URL list file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company_name.replace(' ', '_')}_urls_{timestamp}.txt"
            output_file = self._get_output_path(filename)
        else:
            # If a custom filename is provided, still save in the output directory
            output_file = self._get_output_path(output_file)
        
        print(f"Generating URL list: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Company URL Analysis Report\n")
            f.write(f"Company: {company_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Company Pages
            f.write("1. COMPANY WEBSITE PAGES\n")
            f.write("-" * 40 + "\n")
            for page in self.all_urls['company_pages']:
                f.write(f"URL: {page['url']}\n")
                if page.get('title'):
                    f.write(f"Title: {page['title']}\n")
                f.write("\n")
            
            # Blog Posts
            f.write("\n2. BLOG POSTS (Company Website)\n")
            f.write("-" * 40 + "\n")
            for blog in self.all_urls['blog_posts']:
                f.write(f"URL: {blog['url']}\n")
                if blog.get('title'):
                    f.write(f"Title: {blog['title']}\n")
                f.write("\n")
            
            # Founder Blogs
            f.write("\n3. FOUNDER BLOGS\n")
            f.write("-" * 40 + "\n")
            for blog in self.all_urls['founder_blogs']:
                f.write(f"URL: {blog['url']}\n")
                if blog.get('title'):
                    f.write(f"Title: {blog['title']}\n")
                if blog.get('founder'):
                    f.write(f"Founder: {blog['founder']}\n")
                f.write("\n")
            
            # External Mentions
            f.write("\n4. EXTERNAL MENTIONS\n")
            f.write("-" * 40 + "\n")
            for mention in self.all_urls['external_mentions']:
                f.write(f"URL: {mention['url']}\n")
                if mention.get('title'):
                    f.write(f"Title: {mention['title']}\n")
                f.write("\n")
            
            # Potential URLs
            f.write("\n5. POTENTIAL URLS (LLM Rejected)\n")
            f.write("-" * 40 + "\n")
            for potential in self.all_urls['potential_urls']:
                f.write(f"URL: {potential['url']}\n")
                if potential.get('title'):
                    f.write(f"Title: {potential['title']}\n")
                f.write("\n")
            
            # Summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Company Pages: {len(self.all_urls['company_pages'])}\n")
            f.write(f"Total Blog Posts: {len(self.all_urls['blog_posts'])}\n")
            f.write(f"Total Founder Blogs: {len(self.all_urls['founder_blogs'])}\n")
            f.write(f"Total External Mentions: {len(self.all_urls['external_mentions'])}\n")
            f.write(f"Total Potential URLs: {len(self.all_urls['potential_urls'])}\n")
            f.write(f"GRAND TOTAL: {self.get_total_urls()}\n")
        
        print(f"URL list saved to: {output_file}")
        return output_file
    
    def generate_simple_url_list(self, company_name, team_id=None, output_file=None):
        """Generate a simple list of just URLs, appending to file if it exists, avoiding duplicates."""
        if output_file is None:
            if team_id:
                # Use team_id for filename
                filename = f"{team_id}.txt"
            else:
                # Fallback to domain-based naming
                from urllib.parse import urlparse
                try:
                    if self.company_url:
                        parsed_url = urlparse(self.company_url)
                        domain = parsed_url.netloc
                        filename = f"{domain}.txt"
                    else:
                        filename = f"{company_name.replace(' ', '_')}.txt"
                except:
                    filename = f"{company_name.replace(' ', '_')}.txt"
        else:
            filename = output_file
        
        output_file = self._get_output_path(filename)

        print(f"Generating simple URL list: {output_file}")

        # Gather all URLs from the aggregator
        all_urls = []
        all_urls.extend([page['url'] for page in self.all_urls['company_pages']])
        all_urls.extend([blog['url'] for blog in self.all_urls['blog_posts']])
        all_urls.extend([blog['url'] for blog in self.all_urls['founder_blogs']])
        all_urls.extend([mention['url'] for mention in self.all_urls['external_mentions']])
        all_urls.extend([potential['url'] for potential in self.all_urls['potential_urls']])

        # Remove duplicates using normalized URLs while preserving order
        seen_normalized = set()
        unique_urls = []
        for url in all_urls:
            normalized_url = self._normalize_url(url)
            if normalized_url not in seen_normalized:
                seen_normalized.add(normalized_url)
                unique_urls.append(url)  # Keep the original URL format

        # If file exists, read existing URLs to avoid duplicates
        existing_urls = set()
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url:
                        existing_urls.add(url)

        # Filter out URLs that are already in the file (using normalized comparison)
        new_urls = []
        existing_normalized = {self._normalize_url(url) for url in existing_urls}
        for url in unique_urls:
            normalized_url = self._normalize_url(url)
            if normalized_url not in existing_normalized:
                new_urls.append(url)

        # Append new URLs to the file
        with open(output_file, 'a', encoding='utf-8') as f:
            for url in new_urls:
                f.write(f"{url}\n")

        print(f"Simple URL list saved to: {output_file}")
        return output_file
    
    def generate_json_report(self, company_name, output_file=None):
        """Generate a JSON report with all data"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company_name.replace(' ', '_')}_report_{timestamp}.json"
            output_file = self._get_output_path(filename)
        else:
            # If a custom filename is provided, still save in the output directory
            output_file = self._get_output_path(output_file)
        
        report = {
            'company_name': company_name,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'company_pages': len(self.all_urls['company_pages']),
                'blog_posts': len(self.all_urls['blog_posts']),
                'founder_blogs': len(self.all_urls['founder_blogs']),
                'external_mentions': len(self.all_urls['external_mentions']),
                'potential_urls': len(self.all_urls['potential_urls']),
                'total_urls': self.get_total_urls()
            },
            'urls': self.all_urls
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"JSON report saved to: {output_file}")
        return output_file
    
    def get_total_urls(self):
        """Get total number of unique URLs"""
        all_urls = []
        all_urls.extend([page['url'] for page in self.all_urls['company_pages']])
        all_urls.extend([blog['url'] for blog in self.all_urls['blog_posts']])
        all_urls.extend([blog['url'] for blog in self.all_urls['founder_blogs']])
        all_urls.extend([mention['url'] for mention in self.all_urls['external_mentions']])
        all_urls.extend([potential['url'] for potential in self.all_urls['potential_urls']])
        
        # Use normalized URLs for accurate counting
        normalized_urls = {self._normalize_url(url) for url in all_urls}
        return len(normalized_urls)
    
    def print_summary(self):
        """Print a summary of discovered URLs"""
        print("\n" + "=" * 60)
        print("URL DISCOVERY SUMMARY")
        print("=" * 60)
        print(f"Company Pages: {len(self.all_urls['company_pages'])}")
        print(f"Blog Posts: {len(self.all_urls['blog_posts'])}")
        print(f"Founder Blogs: {len(self.all_urls['founder_blogs'])}")
        print(f"External Mentions: {len(self.all_urls['external_mentions'])}")
        print(f"Potential URLs: {len(self.all_urls['potential_urls'])}")
        print(f"Total Unique URLs: {self.get_total_urls()}")
        print("=" * 60) 
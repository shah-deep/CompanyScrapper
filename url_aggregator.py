import json
from datetime import datetime
from urllib.parse import urlparse

class URLAggregator:
    def __init__(self):
        self.all_urls = {
            'company_pages': [],
            'blog_posts': [],
            'founder_blogs': [],
            'external_mentions': []
        }
        self.company_url = None
    
    def set_company_url(self, url):
        """Set the company homepage URL for filename generation"""
        self.company_url = url
    
    def add_company_pages(self, pages):
        """Add company website pages"""
        self.all_urls['company_pages'].extend(pages)
    
    def add_blog_posts(self, blogs):
        """Add blog posts from company website"""
        self.all_urls['blog_posts'].extend(blogs)
    
    def add_founder_blogs(self, founder_blogs):
        """Add blogs written by founders"""
        self.all_urls['founder_blogs'].extend(founder_blogs)
    
    def add_external_mentions(self, mentions):
        """Add external mentions of the company"""
        self.all_urls['external_mentions'].extend(mentions)
    
    def generate_url_list(self, company_name, output_file=None):
        """Generate a comprehensive URL list file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{company_name.replace(' ', '_')}_urls_{timestamp}.txt"
        
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
            
            # Summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Company Pages: {len(self.all_urls['company_pages'])}\n")
            f.write(f"Total Blog Posts: {len(self.all_urls['blog_posts'])}\n")
            f.write(f"Total Founder Blogs: {len(self.all_urls['founder_blogs'])}\n")
            f.write(f"Total External Mentions: {len(self.all_urls['external_mentions'])}\n")
            f.write(f"GRAND TOTAL: {self.get_total_urls()}\n")
        
        print(f"URL list saved to: {output_file}")
        return output_file
    
    def generate_simple_url_list(self, company_name, output_file=None):
        """Generate a simple list of just URLs"""
        if output_file is None:
            # Use company homepage URL without http/https as filename
            from urllib.parse import urlparse
            try:
                if self.company_url:
                    parsed_url = urlparse(self.company_url)
                    domain = parsed_url.netloc
                    output_file = f"{domain}.txt"
                else:
                    # Fallback to company name if no URL set
                    output_file = f"{company_name.replace(' ', '_')}.txt"
            except:
                # Fallback to company name if parsing fails
                output_file = f"{company_name.replace(' ', '_')}.txt"
        
        print(f"Generating simple URL list: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # All URLs in one list
            all_urls = []
            all_urls.extend([page['url'] for page in self.all_urls['company_pages']])
            all_urls.extend([blog['url'] for blog in self.all_urls['blog_posts']])
            all_urls.extend([blog['url'] for blog in self.all_urls['founder_blogs']])
            all_urls.extend([mention['url'] for mention in self.all_urls['external_mentions']])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in all_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            for url in unique_urls:
                f.write(f"{url}\n")
        
        print(f"Simple URL list saved to: {output_file}")
        return output_file
    
    def generate_json_report(self, company_name, output_file=None):
        """Generate a JSON report with all data"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{company_name.replace(' ', '_')}_report_{timestamp}.json"
        
        report = {
            'company_name': company_name,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'company_pages': len(self.all_urls['company_pages']),
                'blog_posts': len(self.all_urls['blog_posts']),
                'founder_blogs': len(self.all_urls['founder_blogs']),
                'external_mentions': len(self.all_urls['external_mentions']),
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
        
        return len(set(all_urls))
    
    def print_summary(self):
        """Print a summary of discovered URLs"""
        print("\n" + "=" * 60)
        print("URL DISCOVERY SUMMARY")
        print("=" * 60)
        print(f"Company Pages: {len(self.all_urls['company_pages'])}")
        print(f"Blog Posts: {len(self.all_urls['blog_posts'])}")
        print(f"Founder Blogs: {len(self.all_urls['founder_blogs'])}")
        print(f"External Mentions: {len(self.all_urls['external_mentions'])}")
        print(f"Total Unique URLs: {self.get_total_urls()}")
        print("=" * 60) 
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
from datetime import datetime, timedelta
from fake_useragent import UserAgent
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import sys
from typing import List, Dict, Optional, Tuple
import concurrent.futures
from threading import Lock

# Import configuration
try:
    from config import *
except ImportError:
    print("Warning: config.py not found. Using default settings.")
    SCRAPING_CONFIG = {'min_articles': 50, 'max_articles': 150}
    SOURCES = {}
    RELEVANT_KEYWORDS = ['technology', 'finance', 'business']
    OUTPUT_CONFIG = {'csv_filename': 'ft_technology_articles.csv', 'json_filename': 'ft_technology_articles.json'}

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG.get('level', 'INFO')),
    format=LOGGING_CONFIG.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
    handlers=[
        logging.FileHandler(LOGGING_CONFIG.get('file', 'ft_scraper.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FinancialTimesScraper:
    def __init__(self, min_articles=50, max_articles=150):
        self.min_articles = min_articles
        self.max_articles = max_articles
        self.articles = []
        self.articles_lock = Lock()
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Initialize session with headers
        self.update_session_headers()
        
        # Initialize Selenium driver
        self.driver = None
        self.setup_selenium()
    
    def update_session_headers(self):
        """Update session headers with random user agent"""
        user_agent = random.choice(USER_AGENTS) if 'USER_AGENTS' in globals() else self.ua.random
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
    
    def setup_selenium(self):
        """Set up Selenium WebDriver for dynamic content"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f"--user-agent={self.ua.random}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.driver = None
    
    def get_page_with_selenium(self, url, wait_time=10):
        """Get page content using Selenium for dynamic content"""
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None
    
    def get_page_content(self, url, use_selenium=False, max_retries=3):
        """Get page content with retry logic and fallback options"""
        for attempt in range(max_retries):
            try:
                if use_selenium:
                    content = self.get_page_with_selenium(url)
                    if content:
                        return content
                
                # Prepare request
                self.update_session_headers()
                
                response = self.session.get(
                    url, 
                    timeout=SCRAPING_CONFIG.get('request_timeout', 30)
                )
                response.raise_for_status()
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
                    continue
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                return None
        
        return None
    
    def extract_ft_articles(self, url, source_name="Financial Times", category="Technology"):
        """Extract articles from Financial Times pages"""
        logger.info(f"Scraping {source_name}: {url}")
        content = self.get_page_content(url, use_selenium=True)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        # FT-specific selectors
        selectors = [
            'article[data-trackable="article"]',
            '.js-teaser',
            '.o-teaser',
            '.js-article',
            'a[href*="/content/"]',
            '.o-teaser__heading a',
            '.js-teaser__heading a',
            '.o-teaser__title a',
            '.js-teaser__title a',
            '.o-teaser__content a',
            '.js-teaser__content a',
            '.o-teaser__standfirst a',
            '.js-teaser__standfirst a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                try:
                    # Extract link
                    link_elem = element.find('a') if element.name != 'a' else element
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    link = link_elem.get('href')
                    if not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    # Skip if not an FT article
                    if not link.startswith('https://www.ft.com/'):
                        continue
                    
                    # Extract title
                    title = ""
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        title = element.get_text(strip=True)
                    else:
                        # Try to get title from link text
                        title = link_elem.get_text(strip=True)
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Extract summary
                    summary = ""
                    summary_elem = element.find(['p', '.o-teaser__standfirst', '.js-teaser__standfirst'])
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)
                    
                    # Extract date
                    date = ""
                    date_elem = element.find(['time', '.o-teaser__timestamp', '.js-teaser__timestamp'])
                    if date_elem:
                        date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    
                    article = {
                        'source': source_name,
                        'title': title,
                        'url': link,
                        'summary': summary,
                        'date': date,
                        'category': category,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error extracting article from {source_name}: {e}")
                    continue
        
        return articles
    
    def scrape_source_parallel(self, source_config):
        """Scrape a single source (for parallel processing)"""
        try:
            if 'url' in source_config:
                articles = self.extract_ft_articles(
                    source_config['url'],
                    source_config['name'],
                    source_config['category']
                )
            else:
                articles = []
            
            logger.info(f"Found {len(articles)} articles from {source_config['name']}")
            return articles
        except Exception as e:
            logger.error(f"Error scraping {source_config['name']}: {e}")
            return []
    
    def scrape_all_sources(self):
        """Scrape all sources and collect articles"""
        all_articles = []
        
        # Scrape main FT technology source
        main_source = SOURCES.get('ft_technology', {})
        if main_source:
            articles = self.extract_ft_articles(
                main_source['url'],
                main_source['name'],
                main_source['category']
            )
            all_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles from main source")
        
        # Scrape additional sources
        sources_to_scrape = ADDITIONAL_SOURCES if 'ADDITIONAL_SOURCES' in globals() else []
        
        # Use parallel processing for faster scraping
        max_workers = min(3, len(sources_to_scrape))  # Limit concurrent requests
        
        if sources_to_scrape:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_source = {
                    executor.submit(self.scrape_source_parallel, source_config): source_config 
                    for source_config in sources_to_scrape
                }
                
                for future in concurrent.futures.as_completed(future_to_source):
                    source_config = future_to_source[future]
                    try:
                        articles = future.result()
                        all_articles.extend(articles)
                        
                        # Rate limiting between sources
                        time.sleep(random.uniform(
                            SCRAPING_CONFIG.get('rate_limit_min', 2),
                            SCRAPING_CONFIG.get('rate_limit_max', 5)
                        ))
                        
                    except Exception as e:
                        logger.error(f"Error processing {source_config['name']}: {e}")
        
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        logger.info(f"Total unique articles found: {len(unique_articles)}")
        
        # Filter and limit articles
        filtered_articles = self.filter_articles(unique_articles)
        
        # Ensure we have enough articles
        if len(filtered_articles) < self.min_articles:
            logger.warning(f"Only found {len(filtered_articles)} articles, less than minimum {self.min_articles}")
        
        # Limit to maximum
        if len(filtered_articles) > self.max_articles:
            filtered_articles = filtered_articles[:self.max_articles]
            logger.info(f"Limited to {self.max_articles} articles")
        
        self.articles = filtered_articles
        return filtered_articles
    
    def filter_articles(self, articles):
        """Filter articles based on relevance and quality"""
        filtered = []
        
        for article in articles:
            title_lower = article['title'].lower()
            summary_lower = article['summary'].lower()
            
            # Check if article contains relevant keywords
            is_relevant = any(keyword in title_lower or keyword in summary_lower 
                            for keyword in RELEVANT_KEYWORDS)
            
            # Additional quality checks
            has_minimum_length = len(article['title']) >= 10
            has_valid_url = article['url'].startswith('https://www.ft.com/')
            
            if is_relevant and has_minimum_length and has_valid_url:
                filtered.append(article)
        
        logger.info(f"Filtered {len(articles)} articles down to {len(filtered)} relevant articles")
        return filtered
    
    def save_to_csv(self, filename=None):
        """Save articles to CSV file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        filename = filename or OUTPUT_CONFIG.get('csv_filename', 'ft_technology_articles.csv')
        df = pd.DataFrame(self.articles)
        df.to_csv(filename, index=False, encoding=OUTPUT_CONFIG.get('encoding', 'utf-8'))
        logger.info(f"Saved {len(self.articles)} articles to {filename}")
    
    def save_to_json(self, filename=None):
        """Save articles to JSON file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        filename = filename or OUTPUT_CONFIG.get('json_filename', 'ft_technology_articles.json')
        with open(filename, 'w', encoding=OUTPUT_CONFIG.get('encoding', 'utf-8')) as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.articles)} articles to {filename}")
    
    def save_to_excel(self, filename=None):
        """Save articles to Excel file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        filename = filename or OUTPUT_CONFIG.get('excel_filename', 'ft_technology_articles.xlsx')
        df = pd.DataFrame(self.articles)
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"Saved {len(self.articles)} articles to {filename}")
    
    def print_summary(self):
        """Print summary of scraped articles"""
        if not self.articles:
            print("No articles found")
            return
        
        print(f"\n=== SCRAPING SUMMARY ===")
        print(f"Total articles found: {len(self.articles)}")
        
        # Group by source
        source_counts = {}
        category_counts = {}
        for article in self.articles:
            source = article['source']
            category = article['category']
            source_counts[source] = source_counts.get(source, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\nArticles by source:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
        
        print("\nArticles by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        print(f"\nArticles saved to:")
        print(f"  - {OUTPUT_CONFIG.get('csv_filename', 'ft_technology_articles.csv')}")
        print(f"  - {OUTPUT_CONFIG.get('json_filename', 'ft_technology_articles.json')}")
        print(f"  - {OUTPUT_CONFIG.get('excel_filename', 'ft_technology_articles.xlsx')}")
        
        # Show sample articles
        print(f"\nSample articles:")
        for i, article in enumerate(self.articles[:5]):
            print(f"  {i+1}. {article['title']}")
            print(f"     Source: {article['source']}")
            print(f"     URL: {article['url']}")
            print()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")

def main():
    """Main function to run the FT scraper"""
    print("Financial Times Technology Scraper")
    print("=" * 50)
    
    # Initialize scraper
    scraper = FinancialTimesScraper(
        min_articles=SCRAPING_CONFIG.get('min_articles', 50),
        max_articles=SCRAPING_CONFIG.get('max_articles', 150)
    )
    
    try:
        # Scrape all sources
        articles = scraper.scrape_all_sources()
        
        if articles:
            # Save in multiple formats
            scraper.save_to_csv()
            scraper.save_to_json()
            scraper.save_to_excel()
            scraper.print_summary()
        else:
            print("No articles found")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"An error occurred: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()

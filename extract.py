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
import newspaper3k
import feedparser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialNewsScraper:
    def __init__(self, min_articles=100, max_articles=150):
        self.min_articles = min_articles
        self.max_articles = max_articles
        self.articles = []
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Initialize Selenium driver for dynamic content
        self.driver = None
        self.setup_selenium()
        
    def setup_selenium(self):
        """Set up Selenium WebDriver for dynamic content"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"--user-agent={self.ua.random}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
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
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None
    
    def get_page_content(self, url, use_selenium=False):
        """Get page content with fallback options"""
        try:
            if use_selenium:
                content = self.get_page_with_selenium(url)
                if content:
                    return content
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_ft_articles(self, url):
        """Extract articles from Financial Times"""
        logger.info(f"Scraping Financial Times: {url}")
        content = self.get_page_content(url, use_selenium=True)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        # FT article selectors
        article_selectors = [
            'article[data-trackable="article"]',
            '.js-teaser',
            '.o-teaser',
            '.js-article',
            'a[href*="/content/"]',
            '.o-teaser__heading a',
            '.js-teaser__heading a'
        ]
        
        for selector in article_selectors:
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
                    
                    # Extract title
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Extract summary/description
                    summary_elem = element.find(['p', '.o-teaser__standfirst', '.js-teaser__standfirst'])
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    # Extract date
                    date_elem = element.find(['time', '.o-teaser__timestamp', '.js-teaser__timestamp'])
                    date = date_elem.get('datetime') or date_elem.get_text(strip=True) if date_elem else ""
                    
                    articles.append({
                        'source': 'Financial Times',
                        'title': title,
                        'url': link,
                        'summary': summary,
                        'date': date,
                        'category': 'Technology'
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting FT article: {e}")
                    continue
        
        return articles
    
    def extract_moodys_articles(self, url):
        """Extract articles from Moody's"""
        logger.info(f"Scraping Moody's: {url}")
        content = self.get_page_content(url, use_selenium=True)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        # Moody's article selectors
        article_selectors = [
            '.research-item',
            '.article-item',
            '.news-item',
            'a[href*="/researchandratings/"]',
            '.content-item'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                try:
                    link_elem = element.find('a') if element.name != 'a' else element
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    link = link_elem.get('href')
                    if not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 10:
                        continue
                    
                    summary_elem = element.find('p')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    articles.append({
                        'source': 'Moody\'s',
                        'title': title,
                        'url': link,
                        'summary': summary,
                        'date': '',
                        'category': 'Credit Ratings'
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting Moody's article: {e}")
                    continue
        
        return articles
    
    def extract_risknet_articles(self, url):
        """Extract articles from Risk.net"""
        logger.info(f"Scraping Risk.net: {url}")
        content = self.get_page_content(url, use_selenium=True)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        # Risk.net article selectors
        article_selectors = [
            '.article-item',
            '.news-item',
            '.content-item',
            'a[href*="/article/"]',
            '.teaser'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                try:
                    link_elem = element.find('a') if element.name != 'a' else element
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    link = link_elem.get('href')
                    if not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 10:
                        continue
                    
                    summary_elem = element.find('p')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    articles.append({
                        'source': 'Risk.net',
                        'title': title,
                        'url': link,
                        'summary': summary,
                        'date': '',
                        'category': 'Risk Management'
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting Risk.net article: {e}")
                    continue
        
        return articles
    
    def extract_spglobal_articles(self, url):
        """Extract articles from S&P Global"""
        logger.info(f"Scraping S&P Global: {url}")
        content = self.get_page_content(url, use_selenium=True)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        # S&P Global article selectors
        article_selectors = [
            '.news-item',
            '.article-item',
            '.content-item',
            'a[href*="/news/"]',
            '.teaser'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                try:
                    link_elem = element.find('a') if element.name != 'a' else element
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    link = link_elem.get('href')
                    if not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 10:
                        continue
                    
                    summary_elem = element.find('p')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    articles.append({
                        'source': 'S&P Global',
                        'title': title,
                        'url': link,
                        'summary': summary,
                        'date': '',
                        'category': 'Market Data'
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting S&P Global article: {e}")
                    continue
        
        return articles
    
    def scrape_rss_feeds(self):
        """Scrape RSS feeds for additional articles"""
        rss_feeds = [
            'https://www.ft.com/rss/home',
            'https://www.ft.com/rss/technology',
            'https://www.ft.com/rss/companies',
            'https://www.ft.com/rss/markets'
        ]
        
        articles = []
        for feed_url in rss_feeds:
            try:
                logger.info(f"Scraping RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    articles.append({
                        'source': 'Financial Times (RSS)',
                        'title': entry.title,
                        'url': entry.link,
                        'summary': entry.summary if hasattr(entry, 'summary') else '',
                        'date': entry.published if hasattr(entry, 'published') else '',
                        'category': 'Technology'
                    })
                    
            except Exception as e:
                logger.error(f"Error scraping RSS feed {feed_url}: {e}")
                continue
        
        return articles
    
    def scrape_all_sources(self):
        """Scrape all sources and collect articles"""
        sources = [
            ('https://www.ft.com/technology', self.extract_ft_articles),
            ('https://www.moodys.com/researchandratings/region/004001/005000010', self.extract_moodys_articles),
            ('https://www.risk.net/', self.extract_risknet_articles),
            ('https://www.spglobal.com/spdji/en/indices/equity/sp-500-information-technology-sector/#news-research', self.extract_spglobal_articles)
        ]
        
        all_articles = []
        
        # Scrape main sources
        for url, extractor_func in sources:
            try:
                articles = extractor_func(url)
                all_articles.extend(articles)
                logger.info(f"Found {len(articles)} articles from {url}")
                
                # Rate limiting
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        # Scrape RSS feeds
        rss_articles = self.scrape_rss_feeds()
        all_articles.extend(rss_articles)
        logger.info(f"Found {len(rss_articles)} articles from RSS feeds")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
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
        
        # Keywords for relevance
        relevant_keywords = [
            'technology', 'tech', 'ai', 'artificial intelligence', 'machine learning',
            'fintech', 'financial technology', 'blockchain', 'cryptocurrency',
            'cybersecurity', 'digital', 'software', 'hardware', 'semiconductor',
            'cloud', 'data', 'analytics', 'automation', 'innovation',
            'startup', 'venture capital', 'investment', 'market', 'trading',
            'risk', 'compliance', 'regulation', 'banking', 'finance'
        ]
        
        for article in articles:
            title_lower = article['title'].lower()
            summary_lower = article['summary'].lower()
            
            # Check if article contains relevant keywords
            is_relevant = any(keyword in title_lower or keyword in summary_lower 
                            for keyword in relevant_keywords)
            
            # Additional quality checks
            has_minimum_length = len(article['title']) >= 10
            has_valid_url = article['url'].startswith('http')
            
            if is_relevant and has_minimum_length and has_valid_url:
                filtered.append(article)
        
        return filtered
    
    def save_to_csv(self, filename='financial_articles.csv'):
        """Save articles to CSV file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        df = pd.DataFrame(self.articles)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(self.articles)} articles to {filename}")
    
    def save_to_json(self, filename='financial_articles.json'):
        """Save articles to JSON file"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)
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
        for article in self.articles:
            source = article['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print("\nArticles by source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
        
        print(f"\nArticles saved to: financial_articles.csv and financial_articles.json")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")

def main():
    """Main function to run the scraper"""
    scraper = FinancialNewsScraper(min_articles=100, max_articles=150)
    
    try:
        print("Starting financial news scraper...")
        articles = scraper.scrape_all_sources()
        
        if articles:
            scraper.save_to_csv()
            scraper.save_to_json()
            scraper.print_summary()
        else:
            print("No articles found")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
    
# Configuration file for Financial Times Technology Scraper

# Scraping settings
SCRAPING_CONFIG = {
    'min_articles': 50,
    'max_articles': 150,
    'request_timeout': 30,
    'rate_limit_min': 2,
    'rate_limit_max': 5,
    'selenium_wait_time': 10,
    'max_retries': 3
}

# Financial Times sources configuration
SOURCES = {
    'ft_technology': {
        'url': 'https://www.ft.com/technology',
        'name': 'Financial Times Technology',
        'category': 'Technology',
        'selectors': [
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
            '.js-teaser__content a'
        ],
        'title_selectors': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        'summary_selectors': ['p', '.o-teaser__standfirst', '.js-teaser__standfirst'],
        'date_selectors': ['time', '.o-teaser__timestamp', '.js-teaser__timestamp']
    }
}

# Additional FT sections for more articles
ADDITIONAL_SOURCES = [
    {
        'url': 'https://www.ft.com/artificial-intelligence',
        'name': 'Financial Times AI',
        'category': 'Artificial Intelligence'
    },
    {
        'url': 'https://www.ft.com/companies/technology',
        'name': 'Financial Times Tech Companies',
        'category': 'Technology Companies'
    },
    {
        'url': 'https://www.ft.com/tech-sector',
        'name': 'Financial Times Tech Sector',
        'category': 'Tech Sector'
    }
]

# Keywords for relevance filtering
RELEVANT_KEYWORDS = [
    # Technology
    'technology', 'tech', 'ai', 'artificial intelligence', 'machine learning',
    'deep learning', 'neural network', 'algorithm', 'automation', 'digital',
    'software', 'hardware', 'semiconductor', 'chip', 'processor',
    'cloud', 'cloud computing', 'saas', 'platform', 'api',
    'cybersecurity', 'security', 'privacy', 'data protection',
    'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'defi',
    'fintech', 'financial technology', 'digital banking', 'mobile payment',
    
    # Business & Finance
    'startup', 'venture capital', 'vc', 'investment', 'funding', 'ipo',
    'merger', 'acquisition', 'm&a', 'deal', 'partnership',
    'market', 'trading', 'stock', 'equity', 'bond', 'derivative',
    'risk', 'compliance', 'regulation', 'regulatory', 'compliance',
    'banking', 'finance', 'financial', 'bank', 'lending', 'credit',
    
    # Industry specific
    'quantum computing', 'quantum', 'crypto', 'web3', 'metaverse',
    'vr', 'virtual reality', 'ar', 'augmented reality', 'iot',
    'internet of things', '5g', '6g', 'telecom', 'telecommunications',
    'biotech', 'biotechnology', 'healthtech', 'medtech',
    'clean energy', 'renewable', 'solar', 'wind', 'battery',
    'electric vehicle', 'ev', 'autonomous', 'self-driving',
    
    # General business terms
    'revenue', 'profit', 'earnings', 'quarterly', 'annual',
    'growth', 'expansion', 'global', 'international', 'emerging market',
    'innovation', 'research', 'development', 'r&d', 'patent',
    'competition', 'competitive', 'market share', 'customer',
    'user', 'consumer', 'enterprise', 'b2b', 'b2c'
]

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
]

# Output settings
OUTPUT_CONFIG = {
    'csv_filename': 'ft_technology_articles.csv',
    'json_filename': 'ft_technology_articles.json',
    'excel_filename': 'ft_technology_articles.xlsx',
    'encoding': 'utf-8'
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': 'ft_scraper.log'
}

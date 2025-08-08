#!/usr/bin/env python3
"""
Simple script to run the Financial News Scraper
"""

import argparse
import sys
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Financial News Scraper')
    parser.add_argument('--min-articles', type=int, default=100, 
                       help='Minimum number of articles to collect (default: 100)')
    parser.add_argument('--max-articles', type=int, default=150, 
                       help='Maximum number of articles to collect (default: 150)')
    parser.add_argument('--use-proxies', action='store_true', 
                       help='Use proxy servers for scraping')
    parser.add_argument('--output-dir', type=str, default='.', 
                       help='Output directory for saved files (default: current directory)')
    parser.add_argument('--scraper', choices=['basic', 'enhanced'], default='enhanced',
                       help='Choose scraper version (default: enhanced)')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Change to output directory
    os.chdir(args.output_dir)
    
    print(f"Financial News Scraper")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output directory: {os.path.abspath(args.output_dir)}")
    print(f"Target articles: {args.min_articles}-{args.max_articles}")
    print(f"Using proxies: {args.use_proxies}")
    print(f"Scraper version: {args.scraper}")
    print("-" * 50)
    
    try:
        if args.scraper == 'enhanced':
            from enhanced_scraper import EnhancedFinancialNewsScraper
            scraper = EnhancedFinancialNewsScraper(
                min_articles=args.min_articles,
                max_articles=args.max_articles,
                use_proxies=args.use_proxies
            )
        else:
            from extract import FinancialNewsScraper
            scraper = FinancialNewsScraper(
                min_articles=args.min_articles,
                max_articles=args.max_articles
            )
        
        # Run the scraper
        articles = scraper.scrape_all_sources()
        
        if articles:
            # Save results
            scraper.save_to_csv()
            scraper.save_to_json()
            if hasattr(scraper, 'save_to_excel'):
                scraper.save_to_excel()
            
            # Print summary
            scraper.print_summary()
            
            print(f"\nScraping completed successfully!")
            print(f"Total articles collected: {len(articles)}")
        else:
            print("No articles were collected.")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.cleanup()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Barnivore Data Scraper
Downloads company and product data from Barnivore API and stores in SQLite database
"""

import requests
import sqlite3
import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BarnivoreAPI:
    """Handle API requests to Barnivore"""
    
    BASE_URL = "https://www.barnivore.com"
    ENDPOINTS = {
        'beer': f"{BASE_URL}/beer.json",
        'wine': f"{BASE_URL}/wine.json",
        'liquor': f"{BASE_URL}/liquor.json"
    }
    COMPANY_ENDPOINT = f"{BASE_URL}/company"
    
    def __init__(self, delay: float = 1.0):
        """Initialize with optional delay between requests"""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_companies_list(self) -> List[Dict]:
        """Fetch the main list of companies from all endpoints"""
        logger.info("Fetching companies list from all API endpoints...")
        all_companies = []
        
        for endpoint_name, endpoint_url in self.ENDPOINTS.items():
            try:
                logger.info(f"Fetching from {endpoint_name} endpoint...")
                response = self.session.get(endpoint_url, timeout=30)
                response.raise_for_status()
                data = response.json()
                companies = [item['company'] for item in data if 'company' in item]
                logger.info(f"Retrieved {len(companies)} companies from {endpoint_name}")
                all_companies.extend(companies)
            except requests.RequestException as e:
                logger.error(f"Failed to fetch companies from {endpoint_name}: {e}")
                continue
        
        # Remove duplicates based on company ID
        seen_ids = set()
        unique_companies = []
        for company in all_companies:
            if company.get('id') not in seen_ids:
                seen_ids.add(company.get('id'))
                unique_companies.append(company)
        
        logger.info(f"Total unique companies retrieved: {len(unique_companies)}")
        return unique_companies
    
    def get_company_details(self, company_id: int) -> Optional[Dict]:
        """Fetch detailed company information including products"""
        url = f"{self.COMPANY_ENDPOINT}/{company_id}.json"
        try:
            time.sleep(self.delay)  # Rate limiting
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('company')
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch company {company_id}: {e}")
            return None

class BarnivoreDB:
    """Handle SQLite database operations"""
    
    def __init__(self, db_path: str = "barnivore.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        logger.info(f"Initializing database: {self.db_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create company table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company (
                    id INTEGER NOT NULL PRIMARY KEY,
                    address VARCHAR,
                    checkedby VARCHAR,
                    city VARCHAR,
                    companyemail VARCHAR,
                    companyname VARCHAR,
                    country VARCHAR,
                    createdon VARCHAR,
                    doubledby VARCHAR,
                    editor VARCHAR,
                    email VARCHAR,
                    fax VARCHAR,
                    notes VARCHAR,
                    phone VARCHAR,
                    postal VARCHAR,
                    redyellowgreen VARCHAR,
                    region VARCHAR,
                    state VARCHAR,
                    status VARCHAR,
                    updatedon VARCHAR,
                    url VARCHAR
                )
            """)
            
            # Create product table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product (
                    id BIGINT NOT NULL PRIMARY KEY,
                    boozetype VARCHAR,
                    companyid INTEGER,
                    productname VARCHAR,
                    redyellowgreen VARCHAR,
                    FOREIGN KEY (companyid) REFERENCES company (id)
                )
            """)
            
            # Create stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id BIGINT NOT NULL PRIMARY KEY,
                    addressstring VARCHAR,
                    datestring VARCHAR
                )
            """)
            
            conn.commit()
    
    def insert_company(self, company_data: Dict):
        """Insert company data into database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Map API fields to database columns
            company_record = {
                'id': company_data.get('id'),
                'address': company_data.get('address'),
                'checkedby': company_data.get('checked_by'),
                'city': company_data.get('city'),
                'companyemail': company_data.get('company_email'),
                'companyname': company_data.get('company_name'),
                'country': company_data.get('country'),
                'createdon': company_data.get('created_on'),
                'doubledby': company_data.get('doubled_by'),
                'editor': company_data.get('editor'),
                'email': company_data.get('email'),
                'fax': company_data.get('fax'),
                'notes': company_data.get('notes'),
                'phone': company_data.get('phone'),
                'postal': company_data.get('postal'),
                'redyellowgreen': company_data.get('red_yellow_green'),
                'region': company_data.get('region'),
                'state': company_data.get('state'),
                'status': company_data.get('status'),
                'updatedon': company_data.get('updated_on'),
                'url': company_data.get('url')
            }
            
            # Insert or replace company
            cursor.execute("""
                INSERT OR REPLACE INTO company (
                    id, address, checkedby, city, companyemail, companyname,
                    country, createdon, doubledby, editor, email, fax, notes,
                    phone, postal, redyellowgreen, region, state, status,
                    updatedon, url
                ) VALUES (
                    :id, :address, :checkedby, :city, :companyemail, :companyname,
                    :country, :createdon, :doubledby, :editor, :email, :fax, :notes,
                    :phone, :postal, :redyellowgreen, :region, :state, :status,
                    :updatedon, :url
                )
            """, company_record)
            
            conn.commit()
    
    def insert_products(self, company_id: int, products: List[Dict]):
        """Insert products for a company"""
        if not products:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for product in products:
                product_record = {
                    'id': product.get('id'),
                    'boozetype': product.get('booze_type'),
                    'companyid': company_id,
                    'productname': product.get('product_name'),
                    'redyellowgreen': product.get('red_yellow_green')
                }
                
                cursor.execute("""
                    INSERT OR REPLACE INTO product (
                        id, boozetype, companyid, productname, redyellowgreen
                    ) VALUES (
                        :id, :boozetype, :companyid, :productname, :redyellowgreen
                    )
                """, product_record)
            
            conn.commit()
    
    def insert_stats(self, address_string: str = None):
        """Insert statistics record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats_record = {
                'id': int(time.time()),  # Use timestamp as ID
                'addressstring': address_string or f"Data scraped at {datetime.now().isoformat()}",
                'datestring': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            cursor.execute("""
                INSERT INTO stats (id, addressstring, datestring)
                VALUES (:id, :addressstring, :datestring)
            """, stats_record)
            
            conn.commit()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM company")
            company_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM product")
            product_count = cursor.fetchone()[0]
            
            return {
                'companies': company_count,
                'products': product_count
            }

class BarnivoreScraper:
    """Main scraper class"""
    
    def __init__(self, db_path: str = "barnivore.db", delay: float = 1.0):
        self.api = BarnivoreAPI(delay=delay)
        self.db = BarnivoreDB(db_path)
    
    def scrape_all(self):
        """Scrape all company and product data"""
        logger.info("Starting Barnivore data scrape...")
        
        try:
            # Get list of companies
            companies = self.api.get_companies_list()
            
            total_companies = len(companies)
            processed = 0
            failed = 0
            
            # Process each company
            for i, company in enumerate(companies, 1):
                company_id = company.get('id')
                company_name = company.get('company_name', 'Unknown')
                
                logger.info(f"Processing {i}/{total_companies}: {company_name} (ID: {company_id})")
                
                try:
                    # Insert basic company info
                    self.db.insert_company(company)
                    
                    # Get detailed company info with products
                    detailed_company = self.api.get_company_details(company_id)
                    
                    if detailed_company:
                        # Update with detailed info
                        self.db.insert_company(detailed_company)
                        
                        # Insert products
                        products = detailed_company.get('products', [])
                        if products:
                            self.db.insert_products(company_id, products)
                            logger.info(f"  Added {len(products)} products")
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process company {company_id}: {e}")
                    failed += 1
                
                # Progress update every 50 companies
                if i % 50 == 0:
                    stats = self.db.get_stats()
                    logger.info(f"Progress: {i}/{total_companies} companies, "
                              f"{stats['companies']} in DB, {stats['products']} products")
            
            # Insert final stats
            self.db.insert_stats(f"Scraped {processed} companies, {failed} failed")
            
            # Final statistics
            final_stats = self.db.get_stats()
            logger.info(f"Scraping completed!")
            logger.info(f"Successfully processed: {processed}")
            logger.info(f"Failed: {failed}")
            logger.info(f"Total companies in DB: {final_stats['companies']}")
            logger.info(f"Total products in DB: {final_stats['products']}")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Barnivore data to SQLite database')
    parser.add_argument('--db', default=f'barnivore_{datetime.now().strftime("%Y%m%d")}.db', help='Database file path')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Delay between API requests (seconds)')
    parser.add_argument('--stats-only', action='store_true', 
                       help='Show database stats only')
    
    args = parser.parse_args()
    
    if args.stats_only:
        db = BarnivoreDB(args.db)
        stats = db.get_stats()
        print(f"Database: {args.db}")
        print(f"Companies: {stats['companies']}")
        print(f"Products: {stats['products']}")
        return
    
    # Run the scraper
    scraper = BarnivoreScraper(db_path=args.db, delay=args.delay)
    scraper.scrape_all()

if __name__ == "__main__":
    main()

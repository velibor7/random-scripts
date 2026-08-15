#!/usr/bin/env python3
"""
Improved Leonidio Climbing Routes Scraper with better route parsing

This script scrapes all crags and routes from climbinleonidio.com
and saves the data to CSV files with improved parsing.

Author: GitHub Copilot
Date: January 5, 2026
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import urllib.parse
from typing import List, Dict, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeonidioScraperV2:
    def __init__(self):
        self.base_url = "https://climbinleonidio.com"
        self.crags_url = "https://climbinleonidio.com/crags/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.crags_data = []
        self.routes_data = []

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_crag_info(self, crag_link) -> Dict:
        """Extract crag information from the main crags page"""
        crag_text = crag_link.get_text(strip=True)
        
        # Extract crag number
        number_match = re.match(r'^(\d+)', crag_text)
        crag_number = number_match.group(1) if number_match else ""
        
        # Extract crag name - improved pattern matching
        crag_name = ""
        
        # Try multiple patterns for crag name extraction
        patterns = [
            r'^\d+\s*([^A-Z]*?)\s+At\s+\d+m',  # Pattern: "01 Nifada At 800m..."
            r'^\d+\s*([^A-Z]*?)\s+A\s+[a-z]',  # Pattern: "01 Name A description..."
            r'^\d+\s*([^.]{1,50}?)\s+[A-Z][a-z]',  # Pattern: "01 Name Description..."
            r'^\d+\s*([^R]{1,50}?)Routes:',  # Pattern: "01 Name Routes:"
        ]
        
        for pattern in patterns:
            name_match = re.search(pattern, crag_text)
            if name_match:
                crag_name = name_match.group(1).strip()
                break
        
        if not crag_name:
            # Fallback: take first 30 chars after number
            crag_name = re.sub(r'^\d+\s*', '', crag_text)[:30].strip()
        
        # Extract route count
        routes_match = re.search(r'Routes:\s*(\d+)', crag_text)
        route_count = int(routes_match.group(1)) if routes_match else 0
        
        # Extract best period
        period_match = re.search(r'Best period:\s*([^B]+?)(?:\s+Busy|$)', crag_text)
        best_period = period_match.group(1).strip() if period_match else ""
        
        # Extract busy level (number of dots)
        busy_match = re.search(r'Busy:\s*(•+)', crag_text)
        busy_level = len(busy_match.group(1)) if busy_match else 0
        
        # Get crag URL
        crag_href = crag_link.get('href', '')
        crag_url = urllib.parse.urljoin(self.base_url, crag_href) if crag_href else ""
        
        return {
            'crag_number': crag_number,
            'crag_name': crag_name,
            'description': crag_text,
            'route_count': route_count,
            'best_period': best_period,
            'busy_level': busy_level,
            'crag_url': crag_url
        }

    def extract_crag_details(self, crag_url: str, crag_info: Dict) -> Dict:
        """Extract detailed information from individual crag page"""
        soup = self.get_page(crag_url)
        if not soup:
            return crag_info
        
        # Extract additional details
        text_content = soup.get_text()
        
        # Extract exposure
        exposure_match = re.search(r'Exposure:\s*([^B]+?)(?:\s+Best|$)', text_content)
        exposure = exposure_match.group(1).strip() if exposure_match else ""
        
        # Extract shade information
        shade_match = re.search(r'Shade:\s*([^B]+?)(?:\s+Busy|$)', text_content)
        shade = shade_match.group(1).strip() if shade_match else ""
        
        # Extract elevation if mentioned
        elevation_match = re.search(r'(\d+)m?\s+elevation', text_content, re.IGNORECASE)
        elevation = elevation_match.group(1) if elevation_match else ""
        
        crag_info.update({
            'exposure': exposure,
            'shade': shade,
            'elevation_m': elevation
        })
        
        return crag_info

    def parse_route_text(self, route_text: str) -> Dict:
        """Parse route text to extract route information"""
        # Clean up the text
        route_text = route_text.strip()
        
        # Initialize return values
        route_number = ""
        route_name = ""
        grade = ""
        length = ""
        
        # Pattern 1: "01    Hase 6c 18m" (with spaces)
        match1 = re.match(r'^(\d+)\s+(.+?)\s+([0-9]+[a-c]?[+]?)\s+(\d+)m?$', route_text)
        if match1:
            route_number = match1.group(1)
            route_name = match1.group(2).strip()
            grade = match1.group(3)
            length = match1.group(4)
            return {
                'route_number': route_number,
                'route_name': route_name,
                'grade': grade,
                'length_m': length
            }
        
        # Pattern 2: "01Hase6c18m" (no spaces)
        match2 = re.match(r'^(\d+)([^0-9]+?)([0-9]+[a-c]?[+]?)(\d+)m?$', route_text)
        if match2:
            route_number = match2.group(1)
            route_name = match2.group(2).strip()
            grade = match2.group(3)
            length = match2.group(4)
            return {
                'route_number': route_number,
                'route_name': route_name,
                'grade': grade,
                'length_m': length
            }
        
        # Pattern 3: "Route Name 6c 18m" (no number)
        match3 = re.match(r'^(.+?)\s+([0-9]+[a-c]?[+]?)\s+(\d+)m?$', route_text)
        if match3:
            route_name = match3.group(1).strip()
            grade = match3.group(2)
            length = match3.group(3)
            return {
                'route_number': route_number,
                'route_name': route_name,
                'grade': grade,
                'length_m': length
            }
        
        # Pattern 4: Manual parsing for complex cases
        parts = route_text.split()
        if len(parts) >= 2:
            # Find the grade (pattern like 6a, 7b+, 8c)
            grade_idx = -1
            for i, part in enumerate(parts):
                if re.match(r'^[0-9]+[a-c]?[+]?$', part):
                    grade = part
                    grade_idx = i
                    
                    # Check if next part is length
                    if i + 1 < len(parts):
                        next_part = parts[i + 1].replace('m', '')
                        if re.match(r'^\d+$', next_part):
                            length = next_part
                    
                    # Everything before grade might be route info
                    if i > 0:
                        # Check if first part is number
                        if re.match(r'^\d+$', parts[0]):
                            route_number = parts[0]
                            if i > 1:
                                route_name = ' '.join(parts[1:i])
                        else:
                            route_name = ' '.join(parts[:i])
                    break
        
        # If we still don't have a route name, use the whole text minus extracted parts
        if not route_name:
            route_name = route_text
            for remove_part in [route_number, grade, length + 'm']:
                if remove_part:
                    route_name = route_name.replace(remove_part, '').strip()
        
        return {
            'route_number': route_number,
            'route_name': route_name,
            'grade': grade,
            'length_m': length
        }

    def extract_routes_from_crag(self, crag_url: str, crag_info: Dict) -> List[Dict]:
        """Extract all routes from a specific crag page"""
        soup = self.get_page(crag_url)
        if not soup:
            return []
        
        routes = []
        
        # Find all route links
        route_links = soup.find_all('a', href=re.compile(r'/route/'))
        
        for route_link in route_links:
            route_text = route_link.get_text(strip=True)
            
            # Skip empty route text
            if not route_text:
                continue
            
            # Parse the route information
            route_info = self.parse_route_text(route_text)
            
            # Skip if we couldn't extract meaningful info
            if not route_info['route_name'] and not route_info['grade']:
                continue
            
            # Get route URL
            route_href = route_link.get('href', '')
            route_url = urllib.parse.urljoin(self.base_url, route_href) if route_href else ""
            
            route_data = {
                'crag_number': crag_info['crag_number'],
                'crag_name': crag_info['crag_name'],
                'route_number': route_info['route_number'],
                'route_name': route_info['route_name'],
                'grade': route_info['grade'],
                'length_m': route_info['length_m'],
                'route_url': route_url
            }
            
            routes.append(route_data)
        
        return routes

    def scrape_all_crags(self):
        """Scrape all crags from the main page"""
        logger.info("Starting to scrape crags...")
        soup = self.get_page(self.crags_url)
        if not soup:
            logger.error("Could not fetch main crags page")
            return
        
        # Find all crag links
        crag_links = soup.find_all('a', href=re.compile(r'/view/\?crag='))
        logger.info(f"Found {len(crag_links)} crags")
        
        for i, crag_link in enumerate(crag_links, 1):
            logger.info(f"Processing crag {i}/{len(crag_links)}")
            
            # Extract basic crag info
            crag_info = self.extract_crag_info(crag_link)
            
            # Get detailed info from crag page
            if crag_info['crag_url']:
                detailed_info = self.extract_crag_details(crag_info['crag_url'], crag_info)
                self.crags_data.append(detailed_info)
                
                # Extract routes from this crag
                routes = self.extract_routes_from_crag(crag_info['crag_url'], crag_info)
                self.routes_data.extend(routes)
                
                logger.info(f"Found {len(routes)} routes in {crag_info['crag_name']}")
            
            # Be respectful to the server
            time.sleep(1)

    def save_to_csv(self):
        """Save scraped data to CSV files"""
        
        # Save crags data
        crags_filename = 'leonidio_crags_v2.csv'
        logger.info(f"Saving {len(self.crags_data)} crags to {crags_filename}")
        
        crag_fieldnames = [
            'crag_number', 'crag_name', 'description', 'route_count', 
            'best_period', 'busy_level', 'exposure', 'shade', 
            'elevation_m', 'crag_url'
        ]
        
        with open(crags_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=crag_fieldnames)
            writer.writeheader()
            for crag in self.crags_data:
                writer.writerow(crag)
        
        # Save routes data
        routes_filename = 'leonidio_routes_v2.csv'
        logger.info(f"Saving {len(self.routes_data)} routes to {routes_filename}")
        
        route_fieldnames = [
            'crag_number', 'crag_name', 'route_number', 'route_name',
            'grade', 'length_m', 'route_url'
        ]
        
        with open(routes_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=route_fieldnames)
            writer.writeheader()
            for route in self.routes_data:
                writer.writerow(route)
        
        logger.info("CSV files saved successfully!")

    def run(self):
        """Run the complete scraping process"""
        logger.info("Starting Leonidio climbing routes scraper v2...")
        self.scrape_all_crags()
        self.save_to_csv()
        logger.info(f"Scraping complete! Found {len(self.crags_data)} crags and {len(self.routes_data)} routes")

if __name__ == "__main__":
    scraper = LeonidioScraperV2()
    scraper.run()
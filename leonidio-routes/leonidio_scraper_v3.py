#!/usr/bin/env python3
"""
Enhanced Leonidio Climbing Routes Scraper v3

This script scrapes comprehensive crag and route information from climbinleonidio.com
including detailed route information from individual route pages.

Features:
- Accurate crag name extraction
- Complete crag details (exposure, shade, sub-sectors, etc.)
- Individual route details (subsector, rating, notes)
- Improved error handling and logging

Author: GitHub Copilot
Date: January 8, 2026
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

class LeonidioScraperV3:
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

    def clean_crag_name(self, crag_text: str) -> str:
        """Extract clean crag name from the full text"""
        # Remove the leading number
        text_without_number = re.sub(r'^\d+\s*', '', crag_text)
        
        # Common patterns to stop at
        stop_patterns = [
            r'\s+At\s+\d+m',  # "At 800m elevation"
            r'\s+A\s+[a-z]',   # "A world-class"
            r'\s+Good\s+',     # "Good rock"
            r'\s+Big\s+',      # "Big variety"
            r'\s+Quality\s+',  # "Quality climbing"
            r'\s+Well-bolted', # "Well-bolted"
            r'\s+Routes:',     # "Routes:"
            r'\s+Climbing',    # "Climbing Garden"
            r'\s+An?\s+',      # "A massive wall" or "An impressive"
            r'\s+Steep\s+',    # "Steep tufa"
            r'\s+Four\s+',     # "Four sub-sectors"
            r'\s+Easy\s+',     # "Easy and mid-grade"
        ]
        
        crag_name = text_without_number
        for pattern in stop_patterns:
            match = re.search(pattern, crag_name, re.IGNORECASE)
            if match:
                crag_name = crag_name[:match.start()].strip()
                break
        
        # Fallback: if name is too long, take first meaningful part
        if len(crag_name) > 40:
            words = crag_name.split()
            if len(words) > 3:
                crag_name = ' '.join(words[:3])
        
        return crag_name.strip()

    def extract_crag_info(self, crag_link) -> Dict:
        """Extract crag information from the main crags page"""
        crag_text = crag_link.get_text(strip=True)
        
        # Extract crag number
        number_match = re.match(r'^(\d+)', crag_text)
        crag_number = number_match.group(1) if number_match else ""
        
        # Extract clean crag name
        crag_name = self.clean_crag_name(crag_text)
        
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
        
        # Extract all text content
        text_content = soup.get_text()
        
        # Extract exposure
        exposure_match = re.search(r'Exposure:\s*([^B]+?)(?:\s+Best|\s+Shade|$)', text_content, re.IGNORECASE)
        exposure = exposure_match.group(1).strip() if exposure_match else ""
        
        # Extract shade information
        shade_match = re.search(r'Shade:\s*([^B]+?)(?:\s+Best|\s+Busy|\s+Routes|$)', text_content, re.IGNORECASE)
        shade = shade_match.group(1).strip() if shade_match else ""
        
        # Extract elevation if mentioned
        elevation_match = re.search(r'(?:At\s+)?(\d+)m?\s+elevation', text_content, re.IGNORECASE)
        elevation = elevation_match.group(1) if elevation_match else ""
        
        # Extract detailed description/character
        # Look for paragraphs that describe the crag character
        character_patterns = [
            r'A\s+[^.]+?(?:crag|cliff|wall)[^.]+?\.',
            r'(?:Quality|Good|Well-bolted)[^.]+?\.',
            r'[^.]*(?:sub-sector|sub-sectors)[^.]+?\.',
        ]
        
        character_description = ""
        for pattern in character_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                desc = match.group(0).strip()
                if len(desc) > len(character_description):
                    character_description = desc
        
        # Extract sub-sectors information
        subsectors_match = re.search(r'sub-sector[s]?\s+([^.]+?)\.', text_content, re.IGNORECASE)
        subsectors = subsectors_match.group(1).strip() if subsectors_match else ""
        
        crag_info.update({
            'exposure': exposure,
            'shade': shade,
            'elevation_m': elevation,
            'character': character_description,
            'subsectors': subsectors
        })
        
        return crag_info

    def parse_route_text(self, route_text: str) -> Dict:
        """Parse route text to extract basic route information"""
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
        
        # Fallback: try to extract what we can
        grade_match = re.search(r'([0-9]+[a-c]?[+]?)', route_text)
        length_match = re.search(r'(\d+)m?', route_text)
        
        if grade_match:
            grade = grade_match.group(1)
        if length_match:
            length = length_match.group(1)
        
        # Extract route name by removing grade and length
        route_name = route_text
        for remove_part in [grade, length + 'm' if length else '', length]:
            if remove_part:
                route_name = route_name.replace(remove_part, '').strip()
        
        return {
            'route_number': route_number,
            'route_name': route_name,
            'grade': grade,
            'length_m': length
        }

    def extract_route_details(self, route_url: str) -> Dict:
        """Extract detailed information from individual route page"""
        soup = self.get_page(route_url)
        if not soup:
            return {}
        
        details = {
            'subsector': '',
            'rating_stars': '',
            'rating_numeric': 0,
            'route_notes': '',
            'detailed_grade': '',
            'detailed_length': ''
        }
        
        # Extract text content
        text_content = soup.get_text()
        
        # Extract subsector
        subsector_match = re.search(r'Subsector:\s*([^G]+?)(?:\s+Grade|$)', text_content, re.IGNORECASE)
        if subsector_match:
            details['subsector'] = subsector_match.group(1).strip()
        
        # Extract rating (stars)
        star_match = re.search(r'(\d+)★', text_content)
        if star_match:
            details['rating_stars'] = star_match.group(0)
            details['rating_numeric'] = int(star_match.group(1))
        
        # Extract detailed grade and length from the table
        grade_match = re.search(r'Grade\s+Length\s+Rating\s+(\d+[a-c]?[+]?)\s+(\d+)m\.?\s+\d*★?', text_content)
        if grade_match:
            details['detailed_grade'] = grade_match.group(1)
            details['detailed_length'] = grade_match.group(2)
        
        # Extract route notes/description
        # Look for descriptive text that's not part of the structured data
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Skip empty lines and structural elements
            if not line or line in ['Grade', 'Length', 'Rating', 'Crag:', 'Subsector:']:
                continue
            # Look for descriptive text (often after the rating)
            if len(line) > 10 and not re.match(r'^\d+[a-c]?[+]?\s+\d+m', line):
                # Check if it looks like a description
                if any(word in line.lower() for word in ['up', 'climb', 'start', 'follow', 'move', 'right', 'left', 'crack', 'wall']):
                    details['route_notes'] = line
                    break
        
        return details

    def extract_routes_from_crag(self, crag_url: str, crag_info: Dict) -> List[Dict]:
        """Extract all routes from a specific crag page"""
        soup = self.get_page(crag_url)
        if not soup:
            return []
        
        routes = []
        
        # Find all route links
        route_links = soup.find_all('a', href=re.compile(r'/route/'))
        logger.info(f"Found {len(route_links)} route links in {crag_info['crag_name']}")
        
        for i, route_link in enumerate(route_links, 1):
            route_text = route_link.get_text(strip=True)
            
            # Skip empty route text
            if not route_text:
                continue
            
            # Parse the basic route information
            route_info = self.parse_route_text(route_text)
            
            # Skip if we couldn't extract meaningful info
            if not route_info['route_name'] and not route_info['grade']:
                continue
            
            # Get route URL
            route_href = route_link.get('href', '')
            route_url = urllib.parse.urljoin(self.base_url, route_href) if route_href else ""
            
            # Extract detailed route information
            if route_url:
                logger.info(f"Getting details for route {i}/{len(route_links)}: {route_info['route_name']}")
                route_details = self.extract_route_details(route_url)
                time.sleep(0.5)  # Be respectful to the server
            else:
                route_details = {}
            
            route_data = {
                'crag_number': crag_info['crag_number'],
                'crag_name': crag_info['crag_name'],
                'route_number': route_info['route_number'],
                'route_name': route_info['route_name'],
                'grade': route_info['grade'],
                'length_m': route_info['length_m'],
                'subsector': route_details.get('subsector', ''),
                'rating_stars': route_details.get('rating_stars', ''),
                'rating_numeric': route_details.get('rating_numeric', 0),
                'route_notes': route_details.get('route_notes', ''),
                'detailed_grade': route_details.get('detailed_grade', ''),
                'detailed_length': route_details.get('detailed_length', ''),
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
            logger.info(f"Crag: {crag_info['crag_name']}")
            
            # Get detailed info from crag page
            if crag_info['crag_url']:
                detailed_info = self.extract_crag_details(crag_info['crag_url'], crag_info)
                self.crags_data.append(detailed_info)
                
                # Extract routes from this crag
                routes = self.extract_routes_from_crag(crag_info['crag_url'], crag_info)
                self.routes_data.extend(routes)
                
                logger.info(f"Found {len(routes)} routes in {crag_info['crag_name']}")
            
            # Be respectful to the server
            time.sleep(2)

    def save_to_csv(self):
        """Save scraped data to CSV files"""
        
        # Save crags data
        crags_filename = 'leonidio_crags_v3.csv'
        logger.info(f"Saving {len(self.crags_data)} crags to {crags_filename}")
        
        crag_fieldnames = [
            'crag_number', 'crag_name', 'description', 'character', 'subsectors',
            'route_count', 'best_period', 'busy_level', 'exposure', 'shade', 
            'elevation_m', 'crag_url'
        ]
        
        with open(crags_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=crag_fieldnames)
            writer.writeheader()
            for crag in self.crags_data:
                writer.writerow(crag)
        
        # Save routes data
        routes_filename = 'leonidio_routes_v3.csv'
        logger.info(f"Saving {len(self.routes_data)} routes to {routes_filename}")
        
        route_fieldnames = [
            'crag_number', 'crag_name', 'route_number', 'route_name',
            'grade', 'length_m', 'subsector', 'rating_stars', 'rating_numeric',
            'route_notes', 'detailed_grade', 'detailed_length', 'route_url'
        ]
        
        with open(routes_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=route_fieldnames)
            writer.writeheader()
            for route in self.routes_data:
                writer.writerow(route)
        
        logger.info("CSV files saved successfully!")

    def run(self):
        """Run the complete scraping process"""
        logger.info("Starting Leonidio climbing routes scraper v3...")
        self.scrape_all_crags()
        self.save_to_csv()
        logger.info(f"Scraping complete! Found {len(self.crags_data)} crags and {len(self.routes_data)} routes")

if __name__ == "__main__":
    scraper = LeonidioScraperV3()
    scraper.run()
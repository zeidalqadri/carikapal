#!/usr/bin/env python3
"""
Enhanced MOSVA Vessel Discovery System
Orchestrated modular approach for comprehensive vessel data collection
"""

import os
import re
import json
import time
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import concurrent.futures
from pathlib import Path
import hashlib
from datetime import datetime

# Supabase integration
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not installed. Install with: pip install supabase")

@dataclass
class CompanyData:
    """MOSVA company information"""
    name: str
    address: str
    phone: str
    fax: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    member_type: str = "ordinary"  # ordinary or associate
    
@dataclass
class VesselRecord:
    """Enhanced vessel record for marketplace"""
    # Basic identification
    vessel_name: Optional[str] = None
    imo_number: Optional[str] = None
    mmsi_number: Optional[str] = None
    call_sign: Optional[str] = None
    
    # Company information
    owner_company: Optional[str] = None
    operator_company: Optional[str] = None
    company_website: Optional[str] = None
    
    # Vessel specifications
    vessel_type: Optional[str] = None
    build_year: Optional[int] = None
    length_m: Optional[float] = None
    beam_m: Optional[float] = None
    gross_tonnage: Optional[float] = None
    deadweight_tonnage: Optional[float] = None
    
    # OSV specific
    deck_area_sqm: Optional[float] = None
    crane_capacity_tonnes: Optional[float] = None
    accommodation_persons: Optional[int] = None
    dynamic_positioning: Optional[str] = None
    
    # Commercial
    day_rate_usd: Optional[float] = None
    availability_status: Optional[str] = None
    current_location: Optional[str] = None
    
    # Media and documents
    photos: List[str] = None
    spec_sheets: List[str] = None
    
    # Data provenance
    source_url: Optional[str] = None
    last_updated: Optional[str] = None
    data_quality_score: Optional[float] = None

class SupabaseManager:
    """Manages Supabase database operations"""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available")
        
        self.url = "https://juvqqrsdbruskleodzip.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw"
        
        try:
            self.client: Client = create_client(self.url, self.key)
            self.logger = logging.getLogger(__name__)
            self._test_connection()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}")
    
    def _test_connection(self):
        """Test database connection"""
        try:
            # Try to query a table or check connection
            result = self.client.table('vessels').select("id").limit(1).execute()
            self.logger.info("✅ Supabase connection established")
        except Exception as e:
            self.logger.warning(f"⚠️ Supabase connection test failed: {e}")
    
    def upsert_vessel(self, vessel: VesselRecord) -> bool:
        """Insert or update vessel record"""
        try:
            vessel_data = asdict(vessel)
            vessel_data['last_updated'] = datetime.utcnow().isoformat()
            
            # Remove None values
            vessel_data = {k: v for k, v in vessel_data.items() if v is not None}
            
            result = self.client.table('vessels').upsert(vessel_data).execute()
            
            if result.data:
                self.logger.info(f"✅ Upserted vessel: {vessel.vessel_name}")
                return True
            else:
                self.logger.error(f"❌ Failed to upsert vessel: {vessel.vessel_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Database error for {vessel.vessel_name}: {e}")
            return False
    
    def upsert_company(self, company: CompanyData) -> bool:
        """Insert or update company record"""
        try:
            company_data = asdict(company)
            company_data['last_updated'] = datetime.utcnow().isoformat()
            
            result = self.client.table('companies').upsert(company_data).execute()
            
            if result.data:
                self.logger.info(f"✅ Upserted company: {company.name}")
                return True
            else:
                self.logger.error(f"❌ Failed to upsert company: {company.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Database error for {company.name}: {e}")
            return False

class MOSVADataParser:
    """Parses MOSVA member data from JSON files"""
    
    def __init__(self, ordinary_members_file: str, associate_members_file: str):
        self.ordinary_file = ordinary_members_file
        self.associate_file = associate_members_file
        self.companies = []
        self.logger = logging.getLogger(__name__)
    
    def parse_all_members(self) -> List[CompanyData]:
        """Parse both ordinary and associate member files"""
        self.companies = []
        
        # Parse ordinary members
        ordinary_companies = self.parse_member_file(self.ordinary_file, "ordinary")
        self.companies.extend(ordinary_companies)
        
        # Parse associate members
        associate_companies = self.parse_member_file(self.associate_file, "associate")
        self.companies.extend(associate_companies)
        
        self.logger.info(f"Parsed {len(self.companies)} companies from MOSVA data")
        return self.companies
    
    def parse_member_file(self, file_path: str, member_type: str) -> List[CompanyData]:
        """Parse a single MOSVA member file"""
        companies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            markdown = data.get('markdown', '')
            companies = self._extract_companies_from_markdown(markdown, member_type)
            
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
        
        return companies
    
    def _extract_companies_from_markdown(self, markdown: str, member_type: str) -> List[CompanyData]:
        """Extract company data from markdown content"""
        companies = []
        
        # Split into company blocks (each starts with **)
        company_blocks = re.split(r'\*\*([^*]+?)\*\*', markdown)[1:]  # Skip first empty element
        
        for i in range(0, len(company_blocks), 2):
            if i + 1 < len(company_blocks):
                company_name = company_blocks[i].strip()
                company_details = company_blocks[i + 1].strip()
                
                if company_name and company_details:
                    company = self._parse_company_block(company_name, company_details, member_type)
                    if company:
                        companies.append(company)
        
        return companies
    
    def _parse_company_block(self, name: str, details: str, member_type: str) -> Optional[CompanyData]:
        """Parse individual company block"""
        try:
            # Extract contact information
            address_parts = []
            phone = None
            fax = None
            website = None
            email = None
            
            lines = details.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Phone number
                if line.startswith('Tel'):
                    phone = re.sub(r'Tel:?\s*', '', line).strip()
                
                # Fax number
                elif line.startswith('Fax'):
                    fax = re.sub(r'Fax:?\s*', '', line).strip()
                
                # Website
                elif line.startswith('[www.') or line.startswith('www.') or 'http' in line:
                    # Extract URL from markdown link or plain text
                    url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
                    if url_match:
                        website = url_match.group(2)
                    else:
                        # Try to extract plain URL
                        url_match = re.search(r'(www\.[^\s]+|https?://[^\s]+)', line)
                        if url_match:
                            website = url_match.group(1)
                            if not website.startswith('http'):
                                website = 'http://' + website
                
                # Email (if present)
                elif '@' in line:
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line)
                    if email_match:
                        email = email_match.group(0)
                
                # Address lines (everything else that's not tel/fax/website)
                elif not any(keyword in line.lower() for keyword in ['tel', 'fax', 'www', 'http']):
                    address_parts.append(line)
            
            # Clean up address
            address = ', '.join(address_parts) if address_parts else ''
            
            # Create company object
            company = CompanyData(
                name=name,
                address=address,
                phone=phone,
                fax=fax,
                website=website,
                email=email,
                member_type=member_type
            )
            
            return company
            
        except Exception as e:
            self.logger.error(f"Failed to parse company {name}: {e}")
            return None

class WebsiteDiscovery:
    """Discovers and validates company websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
    
    def discover_working_url(self, company: CompanyData) -> Optional[str]:
        """Find working URL for company website"""
        if not company.website:
            # Try to search for company website
            return self._search_company_website(company.name)
        
        # Try original URL
        if self._test_url(company.website):
            return company.website
        
        # Try variations
        variations = self._generate_url_variations(company.website, company.name)
        for url in variations:
            if self._test_url(url):
                return url
        
        # Fallback to search
        return self._search_company_website(company.name)
    
    def _test_url(self, url: str) -> bool:
        """Test if URL is accessible"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    def _generate_url_variations(self, original_url: str, company_name: str) -> List[str]:
        """Generate possible URL variations"""
        variations = []
        
        if original_url:
            # Try HTTPS version
            if original_url.startswith('http://'):
                variations.append(original_url.replace('http://', 'https://'))
            
            # Try without www
            if 'www.' in original_url:
                variations.append(original_url.replace('www.', ''))
            
            # Try with www
            if 'www.' not in original_url:
                parsed = urlparse(original_url)
                variations.append(f"{parsed.scheme}://www.{parsed.netloc}{parsed.path}")
        
        # Generate from company name
        clean_name = re.sub(r'[^\w]+', '', company_name.lower())
        domain_variations = [
            f"http://www.{clean_name}.com",
            f"https://www.{clean_name}.com",
            f"http://www.{clean_name}.com.my",
            f"https://www.{clean_name}.com.my",
            f"http://{clean_name}.com",
            f"https://{clean_name}.com"
        ]
        variations.extend(domain_variations)
        
        return variations
    
    def _search_company_website(self, company_name: str) -> Optional[str]:
        """Search for company website using search engine"""
        try:
            # Use DuckDuckGo instant answers or similar
            search_query = f"{company_name} malaysia website"
            # This would require implementing a search API
            # For now, return None and log that manual search is needed
            self.logger.info(f"Manual search needed for: {company_name}")
            return None
        except Exception as e:
            self.logger.error(f"Search failed for {company_name}: {e}")
            return None

class VesselPageDiscovery:
    """Discovers vessel/fleet pages on company websites"""
    
    VESSEL_KEYWORDS = [
        'vessel', 'fleet', 'ships', 'boat', 'offshore', 'marine',
        'osv', 'supply', 'platform', 'anchor', 'tug', 'barge',
        'workboat', 'crew', 'cargo', 'service', 'support', 'charter'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logger = logging.getLogger(__name__)
    
    def find_vessel_pages(self, company_url: str) -> List[str]:
        """Find all vessel-related pages on website"""
        vessel_urls = set()
        
        try:
            # Get main page
            response = self.session.get(company_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            base_domain = urlparse(company_url).netloc
            
            # Find vessel-related links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                if self._is_vessel_link(text, href):
                    full_url = urljoin(company_url, href)
                    
                    # Only include same domain links
                    if urlparse(full_url).netloc == base_domain:
                        vessel_urls.add(full_url)
            
            # Look for specific sections
            vessel_urls.update(self._find_fleet_sections(soup, company_url))
            
            # If no specific vessel pages found, check common paths
            if not vessel_urls:
                vessel_urls.update(self._try_common_vessel_paths(company_url))
            
        except Exception as e:
            self.logger.warning(f"Failed to discover vessel pages from {company_url}: {e}")
        
        return list(vessel_urls)
    
    def _is_vessel_link(self, text: str, href: str) -> bool:
        """Check if link appears to be vessel-related"""
        combined = f"{text} {href}".lower()
        return any(keyword in combined for keyword in self.VESSEL_KEYWORDS)
    
    def _find_fleet_sections(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find fleet sections in navigation or content"""
        urls = set()
        
        # Check navigation menus
        for nav in soup.find_all(['nav', 'menu', 'ul']):
            for link in nav.find_all('a', href=True):
                text = link.get_text(strip=True).lower()
                if any(keyword in text for keyword in self.VESSEL_KEYWORDS):
                    full_url = urljoin(base_url, link['href'])
                    urls.add(full_url)
        
        return list(urls)
    
    def _try_common_vessel_paths(self, base_url: str) -> List[str]:
        """Try common vessel page paths"""
        common_paths = [
            '/fleet', '/vessels', '/ships', '/marine', '/offshore',
            '/services/fleet', '/services/vessels', '/charter',
            '/fleet.html', '/vessels.html', '/marine.html'
        ]
        
        working_urls = []
        for path in common_paths:
            test_url = urljoin(base_url, path)
            try:
                response = self.session.head(test_url, timeout=5)
                if response.status_code == 200:
                    working_urls.append(test_url)
            except:
                continue
        
        return working_urls

class VesselDataExtractor:
    """Extracts vessel data from web pages"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logger = logging.getLogger(__name__)
    
    def extract_vessels_from_page(self, url: str, company_name: str) -> List[VesselRecord]:
        """Extract vessel data from a web page"""
        vessels = []
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for vessel listings
            vessel_elements = self._find_vessel_elements(soup)
            
            for element in vessel_elements:
                vessel = self._parse_vessel_element(element, company_name, url)
                if vessel:
                    vessels.append(vessel)
            
            # If no structured vessel elements, try to extract from text
            if not vessels:
                vessels = self._extract_from_text(soup, company_name, url)
            
        except Exception as e:
            self.logger.error(f"Failed to extract vessels from {url}: {e}")
        
        return vessels
    
    def _find_vessel_elements(self, soup: BeautifulSoup) -> List:
        """Find elements that likely contain vessel information"""
        vessel_elements = []
        
        # Look for common vessel listing patterns
        patterns = [
            soup.find_all('div', class_=re.compile(r'vessel|ship|fleet', re.I)),
            soup.find_all('div', class_=re.compile(r'boat|marine|offshore', re.I)),
            soup.find_all('table', class_=re.compile(r'vessel|fleet', re.I)),
            soup.find_all('li', class_=re.compile(r'vessel|ship', re.I))
        ]
        
        for pattern in patterns:
            vessel_elements.extend(pattern)
        
        # Look for structured data tables
        tables = soup.find_all('table')
        for table in tables:
            if any(keyword in table.get_text().lower() for keyword in ['vessel', 'ship', 'imo', 'mmsi']):
                vessel_elements.append(table)
        
        return vessel_elements
    
    def _parse_vessel_element(self, element, company_name: str, source_url: str) -> Optional[VesselRecord]:
        """Parse vessel data from an HTML element"""
        try:
            text = element.get_text()
            
            vessel = VesselRecord(
                owner_company=company_name,
                source_url=source_url,
                last_updated=datetime.utcnow().isoformat()
            )
            
            # Extract vessel name
            name_patterns = [
                r'vessel\s+name\s*:?\s*([^\n,]+)',
                r'ship\s+name\s*:?\s*([^\n,]+)',
                r'name\s*:?\s*([^\n,]+)',
                r'^([A-Z][A-Z\s\d]+?)(?:\n|$)'  # All caps name at start
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    vessel.vessel_name = match.group(1).strip()
                    break
            
            # Extract IMO
            imo_match = re.search(r'IMO\s*#?:?\s*(\d{7})', text, re.IGNORECASE)
            if imo_match:
                vessel.imo_number = imo_match.group(1)
            
            # Extract MMSI
            mmsi_match = re.search(r'MMSI\s*#?:?\s*(\d{9})', text, re.IGNORECASE)
            if mmsi_match:
                vessel.mmsi_number = mmsi_match.group(1)
            
            # Extract build year
            year_match = re.search(r'(?:built|build\s+year|year)\s*:?\s*(\d{4})', text, re.IGNORECASE)
            if year_match:
                vessel.build_year = int(year_match.group(1))
            
            # Extract length
            length_match = re.search(r'length\s*:?\s*([\d.]+)\s*m', text, re.IGNORECASE)
            if length_match:
                vessel.length_m = float(length_match.group(1))
            
            # Extract other specifications...
            # (Add more extraction patterns as needed)
            
            # Only return if we found substantial data
            if vessel.vessel_name or vessel.imo_number:
                return vessel
            
        except Exception as e:
            self.logger.error(f"Failed to parse vessel element: {e}")
        
        return None
    
    def _extract_from_text(self, soup: BeautifulSoup, company_name: str, source_url: str) -> List[VesselRecord]:
        """Extract vessels from unstructured text"""
        vessels = []
        text = soup.get_text()
        
        # Look for vessel names in text
        vessel_patterns = [
            r'(?:m\.?v\.?|vessel|ship)\s+([A-Z][A-Z\s\d]+?)(?:\n|\.|\s-)',
            r'IMO\s*:?\s*\d{7}[^\n]*([A-Z][A-Z\s]+)',
        ]
        
        for pattern in vessel_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                vessel_name = match.group(1).strip()
                if len(vessel_name) > 3:  # Filter out short matches
                    vessel = VesselRecord(
                        vessel_name=vessel_name,
                        owner_company=company_name,
                        source_url=source_url,
                        last_updated=datetime.utcnow().isoformat()
                    )
                    vessels.append(vessel)
        
        return vessels

class OrchestrationEngine:
    """Main orchestration engine that coordinates all modules"""
    
    def __init__(self, supabase_manager: Optional[SupabaseManager] = None):
        self.supabase = supabase_manager
        self.mosva_parser = MOSVADataParser('mosva_ordinarymembers.json', 'mosva_associate-member.json')
        self.website_discovery = WebsiteDiscovery()
        self.vessel_discovery = VesselPageDiscovery()
        self.vessel_extractor = VesselDataExtractor()
        
        self.logger = logging.getLogger(__name__)
        self.results = {
            'companies_processed': 0,
            'vessels_found': 0,
            'vessels_saved': 0,
            'errors': []
        }
    
    def run_full_discovery(self) -> Dict[str, Any]:
        """Run complete vessel discovery process"""
        self.logger.info("🚀 Starting MOSVA vessel discovery")
        
        # Parse MOSVA member data
        companies = self.mosva_parser.parse_all_members()
        self.logger.info(f"📋 Found {len(companies)} companies")
        
        # Process each company
        for company in companies:
            try:
                self._process_company(company)
                self.results['companies_processed'] += 1
            except Exception as e:
                error_msg = f"Failed to process {company.name}: {e}"
                self.logger.error(error_msg)
                self.results['errors'].append(error_msg)
        
        self.logger.info(f"✅ Discovery complete: {self.results}")
        return self.results
    
    def _process_company(self, company: CompanyData):
        """Process a single company"""
        self.logger.info(f"🏢 Processing: {company.name}")
        
        # Save company to database
        if self.supabase:
            self.supabase.upsert_company(company)
        
        # Discover working website
        working_url = self.website_discovery.discover_working_url(company)
        if not working_url:
            self.logger.warning(f"⚠️ No working website found for {company.name}")
            return
        
        self.logger.info(f"🌐 Website found: {working_url}")
        
        # Find vessel pages
        vessel_pages = self.vessel_discovery.find_vessel_pages(working_url)
        if not vessel_pages:
            self.logger.warning(f"⚠️ No vessel pages found for {company.name}")
            return
        
        self.logger.info(f"🚢 Found {len(vessel_pages)} vessel pages")
        
        # Extract vessels from each page
        all_vessels = []
        for page_url in vessel_pages:
            try:
                vessels = self.vessel_extractor.extract_vessels_from_page(page_url, company.name)
                all_vessels.extend(vessels)
                self.logger.info(f"📊 Extracted {len(vessels)} vessels from {page_url}")
            except Exception as e:
                self.logger.error(f"Failed to extract from {page_url}: {e}")
        
        # Save vessels to database
        for vessel in all_vessels:
            if self.supabase:
                if self.supabase.upsert_vessel(vessel):
                    self.results['vessels_saved'] += 1
            
            self.results['vessels_found'] += 1
            self.logger.info(f"✅ Processed vessel: {vessel.vessel_name}")

def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize Supabase (optional)
        supabase_manager = None
        if SUPABASE_AVAILABLE:
            try:
                supabase_manager = SupabaseManager()
                logger.info("✅ Supabase integration enabled")
            except Exception as e:
                logger.warning(f"⚠️ Supabase connection failed: {e}")
        
        # Run discovery
        engine = OrchestrationEngine(supabase_manager)
        results = engine.run_full_discovery()
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 MOSVA Vessel Discovery Complete")
        print("="*60)
        print(f"Companies processed: {results['companies_processed']}")
        print(f"Vessels found: {results['vessels_found']}")
        print(f"Vessels saved: {results['vessels_saved']}")
        print(f"Errors: {len(results['errors'])}")
        
        if results['errors']:
            print("\n❌ Errors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"  • {error}")
        
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        raise

if __name__ == "__main__":
    main()
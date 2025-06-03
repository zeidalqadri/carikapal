#!/usr/bin/env python3
"""
Advanced IMO-Based Vessel Search System
Comprehensive search across multiple maritime databases and photo sources
"""

import os
import re
import json
import time
import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote
from datetime import datetime, timedelta

import aiohttp
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io

@dataclass
class VesselSearchResult:
    """Comprehensive vessel search result"""
    # Basic identification
    vessel_name: Optional[str] = None
    imo_number: Optional[str] = None
    mmsi_number: Optional[str] = None
    call_sign: Optional[str] = None
    
    # Registration and classification
    flag_state: Optional[str] = None
    classification_society: Optional[str] = None
    port_of_registry: Optional[str] = None
    
    # Physical characteristics
    vessel_type: Optional[str] = None
    build_year: Optional[int] = None
    length_m: Optional[float] = None
    beam_m: Optional[float] = None
    gross_tonnage: Optional[float] = None
    deadweight_tonnage: Optional[float] = None
    
    # Propulsion and performance
    main_engine_power_kw: Optional[float] = None
    max_speed_knots: Optional[float] = None
    service_speed_knots: Optional[float] = None
    
    # Current status and location
    current_location: Optional[str] = None
    current_status: Optional[str] = None
    last_port: Optional[str] = None
    next_port: Optional[str] = None
    eta: Optional[str] = None
    
    # Commercial information
    owner_company: Optional[str] = None
    operator_company: Optional[str] = None
    manager_company: Optional[str] = None
    
    # Media and documents
    photos: List[str] = None
    documents: List[str] = None
    
    # Data provenance
    sources: List[str] = None
    confidence_score: float = 0.0
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.documents is None:
            self.documents = []
        if self.sources is None:
            self.sources = []

class AdvancedIMOSearchEngine:
    """Advanced search engine for vessel data using IMO numbers"""
    
    # Comprehensive list of maritime data sources
    MARITIME_SOURCES = {
        'primary_registries': [
            {
                'name': 'MarineTraffic',
                'base_url': 'https://www.marinetraffic.com',
                'imo_url': 'https://www.marinetraffic.com/en/ais/details/ships/imo:{imo}',
                'search_url': 'https://www.marinetraffic.com/en/ais/search?imo={imo}',
                'reliability': 0.95,
                'rate_limit': 3.0,
                'has_photos': True,
                'has_tracking': True
            },
            {
                'name': 'VesselFinder',
                'base_url': 'https://www.vesselfinder.com',
                'imo_url': 'https://www.vesselfinder.com/vessels/imo-{imo}',
                'search_url': 'https://www.vesselfinder.com/vessels/{imo}',
                'reliability': 0.90,
                'rate_limit': 2.0,
                'has_photos': True,
                'has_tracking': True
            },
            {
                'name': 'FleetMon',
                'base_url': 'https://www.fleetmon.com',
                'imo_url': 'https://www.fleetmon.com/vessels/{imo}',
                'search_url': 'https://www.fleetmon.com/vessels/search?imo={imo}',
                'reliability': 0.85,
                'rate_limit': 2.5,
                'has_photos': True,
                'has_tracking': True
            }
        ],
        'classification_societies': [
            {
                'name': 'Lloyd\'s Register',
                'base_url': 'https://www.lr.org',
                'search_url': 'https://www.lr.org/en/ship-search/?imo={imo}',
                'reliability': 0.95,
                'rate_limit': 4.0,
                'has_certificates': True
            },
            {
                'name': 'DNV',
                'base_url': 'https://www.dnv.com',
                'search_url': 'https://exchange.dnv.com/maritime/search?imo={imo}',
                'reliability': 0.90,
                'rate_limit': 4.0,
                'has_certificates': True
            },
            {
                'name': 'ABS',
                'base_url': 'https://ww2.eagle.org',
                'search_url': 'https://ww2.eagle.org/eaglexpress/eagleexpress?imo={imo}',
                'reliability': 0.90,
                'rate_limit': 4.0,
                'has_certificates': True
            }
        ],
        'national_registries': [
            {
                'name': 'Marine21 Malaysia',
                'base_url': 'https://marine21.marine.gov.my',
                'search_url': 'https://marine21.marine.gov.my/Ship/public_list_ship.cfm?imo={imo}',
                'reliability': 0.85,
                'rate_limit': 3.0,
                'country': 'Malaysia'
            },
            {
                'name': 'MISR Malaysia',
                'base_url': 'https://misr.com',
                'search_url': 'https://misr.com/registry/search?imo={imo}',
                'reliability': 0.80,
                'rate_limit': 3.0,
                'country': 'Malaysia'
            },
            {
                'name': 'Singapore Maritime Registry',
                'base_url': 'https://www.mpa.gov.sg',
                'search_url': 'https://www.mpa.gov.sg/maritime-singapore/singapore-registry-of-ships/ship-search?imo={imo}',
                'reliability': 0.90,
                'rate_limit': 4.0,
                'country': 'Singapore'
            }
        ],
        'photo_sources': [
            {
                'name': 'ShipSpotting',
                'base_url': 'https://www.shipspotting.com',
                'search_url': 'https://www.shipspotting.com/photos/search?imo={imo}',
                'reliability': 0.85,
                'rate_limit': 2.0,
                'photo_quality': 'high'
            },
            {
                'name': 'Flickr Maritime',
                'base_url': 'https://www.flickr.com',
                'search_url': 'https://www.flickr.com/search/?text={imo}+vessel+ship',
                'reliability': 0.70,
                'rate_limit': 2.0,
                'photo_quality': 'variable'
            },
            {
                'name': 'Maritime Connector',
                'base_url': 'https://maritime-connector.com',
                'search_url': 'https://maritime-connector.com/ships/search?imo={imo}',
                'reliability': 0.75,
                'rate_limit': 1.5,
                'photo_quality': 'medium'
            }
        ],
        'specialized_databases': [
            {
                'name': 'IHS Sea-web',
                'base_url': 'https://sea-web.ihs.com',
                'search_url': 'https://sea-web.ihs.com/search?imo={imo}',
                'reliability': 0.95,
                'rate_limit': 5.0,
                'requires_subscription': True,
                'data_quality': 'premium'
            },
            {
                'name': 'Equasis',
                'base_url': 'http://www.equasis.org',
                'search_url': 'http://www.equasis.org/EquasisWeb/public/PublicShipSearch?imo={imo}',
                'reliability': 0.90,
                'rate_limit': 4.0,
                'free': True,
                'has_inspections': True
            }
        ]
    }
    
    def __init__(self, cache_dir: str = "imo_search_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.source_performance = self._load_performance_cache()
        
    def _load_performance_cache(self) -> Dict:
        """Load source performance cache"""
        cache_file = os.path.join(self.cache_dir, "source_performance.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load performance cache: {e}")
        return {}
    
    def _save_performance_cache(self):
        """Save source performance cache"""
        cache_file = os.path.join(self.cache_dir, "source_performance.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.source_performance, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save performance cache: {e}")
    
    def _update_source_performance(self, source_name: str, success: bool, response_time: float):
        """Update source performance metrics"""
        if source_name not in self.source_performance:
            self.source_performance[source_name] = {
                'attempts': 0,
                'successes': 0,
                'avg_response_time': 0,
                'last_success': None,
                'last_attempt': None
            }
        
        perf = self.source_performance[source_name]
        perf['attempts'] += 1
        perf['last_attempt'] = datetime.utcnow().isoformat()
        
        if success:
            perf['successes'] += 1
            perf['last_success'] = datetime.utcnow().isoformat()
        
        # Update running average response time
        perf['avg_response_time'] = (perf['avg_response_time'] + response_time) / 2
        
        self._save_performance_cache()
    
    def _get_cache_key(self, imo: str, source: str) -> str:
        """Generate cache key for IMO search"""
        return hashlib.md5(f"{imo}_{source}".encode()).hexdigest()
    
    def _is_cache_valid(self, cache_file: str, max_age_hours: int = 24) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(cache_file):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_file)
        return file_age < (max_age_hours * 3600)
    
    async def search_by_imo(self, imo: str, include_photos: bool = True, 
                           include_tracking: bool = True) -> VesselSearchResult:
        """Comprehensive IMO-based vessel search"""
        if not self._validate_imo(imo):
            raise ValueError(f"Invalid IMO number: {imo}")
        
        self.logger.info(f"🔍 Starting comprehensive search for IMO: {imo}")
        
        # Check cache first
        cache_key = self._get_cache_key(imo, "comprehensive")
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                self.logger.info(f"📋 Using cached data for IMO: {imo}")
                return VesselSearchResult(**cached_data)
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")
        
        # Perform comprehensive search
        result = VesselSearchResult(imo_number=imo)
        
        # Search primary registries
        await self._search_primary_registries(imo, result)
        
        # Search classification societies
        await self._search_classification_societies(imo, result)
        
        # Search national registries
        await self._search_national_registries(imo, result)
        
        # Search for photos if requested
        if include_photos:
            await self._search_photo_sources(imo, result)
        
        # Search specialized databases
        await self._search_specialized_databases(imo, result)
        
        # Calculate overall confidence score
        result.confidence_score = self._calculate_confidence_score(result)
        result.last_updated = datetime.utcnow().isoformat()
        
        # Cache the result
        try:
            with open(cache_file, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to cache result: {e}")
        
        self.logger.info(f"✅ Search completed for IMO: {imo}, confidence: {result.confidence_score:.2f}")
        return result
    
    async def _search_primary_registries(self, imo: str, result: VesselSearchResult):
        """Search primary vessel tracking registries"""
        sources = self.MARITIME_SOURCES['primary_registries']
        
        for source in sources:
            try:
                start_time = time.time()
                
                # Get best performing sources first
                if self._should_skip_source(source['name']):
                    continue
                
                data = await self._search_marinetraffic(imo) if source['name'] == 'MarineTraffic' else \
                       await self._search_vesselfinder(imo) if source['name'] == 'VesselFinder' else \
                       await self._search_fleetmon(imo)
                
                if data:
                    self._merge_vessel_data(result, data, source['name'])
                    self._update_source_performance(source['name'], True, time.time() - start_time)
                else:
                    self._update_source_performance(source['name'], False, time.time() - start_time)
                
                # Rate limiting
                await asyncio.sleep(source.get('rate_limit', 2.0))
                
            except Exception as e:
                self.logger.error(f"Error searching {source['name']}: {e}")
                self._update_source_performance(source['name'], False, time.time() - start_time)
    
    async def _search_marinetraffic(self, imo: str) -> Optional[Dict]:
        """Search MarineTraffic for vessel data"""
        try:
            url = f"https://www.marinetraffic.com/en/ais/details/ships/imo:{imo}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        data = {}
                        
                        # Extract vessel name
                        name_elem = soup.find('h1', class_='vessel-name')
                        if name_elem:
                            data['vessel_name'] = name_elem.get_text(strip=True)
                        
                        # Extract vessel details from tables
                        for table in soup.find_all('table'):
                            rows = table.find_all('tr')
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    key = cells[0].get_text(strip=True).lower()
                                    value = cells[1].get_text(strip=True)
                                    
                                    self._parse_table_data(key, value, data)
                        
                        # Extract current position and status
                        position_elem = soup.find('div', class_='vessel-position')
                        if position_elem:
                            data['current_location'] = position_elem.get_text(strip=True)
                        
                        # Extract photos
                        photo_links = soup.find_all('img', src=re.compile(r'vessel|ship'))
                        data['photos'] = [urljoin(url, img['src']) for img in photo_links[:5]]
                        
                        return data
                        
        except Exception as e:
            self.logger.error(f"MarineTraffic search failed: {e}")
        
        return None
    
    async def _search_vesselfinder(self, imo: str) -> Optional[Dict]:
        """Search VesselFinder for vessel data"""
        try:
            url = f"https://www.vesselfinder.com/vessels/imo-{imo}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        data = {}
                        
                        # Extract vessel information
                        info_section = soup.find('div', class_='vessel-info')
                        if info_section:
                            # Extract name
                            name_elem = info_section.find('h1')
                            if name_elem:
                                data['vessel_name'] = name_elem.get_text(strip=True)
                            
                            # Extract specifications
                            spec_items = info_section.find_all('div', class_='spec-item')
                            for item in spec_items:
                                label = item.find('span', class_='label')
                                value = item.find('span', class_='value')
                                
                                if label and value:
                                    key = label.get_text(strip=True).lower()
                                    val = value.get_text(strip=True)
                                    self._parse_table_data(key, val, data)
                        
                        # Extract photos
                        gallery = soup.find('div', class_='photo-gallery')
                        if gallery:
                            images = gallery.find_all('img')
                            data['photos'] = [urljoin(url, img['src']) for img in images[:5]]
                        
                        return data
                        
        except Exception as e:
            self.logger.error(f"VesselFinder search failed: {e}")
        
        return None
    
    async def _search_fleetmon(self, imo: str) -> Optional[Dict]:
        """Search FleetMon for vessel data"""
        try:
            url = f"https://www.fleetmon.com/vessels/{imo}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        data = {}
                        
                        # Extract vessel details
                        details_section = soup.find('div', class_='vessel-details')
                        if details_section:
                            detail_rows = details_section.find_all('div', class_='detail-row')
                            for row in detail_rows:
                                label = row.find('span', class_='label')
                                value = row.find('span', class_='value')
                                
                                if label and value:
                                    key = label.get_text(strip=True).lower()
                                    val = value.get_text(strip=True)
                                    self._parse_table_data(key, val, data)
                        
                        return data
                        
        except Exception as e:
            self.logger.error(f"FleetMon search failed: {e}")
        
        return None
    
    async def _search_classification_societies(self, imo: str, result: VesselSearchResult):
        """Search classification society databases"""
        # Implementation for classification societies
        pass
    
    async def _search_national_registries(self, imo: str, result: VesselSearchResult):
        """Search national ship registries"""
        # Implementation for national registries
        pass
    
    async def _search_photo_sources(self, imo: str, result: VesselSearchResult):
        """Search photo sources for vessel images"""
        sources = self.MARITIME_SOURCES['photo_sources']
        
        for source in sources:
            try:
                if source['name'] == 'ShipSpotting':
                    photos = await self._search_shipspotting_photos(imo)
                    if photos:
                        result.photos.extend(photos[:3])  # Limit to 3 photos per source
                
                await asyncio.sleep(source.get('rate_limit', 2.0))
                
            except Exception as e:
                self.logger.error(f"Photo search failed for {source['name']}: {e}")
    
    async def _search_shipspotting_photos(self, imo: str) -> List[str]:
        """Search ShipSpotting for vessel photos"""
        try:
            url = f"https://www.shipspotting.com/photos/search?imo={imo}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        photos = []
                        photo_containers = soup.find_all('div', class_=['photo-item', 'image-container'])
                        
                        for container in photo_containers:
                            img = container.find('img')
                            if img and img.get('src'):
                                photo_url = urljoin(url, img['src'])
                                photos.append(photo_url)
                        
                        return photos[:5]  # Limit to 5 photos
                        
        except Exception as e:
            self.logger.error(f"ShipSpotting photo search failed: {e}")
        
        return []
    
    async def _search_specialized_databases(self, imo: str, result: VesselSearchResult):
        """Search specialized maritime databases"""
        # Implementation for specialized databases like IHS Sea-web, Equasis
        pass
    
    def _parse_table_data(self, key: str, value: str, data: Dict):
        """Parse table data into structured vessel information"""
        key = key.lower().replace(' ', '_').replace('-', '_')
        
        # MMSI
        if 'mmsi' in key and value.isdigit():
            data['mmsi_number'] = value
        
        # Call sign
        elif 'call' in key and 'sign' in key:
            data['call_sign'] = value
        
        # Flag
        elif 'flag' in key:
            data['flag_state'] = value
        
        # Vessel type
        elif 'type' in key or 'category' in key:
            data['vessel_type'] = value
        
        # Build year
        elif 'built' in key or 'year' in key:
            year_match = re.search(r'(\d{4})', value)
            if year_match:
                data['build_year'] = int(year_match.group(1))
        
        # Length
        elif 'length' in key:
            length_match = re.search(r'([\d.]+)', value)
            if length_match:
                data['length_m'] = float(length_match.group(1))
        
        # Beam
        elif 'beam' in key or 'breadth' in key:
            beam_match = re.search(r'([\d.]+)', value)
            if beam_match:
                data['beam_m'] = float(beam_match.group(1))
        
        # Gross tonnage
        elif 'gross' in key and 'tonnage' in key:
            gt_match = re.search(r'([\d,]+)', value)
            if gt_match:
                data['gross_tonnage'] = float(gt_match.group(1).replace(',', ''))
        
        # Deadweight
        elif 'deadweight' in key or 'dwt' in key:
            dwt_match = re.search(r'([\d,]+)', value)
            if dwt_match:
                data['deadweight_tonnage'] = float(dwt_match.group(1).replace(',', ''))
        
        # Owner
        elif 'owner' in key:
            data['owner_company'] = value
        
        # Operator
        elif 'operator' in key or 'manager' in key:
            data['operator_company'] = value
        
        # Current status
        elif 'status' in key:
            data['current_status'] = value
    
    def _merge_vessel_data(self, result: VesselSearchResult, new_data: Dict, source: str):
        """Merge new vessel data into result"""
        result.sources.append(source)
        
        for key, value in new_data.items():
            if value and hasattr(result, key):
                current_value = getattr(result, key)
                
                if key == 'photos':
                    result.photos.extend(value)
                elif key == 'documents':
                    result.documents.extend(value)
                elif current_value is None:
                    setattr(result, key, value)
                # For conflicting data, prefer data from more reliable sources
                # This could be enhanced with source reliability weighting
    
    def _calculate_confidence_score(self, result: VesselSearchResult) -> float:
        """Calculate overall confidence score for the result"""
        score = 0.0
        
        # Basic fields (essential)
        if result.vessel_name:
            score += 0.2
        if result.imo_number:
            score += 0.15
        if result.vessel_type:
            score += 0.1
        
        # Important fields
        if result.build_year:
            score += 0.08
        if result.flag_state:
            score += 0.08
        if result.length_m:
            score += 0.07
        if result.gross_tonnage:
            score += 0.07
        
        # Additional data
        if result.mmsi_number:
            score += 0.05
        if result.owner_company:
            score += 0.05
        if result.photos:
            score += 0.05
        
        # Source diversity bonus
        if len(set(result.sources)) > 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _should_skip_source(self, source_name: str) -> bool:
        """Determine if source should be skipped based on performance"""
        if source_name not in self.source_performance:
            return False
        
        perf = self.source_performance[source_name]
        
        # Skip if success rate is very low and we've tried recently
        if perf['attempts'] > 5:
            success_rate = perf['successes'] / perf['attempts']
            if success_rate < 0.2:
                last_attempt = perf.get('last_attempt')
                if last_attempt:
                    last_time = datetime.fromisoformat(last_attempt)
                    if datetime.utcnow() - last_time < timedelta(hours=1):
                        return True
        
        return False
    
    def _validate_imo(self, imo: str) -> bool:
        """Validate IMO number format and check digit"""
        if not imo or len(imo) != 7 or not imo.isdigit():
            return False
        
        # Calculate check digit
        digits = [int(d) for d in imo[:6]]
        multipliers = [7, 6, 5, 4, 3, 2]
        
        sum_value = sum(d * m for d, m in zip(digits, multipliers))
        check_digit = sum_value % 10
        
        return check_digit == int(imo[6])

async def main():
    """Test the advanced IMO search system"""
    logging.basicConfig(level=logging.INFO)
    
    engine = AdvancedIMOSearchEngine()
    
    # Test with a valid IMO (example)
    test_imo = "9876543"  # Replace with actual IMO for testing
    
    print(f"🔍 Testing advanced IMO search for: {test_imo}")
    
    try:
        result = await engine.search_by_imo(test_imo)
        
        print(f"\n✅ Search Results:")
        print(f"   Vessel Name: {result.vessel_name}")
        print(f"   IMO: {result.imo_number}")
        print(f"   MMSI: {result.mmsi_number}")
        print(f"   Type: {result.vessel_type}")
        print(f"   Flag: {result.flag_state}")
        print(f"   Build Year: {result.build_year}")
        print(f"   Owner: {result.owner_company}")
        print(f"   Photos Found: {len(result.photos)}")
        print(f"   Sources: {', '.join(result.sources)}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
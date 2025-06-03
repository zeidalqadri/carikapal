#!/usr/bin/env python3
"""
Vessel Media and Document Collector
Comprehensive system for collecting vessel photos, specifications, and documents
"""

import os
import re
import json
import time
import logging
import requests
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from dataclasses import dataclass
from pathlib import Path
import concurrent.futures
from PIL import Image
import io
import fitz  # PyMuPDF
import aiohttp
import asyncio

@dataclass
class MediaResult:
    """Represents found vessel media"""
    url: str
    media_type: str  # 'photo', 'specification', 'brochure', 'manual'
    source: str
    title: str
    description: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    confidence_score: float = 0.0
    local_path: Optional[str] = None
    extracted_text: Optional[str] = None

class ReliableSourceManager:
    """Manages list of reliable sources for vessel information"""
    
    RELIABLE_SOURCES = {
        'vessel_tracking': [
            {
                'name': 'VesselFinder',
                'base_url': 'https://www.vesselfinder.com',
                'search_pattern': '/vessels/{imo}',
                'search_url': 'https://www.vesselfinder.com/vessels?name={name}',
                'reliability': 0.9,
                'rate_limit': 2.0
            },
            {
                'name': 'MarineTraffic', 
                'base_url': 'https://www.marinetraffic.com',
                'search_pattern': '/en/ais/details/ships/shipid:{mmsi}',
                'search_url': 'https://www.marinetraffic.com/en/ais/search?ship_name={name}',
                'reliability': 0.95,
                'rate_limit': 3.0
            },
            {
                'name': 'FleetMon',
                'base_url': 'https://www.fleetmon.com',
                'search_pattern': '/vessels/{imo}',
                'search_url': 'https://www.fleetmon.com/vessels?q={name}',
                'reliability': 0.8,
                'rate_limit': 2.5
            }
        ],
        'photo_sources': [
            {
                'name': 'ShipSpotting',
                'base_url': 'https://www.shipspotting.com',
                'search_url': 'https://www.shipspotting.com/photos/search?query={name}',
                'reliability': 0.85,
                'rate_limit': 2.0
            },
            {
                'name': 'Maritime Connector',
                'base_url': 'https://maritime-connector.com',
                'search_url': 'https://maritime-connector.com/ships/search?q={name}',
                'reliability': 0.7,
                'rate_limit': 1.5
            }
        ],
        'specification_sources': [
            {
                'name': 'Marine21 Malaysia',
                'base_url': 'https://marine21.marine.gov.my',
                'search_pattern': '/Ship/public_list_ship.cfm?imo={imo}',
                'reliability': 0.9,
                'rate_limit': 3.0
            },
            {
                'name': 'MISR Malaysia',
                'base_url': 'https://misr.com',
                'search_pattern': '/registry/{imo}',
                'reliability': 0.8,
                'rate_limit': 2.5
            },
            {
                'name': 'ClassNK Database',
                'base_url': 'https://www.classnk.or.jp',
                'search_url': 'https://www.classnk.or.jp/hp/en/activities/statutory/register/search.aspx',
                'reliability': 0.85,
                'rate_limit': 4.0
            }
        ]
    }
    
    def __init__(self, cache_file: str = "reliable_sources_cache.json"):
        self.cache_file = cache_file
        self.source_performance = self._load_performance_cache()
        self.logger = logging.getLogger(__name__)
    
    def _load_performance_cache(self) -> Dict:
        """Load source performance metrics"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load performance cache: {e}")
        return {}
    
    def _save_performance_cache(self):
        """Save source performance metrics"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.source_performance, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save performance cache: {e}")
    
    def get_best_sources(self, category: str, vessel_data: Dict) -> List[Dict]:
        """Get best sources for a category based on performance"""
        sources = self.RELIABLE_SOURCES.get(category, [])
        
        # Sort by reliability and recent performance
        def source_score(source):
            base_score = source.get('reliability', 0.5)
            performance_data = self.source_performance.get(source['name'], {})
            recent_success_rate = performance_data.get('success_rate', 0.5)
            return (base_score * 0.7) + (recent_success_rate * 0.3)
        
        return sorted(sources, key=source_score, reverse=True)
    
    def record_source_performance(self, source_name: str, success: bool, response_time: float):
        """Record source performance for future optimization"""
        if source_name not in self.source_performance:
            self.source_performance[source_name] = {
                'attempts': 0,
                'successes': 0,
                'avg_response_time': 0,
                'success_rate': 0
            }
        
        perf = self.source_performance[source_name]
        perf['attempts'] += 1
        if success:
            perf['successes'] += 1
        
        # Update running averages
        perf['success_rate'] = perf['successes'] / perf['attempts']
        perf['avg_response_time'] = (perf['avg_response_time'] + response_time) / 2
        
        self._save_performance_cache()

class VesselMediaCollector:
    """Collects vessel photos and media from multiple sources"""
    
    def __init__(self, download_dir: str = "vessel_media"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        (self.download_dir / "photos").mkdir(exist_ok=True)
        (self.download_dir / "documents").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.source_manager = ReliableSourceManager()
        self.logger = logging.getLogger(__name__)
    
    async def collect_vessel_media(self, vessel_data: Dict, max_photos: int = 10) -> List[MediaResult]:
        """Collect all media for a vessel"""
        all_media = []
        
        # Collect photos
        photos = await self._collect_photos(vessel_data, max_photos)
        all_media.extend(photos)
        
        # Collect specification documents
        specifications = await self._collect_specifications(vessel_data)
        all_media.extend(specifications)
        
        # Download and process media
        processed_media = await self._process_media(all_media)
        
        return processed_media
    
    async def _collect_photos(self, vessel_data: Dict, max_photos: int) -> List[MediaResult]:
        """Collect vessel photos from reliable sources"""
        photos = []
        
        photo_sources = self.source_manager.get_best_sources('photo_sources', vessel_data)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in photo_sources[:3]:  # Use top 3 sources
                task = self._search_photo_source(session, source, vessel_data, max_photos // 3)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    photos.extend(result)
        
        # Sort by confidence and return top results
        photos.sort(key=lambda x: x.confidence_score, reverse=True)
        return photos[:max_photos]
    
    async def _search_photo_source(self, session: aiohttp.ClientSession, source: Dict, 
                                 vessel_data: Dict, max_results: int) -> List[MediaResult]:
        """Search a specific photo source"""
        photos = []
        start_time = time.time()
        
        try:
            vessel_name = vessel_data.get('vessel_name', '')
            imo = vessel_data.get('imo_number', '')
            
            # Build search URL
            search_url = source['search_url'].format(
                name=quote(vessel_name),
                imo=imo
            )
            
            async with session.get(search_url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if source['name'] == 'ShipSpotting':
                        photos = self._parse_shipspotting_photos(soup, vessel_data, source['name'])
                    elif source['name'] == 'Maritime Connector':
                        photos = self._parse_maritime_connector_photos(soup, vessel_data, source['name'])
                    
                    # Rate limiting
                    await asyncio.sleep(source.get('rate_limit', 2.0))
            
            # Record performance
            self.source_manager.record_source_performance(
                source['name'], 
                len(photos) > 0, 
                time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Photo search failed for {source['name']}: {e}")
            self.source_manager.record_source_performance(source['name'], False, time.time() - start_time)
        
        return photos[:max_results]
    
    def _parse_shipspotting_photos(self, soup: BeautifulSoup, vessel_data: Dict, source: str) -> List[MediaResult]:
        """Parse ShipSpotting photo results"""
        photos = []
        
        photo_containers = soup.find_all('div', class_=['photo-item', 'photo-card', 'image-container'])
        
        for container in photo_containers:
            try:
                img_tag = container.find('img')
                if not img_tag:
                    continue
                
                photo_url = img_tag.get('src') or img_tag.get('data-src')
                if not photo_url:
                    continue
                
                if not photo_url.startswith('http'):
                    photo_url = urljoin('https://www.shipspotting.com', photo_url)
                
                title = img_tag.get('alt', '') or container.get_text(strip=True)
                
                # Calculate confidence based on vessel name match
                confidence = self._calculate_photo_confidence(
                    vessel_data.get('vessel_name', ''), 
                    title
                )
                
                if confidence > 0.3:  # Only include reasonably confident matches
                    photos.append(MediaResult(
                        url=photo_url,
                        media_type='photo',
                        source=source,
                        title=title,
                        confidence_score=confidence
                    ))
                    
            except Exception as e:
                self.logger.debug(f"Failed to parse photo container: {e}")
                continue
        
        return photos
    
    def _parse_maritime_connector_photos(self, soup: BeautifulSoup, vessel_data: Dict, source: str) -> List[MediaResult]:
        """Parse Maritime Connector photo results"""
        photos = []
        
        # Look for vessel images
        img_tags = soup.find_all('img', src=re.compile(r'ship|vessel|boat', re.I))
        
        for img_tag in img_tags:
            try:
                photo_url = img_tag.get('src')
                if not photo_url or 'placeholder' in photo_url.lower():
                    continue
                
                if not photo_url.startswith('http'):
                    photo_url = urljoin('https://maritime-connector.com', photo_url)
                
                title = img_tag.get('alt', '') or f"Vessel {vessel_data.get('vessel_name', 'Unknown')}"
                
                confidence = self._calculate_photo_confidence(
                    vessel_data.get('vessel_name', ''), 
                    title
                )
                
                if confidence > 0.3:
                    photos.append(MediaResult(
                        url=photo_url,
                        media_type='photo',
                        source=source,
                        title=title,
                        confidence_score=confidence
                    ))
                    
            except Exception as e:
                self.logger.debug(f"Failed to parse image: {e}")
                continue
        
        return photos
    
    def _calculate_photo_confidence(self, vessel_name: str, photo_title: str) -> float:
        """Calculate confidence score for photo match"""
        if not vessel_name or not photo_title:
            return 0.0
        
        vessel_lower = vessel_name.lower()
        title_lower = photo_title.lower()
        
        # Exact match
        if vessel_lower in title_lower:
            return 0.9
        
        # Word matching
        vessel_words = set(re.findall(r'\w+', vessel_lower))
        title_words = set(re.findall(r'\w+', title_lower))
        
        if vessel_words and title_words:
            word_match_ratio = len(vessel_words & title_words) / len(vessel_words)
            return word_match_ratio * 0.8
        
        return 0.1
    
    async def _collect_specifications(self, vessel_data: Dict) -> List[MediaResult]:
        """Collect vessel specification documents"""
        specifications = []
        
        imo = vessel_data.get('imo_number')
        if not imo:
            return specifications
        
        spec_sources = self.source_manager.get_best_sources('specification_sources', vessel_data)
        
        async with aiohttp.ClientSession() as session:
            for source in spec_sources[:2]:  # Use top 2 spec sources
                try:
                    specs = await self._search_specification_source(session, source, vessel_data)
                    specifications.extend(specs)
                except Exception as e:
                    self.logger.error(f"Spec search failed for {source['name']}: {e}")
        
        return specifications
    
    async def _search_specification_source(self, session: aiohttp.ClientSession, 
                                         source: Dict, vessel_data: Dict) -> List[MediaResult]:
        """Search for vessel specifications at a source"""
        specifications = []
        
        try:
            imo = vessel_data.get('imo_number', '')
            
            if 'search_pattern' in source:
                search_url = source['base_url'] + source['search_pattern'].format(imo=imo)
            else:
                search_url = source['search_url'].format(imo=imo)
            
            async with session.get(search_url, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for downloadable documents
                    doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx|xls|xlsx)$', re.I))
                    
                    for link in doc_links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(search_url, href)
                            title = link.get_text(strip=True) or os.path.basename(href)
                            
                            specifications.append(MediaResult(
                                url=full_url,
                                media_type='specification',
                                source=source['name'],
                                title=title,
                                confidence_score=0.8
                            ))
            
            await asyncio.sleep(source.get('rate_limit', 3.0))
            
        except Exception as e:
            self.logger.error(f"Specification search failed: {e}")
        
        return specifications
    
    async def _process_media(self, media_list: List[MediaResult]) -> List[MediaResult]:
        """Download and process media files"""
        processed_media = []
        
        for media in media_list:
            try:
                if media.media_type == 'photo':
                    processed = await self._download_and_process_photo(media)
                elif media.media_type == 'specification':
                    processed = await self._download_and_process_document(media)
                else:
                    processed = media
                
                if processed:
                    processed_media.append(processed)
                    
            except Exception as e:
                self.logger.error(f"Failed to process media {media.url}: {e}")
                # Include unprocessed media anyway
                processed_media.append(media)
        
        return processed_media
    
    async def _download_and_process_photo(self, photo: MediaResult) -> Optional[MediaResult]:
        """Download and process photo"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(photo.url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Create filename
                        filename = hashlib.md5(photo.url.encode()).hexdigest() + '.jpg'
                        local_path = self.download_dir / "photos" / filename
                        
                        # Process image
                        img = Image.open(io.BytesIO(content))
                        
                        # Save optimized version
                        img.thumbnail((1024, 768), Image.Resampling.LANCZOS)
                        img.save(local_path, "JPEG", quality=85, optimize=True)
                        
                        # Update media result
                        photo.local_path = str(local_path)
                        photo.file_size = len(content)
                        photo.file_format = img.format
                        
                        return photo
                        
        except Exception as e:
            self.logger.error(f"Failed to download photo {photo.url}: {e}")
        
        return photo
    
    async def _download_and_process_document(self, doc: MediaResult) -> Optional[MediaResult]:
        """Download and process document"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(doc.url, timeout=60) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Create filename
                        ext = os.path.splitext(urlparse(doc.url).path)[1] or '.pdf'
                        filename = hashlib.md5(doc.url.encode()).hexdigest() + ext
                        local_path = self.download_dir / "documents" / filename
                        
                        # Save document
                        with open(local_path, 'wb') as f:
                            f.write(content)
                        
                        # Extract text if PDF
                        if ext.lower() == '.pdf':
                            try:
                                pdf_doc = fitz.open(stream=content, filetype="pdf")
                                text = ""
                                for page in pdf_doc:
                                    text += page.get_text()
                                doc.extracted_text = text[:5000]  # Limit text length
                            except:
                                pass
                        
                        # Update document result
                        doc.local_path = str(local_path)
                        doc.file_size = len(content)
                        doc.file_format = ext
                        
                        return doc
                        
        except Exception as e:
            self.logger.error(f"Failed to download document {doc.url}: {e}")
        
        return doc

class VesselSpecificationParser:
    """Parses vessel specifications from documents and text"""
    
    SPECIFICATION_PATTERNS = {
        'length_overall': [
            r'length\s+overall\s*:?\s*([\d.]+)\s*m',
            r'loa\s*:?\s*([\d.]+)\s*m',
            r'overall\s+length\s*:?\s*([\d.]+)\s*m'
        ],
        'beam': [
            r'beam\s*:?\s*([\d.]+)\s*m',
            r'breadth\s*:?\s*([\d.]+)\s*m',
            r'width\s*:?\s*([\d.]+)\s*m'
        ],
        'draft': [
            r'draft\s*:?\s*([\d.]+)\s*m',
            r'draught\s*:?\s*([\d.]+)\s*m',
            r'design\s+draft\s*:?\s*([\d.]+)\s*m'
        ],
        'gross_tonnage': [
            r'gross\s+tonnage\s*:?\s*([\d,]+)',
            r'gt\s*:?\s*([\d,]+)',
            r'grt\s*:?\s*([\d,]+)'
        ],
        'deadweight': [
            r'deadweight\s*:?\s*([\d,]+)',
            r'dwt\s*:?\s*([\d,]+)',
            r'dead\s+weight\s*:?\s*([\d,]+)'
        ],
        'engine_power': [
            r'main\s+engine\s*:?\s*([\d,]+)\s*kw',
            r'power\s*:?\s*([\d,]+)\s*kw',
            r'engine\s+power\s*:?\s*([\d,]+)\s*kw'
        ],
        'build_year': [
            r'built\s*:?\s*(\d{4})',
            r'build\s+year\s*:?\s*(\d{4})',
            r'year\s+built\s*:?\s*(\d{4})'
        ],
        'flag': [
            r'flag\s*:?\s*([A-Za-z\s]+)',
            r'flag\s+state\s*:?\s*([A-Za-z\s]+)'
        ],
        'class_society': [
            r'classification\s*:?\s*([A-Za-z\s&]+)',
            r'class\s*:?\s*([A-Za-z\s&]+)',
            r'certified\s+by\s*:?\s*([A-Za-z\s&]+)'
        ]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_specifications(self, text: str) -> Dict[str, Any]:
        """Parse vessel specifications from text"""
        specifications = {}
        
        if not text:
            return specifications
        
        text_lower = text.lower()
        
        for spec_name, patterns in self.SPECIFICATION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    
                    # Clean and convert value
                    if spec_name in ['length_overall', 'beam', 'draft']:
                        try:
                            specifications[spec_name] = float(value)
                        except ValueError:
                            pass
                    elif spec_name in ['gross_tonnage', 'deadweight', 'engine_power']:
                        try:
                            # Remove commas and convert to int
                            clean_value = value.replace(',', '')
                            specifications[spec_name] = int(clean_value)
                        except ValueError:
                            pass
                    elif spec_name == 'build_year':
                        try:
                            specifications[spec_name] = int(value)
                        except ValueError:
                            pass
                    else:
                        specifications[spec_name] = value
                    
                    break  # Use first match
        
        return specifications
    
    def extract_vessel_features(self, text: str) -> List[str]:
        """Extract vessel features and capabilities"""
        features = []
        
        if not text:
            return features
        
        text_lower = text.lower()
        
        feature_keywords = {
            'dynamic_positioning': ['dp', 'dynamic positioning', 'dps'],
            'helicopter_deck': ['helicopter deck', 'helideck', 'heli deck'],
            'crane': ['crane', 'deck crane', 'lifting'],
            'moon_pool': ['moon pool', 'moonpool'],
            'diving_support': ['diving support', 'dive support', 'saturation diving'],
            'fire_fighting': ['fire fighting', 'firefighting', 'fifi'],
            'anchor_handling': ['anchor handling', 'ahts', 'anchor handler'],
            'supply_vessel': ['supply vessel', 'platform supply', 'psv'],
            'accommodation': ['accommodation', 'berths', 'crew quarters']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                features.append(feature)
        
        return features

async def main():
    """Test the media collection system"""
    logging.basicConfig(level=logging.INFO)
    
    # Test vessel data
    test_vessel = {
        'vessel_name': 'Perdana Express',
        'imo_number': '1234567',
        'owner_company': 'Perdana Petroleum Berhad'
    }
    
    collector = VesselMediaCollector()
    
    print("🔍 Collecting vessel media...")
    media_results = await collector.collect_vessel_media(test_vessel, max_photos=5)
    
    print(f"\n✅ Collected {len(media_results)} media items:")
    for media in media_results:
        print(f"  📸 {media.media_type}: {media.title}")
        print(f"     Source: {media.source}")
        print(f"     Confidence: {media.confidence_score:.2f}")
        if media.local_path:
            print(f"     Downloaded: {media.local_path}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
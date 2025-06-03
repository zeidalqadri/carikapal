#!/usr/bin/env python3
"""
OSV Marketplace Integration Module
Handles integration of vessel data into the OSV marketplace platform
"""

import os
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
import uuid

from pydantic import BaseModel, Field, validator
from supabase import create_client, Client

@dataclass
class MarketplaceVessel:
    """Vessel data structure optimized for marketplace"""
    # Core identification
    id: Optional[str] = None
    vessel_name: str = ""
    imo_number: Optional[str] = None
    mmsi_number: Optional[str] = None
    
    # Classification and type
    vessel_type: str = "OSV"
    vessel_subtype: Optional[str] = None
    category: str = "offshore_support"
    
    # Physical specifications
    length_overall_m: Optional[float] = None
    beam_m: Optional[float] = None
    gross_tonnage: Optional[float] = None
    deadweight_tonnage: Optional[float] = None
    build_year: Optional[int] = None
    
    # Operational capabilities
    accommodation_persons: Optional[int] = None
    deck_area_sqm: Optional[float] = None
    crane_capacity_tonnes: Optional[float] = None
    dynamic_positioning: Optional[str] = None
    
    # Commercial information
    owner_company: Optional[str] = None
    operator_company: Optional[str] = None
    flag_state: Optional[str] = None
    home_port: Optional[str] = None
    
    # Availability and status
    availability_status: str = "unknown"  # available, chartered, unavailable, unknown
    current_location: Optional[str] = None
    day_rate_usd: Optional[float] = None
    currency: str = "USD"
    
    # Media and documentation
    primary_photo_url: Optional[str] = None
    photos: List[str] = None
    specification_sheets: List[str] = None
    
    # Data quality and verification
    data_quality_score: float = 0.0
    verification_status: str = "unverified"  # verified, pending, unverified
    last_verified: Optional[str] = None
    
    # Marketplace metadata
    featured: bool = False
    listing_status: str = "active"  # active, inactive, draft
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.specification_sheets is None:
            self.specification_sheets = []
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

class MarketplaceDataProcessor:
    """Processes and transforms crawler data for marketplace integration"""
    
    VESSEL_TYPE_MAPPING = {
        'supply vessel': 'Platform Supply Vessel',
        'anchor handling': 'Anchor Handling Tug Supply',
        'ahts': 'Anchor Handling Tug Supply',
        'psv': 'Platform Supply Vessel',
        'osv': 'Offshore Support Vessel',
        'crew boat': 'Crew Transfer Vessel',
        'workboat': 'Offshore Workboat',
        'tug': 'Offshore Tug',
        'barge': 'Offshore Barge',
        'diving support': 'Diving Support Vessel',
        'survey': 'Survey Vessel',
        'construction': 'Construction Support Vessel'
    }
    
    AVAILABILITY_STATUS_MAPPING = {
        'available': 'available',
        'in service': 'chartered',
        'under charter': 'chartered',
        'laid up': 'unavailable',
        'maintenance': 'unavailable',
        'repair': 'unavailable',
        'active': 'available',
        'inactive': 'unavailable'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_vessel_data(self, raw_vessel_data: Dict) -> MarketplaceVessel:
        """Transform raw vessel data into marketplace format"""
        try:
            vessel = MarketplaceVessel()
            
            # Core identification
            vessel.vessel_name = self._clean_vessel_name(raw_vessel_data.get('vessel_name', ''))
            vessel.imo_number = raw_vessel_data.get('imo_number')
            vessel.mmsi_number = raw_vessel_data.get('mmsi_number')
            
            # Classification
            vessel.vessel_type = self._standardize_vessel_type(raw_vessel_data.get('vessel_type', ''))
            vessel.vessel_subtype = raw_vessel_data.get('vessel_subtype')
            
            # Physical specifications
            vessel.length_overall_m = self._safe_float(raw_vessel_data.get('length_overall_m'))
            vessel.beam_m = self._safe_float(raw_vessel_data.get('beam_m'))
            vessel.gross_tonnage = self._safe_float(raw_vessel_data.get('gross_tonnage'))
            vessel.deadweight_tonnage = self._safe_float(raw_vessel_data.get('deadweight_tonnage'))
            vessel.build_year = self._safe_int(raw_vessel_data.get('build_year'))
            
            # Operational capabilities
            vessel.accommodation_persons = self._safe_int(raw_vessel_data.get('accommodation_persons'))
            vessel.deck_area_sqm = self._safe_float(raw_vessel_data.get('deck_area_sqm'))
            vessel.crane_capacity_tonnes = self._safe_float(raw_vessel_data.get('crane_capacity_tonnes'))
            vessel.dynamic_positioning = raw_vessel_data.get('dynamic_positioning_system')
            
            # Commercial information
            vessel.owner_company = self._clean_company_name(raw_vessel_data.get('owner_company'))
            vessel.operator_company = self._clean_company_name(raw_vessel_data.get('operator_company'))
            vessel.flag_state = raw_vessel_data.get('flag_state')
            vessel.home_port = raw_vessel_data.get('home_port')
            
            # Status and availability
            vessel.availability_status = self._standardize_availability(
                raw_vessel_data.get('current_status', raw_vessel_data.get('availability_status', 'unknown'))
            )
            vessel.current_location = raw_vessel_data.get('current_location')
            vessel.day_rate_usd = self._safe_float(raw_vessel_data.get('day_rate_usd'))
            
            # Media
            vessel.photos = raw_vessel_data.get('photos', [])
            if vessel.photos:
                vessel.primary_photo_url = vessel.photos[0]
            
            vessel.specification_sheets = raw_vessel_data.get('spec_sheets', [])
            
            # Data quality
            vessel.data_quality_score = raw_vessel_data.get('data_quality_score', 0.0)
            
            return vessel
            
        except Exception as e:
            self.logger.error(f"Failed to process vessel data: {e}")
            raise
    
    def _clean_vessel_name(self, name: str) -> str:
        """Clean and standardize vessel name"""
        if not name:
            return ""
        
        # Remove common prefixes
        name = re.sub(r'^(m\.?v\.?|m\.?s\.?|m\.?t\.?)\s*', '', name, flags=re.IGNORECASE)
        
        # Clean up spacing and capitalization
        name = ' '.join(name.split())
        name = name.title()
        
        return name
    
    def _standardize_vessel_type(self, vessel_type: str) -> str:
        """Standardize vessel type for marketplace"""
        if not vessel_type:
            return "Offshore Support Vessel"
        
        vessel_type_lower = vessel_type.lower()
        
        for key, standard_type in self.VESSEL_TYPE_MAPPING.items():
            if key in vessel_type_lower:
                return standard_type
        
        return vessel_type.title()
    
    def _standardize_availability(self, status: str) -> str:
        """Standardize availability status"""
        if not status:
            return "unknown"
        
        status_lower = status.lower()
        
        for key, standard_status in self.AVAILABILITY_STATUS_MAPPING.items():
            if key in status_lower:
                return standard_status
        
        return "unknown"
    
    def _clean_company_name(self, name: str) -> Optional[str]:
        """Clean company name"""
        if not name:
            return None
        
        # Remove common company suffixes for cleaning
        name = name.strip()
        return name if name else None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Remove commas and other non-numeric characters except decimal point
                cleaned = re.sub(r'[^\d.]', '', value)
                return float(cleaned) if cleaned else None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                cleaned = re.sub(r'[^\d]', '', value)
                return int(cleaned) if cleaned else None
            return int(value)
        except (ValueError, TypeError):
            return None

class MarketplaceSync:
    """Handles synchronization with marketplace database"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_client = create_client(supabase_url, supabase_key)
        self.logger = logging.getLogger(__name__)
        self.processor = MarketplaceDataProcessor()
    
    async def sync_vessel_data(self, raw_vessel_data: List[Dict]) -> Dict[str, Any]:
        """Sync vessel data to marketplace"""
        results = {
            'total_processed': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'updated_vessels': 0,
            'new_vessels': 0,
            'errors': []
        }
        
        for vessel_data in raw_vessel_data:
            try:
                # Process vessel data
                marketplace_vessel = self.processor.process_vessel_data(vessel_data)
                
                # Sync to marketplace
                success, is_new = await self._sync_single_vessel(marketplace_vessel)
                
                results['total_processed'] += 1
                
                if success:
                    results['successful_syncs'] += 1
                    if is_new:
                        results['new_vessels'] += 1
                    else:
                        results['updated_vessels'] += 1
                else:
                    results['failed_syncs'] += 1
                
            except Exception as e:
                error_msg = f"Failed to sync vessel {vessel_data.get('vessel_name', 'Unknown')}: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed_syncs'] += 1
        
        return results
    
    async def _sync_single_vessel(self, vessel: MarketplaceVessel) -> Tuple[bool, bool]:
        """Sync a single vessel to marketplace"""
        try:
            # Check if vessel already exists
            existing_vessel = await self._find_existing_vessel(vessel)
            
            if existing_vessel:
                # Update existing vessel
                success = await self._update_existing_vessel(existing_vessel, vessel)
                return success, False
            else:
                # Create new vessel
                success = await self._create_new_vessel(vessel)
                return success, True
                
        except Exception as e:
            self.logger.error(f"Failed to sync vessel {vessel.vessel_name}: {e}")
            return False, False
    
    async def _find_existing_vessel(self, vessel: MarketplaceVessel) -> Optional[Dict]:
        """Find existing vessel in marketplace"""
        try:
            # First try to find by IMO (most reliable)
            if vessel.imo_number:
                result = self.supabase_client.table('vessels')\
                    .select('*')\
                    .eq('imo_number', vessel.imo_number)\
                    .execute()
                
                if result.data:
                    return result.data[0]
            
            # Try by MMSI
            if vessel.mmsi_number:
                result = self.supabase_client.table('vessels')\
                    .select('*')\
                    .eq('mmsi_number', vessel.mmsi_number)\
                    .execute()
                
                if result.data:
                    return result.data[0]
            
            # Try by vessel name and owner (fuzzy match)
            if vessel.vessel_name and vessel.owner_company:
                result = self.supabase_client.table('vessels')\
                    .select('*')\
                    .eq('vessel_name', vessel.vessel_name)\
                    .eq('owner_company', vessel.owner_company)\
                    .execute()
                
                if result.data:
                    return result.data[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding existing vessel: {e}")
            return None
    
    async def _update_existing_vessel(self, existing: Dict, new_vessel: MarketplaceVessel) -> bool:
        """Update existing vessel with new data"""
        try:
            # Merge data intelligently
            updated_data = self._merge_vessel_data(existing, new_vessel)
            
            # Update in database
            result = self.supabase_client.table('vessels')\
                .update(updated_data)\
                .eq('id', existing['id'])\
                .execute()
            
            if result.data:
                self.logger.info(f"Updated vessel: {new_vessel.vessel_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update vessel {new_vessel.vessel_name}: {e}")
            return False
    
    async def _create_new_vessel(self, vessel: MarketplaceVessel) -> bool:
        """Create new vessel in marketplace"""
        try:
            vessel_data = asdict(vessel)
            
            # Remove None values
            vessel_data = {k: v for k, v in vessel_data.items() if v is not None}
            
            result = self.supabase_client.table('vessels')\
                .insert(vessel_data)\
                .execute()
            
            if result.data:
                self.logger.info(f"Created new vessel: {vessel.vessel_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create vessel {vessel.vessel_name}: {e}")
            return False
    
    def _merge_vessel_data(self, existing: Dict, new_vessel: MarketplaceVessel) -> Dict:
        """Merge existing and new vessel data intelligently"""
        merged = existing.copy()
        new_data = asdict(new_vessel)
        
        # Always update these fields
        always_update = ['updated_at', 'current_location', 'availability_status']
        
        # Update if better data quality
        quality_dependent = [
            'vessel_name', 'vessel_type', 'length_overall_m', 'beam_m',
            'gross_tonnage', 'build_year', 'accommodation_persons'
        ]
        
        # Only add if missing
        fill_missing = [
            'imo_number', 'mmsi_number', 'flag_state', 'owner_company',
            'operator_company', 'home_port'
        ]
        
        for field in always_update:
            if new_data.get(field):
                merged[field] = new_data[field]
        
        # Update if new data has better quality score
        new_quality = new_data.get('data_quality_score', 0)
        existing_quality = existing.get('data_quality_score', 0)
        
        if new_quality > existing_quality:
            for field in quality_dependent:
                if new_data.get(field):
                    merged[field] = new_data[field]
        
        # Fill missing fields
        for field in fill_missing:
            if not merged.get(field) and new_data.get(field):
                merged[field] = new_data[field]
        
        # Merge photos (avoid duplicates)
        existing_photos = set(merged.get('photos', []))
        new_photos = set(new_data.get('photos', []))
        merged['photos'] = list(existing_photos | new_photos)
        
        # Update primary photo if we don't have one
        if not merged.get('primary_photo_url') and merged['photos']:
            merged['primary_photo_url'] = merged['photos'][0]
        
        return merged
    
    async def create_marketplace_listing(self, vessel_id: str, listing_data: Dict) -> bool:
        """Create a marketplace listing for a vessel"""
        try:
            listing = {
                'vessel_id': vessel_id,
                'listing_type': listing_data.get('type', 'charter'),
                'title': listing_data.get('title', ''),
                'description': listing_data.get('description', ''),
                'price_usd': listing_data.get('price'),
                'price_type': listing_data.get('price_type', 'day_rate'),
                'available_from': listing_data.get('available_from'),
                'available_until': listing_data.get('available_until'),
                'contact_company_id': listing_data.get('contact_company_id'),
                'contact_person': listing_data.get('contact_person'),
                'contact_email': listing_data.get('contact_email'),
                'contact_phone': listing_data.get('contact_phone'),
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase_client.table('vessel_listings')\
                .insert(listing)\
                .execute()
            
            if result.data:
                self.logger.info(f"Created marketplace listing for vessel {vessel_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create marketplace listing: {e}")
            return False
    
    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get current marketplace statistics"""
        try:
            stats = {}
            
            # Total vessels
            vessels_result = self.supabase_client.table('vessels').select('id, data_quality_score, availability_status').execute()
            stats['total_vessels'] = len(vessels_result.data)
            
            # Available vessels
            available_vessels = [v for v in vessels_result.data if v.get('availability_status') == 'available']
            stats['available_vessels'] = len(available_vessels)
            
            # Average data quality
            quality_scores = [v.get('data_quality_score', 0) for v in vessels_result.data if v.get('data_quality_score')]
            stats['avg_data_quality'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Active listings
            listings_result = self.supabase_client.table('vessel_listings').select('id').eq('status', 'active').execute()
            stats['active_listings'] = len(listings_result.data)
            
            # Vessel types breakdown
            vessel_types = {}
            for vessel in vessels_result.data:
                vessel_type = vessel.get('vessel_type', 'Unknown')
                vessel_types[vessel_type] = vessel_types.get(vessel_type, 0) + 1
            stats['vessel_types'] = vessel_types
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get marketplace stats: {e}")
            return {}

class MarketplaceIntegrationManager:
    """Main manager for marketplace integration"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.marketplace_sync = MarketplaceSync(supabase_url, supabase_key)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize the marketplace integration manager"""
        try:
            self.logger.info("🔧 Initializing marketplace integration manager...")
            # Test database connection
            stats = await self.marketplace_sync.get_marketplace_stats()
            self.logger.info("✅ Marketplace integration manager initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize marketplace manager: {e}")
            return False
    
    async def full_integration_cycle(self) -> Dict[str, Any]:
        """Run complete integration cycle from crawler data to marketplace"""
        self.logger.info("🚀 Starting marketplace integration cycle")
        
        try:
            # Get latest vessel data from crawler
            vessel_data = await self._get_crawler_data()
            
            if not vessel_data:
                self.logger.warning("No vessel data found from crawler")
                return {'status': 'no_data'}
            
            # Sync to marketplace
            sync_results = await self.marketplace_sync.sync_vessel_data(vessel_data)
            
            # Get updated marketplace stats
            marketplace_stats = await self.marketplace_sync.get_marketplace_stats()
            
            # Generate summary report
            report = {
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat(),
                'sync_results': sync_results,
                'marketplace_stats': marketplace_stats,
                'summary': self._generate_summary(sync_results, marketplace_stats)
            }
            
            self.logger.info(f"✅ Integration cycle completed: {report['summary']}")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Integration cycle failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _get_crawler_data(self) -> List[Dict]:
        """Get latest vessel data from crawler database"""
        try:
            # Get vessels from last 24 hours or all vessels if none recent
            cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            result = self.marketplace_sync.supabase_client.table('vessels')\
                .select('*')\
                .gte('updated_at', cutoff_time)\
                .execute()
            
            if not result.data:
                # Get all vessels if no recent updates
                result = self.marketplace_sync.supabase_client.table('vessels')\
                    .select('*')\
                    .limit(1000)\
                    .execute()
            
            return result.data
            
        except Exception as e:
            self.logger.error(f"Failed to get crawler data: {e}")
            return []
    
    def _generate_summary(self, sync_results: Dict, marketplace_stats: Dict) -> str:
        """Generate human-readable summary"""
        return (
            f"Processed {sync_results['total_processed']} vessels, "
            f"{sync_results['new_vessels']} new, "
            f"{sync_results['updated_vessels']} updated. "
            f"Marketplace now has {marketplace_stats.get('total_vessels', 0)} vessels "
            f"with {marketplace_stats.get('available_vessels', 0)} available."
        )

async def main():
    """Test marketplace integration"""
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    supabase_url = "https://juvqqrsdbruskleodzip.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw"
    
    manager = MarketplaceIntegrationManager(supabase_url, supabase_key)
    
    print("🔄 Running marketplace integration test...")
    
    try:
        results = await manager.full_integration_cycle()
        
        print("\n✅ Integration Results:")
        print(f"   Status: {results['status']}")
        if results.get('summary'):
            print(f"   Summary: {results['summary']}")
        
        if results.get('sync_results'):
            sync = results['sync_results']
            print(f"   Sync Details:")
            print(f"     - Total processed: {sync['total_processed']}")
            print(f"     - New vessels: {sync['new_vessels']}")
            print(f"     - Updated vessels: {sync['updated_vessels']}")
            print(f"     - Failed syncs: {sync['failed_syncs']}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
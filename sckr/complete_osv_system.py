#!/usr/bin/env python3
"""
Complete OSV Discovery System Integration
Orchestrates all components for comprehensive vessel data collection
"""

import os
import sys
import json
import time
import logging
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Import all our modules
from mosva_vessel_discovery import (
    OrchestrationEngine, SupabaseManager, MOSVADataParser,
    CompanyData, VesselRecord
)
from vessel_media_collector import (
    VesselMediaCollector, VesselSpecificationParser, 
    ReliableSourceManager, MediaResult
)

# Configuration
class OSVSystemConfig:
    """Complete system configuration"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.data_dir = self.base_dir / "osv_data"
        self.logs_dir = self.base_dir / "logs" 
        self.media_dir = self.base_dir / "vessel_media"
        self.cache_dir = self.base_dir / "cache"
        
        # Create directories
        for directory in [self.data_dir, self.logs_dir, self.media_dir, self.cache_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crawler settings
        self.max_workers = 4
        self.rate_limit_delay = 1.5
        self.enable_media_collection = True
        self.enable_specification_parsing = True
        self.max_photos_per_vessel = 5
        self.download_documents = True
        
        # Database settings
        self.supabase_url = "https://juvqqrsdbruskleodzip.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw"
        
        # MOSVA data files
        self.ordinary_members_file = "mosva_ordinarymembers.json"
        self.associate_members_file = "mosva_associate-member.json"

class ComprehensiveVesselDiscovery:
    """Main system that orchestrates all components"""
    
    def __init__(self, config: OSVSystemConfig):
        self.config = config
        self.setup_logging()
        
        # Initialize components
        self.supabase_manager = None
        self.orchestration_engine = None
        self.media_collector = None
        self.spec_parser = VesselSpecificationParser()
        self.source_manager = ReliableSourceManager()
        
        # Statistics
        self.session_stats = {
            'session_id': None,
            'companies_processed': 0,
            'vessels_discovered': 0,
            'vessels_enriched': 0,
            'media_collected': 0,
            'specifications_extracted': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.config.logs_dir / f"osv_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🚀 OSV Discovery System initialized - Log: {log_file}")
    
    async def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("🔧 Initializing system components...")
            
            # Initialize Supabase
            try:
                self.supabase_manager = SupabaseManager()
                self.logger.info("✅ Supabase connected")
            except Exception as e:
                self.logger.error(f"❌ Supabase initialization failed: {e}")
                return False
            
            # Initialize orchestration engine
            self.orchestration_engine = OrchestrationEngine(self.supabase_manager)
            
            # Initialize media collector
            self.media_collector = VesselMediaCollector(str(self.config.media_dir))
            
            # Create session record
            session_data = {
                'session_type': 'comprehensive_discovery',
                'status': 'running',
                'config': asdict(self.config),
                'started_at': datetime.utcnow().isoformat()
            }
            
            # Record session in database
            result = self.supabase_manager.client.table('crawl_sessions').insert(session_data).execute()
            if result.data:
                self.session_stats['session_id'] = result.data[0]['id']
                self.logger.info(f"📊 Session {self.session_stats['session_id']} started")
            
            self.logger.info("✅ All components initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def run_comprehensive_discovery(self) -> Dict[str, Any]:
        """Run complete vessel discovery with media collection"""
        self.session_stats['start_time'] = datetime.utcnow()
        
        try:
            # Phase 1: Basic vessel discovery
            self.logger.info("📋 Phase 1: Basic vessel discovery from MOSVA data")
            basic_results = await self._run_basic_discovery()
            
            # Phase 2: Enhanced data collection
            self.logger.info("🔍 Phase 2: Enhanced media and specification collection")
            enhancement_results = await self._run_enhancement_phase()
            
            # Phase 3: Data validation and cleanup
            self.logger.info("🧹 Phase 3: Data validation and cleanup")
            validation_results = await self._run_validation_phase()
            
            # Finalize session
            await self._finalize_session()
            
            return {
                'basic_discovery': basic_results,
                'enhancement': enhancement_results,
                'validation': validation_results,
                'session_stats': self.session_stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Discovery failed: {e}")
            self.session_stats['errors'].append(str(e))
            await self._finalize_session('failed')
            raise
    
    async def _run_basic_discovery(self) -> Dict[str, Any]:
        """Phase 1: Basic vessel discovery"""
        try:
            # Use existing orchestration engine
            results = self.orchestration_engine.run_full_discovery()
            
            self.session_stats['companies_processed'] = results['companies_processed']
            self.session_stats['vessels_discovered'] = results['vessels_found']
            
            return results
            
        except Exception as e:
            self.logger.error(f"Basic discovery failed: {e}")
            raise
    
    async def _run_enhancement_phase(self) -> Dict[str, Any]:
        """Phase 2: Enhanced media and specification collection"""
        enhancement_stats = {
            'vessels_processed': 0,
            'media_collected': 0,
            'specifications_extracted': 0,
            'errors': 0
        }
        
        try:
            # Get all vessels from database
            vessels_result = self.supabase_manager.client.table('vessels').select('*').execute()
            
            if not vessels_result.data:
                self.logger.warning("No vessels found in database for enhancement")
                return enhancement_stats
            
            vessels = vessels_result.data
            self.logger.info(f"🚢 Processing {len(vessels)} vessels for enhancement")
            
            # Process vessels in batches
            batch_size = 5
            for i in range(0, len(vessels), batch_size):
                batch = vessels[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [self._enhance_single_vessel(vessel) for vessel in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        enhancement_stats['errors'] += 1
                        self.logger.error(f"Vessel enhancement error: {result}")
                    elif result:
                        enhancement_stats['vessels_processed'] += 1
                        enhancement_stats['media_collected'] += result.get('media_count', 0)
                        enhancement_stats['specifications_extracted'] += result.get('specs_count', 0)
                
                # Rate limiting between batches
                await asyncio.sleep(self.config.rate_limit_delay)
                
                # Update progress
                progress = ((i + batch_size) / len(vessels)) * 100
                self.logger.info(f"📈 Enhancement progress: {progress:.1f}%")
            
            self.session_stats['vessels_enriched'] = enhancement_stats['vessels_processed']
            self.session_stats['media_collected'] = enhancement_stats['media_collected']
            self.session_stats['specifications_extracted'] = enhancement_stats['specifications_extracted']
            
            return enhancement_stats
            
        except Exception as e:
            self.logger.error(f"Enhancement phase failed: {e}")
            raise
    
    async def _enhance_single_vessel(self, vessel_data: Dict) -> Optional[Dict]:
        """Enhance a single vessel with media and specifications"""
        try:
            vessel_id = vessel_data['id']
            vessel_name = vessel_data.get('vessel_name', 'Unknown')
            
            self.logger.info(f"🔍 Enhancing vessel: {vessel_name}")
            
            results = {'media_count': 0, 'specs_count': 0}
            
            # Collect media
            if self.config.enable_media_collection:
                media_results = await self.media_collector.collect_vessel_media(
                    vessel_data, 
                    max_photos=self.config.max_photos_per_vessel
                )
                
                # Save media to database
                for media in media_results:
                    media_record = {
                        'vessel_id': vessel_id,
                        'media_type': media.media_type,
                        'title': media.title,
                        'description': media.description,
                        'original_url': media.url,
                        'local_path': media.local_path,
                        'file_size': media.file_size,
                        'file_format': media.file_format,
                        'source': media.source,
                        'confidence_score': media.confidence_score,
                        'extracted_text': media.extracted_text
                    }
                    
                    try:
                        self.supabase_manager.client.table('vessel_media').insert(media_record).execute()
                        results['media_count'] += 1
                    except Exception as e:
                        self.logger.error(f"Failed to save media for {vessel_name}: {e}")
            
            # Extract specifications from documents
            if self.config.enable_specification_parsing:
                # Get documents for this vessel
                docs_result = self.supabase_manager.client.table('vessel_media')\
                    .select('*')\
                    .eq('vessel_id', vessel_id)\
                    .in_('media_type', ['specification', 'brochure', 'manual'])\
                    .execute()
                
                for doc in docs_result.data:
                    if doc.get('extracted_text'):
                        # Parse specifications
                        specifications = self.spec_parser.parse_specifications(doc['extracted_text'])
                        features = self.spec_parser.extract_vessel_features(doc['extracted_text'])
                        
                        if specifications:
                            # Save specifications
                            spec_record = {
                                'vessel_id': vessel_id,
                                'media_id': doc['id'],
                                'specifications': specifications,
                                'source_document': doc['title'],
                                'extraction_method': 'automated_parsing',
                                'confidence_score': 0.8
                            }
                            
                            try:
                                self.supabase_manager.client.table('vessel_specifications')\
                                    .insert(spec_record).execute()
                                results['specs_count'] += 1
                            except Exception as e:
                                self.logger.error(f"Failed to save specifications for {vessel_name}: {e}")
                        
                        # Save features
                        for feature in features:
                            feature_record = {
                                'vessel_id': vessel_id,
                                'feature_name': feature,
                                'feature_category': 'capability',
                                'confidence_score': 0.7,
                                'source_type': 'extracted'
                            }
                            
                            try:
                                self.supabase_manager.client.table('vessel_features')\
                                    .upsert(feature_record).execute()
                            except Exception as e:
                                self.logger.debug(f"Feature save error for {vessel_name}: {e}")
            
            self.logger.info(f"✅ Enhanced {vessel_name}: {results['media_count']} media, {results['specs_count']} specs")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to enhance vessel {vessel_data.get('vessel_name', 'Unknown')}: {e}")
            return None
    
    async def _run_validation_phase(self) -> Dict[str, Any]:
        """Phase 3: Data validation and cleanup"""
        validation_stats = {
            'vessels_validated': 0,
            'duplicates_merged': 0,
            'data_quality_improved': 0
        }
        
        try:
            # Validate vessel data quality
            vessels_result = self.supabase_manager.client.table('vessels').select('*').execute()
            
            for vessel in vessels_result.data:
                try:
                    # Calculate data quality score
                    quality_score = self._calculate_vessel_quality_score(vessel)
                    
                    # Update vessel with quality score
                    self.supabase_manager.client.table('vessels')\
                        .update({'data_quality_score': quality_score})\
                        .eq('id', vessel['id'])\
                        .execute()
                    
                    validation_stats['vessels_validated'] += 1
                    
                    if quality_score > vessel.get('data_quality_score', 0):
                        validation_stats['data_quality_improved'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Validation error for vessel {vessel.get('vessel_name')}: {e}")
            
            # TODO: Implement duplicate detection and merging
            # TODO: Implement data consistency checks
            
            return validation_stats
            
        except Exception as e:
            self.logger.error(f"Validation phase failed: {e}")
            raise
    
    def _calculate_vessel_quality_score(self, vessel: Dict) -> float:
        """Calculate data quality score for a vessel"""
        score = 0.0
        max_score = 0.0
        
        # Essential fields (high weight)
        essential_fields = [
            ('vessel_name', 0.15),
            ('imo_number', 0.15),
            ('vessel_type', 0.10),
            ('owner_company', 0.10)
        ]
        
        for field, weight in essential_fields:
            max_score += weight
            if vessel.get(field):
                score += weight
        
        # Important fields (medium weight)
        important_fields = [
            ('build_year', 0.08),
            ('length_overall_m', 0.08),
            ('gross_tonnage', 0.08),
            ('flag_state', 0.06)
        ]
        
        for field, weight in important_fields:
            max_score += weight
            if vessel.get(field):
                score += weight
        
        # Desirable fields (low weight)
        desirable_fields = [
            ('mmsi_number', 0.04),
            ('beam_m', 0.04),
            ('main_engine_power_kw', 0.04),
            ('accommodation_persons', 0.04),
            ('current_status', 0.04)
        ]
        
        for field, weight in desirable_fields:
            max_score += weight
            if vessel.get(field):
                score += weight
        
        # Normalize to 0-1 scale
        return min(score / max_score, 1.0) if max_score > 0 else 0.0
    
    async def _finalize_session(self, status: str = 'completed'):
        """Finalize the discovery session"""
        self.session_stats['end_time'] = datetime.utcnow()
        duration = (self.session_stats['end_time'] - self.session_stats['start_time']).total_seconds()
        
        # Update session in database
        if self.session_stats['session_id']:
            update_data = {
                'status': status,
                'companies_processed': self.session_stats['companies_processed'],
                'vessels_found': self.session_stats['vessels_discovered'],
                'vessels_updated': self.session_stats['vessels_enriched'],
                'media_collected': self.session_stats['media_collected'],
                'errors_count': len(self.session_stats['errors']),
                'completed_at': self.session_stats['end_time'].isoformat(),
                'duration_seconds': int(duration),
                'results': self.session_stats,
                'error_log': self.session_stats['errors']
            }
            
            try:
                self.supabase_manager.client.table('crawl_sessions')\
                    .update(update_data)\
                    .eq('id', self.session_stats['session_id'])\
                    .execute()
            except Exception as e:
                self.logger.error(f"Failed to update session: {e}")
        
        self.logger.info(f"🎉 Session finalized with status: {status}")

async def run_discovery_system(config: OSVSystemConfig) -> Dict[str, Any]:
    """Main function to run the complete discovery system"""
    system = ComprehensiveVesselDiscovery(config)
    
    # Initialize system
    if not await system.initialize_system():
        raise RuntimeError("System initialization failed")
    
    # Run comprehensive discovery
    results = await system.run_comprehensive_discovery()
    
    return results

def create_sample_mosva_files():
    """Create sample MOSVA files if they don't exist"""
    ordinary_sample = {
        "markdown": "**Alam Maritim (M) Sdn Bhd**\n\nNo. 38F, Level 2, Jalan Radin Anum,\nBandar Baru Sri Petaling,\n57000 Kuala Lumpur, Malaysia\nTel: +603-90582244\nFax: +603-90596845\n[www.alam-maritim.com.my](http://www.alam-maritim.com.my/)\n\n**Icon Offshore Berhad**\n\n16-01, Level 16, Menara Tan & Tan,\n207, Jalan Tun Razak,\n50450 Kuala Lumpur, Malaysia\nTel: +603-27700500\nFax: +603-27700600\n[www.iconoffshore.com.my](http://www.iconoffshore.com.my/)",
        "metadata": {"title": "ordinary members | MOSVA"}
    }
    
    associate_sample = {
        "markdown": "**ABS Classification Malaysia Sdn. Bhd.**\n\n27.01, 27th Floor, Menara Multi-Purpose,\nNo.8 Jalan Munshi Abdullah,\n50100 Kuala Lumpur, Malaysia\nTel: +603-26912885/2886\nFax: +603-26912872/2873\n[www.ww2.eagle.org](http://www.ww2.eagle.org/)",
        "metadata": {"title": "associate member | MOSVA"}
    }
    
    if not os.path.exists("mosva_ordinarymembers.json"):
        with open("mosva_ordinarymembers.json", 'w') as f:
            json.dump(ordinary_sample, f, indent=2)
        print("📄 Created sample mosva_ordinarymembers.json")
    
    if not os.path.exists("mosva_associate-member.json"):
        with open("mosva_associate-member.json", 'w') as f:
            json.dump(associate_sample, f, indent=2)
        print("📄 Created sample mosva_associate-member.json")

def main():
    """Main entry point with CLI interface"""
    parser = argparse.ArgumentParser(description="Comprehensive OSV Discovery System")
    parser.add_argument("--mode", choices=['discovery', 'setup', 'test'], default='discovery',
                       help="Operation mode")
    parser.add_argument("--max-workers", type=int, default=4,
                       help="Maximum worker threads")
    parser.add_argument("--no-media", action="store_true",
                       help="Disable media collection")
    parser.add_argument("--no-specs", action="store_true", 
                       help="Disable specification parsing")
    parser.add_argument("--max-photos", type=int, default=5,
                       help="Maximum photos per vessel")
    parser.add_argument("--rate-limit", type=float, default=1.5,
                       help="Rate limit delay in seconds")
    
    args = parser.parse_args()
    
    # Setup configuration
    config = OSVSystemConfig()
    config.max_workers = args.max_workers
    config.rate_limit_delay = args.rate_limit
    config.enable_media_collection = not args.no_media
    config.enable_specification_parsing = not args.no_specs
    config.max_photos_per_vessel = args.max_photos
    
    if args.mode == 'setup':
        print("🔧 Setting up OSV Discovery System...")
        create_sample_mosva_files()
        print("✅ Setup complete!")
        return
    
    elif args.mode == 'test':
        print("🧪 Running system tests...")
        # Add test functionality here
        return
    
    # Run discovery
    print("🚀 Starting Comprehensive OSV Discovery System")
    print("=" * 60)
    
    try:
        results = asyncio.run(run_discovery_system(config))
        
        print("\n" + "=" * 60)
        print("🎉 Discovery Complete!")
        print("=" * 60)
        print(f"📊 Session Statistics:")
        print(f"   Companies processed: {results['session_stats']['companies_processed']}")
        print(f"   Vessels discovered: {results['session_stats']['vessels_discovered']}")
        print(f"   Vessels enriched: {results['session_stats']['vessels_enriched']}")
        print(f"   Media collected: {results['session_stats']['media_collected']}")
        print(f"   Specifications extracted: {results['session_stats']['specifications_extracted']}")
        
        if results['session_stats']['errors']:
            print(f"\n⚠️ Errors encountered: {len(results['session_stats']['errors'])}")
            for error in results['session_stats']['errors'][:3]:
                print(f"   • {error}")
        
        duration = (results['session_stats']['end_time'] - results['session_stats']['start_time']).total_seconds()
        print(f"\n⏱️ Total duration: {duration/60:.1f} minutes")
        
    except KeyboardInterrupt:
        print("\n⏹️ Discovery interrupted by user")
    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")
        raise

if __name__ == "__main__":
    main()
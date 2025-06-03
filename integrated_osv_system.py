#!/usr/bin/env python3
"""
Integrated OSV Discovery System - Master Orchestrator
Seamlessly integrates all /sckr modules into a unified, comprehensive system
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add sckr directory to Python path
sys.path.append(str(Path(__file__).parent / "sckr"))

# Import all system modules
from sckr.complete_osv_system import ComprehensiveVesselDiscovery, OSVSystemConfig
from sckr.mosva_vessel_discovery import OrchestrationEngine, SupabaseManager, MOSVADataParser
from sckr.vessel_media_collector import VesselMediaCollector, VesselSpecificationParser, ReliableSourceManager
from sckr.real_time_dashboard import OSVDashboard, DashboardStats
from sckr.advanced_imo_search import AdvancedIMOSearchEngine
from sckr.marketplace_integration import MarketplaceIntegrationManager, MarketplaceDataProcessor
from sckr.deployment_manager import OSVSystemDeployment

@dataclass
class SystemStatus:
    """Overall system status"""
    components: Dict[str, str]
    database_status: str
    last_crawl: Optional[str]
    total_vessels: int
    total_companies: int
    system_health: str
    uptime: str

class IntegratedOSVSystem:
    """Master orchestrator for the complete OSV Discovery System"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.setup_logging()
        self.config = OSVSystemConfig()
        
        # Initialize all system components
        self.components = {}
        self.system_status = SystemStatus(
            components={},
            database_status="unknown",
            last_crawl=None,
            total_vessels=0,
            total_companies=0,
            system_health="unknown",
            uptime="0s"
        )
        
        self.start_time = datetime.utcnow()
        self.is_running = False
        
    def setup_logging(self):
        """Setup comprehensive system logging"""
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"integrated_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 Integrated OSV System Starting...")
    
    async def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("🔧 Initializing all system components...")
            
            # Initialize database manager
            self.logger.info("📊 Initializing database manager...")
            self.components['database'] = SupabaseManager()
            self.system_status.components['database'] = 'connected'
            
            # Initialize vessel discovery
            self.logger.info("🚢 Initializing vessel discovery system...")
            self.components['vessel_discovery'] = ComprehensiveVesselDiscovery(self.config)
            await self.components['vessel_discovery'].initialize_system()
            self.system_status.components['vessel_discovery'] = 'ready'
            
            # Initialize media collector
            self.logger.info("📸 Initializing media collector...")
            self.components['media_collector'] = VesselMediaCollector()
            self.system_status.components['media_collector'] = 'ready'
            
            # Initialize IMO search engine
            self.logger.info("🔍 Initializing IMO search engine...")
            self.components['imo_search'] = AdvancedIMOSearchEngine()
            self.system_status.components['imo_search'] = 'ready'
            
            # Initialize marketplace integration
            self.logger.info("🏪 Initializing marketplace integration...")
            self.components['marketplace'] = MarketplaceIntegrationManager(
                self.config.supabase_url, 
                self.config.supabase_key
            )
            await self.components['marketplace'].initialize()
            self.system_status.components['marketplace'] = 'ready'
            
            # Initialize dashboard
            self.logger.info("📊 Initializing real-time dashboard...")
            self.components['dashboard'] = OSVDashboard()
            self.system_status.components['dashboard'] = 'ready'
            
            # Initialize specification parser
            self.logger.info("📄 Initializing specification parser...")
            self.components['spec_parser'] = VesselSpecificationParser()
            self.system_status.components['spec_parser'] = 'ready'
            
            self.system_status.system_health = 'healthy'
            self.is_running = True
            
            self.logger.info("✅ All system components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            self.system_status.system_health = 'error'
            return False
    
    async def run_comprehensive_discovery(self, enable_media: bool = True, enable_imo_search: bool = True) -> Dict[str, Any]:
        """Run complete vessel discovery with all components"""
        self.logger.info("🌊 Starting comprehensive OSV discovery process...")
        
        results = {
            'discovery_session': None,
            'vessels_processed': 0,
            'media_collected': 0,
            'imo_enrichment': 0,
            'marketplace_sync': 0,
            'errors': [],
            'duration': None
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Phase 1: Core vessel discovery
            self.logger.info("📋 Phase 1: Core vessel discovery")
            discovery_results = await self.components['vessel_discovery'].run_comprehensive_discovery()
            results['discovery_session'] = discovery_results['session_stats']
            results['vessels_processed'] = discovery_results['session_stats']['vessels_discovered']
            
            # Phase 2: Enhanced media collection
            if enable_media:
                self.logger.info("📸 Phase 2: Enhanced media collection")
                await self._run_media_collection_phase(results)
            
            # Phase 3: IMO-based enrichment
            if enable_imo_search:
                self.logger.info("🔍 Phase 3: IMO-based vessel enrichment")
                await self._run_imo_enrichment_phase(results)
            
            # Phase 4: Marketplace synchronization
            self.logger.info("🏪 Phase 4: Marketplace synchronization")
            await self._run_marketplace_sync_phase(results)
            
            # Update system status
            await self._update_system_status()
            
            results['duration'] = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"✅ Comprehensive discovery completed in {results['duration']:.1f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive discovery failed: {e}")
            results['errors'].append(str(e))
            return results
    
    async def _run_media_collection_phase(self, results: Dict):
        """Run media collection for all vessels"""
        try:
            # Get all vessels from database
            vessels_result = self.components['database'].client.table('vessels').select('*').execute()
            
            if not vessels_result.data:
                self.logger.warning("No vessels found for media collection")
                return
            
            vessels = vessels_result.data
            self.logger.info(f"🔄 Processing {len(vessels)} vessels for media collection")
            
            for vessel in vessels[:10]:  # Limit for demo
                try:
                    vessel_data = dict(vessel)
                    media_results = await self.components['media_collector'].collect_vessel_media(
                        vessel_data, max_photos=3
                    )
                    
                    # Save media to database
                    for media in media_results:
                        media_record = {
                            'vessel_id': vessel['id'],
                            'media_type': media.media_type,
                            'title': media.title,
                            'description': media.description,
                            'original_url': media.url,
                            'local_path': media.local_path,
                            'source': media.source,
                            'confidence_score': media.confidence_score
                        }
                        
                        self.components['database'].client.table('vessel_media').insert(media_record).execute()
                        results['media_collected'] += 1
                    
                    self.logger.info(f"📸 Collected {len(media_results)} media items for {vessel_data.get('vessel_name', 'Unknown')}")
                    
                except Exception as e:
                    self.logger.error(f"Media collection failed for vessel {vessel.get('vessel_name')}: {e}")
                    results['errors'].append(f"Media collection: {e}")
                
                # Rate limiting
                await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Media collection phase failed: {e}")
            results['errors'].append(f"Media collection phase: {e}")
    
    async def _run_imo_enrichment_phase(self, results: Dict):
        """Run IMO-based vessel enrichment"""
        try:
            # Get vessels with IMO numbers
            vessels_result = self.components['database'].client.table('vessels')\
                .select('*')\
                .not_.is_('imo_number', 'null')\
                .limit(5)\
                .execute()
            
            if not vessels_result.data:
                self.logger.warning("No vessels with IMO numbers found for enrichment")
                return
            
            vessels = vessels_result.data
            self.logger.info(f"🔄 Processing {len(vessels)} vessels for IMO enrichment")
            
            for vessel in vessels:
                try:
                    imo = vessel.get('imo_number')
                    if not imo:
                        continue
                    
                    # Search for additional vessel data
                    imo_result = await self.components['imo_search'].search_by_imo(imo)
                    
                    # Update vessel with enriched data
                    update_data = {}
                    if imo_result.flag_state and not vessel.get('flag_state'):
                        update_data['flag_state'] = imo_result.flag_state
                    if imo_result.build_year and not vessel.get('build_year'):
                        update_data['build_year'] = imo_result.build_year
                    if imo_result.gross_tonnage and not vessel.get('gross_tonnage'):
                        update_data['gross_tonnage'] = imo_result.gross_tonnage
                    
                    if update_data:
                        self.components['database'].client.table('vessels')\
                            .update(update_data)\
                            .eq('id', vessel['id'])\
                            .execute()
                        
                        results['imo_enrichment'] += 1
                        self.logger.info(f"🔍 Enriched {vessel.get('vessel_name')} with IMO data")
                    
                except Exception as e:
                    self.logger.error(f"IMO enrichment failed for {vessel.get('vessel_name')}: {e}")
                    results['errors'].append(f"IMO enrichment: {e}")
                
                # Rate limiting
                await asyncio.sleep(2)
            
        except Exception as e:
            self.logger.error(f"IMO enrichment phase failed: {e}")
            results['errors'].append(f"IMO enrichment phase: {e}")
    
    async def _run_marketplace_sync_phase(self, results: Dict):
        """Run marketplace synchronization"""
        try:
            # Run marketplace integration
            sync_results = await self.components['marketplace'].full_integration_cycle()
            
            results['marketplace_sync'] = sync_results.get('vessels_processed', 0)
            
            self.logger.info(f"🏪 Marketplace sync completed: {results['marketplace_sync']} vessels processed")
            
        except Exception as e:
            self.logger.error(f"Marketplace sync failed: {e}")
            results['errors'].append(f"Marketplace sync: {e}")
    
    async def _update_system_status(self):
        """Update overall system status"""
        try:
            # Get vessel count
            vessels_result = self.components['database'].client.table('vessels').select('id').execute()
            self.system_status.total_vessels = len(vessels_result.data) if vessels_result.data else 0
            
            # Get company count
            companies_result = self.components['database'].client.table('companies').select('id').execute()
            self.system_status.total_companies = len(companies_result.data) if companies_result.data else 0
            
            # Update uptime
            uptime = datetime.utcnow() - self.start_time
            self.system_status.uptime = f"{uptime.total_seconds():.0f}s"
            
            self.system_status.database_status = "connected"
            
        except Exception as e:
            self.logger.error(f"Failed to update system status: {e}")
            self.system_status.database_status = "error"
    
    async def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        await self._update_system_status()
        return self.system_status
    
    async def start_dashboard_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the integrated dashboard server"""
        self.logger.info(f"🌐 Starting integrated dashboard server on {host}:{port}")
        
        try:
            # Create enhanced dashboard that integrates all components
            from cli_style_dashboard import CLIDashboard
            
            dashboard = CLIDashboard()
            
            # Add enhanced endpoints for integrated system
            @dashboard.app.get("/api/integrated-status")
            async def get_integrated_status():
                status = await self.get_system_status()
                return asdict(status)
            
            @dashboard.app.post("/api/run-full-discovery")
            async def run_full_discovery():
                """Run complete discovery with all components"""
                try:
                    results = await self.run_comprehensive_discovery()
                    return {"status": "success", "results": results}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
            
            @dashboard.app.get("/api/component-health")
            async def get_component_health():
                """Get health status of all components"""
                health = {}
                for name, component in self.components.items():
                    try:
                        if hasattr(component, 'health_check'):
                            health[name] = await component.health_check()
                        else:
                            health[name] = "operational"
                    except Exception as e:
                        health[name] = f"error: {e}"
                
                return {"component_health": health}
            
            # Start the enhanced dashboard
            import uvicorn
            uvicorn.run(
                dashboard.app,
                host=host,
                port=port,
                log_level="info",
                reload=False
            )
            
        except Exception as e:
            self.logger.error(f"Dashboard server failed: {e}")
            raise
    
    def install_and_setup(self) -> bool:
        """Install and setup the complete system"""
        self.logger.info("🔧 Running complete system installation and setup...")
        
        try:
            deployment = OSVSystemDeployment()
            success = deployment.run_complete_deployment()
            
            if success:
                self.logger.info("✅ System installation completed successfully")
            else:
                self.logger.error("❌ System installation failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return False

def create_integrated_system() -> IntegratedOSVSystem:
    """Create and return the integrated system"""
    return IntegratedOSVSystem()

async def main():
    """Main entry point for the integrated system"""
    parser = argparse.ArgumentParser(description="Integrated OSV Discovery System")
    parser.add_argument("command", choices=[
        "install", "dashboard", "discovery", "status", "full-system"
    ], help="Command to run")
    parser.add_argument("--host", default="0.0.0.0", help="Dashboard host")
    parser.add_argument("--port", type=int, default=8000, help="Dashboard port")
    parser.add_argument("--enable-media", action="store_true", default=True, help="Enable media collection")
    parser.add_argument("--enable-imo", action="store_true", default=True, help="Enable IMO search")
    
    args = parser.parse_args()
    
    # Create integrated system
    system = create_integrated_system()
    
    if args.command == "install":
        print("🔧 Installing and setting up complete OSV Discovery System...")
        success = system.install_and_setup()
        if success:
            print("✅ Installation completed! Run 'python integrated_osv_system.py dashboard' to start")
        else:
            print("❌ Installation failed!")
            sys.exit(1)
    
    elif args.command == "dashboard":
        print("🌐 Starting integrated dashboard...")
        await system.initialize_system()
        await system.start_dashboard_server(args.host, args.port)
    
    elif args.command == "discovery":
        print("🚢 Starting comprehensive vessel discovery...")
        await system.initialize_system()
        results = await system.run_comprehensive_discovery(args.enable_media, args.enable_imo)
        print(f"✅ Discovery completed: {results}")
    
    elif args.command == "status":
        print("📊 Getting system status...")
        await system.initialize_system()
        status = await system.get_system_status()
        print(f"System Status: {asdict(status)}")
    
    elif args.command == "full-system":
        print("🚀 Starting complete OSV Discovery System...")
        await system.initialize_system()
        
        # Start discovery in background
        discovery_task = asyncio.create_task(
            system.run_comprehensive_discovery(args.enable_media, args.enable_imo)
        )
        
        # Start dashboard
        await system.start_dashboard_server(args.host, args.port)

if __name__ == "__main__":
    asyncio.run(main())

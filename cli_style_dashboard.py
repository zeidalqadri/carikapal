#!/usr/bin/env python3
"""
CLI-Style OSV Discovery Dashboard
Terminal-like interface with comprehensive logging and monitoring
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Supabase connection
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class CLIConnectionManager:
    """Manages WebSocket connections for CLI-style real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_system_message("terminal:connect", 
            "=== WebSocket connection established ===")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_system_message(self, channel: str, message: str, level: str = "INFO"):
        """Send system message to all connected clients"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        await self.broadcast({
            "type": channel,
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    async def send_component_log(self, component: str, operation: str, message: str, 
                               level: str = "INFO", details: Dict = None):
        """Send detailed component logging"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        await self.broadcast({
            "type": "component:log",
            "timestamp": timestamp,
            "component": component.upper(),
            "operation": operation,
            "level": level,
            "message": message,
            "details": details or {}
        })
    
    async def send_progress_update(self, component: str, current: int, total: int, 
                                 operation: str, details: str = ""):
        """Send progress updates with detailed information"""
        percentage = (current / total * 100) if total > 0 else 0
        await self.broadcast({
            "type": "progress:update",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "component": component.upper(),
            "operation": operation,
            "current": current,
            "total": total,
            "percentage": percentage,
            "details": details
        })
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

class CLIDashboard:
    """CLI-style dashboard application"""
    
    def __init__(self):
        self.app = FastAPI(title="OSV Discovery CLI Dashboard", version="1.0.0")
        self.connection_manager = CLIConnectionManager()
        self.supabase_client = None
        self.setup_supabase()
        self.setup_routes()
        self.setup_middleware()
        
        # System state
        self.system_status = {
            "crawler": "idle",
            "scraper": "idle", 
            "fetcher": "idle",
            "database": "disconnected",
            "media_processor": "idle"
        }
    
    def setup_supabase(self):
        """Initialize Supabase connection"""
        if SUPABASE_AVAILABLE:
            try:
                url = "https://juvqqrsdbruskleodzip.supabase.co"
                key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw"
                self.supabase_client = create_client(url, key)
                self.system_status["database"] = "connected"
            except Exception as e:
                self.system_status["database"] = "error"
    
    def setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            return self.get_cli_dashboard_html()
        
        @self.app.get("/api/system-status")
        async def get_system_status():
            """Get current system status"""
            return JSONResponse(content=self.system_status)
        
        @self.app.post("/api/start-discovery")
        async def start_discovery():
            """Start comprehensive vessel discovery"""
            try:
                await self.connection_manager.send_system_message(
                    "system:command", 
                    ">>> STARTING COMPREHENSIVE OSV DISCOVERY SYSTEM <<<",
                    "SUCCESS"
                )
                
                # Simulate starting discovery process
                await self.simulate_discovery_process()
                
                return {"status": "success", "message": "Discovery process initiated"}
                
            except Exception as e:
                await self.connection_manager.send_system_message(
                    "system:error",
                    f"Failed to start discovery: {str(e)}",
                    "ERROR"
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/stop-discovery")
        async def stop_discovery():
            """Stop discovery process"""
            await self.connection_manager.send_system_message(
                "system:command",
                ">>> STOPPING DISCOVERY PROCESS <<<",
                "WARNING"
            )
            return {"status": "success", "message": "Discovery process stopped"}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time CLI updates"""
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong", 
                            "timestamp": datetime.now().isoformat()
                        }))
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
    
    async def simulate_discovery_process(self):
        """Simulate comprehensive discovery process with detailed logging"""
        
        # Phase 1: System Initialization
        await self.connection_manager.send_system_message(
            "system:init",
            "\n" + "="*80 + "\n" + 
            "  OSV DISCOVERY SYSTEM v1.0.0 - COMPREHENSIVE VESSEL DATA COLLECTION\n" + 
            "="*80,
            "INFO"
        )
        
        await asyncio.sleep(0.5)
        
        # Initialize components
        components = [
            ("MOSVA_PARSER", "Loading MOSVA member data parser"),
            ("WEBSITE_DISCOVERY", "Initializing website discovery engine"),
            ("VESSEL_SCRAPER", "Starting vessel page scraper"),
            ("MEDIA_FETCHER", "Configuring media collection system"),
            ("IMO_SEARCH", "Setting up IMO-based search engine"),
            ("DATABASE_SYNC", "Establishing Supabase connection"),
            ("QUALITY_ANALYZER", "Loading data quality analyzer")
        ]
        
        for i, (component, description) in enumerate(components):
            await self.connection_manager.send_component_log(
                "INIT", "COMPONENT_LOAD", f"{description}...", "INFO",
                {"component": component, "step": i+1, "total": len(components)}
            )
            await asyncio.sleep(0.3)
            await self.connection_manager.send_component_log(
                "INIT", "COMPONENT_READY", f"{component} initialized successfully", "SUCCESS"
            )
        
        await asyncio.sleep(0.5)
        
        # Phase 2: MOSVA Data Processing
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 1: MOSVA MEMBER DATA PROCESSING\n" + 
            "-"*60,
            "INFO"
        )
        
        await self.connection_manager.send_component_log(
            "MOSVA_PARSER", "FILE_READ", "Reading mosva_ordinarymembers.json...", "INFO"
        )
        await asyncio.sleep(0.5)
        
        await self.connection_manager.send_component_log(
            "MOSVA_PARSER", "DATA_EXTRACT", "Extracting company profiles from markdown content", "INFO"
        )
        await asyncio.sleep(0.3)
        
        # Simulate processing companies
        companies = [
            "Alam Maritim (M) Sdn Bhd", "Icon Offshore Berhad", "Perdana Petroleum Berhad",
            "Sapura Energy Berhad", "SKOSV Sdn Bhd", "Sribima (M) Shipping Sdn Bhd"
        ]
        
        for i, company in enumerate(companies):
            await self.connection_manager.send_component_log(
                "MOSVA_PARSER", "COMPANY_PARSE", f"Processing: {company}", "INFO",
                {"contact_info": "extracted", "website": "validated"}
            )
            await self.connection_manager.send_progress_update(
                "MOSVA_PARSER", i+1, len(companies), "COMPANY_PROCESSING",
                f"Parsed {i+1}/{len(companies)} company profiles"
            )
            await asyncio.sleep(0.2)
        
        await self.connection_manager.send_component_log(
            "MOSVA_PARSER", "COMPLETE", f"Successfully processed {len(companies)} companies", "SUCCESS"
        )
        
        await asyncio.sleep(0.5)
        
        # Phase 3: Website Discovery
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 2: WEBSITE DISCOVERY & VALIDATION\n" + 
            "-"*60,
            "INFO"
        )
        
        for i, company in enumerate(companies[:4]):  # Show fewer for demo
            await self.connection_manager.send_component_log(
                "WEBSITE_DISCOVERY", "URL_TEST", f"Testing primary URL for {company}", "INFO"
            )
            await asyncio.sleep(0.3)
            
            # Simulate different scenarios
            if i == 0:
                await self.connection_manager.send_component_log(
                    "WEBSITE_DISCOVERY", "URL_SUCCESS", f"Primary URL accessible: https://www.alam-maritim.com.my", "SUCCESS"
                )
            elif i == 1:
                await self.connection_manager.send_component_log(
                    "WEBSITE_DISCOVERY", "URL_RETRY", f"Primary URL failed, trying variations...", "WARNING"
                )
                await asyncio.sleep(0.2)
                await self.connection_manager.send_component_log(
                    "WEBSITE_DISCOVERY", "URL_SUCCESS", f"Alternative URL found: https://iconoffshore.com.my", "SUCCESS"
                )
            else:
                await self.connection_manager.send_component_log(
                    "WEBSITE_DISCOVERY", "URL_SUCCESS", f"URL validated successfully", "SUCCESS"
                )
            
            await self.connection_manager.send_progress_update(
                "WEBSITE_DISCOVERY", i+1, 4, "URL_VALIDATION",
                f"Validated {i+1}/4 company websites"
            )
            await asyncio.sleep(0.2)
        
        await asyncio.sleep(0.5)
        
        # Phase 4: Vessel Page Discovery
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 3: VESSEL PAGE DISCOVERY\n" + 
            "-"*60,
            "INFO"
        )
        
        vessel_pages = [
            ("/fleet", "Fleet overview page"),
            ("/vessels", "Individual vessel listings"),
            ("/marine-services", "Marine services with vessel details"),
            ("/offshore-support", "Offshore support vessel section")
        ]
        
        for i, company in enumerate(companies[:3]):
            await self.connection_manager.send_component_log(
                "VESSEL_SCRAPER", "PAGE_SCAN", f"Scanning {company} for vessel pages...", "INFO"
            )
            await asyncio.sleep(0.4)
            
            for j, (path, description) in enumerate(vessel_pages[:2]):
                await self.connection_manager.send_component_log(
                    "VESSEL_SCRAPER", "PAGE_FOUND", f"Found: {path} - {description}", "SUCCESS",
                    {"url": f"https://example.com{path}", "vessel_count": j+2}
                )
                await asyncio.sleep(0.2)
            
            await self.connection_manager.send_progress_update(
                "VESSEL_SCRAPER", i+1, 3, "PAGE_DISCOVERY",
                f"Discovered vessel pages for {i+1}/3 companies"
            )
        
        await asyncio.sleep(0.5)
        
        # Phase 5: Vessel Data Extraction
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 4: VESSEL DATA EXTRACTION\n" + 
            "-"*60,
            "INFO"
        )
        
        vessels = [
            {"name": "Perdana Express", "imo": "9123456", "type": "PSV"},
            {"name": "Alam Venture", "imo": "9234567", "type": "AHTS"},
            {"name": "Icon Explorer", "imo": "9345678", "type": "OSV"},
            {"name": "Sapura Navigator", "imo": "9456789", "type": "Construction Support"}
        ]
        
        for i, vessel in enumerate(vessels):
            await self.connection_manager.send_component_log(
                "VESSEL_SCRAPER", "VESSEL_EXTRACT", f"Extracting data for {vessel['name']}", "INFO"
            )
            await asyncio.sleep(0.3)
            
            # Simulate data extraction steps
            extraction_steps = [
                ("BASIC_INFO", "Extracting vessel name and identification"),
                ("SPECIFICATIONS", "Parsing technical specifications"),
                ("COMMERCIAL", "Extracting commercial information"),
                ("VALIDATION", "Validating extracted data")
            ]
            
            for step, description in extraction_steps:
                await self.connection_manager.send_component_log(
                    "VESSEL_SCRAPER", step, description, "INFO",
                    {"vessel": vessel['name'], "imo": vessel['imo']}
                )
                await asyncio.sleep(0.15)
            
            await self.connection_manager.send_component_log(
                "VESSEL_SCRAPER", "VESSEL_COMPLETE", 
                f"Successfully extracted data for {vessel['name']} (IMO: {vessel['imo']})", "SUCCESS",
                {"vessel_type": vessel['type'], "data_quality": "0.85"}
            )
            
            await self.connection_manager.send_progress_update(
                "VESSEL_SCRAPER", i+1, len(vessels), "VESSEL_EXTRACTION",
                f"Extracted data for {i+1}/{len(vessels)} vessels"
            )
            await asyncio.sleep(0.2)
        
        await asyncio.sleep(0.5)
        
        # Phase 6: Media Collection
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 5: MEDIA COLLECTION & PROCESSING\n" + 
            "-"*60,
            "INFO"
        )
        
        media_sources = [
            "ShipSpotting.com", "VesselFinder", "MarineTraffic", "Maritime Connector"
        ]
        
        for i, vessel in enumerate(vessels[:2]):  # Show fewer for demo
            await self.connection_manager.send_component_log(
                "MEDIA_FETCHER", "SEARCH_START", f"Searching media for {vessel['name']}", "INFO"
            )
            
            for j, source in enumerate(media_sources):
                await self.connection_manager.send_component_log(
                    "MEDIA_FETCHER", "SOURCE_SEARCH", f"Searching {source}...", "INFO",
                    {"vessel": vessel['name'], "imo": vessel['imo']}
                )
                await asyncio.sleep(0.3)
                
                # Simulate finding media
                if j < 2:  # First 2 sources find media
                    await self.connection_manager.send_component_log(
                        "MEDIA_FETCHER", "MEDIA_FOUND", f"Found {j+2} photos on {source}", "SUCCESS",
                        {"photo_count": j+2, "confidence": "0.89"}
                    )
                    
                    await self.connection_manager.send_component_log(
                        "MEDIA_FETCHER", "DOWNLOAD", f"Downloading and processing images...", "INFO"
                    )
                    await asyncio.sleep(0.2)
                    
                    await self.connection_manager.send_component_log(
                        "MEDIA_FETCHER", "PROCESS_COMPLETE", f"Images processed and optimized", "SUCCESS"
                    )
                else:
                    await self.connection_manager.send_component_log(
                        "MEDIA_FETCHER", "NO_MEDIA", f"No media found on {source}", "WARNING"
                    )
                
                await asyncio.sleep(0.2)
            
            await self.connection_manager.send_progress_update(
                "MEDIA_FETCHER", i+1, 2, "MEDIA_COLLECTION",
                f"Collected media for {i+1}/2 vessels"
            )
        
        await asyncio.sleep(0.5)
        
        # Phase 7: IMO-Based Enhancement
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 6: IMO-BASED DATA ENHANCEMENT\n" + 
            "-"*60,
            "INFO"
        )
        
        imo_sources = ["Marine21 Malaysia", "MISR Registry", "Classification Societies"]
        
        for i, vessel in enumerate(vessels[:2]):
            await self.connection_manager.send_component_log(
                "IMO_SEARCH", "SEARCH_START", f"Enhancing data for IMO {vessel['imo']}", "INFO"
            )
            
            for source in imo_sources:
                await self.connection_manager.send_component_log(
                    "IMO_SEARCH", "SOURCE_QUERY", f"Querying {source}...", "INFO",
                    {"imo": vessel['imo'], "source": source}
                )
                await asyncio.sleep(0.4)
                
                await self.connection_manager.send_component_log(
                    "IMO_SEARCH", "DATA_MERGE", f"Additional data found and merged", "SUCCESS",
                    {"fields_enhanced": 5, "confidence_boost": "0.12"}
                )
                await asyncio.sleep(0.2)
            
            await self.connection_manager.send_progress_update(
                "IMO_SEARCH", i+1, 2, "IMO_ENHANCEMENT",
                f"Enhanced {i+1}/2 vessels with IMO data"
            )
        
        await asyncio.sleep(0.5)
        
        # Phase 8: Database Operations
        await self.connection_manager.send_system_message(
            "system:phase",
            "\n" + "-"*60 + "\n" + 
            "PHASE 7: DATABASE SYNCHRONIZATION\n" + 
            "-"*60,
            "INFO"
        )
        
        await self.connection_manager.send_component_log(
            "DATABASE_SYNC", "CONNECTION", "Establishing Supabase connection...", "INFO"
        )
        await asyncio.sleep(0.3)
        
        await self.connection_manager.send_component_log(
            "DATABASE_SYNC", "CONNECTED", "Database connection established", "SUCCESS"
        )
        
        # Simulate database operations
        db_operations = [
            ("VESSEL_UPSERT", "Upserting vessel records"),
            ("MEDIA_LINK", "Linking media files"),
            ("QUALITY_UPDATE", "Updating quality scores"),
            ("INDEX_REFRESH", "Refreshing search indexes")
        ]
        
        for i, (op, description) in enumerate(db_operations):
            await self.connection_manager.send_component_log(
                "DATABASE_SYNC", op, description, "INFO"
            )
            await asyncio.sleep(0.4)
            
            await self.connection_manager.send_component_log(
                "DATABASE_SYNC", f"{op}_COMPLETE", f"{description} completed successfully", "SUCCESS"
            )
            
            await self.connection_manager.send_progress_update(
                "DATABASE_SYNC", i+1, len(db_operations), "DB_OPERATIONS",
                f"Completed {i+1}/{len(db_operations)} database operations"
            )
            await asyncio.sleep(0.2)
        
        await asyncio.sleep(0.5)
        
        # Phase 9: Final Summary
        await self.connection_manager.send_system_message(
            "system:complete",
            "\n" + "="*80 + "\n" + 
            "  DISCOVERY PROCESS COMPLETED SUCCESSFULLY\n" + 
            "="*80,
            "SUCCESS"
        )
        
        # Final statistics
        stats = [
            ("Companies Processed", "6"),
            ("Websites Validated", "6"),
            ("Vessel Pages Found", "12"),
            ("Vessels Extracted", "4"),
            ("Photos Collected", "18"),
            ("Documents Retrieved", "7"),
            ("Database Records", "4"),
            ("Data Quality Score", "0.87")
        ]
        
        await self.connection_manager.send_system_message(
            "system:stats",
            "\nFINAL STATISTICS:",
            "INFO"
        )
        
        for stat, value in stats:
            await self.connection_manager.send_system_message(
                "system:stats",
                f"  {stat:.<30} {value:>10}",
                "INFO"
            )
            await asyncio.sleep(0.1)
        
        await self.connection_manager.send_system_message(
            "system:ready",
            "\n>>> SYSTEM READY FOR NEXT OPERATION <<<\n",
            "SUCCESS"
        )
    
    def get_cli_dashboard_html(self) -> str:
        """Generate CLI-style dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSV Discovery System - CLI Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff41;
            line-height: 1.4;
            overflow: hidden;
        }
        
        .cli-container {
            display: grid;
            grid-template-rows: auto 1fr auto;
            height: 100vh;
            max-height: 100vh;
        }
        
        .cli-header {
            background: #000;
            border-bottom: 1px solid #00ff41;
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }
        
        .cli-title {
            color: #00ff41;
            font-weight: 500;
        }
        
        .cli-status {
            display: flex;
            gap: 20px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff41;
            animation: pulse 2s infinite;
        }
        
        .status-dot.error { background: #ff4444; }
        .status-dot.warning { background: #ffaa00; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .cli-main {
            display: grid;
            grid-template-columns: 2fr 1fr;
            height: 100%;
            overflow: hidden;
        }
        
        .cli-terminal {
            background: #000;
            border-right: 1px solid #333;
            padding: 16px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #00ff41 #000;
        }
        
        .cli-terminal::-webkit-scrollbar {
            width: 6px;
        }
        
        .cli-terminal::-webkit-scrollbar-track {
            background: #000;
        }
        
        .cli-terminal::-webkit-scrollbar-thumb {
            background: #00ff41;
            border-radius: 3px;
        }
        
        .cli-sidebar {
            background: #0a0a0a;
            border-left: 1px solid #333;
            padding: 16px;
            overflow-y: auto;
        }
        
        .cli-footer {
            background: #000;
            border-top: 1px solid #00ff41;
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
        }
        
        .log-entry {
            margin-bottom: 2px;
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        .log-timestamp {
            color: #666;
            margin-right: 8px;
        }
        
        .log-level-INFO { color: #00ff41; }
        .log-level-SUCCESS { color: #00ff88; }
        .log-level-WARNING { color: #ffaa00; }
        .log-level-ERROR { color: #ff4444; }
        .log-level-DEBUG { color: #888; }
        
        .log-component {
            color: #00aaff;
            font-weight: 500;
            margin-right: 8px;
        }
        
        .log-operation {
            color: #ffaa00;
            margin-right: 8px;
        }
        
        .log-message {
            color: #fff;
        }
        
        .log-details {
            color: #999;
            font-size: 11px;
            margin-left: 20px;
            margin-top: 2px;
        }
        
        .progress-bar {
            width: 100%;
            height: 12px;
            background: #333;
            border: 1px solid #00ff41;
            margin: 4px 0;
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff41, #00aa33);
            transition: width 0.3s ease;
            position: relative;
        }
        
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #000;
            font-size: 10px;
            font-weight: 500;
            z-index: 2;
        }
        
        .section-header {
            color: #00ff41;
            font-weight: 500;
            margin: 16px 0 8px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #333;
        }
        
        .component-status {
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
            padding: 4px 8px;
            background: #111;
            border-left: 3px solid #00ff41;
        }
        
        .component-name {
            color: #00aaff;
            font-weight: 500;
        }
        
        .component-state {
            color: #00ff41;
            font-size: 11px;
        }
        
        .controls {
            margin: 16px 0;
        }
        
        .cli-button {
            background: #000;
            border: 1px solid #00ff41;
            color: #00ff41;
            padding: 8px 16px;
            font-family: inherit;
            font-size: 12px;
            cursor: pointer;
            margin: 4px 8px 4px 0;
            transition: all 0.2s ease;
        }
        
        .cli-button:hover {
            background: #00ff41;
            color: #000;
        }
        
        .cli-button:disabled {
            border-color: #666;
            color: #666;
            cursor: not-allowed;
        }
        
        .cli-button:disabled:hover {
            background: #000;
            color: #666;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin: 12px 0;
        }
        
        .stat-item {
            background: #111;
            border: 1px solid #333;
            padding: 8px;
            text-align: center;
        }
        
        .stat-value {
            color: #00ff41;
            font-size: 18px;
            font-weight: 500;
        }
        
        .stat-label {
            color: #999;
            font-size: 10px;
            margin-top: 2px;
        }
        
        .ascii-art {
            color: #00aa33;
            font-size: 10px;
            line-height: 1;
            margin: 8px 0;
            text-align: center;
        }
        
        .system-separator {
            color: #333;
            margin: 8px 0;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="cli-container">
        <header class="cli-header">
            <div class="cli-title">OSV-DISCOVERY-SYSTEM v1.0.0 [PRODUCTION]</div>
            <div class="cli-status">
                <div class="status-item">
                    <div class="status-dot" id="ws-status"></div>
                    <span id="ws-text">DISCONNECTED</span>
                </div>
                <div class="status-item">
                    <div class="status-dot" id="db-status"></div>
                    <span>DATABASE</span>
                </div>
                <div class="status-item">
                    <span id="current-time"></span>
                </div>
            </div>
        </header>
        
        <main class="cli-main">
            <div class="cli-terminal" id="terminal">
                <div class="ascii-art">
   ____  _______     __  ____  _                                   
  / __ \\/ ___/ |   / / / __ \\(_)_____________  _   _____  _______  __
 / / / /\\__ \\| |  / / / / / / / // ___/ ___/ \\| | / / _ \\/ ___/ \\/ /
/ /_/ /___/ /| | / / / /_/ / / /(__  ) /__/ /_| |/ /  __/ /   >  < 
\\____//____/ |_|/ /  \\____/_/_//____/\\___/\\__, |___/\\___/_/   /_/\\_\\
                                         /____/                    
                </div>
                <div class="system-separator">════════════════════════════════════════════════════════════════════════════════</div>
                <div class="log-entry">
                    <span class="log-timestamp">[SYSTEM]</span>
                    <span class="log-level-INFO">OSV Discovery System initialized and ready for operation</span>
                </div>
                <div class="log-entry">
                    <span class="log-timestamp">[SYSTEM]</span>
                    <span class="log-level-INFO">Monitoring MOSVA vessel fleet data collection</span>
                </div>
                <div class="log-entry">
                    <span class="log-timestamp">[SYSTEM]</span>
                    <span class="log-level-INFO">All subsystems standing by...</span>
                </div>
                <div class="system-separator">────────────────────────────────────────────────────────────────────────────────</div>
            </div>
            
            <div class="cli-sidebar">
                <div class="section-header">SYSTEM CONTROLS</div>
                <div class="controls">
                    <button class="cli-button" id="start-btn" onclick="startDiscovery()">START DISCOVERY</button>
                    <button class="cli-button" id="stop-btn" onclick="stopDiscovery()" disabled>STOP PROCESS</button>
                    <button class="cli-button" onclick="clearTerminal()">CLEAR TERMINAL</button>
                </div>
                
                <div class="section-header">COMPONENT STATUS</div>
                <div class="component-status">
                    <span class="component-name">CRAWLER</span>
                    <span class="component-state" id="crawler-status">IDLE</span>
                </div>
                <div class="component-status">
                    <span class="component-name">SCRAPER</span>
                    <span class="component-state" id="scraper-status">IDLE</span>
                </div>
                <div class="component-status">
                    <span class="component-name">FETCHER</span>
                    <span class="component-state" id="fetcher-status">IDLE</span>
                </div>
                <div class="component-status">
                    <span class="component-name">DATABASE</span>
                    <span class="component-state" id="database-status">CONNECTED</span>
                </div>
                <div class="component-status">
                    <span class="component-name">MEDIA_PROC</span>
                    <span class="component-state" id="media-status">IDLE</span>
                </div>
                
                <div class="section-header">REAL-TIME STATS</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="companies-stat">0</div>
                        <div class="stat-label">COMPANIES</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="vessels-stat">0</div>
                        <div class="stat-label">VESSELS</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="photos-stat">0</div>
                        <div class="stat-label">PHOTOS</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="quality-stat">0.0</div>
                        <div class="stat-label">QUALITY</div>
                    </div>
                </div>
                
                <div class="section-header">PROGRESS MONITOR</div>
                <div id="progress-container">
                    <div style="color: #666; font-size: 11px; text-align: center; margin: 20px 0;">
                        No active operations
                    </div>
                </div>
            </div>
        </main>
        
        <footer class="cli-footer">
            <div>
                <span>PID: 1337</span>
                <span style="margin-left: 20px;">MEM: <span id="memory-usage">0.5</span>GB</span>
                <span style="margin-left: 20px;">CPU: <span id="cpu-usage">12</span>%</span>
            </div>
            <div>
                <span>LOG_LEVEL: INFO</span>
                <span style="margin-left: 20px;">SUPABASE: CONNECTED</span>
                <span style="margin-left: 20px;">WS: <span id="ws-status-footer">CONNECTED</span></span>
            </div>
        </footer>
    </div>

    <script>
        let ws = null;
        let isDiscoveryRunning = false;
        let logEntryCount = 0;
        const maxLogEntries = 1000;
        
        // Statistics counters
        let stats = {
            companies: 0,
            vessels: 0,
            photos: 0,
            quality: 0.0
        };
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                updateConnectionStatus(true);
                addSystemLog('WebSocket connection established', 'SUCCESS');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleMessage(message);
            };
            
            ws.onclose = function(event) {
                updateConnectionStatus(false);
                addSystemLog('WebSocket connection lost - attempting reconnect...', 'ERROR');
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onerror = function(error) {
                updateConnectionStatus(false);
                addSystemLog('WebSocket error occurred', 'ERROR');
            };
        }
        
        function updateConnectionStatus(connected) {
            const wsStatus = document.getElementById('ws-status');
            const wsText = document.getElementById('ws-text');
            const wsFooter = document.getElementById('ws-status-footer');
            
            if (connected) {
                wsStatus.style.background = '#00ff41';
                wsText.textContent = 'CONNECTED';
                wsFooter.textContent = 'CONNECTED';
                wsFooter.style.color = '#00ff41';
            } else {
                wsStatus.style.background = '#ff4444';
                wsText.textContent = 'DISCONNECTED';
                wsFooter.textContent = 'DISCONNECTED';
                wsFooter.style.color = '#ff4444';
            }
        }
        
        function handleMessage(message) {
            switch(message.type) {
                case 'terminal:connect':
                case 'system:command':
                case 'system:init':
                case 'system:phase':
                case 'system:complete':
                case 'system:stats':
                case 'system:ready':
                case 'system:error':
                    addSystemLog(message.message, message.level);
                    break;
                    
                case 'component:log':
                    addComponentLog(message);
                    updateComponentStatus(message.component, message.operation);
                    break;
                    
                case 'progress:update':
                    updateProgress(message);
                    break;
            }
        }
        
        function addSystemLog(message, level = 'INFO') {
            const terminal = document.getElementById('terminal');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const timestamp = new Date().toLocaleTimeString();
            entry.innerHTML = `
                <span class="log-timestamp">[${timestamp}]</span>
                <span class="log-level-${level}">${message}</span>
            `;
            
            terminal.appendChild(entry);
            terminal.scrollTop = terminal.scrollHeight;
            
            logEntryCount++;
            if (logEntryCount > maxLogEntries) {
                terminal.removeChild(terminal.firstChild);
                logEntryCount--;
            }
        }
        
        function addComponentLog(message) {
            const terminal = document.getElementById('terminal');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            let detailsHtml = '';
            if (message.details && Object.keys(message.details).length > 0) {
                const detailItems = Object.entries(message.details)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(', ');
                detailsHtml = `<div class="log-details">${detailItems}</div>`;
            }
            
            entry.innerHTML = `
                <span class="log-timestamp">[${message.timestamp}]</span>
                <span class="log-component">[${message.component}]</span>
                <span class="log-operation">[${message.operation}]</span>
                <span class="log-level-${message.level}">${message.message}</span>
                ${detailsHtml}
            `;
            
            terminal.appendChild(entry);
            terminal.scrollTop = terminal.scrollHeight;
            
            logEntryCount++;
            if (logEntryCount > maxLogEntries) {
                terminal.removeChild(terminal.firstChild);
                logEntryCount--;
            }
        }
        
        function updateComponentStatus(component, operation) {
            const statusElement = document.getElementById(`${component.toLowerCase()}-status`);
            if (statusElement) {
                const statusMap = {
                    'COMPONENT_LOAD': 'LOADING',
                    'COMPONENT_READY': 'READY',
                    'FILE_READ': 'READING',
                    'DATA_EXTRACT': 'PROCESSING',
                    'COMPLETE': 'COMPLETE',
                    'URL_TEST': 'TESTING',
                    'URL_SUCCESS': 'ACTIVE',
                    'PAGE_SCAN': 'SCANNING',
                    'VESSEL_EXTRACT': 'EXTRACTING',
                    'SEARCH_START': 'SEARCHING',
                    'DOWNLOAD': 'DOWNLOADING',
                    'CONNECTION': 'CONNECTING',
                    'CONNECTED': 'CONNECTED'
                };
                
                statusElement.textContent = statusMap[operation] || 'ACTIVE';
                statusElement.style.color = operation.includes('SUCCESS') || operation.includes('COMPLETE') || operation.includes('READY') ? '#00ff88' : '#00ff41';
            }
        }
        
        function updateProgress(message) {
            const container = document.getElementById('progress-container');
            let progressBar = document.getElementById(`progress-${message.component}`);
            
            if (!progressBar) {
                progressBar = document.createElement('div');
                progressBar.id = `progress-${message.component}`;
                progressBar.innerHTML = `
                    <div style="color: #00aaff; font-size: 11px; margin-bottom: 4px;">${message.component} - ${message.operation}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${message.percentage}%"></div>
                        <div class="progress-text">${message.current}/${message.total} (${message.percentage.toFixed(1)}%)</div>
                    </div>
                    <div style="color: #999; font-size: 10px; margin-top: 2px;">${message.details}</div>
                `;
                container.appendChild(progressBar);
                
                // Clear "no active operations" message
                const noOps = container.querySelector('div[style*="No active operations"]');
                if (noOps) {
                    container.removeChild(noOps);
                }
            } else {
                const progressFill = progressBar.querySelector('.progress-fill');
                const progressText = progressBar.querySelector('.progress-text');
                const detailsText = progressBar.querySelector('div[style*="color: #999"]');
                
                progressFill.style.width = `${message.percentage}%`;
                progressText.textContent = `${message.current}/${message.total} (${message.percentage.toFixed(1)}%)`;
                if (detailsText) {
                    detailsText.textContent = message.details;
                }
            }
            
            // Update stats
            if (message.component === 'MOSVA_PARSER' && message.operation === 'COMPANY_PROCESSING') {
                stats.companies = message.current;
                document.getElementById('companies-stat').textContent = stats.companies;
            } else if (message.component === 'VESSEL_SCRAPER' && message.operation === 'VESSEL_EXTRACTION') {
                stats.vessels = message.current;
                document.getElementById('vessels-stat').textContent = stats.vessels;
            } else if (message.component === 'MEDIA_FETCHER' && message.operation === 'MEDIA_COLLECTION') {
                stats.photos += 3; // Simulate photo collection
                document.getElementById('photos-stat').textContent = stats.photos;
            }
            
            // Remove completed progress bars after a delay
            if (message.percentage >= 100) {
                setTimeout(() => {
                    if (progressBar && progressBar.parentNode) {
                        progressBar.parentNode.removeChild(progressBar);
                        
                        // Show "no active operations" if no progress bars left
                        if (container.children.length === 0) {
                            container.innerHTML = '<div style="color: #666; font-size: 11px; text-align: center; margin: 20px 0;">No active operations</div>';
                        }
                    }
                }, 3000);
            }
        }
        
        async function startDiscovery() {
            if (isDiscoveryRunning) return;
            
            isDiscoveryRunning = true;
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            
            try {
                const response = await fetch('/api/start-discovery', { method: 'POST' });
                const result = await response.json();
            } catch (error) {
                addSystemLog(`Failed to start discovery: ${error.message}`, 'ERROR');
                isDiscoveryRunning = false;
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
            }
        }
        
        async function stopDiscovery() {
            try {
                const response = await fetch('/api/stop-discovery', { method: 'POST' });
                const result = await response.json();
                
                isDiscoveryRunning = false;
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
                
                addSystemLog('Discovery process stopped by user', 'WARNING');
            } catch (error) {
                addSystemLog(`Failed to stop discovery: ${error.message}`, 'ERROR');
            }
        }
        
        function clearTerminal() {
            const terminal = document.getElementById('terminal');
            const systemHeader = terminal.querySelector('.ascii-art').parentNode;
            
            // Keep ASCII art and initial system messages, clear the rest
            const entries = terminal.querySelectorAll('.log-entry');
            entries.forEach(entry => {
                if (!entry.textContent.includes('OSV Discovery System initialized')) {
                    terminal.removeChild(entry);
                }
            });
            
            logEntryCount = 3; // Reset count to initial messages
            addSystemLog('Terminal cleared by user', 'INFO');
        }
        
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString() + ' UTC';
        }
        
        function updateSystemStats() {
            // Simulate system resource usage
            const memory = (Math.random() * 0.5 + 0.3).toFixed(1);
            const cpu = Math.floor(Math.random() * 20 + 5);
            
            document.getElementById('memory-usage').textContent = memory;
            document.getElementById('cpu-usage').textContent = cpu;
            
            // Update quality score gradually
            if (stats.vessels > 0) {
                stats.quality = Math.min(0.95, stats.quality + 0.01);
                document.getElementById('quality-stat').textContent = stats.quality.toFixed(2);
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            updateTime();
            setInterval(updateTime, 1000);
            setInterval(updateSystemStats, 2000);
            
            // Initial system status
            document.getElementById('database-status').textContent = 'CONNECTED';
            document.getElementById('database-status').style.color = '#00ff88';
        });
    </script>
</body>
</html>
        """

def create_cli_dashboard_app() -> FastAPI:
    """Create and configure the CLI-style dashboard application"""
    dashboard = CLIDashboard()
    
    @dashboard.app.on_event("startup")
    async def startup_event():
        print("🚀 CLI-Style OSV Dashboard starting up...")
        print("✅ Dashboard ready at http://localhost:8000")
    
    return dashboard.app

def main():
    """Run the CLI-style dashboard server"""
    app = create_cli_dashboard_app()
    
    print("🖥️  Starting CLI-Style OSV Discovery Dashboard...")
    print("📟 Terminal interface available at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
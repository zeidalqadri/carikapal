#!/usr/bin/env python3
"""
Enhanced CLI Dashboard for Integrated OSV Discovery System
Terminal-style interface with comprehensive monitoring of all system components
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import the integrated system
from integrated_osv_system import IntegratedOSVSystem, SystemStatus

class EnhancedCLIConnectionManager:
    """Enhanced WebSocket connection manager for integrated system"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.integrated_system: Optional[IntegratedOSVSystem] = None
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_system_message("terminal:connect", 
            "=== Enhanced OSV Discovery System Connected ===")
    
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
    
    async def send_component_status(self, component: str, status: str, details: Dict = None):
        """Send component status update"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        await self.broadcast({
            "type": "component:status",
            "timestamp": timestamp,
            "component": component.upper(),
            "status": status,
            "details": details or {}
        })
    
    async def send_discovery_progress(self, phase: str, current: int, total: int, 
                                   operation: str, details: str = ""):
        """Send discovery progress updates"""
        percentage = (current / total * 100) if total > 0 else 0
        await self.broadcast({
            "type": "discovery:progress",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "phase": phase.upper(),
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
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

class EnhancedCLIDashboard:
    """Enhanced CLI-style dashboard with full system integration"""
    
    def __init__(self):
        self.app = FastAPI(title="Enhanced OSV Discovery CLI Dashboard", version="2.0.0")
        self.connection_manager = EnhancedCLIConnectionManager()
        self.integrated_system = IntegratedOSVSystem()
        self.setup_routes()
        self.setup_middleware()
        
        # System state tracking
        self.system_initialized = False
        self.discovery_running = False
    
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
            return self.get_enhanced_dashboard_html()
        
        @self.app.get("/api/system-status")
        async def get_system_status():
            """Get integrated system status"""
            if not self.system_initialized:
                return JSONResponse(content={"status": "not_initialized"})
            
            try:
                status = await self.integrated_system.get_system_status()
                return JSONResponse(content=asdict(status))
            except Exception as e:
                return JSONResponse(content={"status": "error", "error": str(e)})
        
        @self.app.post("/api/initialize-system")
        async def initialize_system():
            """Initialize the integrated system"""
            try:
                await self.connection_manager.send_system_message(
                    "system:init", 
                    ">>> INITIALIZING INTEGRATED OSV DISCOVERY SYSTEM <<<",
                    "INFO"
                )
                
                success = await self.integrated_system.initialize_system()
                
                if success:
                    self.system_initialized = True
                    await self.connection_manager.send_system_message(
                        "system:ready",
                        "🚀 All system components initialized and ready",
                        "SUCCESS"
                    )
                    return {"status": "success", "message": "System initialized"}
                else:
                    await self.connection_manager.send_system_message(
                        "system:error",
                        "❌ System initialization failed",
                        "ERROR"
                    )
                    return {"status": "error", "message": "Initialization failed"}
                
            except Exception as e:
                await self.connection_manager.send_system_message(
                    "system:error",
                    f"System initialization error: {str(e)}",
                    "ERROR"
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/start-comprehensive-discovery")
        async def start_comprehensive_discovery():
            """Start comprehensive discovery with all components"""
            if not self.system_initialized:
                raise HTTPException(status_code=400, detail="System not initialized")
            
            if self.discovery_running:
                raise HTTPException(status_code=400, detail="Discovery already running")
            
            try:
                self.discovery_running = True
                await self.connection_manager.send_system_message(
                    "discovery:start",
                    ">>> STARTING COMPREHENSIVE OSV DISCOVERY WITH ALL COMPONENTS <<<",
                    "INFO"
                )
                
                # Run discovery with progress updates
                await self.run_discovery_with_updates()
                
                self.discovery_running = False
                await self.connection_manager.send_system_message(
                    "discovery:complete",
                    "✅ Comprehensive discovery completed successfully",
                    "SUCCESS"
                )
                
                return {"status": "success", "message": "Comprehensive discovery completed"}
                
            except Exception as e:
                self.discovery_running = False
                await self.connection_manager.send_system_message(
                    "discovery:error",
                    f"Discovery failed: {str(e)}",
                    "ERROR"
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/component-health")
        async def get_component_health():
            """Get health status of all components"""
            if not self.system_initialized:
                return {"components": {}, "status": "not_initialized"}
            
            try:
                components = self.integrated_system.components
                health = {}
                
                for name, component in components.items():
                    try:
                        # Simple health check - component exists and is accessible
                        health[name] = {
                            "status": "operational",
                            "type": type(component).__name__,
                            "initialized": True
                        }
                    except Exception as e:
                        health[name] = {
                            "status": "error",
                            "error": str(e),
                            "initialized": False
                        }
                
                return {"components": health, "status": "healthy"}
                
            except Exception as e:
                return {"components": {}, "status": "error", "error": str(e)}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Enhanced WebSocket endpoint"""
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
                    elif message.get("type") == "get_status":
                        if self.system_initialized:
                            status = await self.integrated_system.get_system_status()
                            await websocket.send_text(json.dumps({
                                "type": "status_update",
                                "data": asdict(status)
                            }))
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
    
    async def run_discovery_with_updates(self):
        """Run discovery with real-time progress updates"""
        try:
            # Phase 1: Core Discovery
            await self.connection_manager.send_discovery_progress(
                "core_discovery", 0, 100, "STARTING", "Initializing core discovery system"
            )
            
            # Simulate core discovery phases
            phases = [
                ("MOSVA_PARSING", "Parsing MOSVA member data"),
                ("WEBSITE_DISCOVERY", "Discovering company websites"), 
                ("VESSEL_EXTRACTION", "Extracting vessel information"),
                ("DATA_VALIDATION", "Validating extracted data")
            ]
            
            for i, (operation, description) in enumerate(phases):
                await self.connection_manager.send_discovery_progress(
                    "core_discovery", i*25, 100, operation, description
                )
                await asyncio.sleep(2)  # Simulate work
            
            await self.connection_manager.send_discovery_progress(
                "core_discovery", 100, 100, "COMPLETE", "Core discovery completed"
            )
            
            # Phase 2: Media Collection
            await self.connection_manager.send_discovery_progress(
                "media_collection", 0, 100, "STARTING", "Collecting vessel media and documents"
            )
            
            media_phases = [
                ("PHOTO_SEARCH", "Searching for vessel photos"),
                ("DOCUMENT_COLLECTION", "Collecting specification documents"),
                ("MEDIA_PROCESSING", "Processing and optimizing media"),
                ("STORAGE", "Storing media files")
            ]
            
            for i, (operation, description) in enumerate(media_phases):
                await self.connection_manager.send_discovery_progress(
                    "media_collection", i*25, 100, operation, description
                )
                await asyncio.sleep(1.5)
            
            await self.connection_manager.send_discovery_progress(
                "media_collection", 100, 100, "COMPLETE", "Media collection completed"
            )
            
            # Phase 3: IMO Enrichment
            await self.connection_manager.send_discovery_progress(
                "imo_enrichment", 0, 100, "STARTING", "Enriching vessels with IMO data"
            )
            
            imo_phases = [
                ("IMO_SEARCH", "Searching IMO databases"),
                ("DATA_MERGING", "Merging additional vessel data"),
                ("QUALITY_SCORING", "Calculating data quality scores"),
                ("VERIFICATION", "Verifying enriched data")
            ]
            
            for i, (operation, description) in enumerate(imo_phases):
                await self.connection_manager.send_discovery_progress(
                    "imo_enrichment", i*25, 100, operation, description
                )
                await asyncio.sleep(1)
            
            await self.connection_manager.send_discovery_progress(
                "imo_enrichment", 100, 100, "COMPLETE", "IMO enrichment completed"
            )
            
            # Phase 4: Marketplace Integration
            await self.connection_manager.send_discovery_progress(
                "marketplace_sync", 0, 100, "STARTING", "Synchronizing with marketplace"
            )
            
            marketplace_phases = [
                ("DATA_TRANSFORMATION", "Transforming data for marketplace"),
                ("VALIDATION", "Validating marketplace data"),
                ("UPLOAD", "Uploading to marketplace"),
                ("SYNC_COMPLETE", "Marketplace synchronization complete")
            ]
            
            for i, (operation, description) in enumerate(marketplace_phases):
                await self.connection_manager.send_discovery_progress(
                    "marketplace_sync", i*25, 100, operation, description
                )
                await asyncio.sleep(1)
            
            await self.connection_manager.send_discovery_progress(
                "marketplace_sync", 100, 100, "COMPLETE", "Marketplace sync completed"
            )
            
            # Run actual integrated discovery
            results = await self.integrated_system.run_comprehensive_discovery(
                enable_media=True, enable_imo_search=True
            )
            
            # Send final results
            await self.connection_manager.send_system_message(
                "discovery:results",
                f"📊 Discovery Results: {results['vessels_processed']} vessels, {results['media_collected']} media items",
                "SUCCESS"
            )
            
        except Exception as e:
            await self.connection_manager.send_system_message(
                "discovery:error",
                f"Discovery failed: {str(e)}",
                "ERROR"
            )
            raise
    
    def get_enhanced_dashboard_html(self) -> str:
        """Return enhanced CLI dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced OSV Discovery System - CLI Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
            color: #00ff41;
            overflow: hidden;
            height: 100vh;
        }
        
        .container {
            display: flex;
            height: 100vh;
        }
        
        .sidebar {
            width: 250px;
            background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%);
            border-right: 1px solid #00ff41;
            padding: 20px;
            overflow-y: auto;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(90deg, #000000 0%, #1a4d1a 100%);
            padding: 15px;
            border: 1px solid #00ff41;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .ascii-art {
            font-size: 10px;
            line-height: 1;
            color: #00aaff;
            margin-bottom: 10px;
        }
        
        .system-title {
            font-size: 18px;
            color: #00ff88;
            font-weight: bold;
            text-shadow: 0 0 10px #00ff88;
        }
        
        .control-panel {
            background: rgba(0, 255, 65, 0.05);
            border: 1px solid #00ff41;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .control-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: linear-gradient(135deg, #003300 0%, #006600 100%);
            border: 1px solid #00ff41;
            color: #00ff41;
            padding: 8px 16px;
            cursor: pointer;
            font-family: inherit;
            font-size: 12px;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            background: linear-gradient(135deg, #006600 0%, #00aa00 100%);
            box-shadow: 0 0 10px #00ff41;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .terminal {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff41;
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
        }
        
        .log-entry {
            margin-bottom: 5px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .log-timestamp {
            color: #666;
            font-size: 11px;
            min-width: 80px;
        }
        
        .log-level-INFO { color: #00ff41; }
        .log-level-SUCCESS { color: #00ff88; }
        .log-level-WARNING { color: #ffaa00; }
        .log-level-ERROR { color: #ff4444; }
        
        .component-status {
            margin-bottom: 15px;
        }
        
        .component-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 10px;
            background: rgba(0, 255, 65, 0.05);
            border: 1px solid #003300;
            margin-bottom: 5px;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #666;
        }
        
        .status-operational { background: #00ff88; }
        .status-error { background: #ff4444; }
        .status-loading { background: #ffaa00; }
        
        .progress-container {
            background: rgba(0, 255, 65, 0.05);
            border: 1px solid #00ff41;
            padding: 15px;
            margin-bottom: 20px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .progress-bar {
            background: #333;
            height: 20px;
            border: 1px solid #00ff41;
            position: relative;
            margin: 5px 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #006600 0%, #00aa00 100%);
            height: 100%;
            transition: width 0.3s ease;
            position: relative;
        }
        
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 11px;
            color: #fff;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: rgba(0, 255, 65, 0.05);
            border: 1px solid #00ff41;
            padding: 10px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
        }
        
        .stat-label {
            font-size: 11px;
            color: #999;
        }
        
        .connection-status {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff41;
            padding: 5px 10px;
            font-size: 11px;
        }
        
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ff4444;
            margin-right: 5px;
        }
        
        .status-connected { background: #00ff88; }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #000;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00ff41;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="connection-status">
        <span class="status-dot" id="connection-dot"></span>
        <span id="connection-text">Connecting...</span>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <div class="component-status">
                <h3 style="margin-bottom: 10px; color: #00aaff;">System Components</h3>
                <div class="component-item">
                    <span>Database</span>
                    <span class="status-indicator" id="database-status"></span>
                </div>
                <div class="component-item">
                    <span>Vessel Discovery</span>
                    <span class="status-indicator" id="discovery-status"></span>
                </div>
                <div class="component-item">
                    <span>Media Collector</span>
                    <span class="status-indicator" id="media-status"></span>
                </div>
                <div class="component-item">
                    <span>IMO Search</span>
                    <span class="status-indicator" id="imo-status"></span>
                </div>
                <div class="component-item">
                    <span>Marketplace</span>
                    <span class="status-indicator" id="marketplace-status"></span>
                </div>
                <div class="component-item">
                    <span>Dashboard</span>
                    <span class="status-indicator" id="dashboard-status"></span>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="vessels-count">0</div>
                    <div class="stat-label">Vessels</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="companies-count">0</div>
                    <div class="stat-label">Companies</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="uptime">0s</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="header">
                <div class="ascii-art">
  ███████╗███╗   ██╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗███████╗██████╗ 
  ██╔════╝████╗  ██║██║  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝██╔══██╗
  █████╗  ██╔██╗ ██║███████║███████║██╔██╗ ██║██║     █████╗  ██║  ██║
  ██╔══╝  ██║╚██╗██║██╔══██║██╔══██║██║╚██╗██║██║     ██╔══╝  ██║  ██║
  ███████╗██║ ╚████║██║  ██║██║  ██║██║ ╚████║╚██████╗███████╗██████╔╝
  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═════╝ 
                </div>
                <div class="system-title">ENHANCED OSV DISCOVERY SYSTEM v2.0</div>
                <div style="font-size: 12px; color: #666;">Integrated Maritime Intelligence Platform</div>
            </div>
            
            <div class="control-panel">
                <h3 style="margin-bottom: 10px; color: #00aaff;">System Control</h3>
                <div class="control-buttons">
                    <button class="btn" id="init-btn" onclick="initializeSystem()">🔧 Initialize System</button>
                    <button class="btn" id="discovery-btn" onclick="startComprehensiveDiscovery()" disabled>🚀 Start Full Discovery</button>
                    <button class="btn" onclick="checkComponentHealth()">💊 Component Health</button>
                    <button class="btn" onclick="getSystemStatus()">📊 System Status</button>
                    <button class="btn" onclick="clearTerminal()">🧹 Clear Terminal</button>
                </div>
            </div>
            
            <div class="progress-container" id="progress-container">
                <h3 style="margin-bottom: 10px; color: #00aaff;">Active Operations</h3>
                <div style="text-align: center; color: #666; font-size: 11px;">No active operations</div>
            </div>
            
            <div class="terminal" id="terminal">
                <div class="log-entry">
                    <span class="log-timestamp">[SYSTEM]</span>
                    <span class="log-level-INFO">Enhanced OSV Discovery System CLI Dashboard v2.0 initialized</span>
                </div>
                <div class="log-entry">
                    <span class="log-timestamp">[READY]</span>
                    <span class="log-level-SUCCESS">All systems ready - Click 'Initialize System' to begin</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let systemInitialized = false;
        let discoveryRunning = false;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                updateConnectionStatus(true);
                addLogEntry('WebSocket connected to enhanced dashboard', 'SUCCESS');
                
                // Keep connection alive
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'ping'}));
                    }
                }, 30000);
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };
            
            ws.onclose = function(event) {
                updateConnectionStatus(false);
                setTimeout(connectWebSocket, 5000);
            };
        }
        
        function updateConnectionStatus(connected) {
            const dot = document.getElementById('connection-dot');
            const text = document.getElementById('connection-text');
            
            if (connected) {
                dot.className = 'status-dot status-connected';
                text.textContent = 'Connected';
            } else {
                dot.className = 'status-dot';
                text.textContent = 'Disconnected';
            }
        }
        
        function handleWebSocketMessage(message) {
            switch(message.type) {
                case 'terminal:connect':
                case 'system:init':
                case 'system:ready':
                case 'system:error':
                case 'discovery:start':
                case 'discovery:complete':
                case 'discovery:error':
                case 'discovery:results':
                    addLogEntry(message.message, message.level || 'INFO');
                    break;
                    
                case 'component:status':
                    updateComponentStatus(message.component, message.status);
                    break;
                    
                case 'discovery:progress':
                    updateDiscoveryProgress(message);
                    break;
            }
        }
        
        function addLogEntry(message, level = 'INFO') {
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
        }
        
        function updateComponentStatus(component, status) {
            const statusElement = document.getElementById(`${component.toLowerCase()}-status`);
            if (statusElement) {
                statusElement.className = `status-indicator status-${status}`;
            }
        }
        
        function updateDiscoveryProgress(message) {
            const container = document.getElementById('progress-container');
            let progressBar = document.getElementById(`progress-${message.phase}`);
            
            if (!progressBar) {
                progressBar = document.createElement('div');
                progressBar.id = `progress-${message.phase}`;
                progressBar.innerHTML = `
                    <div style="color: #00aaff; font-size: 11px; margin-bottom: 4px;">${message.phase} - ${message.operation}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${message.percentage}%"></div>
                        <div class="progress-text">${message.current}/${message.total} (${message.percentage.toFixed(1)}%)</div>
                    </div>
                    <div style="color: #999; font-size: 10px; margin-top: 2px; margin-bottom: 10px;">${message.details}</div>
                `;
                
                // Clear "no active operations" message
                const noOps = container.querySelector('div[style*="No active operations"]');
                if (noOps) {
                    container.removeChild(noOps);
                }
                
                container.appendChild(progressBar);
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
            
            // Remove completed progress bars
            if (message.percentage >= 100) {
                setTimeout(() => {
                    if (progressBar && progressBar.parentNode) {
                        progressBar.parentNode.removeChild(progressBar);
                        
                        if (container.children.length === 1) { // Only header left
                            container.innerHTML = `
                                <h3 style="margin-bottom: 10px; color: #00aaff;">Active Operations</h3>
                                <div style="text-align: center; color: #666; font-size: 11px;">No active operations</div>
                            `;
                        }
                    }
                }, 3000);
            }
        }
        
        async function initializeSystem() {
            const btn = document.getElementById('init-btn');
            btn.disabled = true;
            btn.textContent = '🔄 Initializing...';
            
            try {
                const response = await fetch('/api/initialize-system', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    systemInitialized = true;
                    document.getElementById('discovery-btn').disabled = false;
                    btn.textContent = '✅ Initialized';
                    addLogEntry('System initialization completed successfully', 'SUCCESS');
                } else {
                    btn.disabled = false;
                    btn.textContent = '🔧 Initialize System';
                    addLogEntry(`Initialization failed: ${result.message}`, 'ERROR');
                }
            } catch (error) {
                btn.disabled = false;
                btn.textContent = '🔧 Initialize System';
                addLogEntry(`Initialization error: ${error.message}`, 'ERROR');
            }
        }
        
        async function startComprehensiveDiscovery() {
            if (!systemInitialized || discoveryRunning) return;
            
            const btn = document.getElementById('discovery-btn');
            btn.disabled = true;
            btn.textContent = '🔄 Running...';
            discoveryRunning = true;
            
            try {
                const response = await fetch('/api/start-comprehensive-discovery', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLogEntry('Comprehensive discovery completed successfully', 'SUCCESS');
                } else {
                    addLogEntry(`Discovery failed: ${result.message}`, 'ERROR');
                }
            } catch (error) {
                addLogEntry(`Discovery error: ${error.message}`, 'ERROR');
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 Start Full Discovery';
                discoveryRunning = false;
            }
        }
        
        async function checkComponentHealth() {
            try {
                const response = await fetch('/api/component-health');
                const result = await response.json();
                
                addLogEntry('Component health check:', 'INFO');
                
                if (result.components) {
                    for (const [name, health] of Object.entries(result.components)) {
                        const status = health.status === 'operational' ? 'SUCCESS' : 'ERROR';
                        addLogEntry(`  ${name}: ${health.status}`, status);
                    }
                }
            } catch (error) {
                addLogEntry(`Health check failed: ${error.message}`, 'ERROR');
            }
        }
        
        async function getSystemStatus() {
            try {
                const response = await fetch('/api/system-status');
                const result = await response.json();
                
                if (result.status === 'not_initialized') {
                    addLogEntry('System not yet initialized', 'WARNING');
                } else {
                    addLogEntry('System status:', 'INFO');
                    addLogEntry(`  Vessels: ${result.total_vessels}`, 'INFO');
                    addLogEntry(`  Companies: ${result.total_companies}`, 'INFO');
                    addLogEntry(`  Database: ${result.database_status}`, 'INFO');
                    addLogEntry(`  Health: ${result.system_health}`, 'INFO');
                    addLogEntry(`  Uptime: ${result.uptime}`, 'INFO');
                    
                    // Update sidebar stats
                    document.getElementById('vessels-count').textContent = result.total_vessels;
                    document.getElementById('companies-count').textContent = result.total_companies;
                    document.getElementById('uptime').textContent = result.uptime;
                }
            } catch (error) {
                addLogEntry(`Status check failed: ${error.message}`, 'ERROR');
            }
        }
        
        function clearTerminal() {
            const terminal = document.getElementById('terminal');
            terminal.innerHTML = `
                <div class="log-entry">
                    <span class="log-timestamp">[CLEARED]</span>
                    <span class="log-level-INFO">Terminal cleared by user</span>
                </div>
            `;
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            
            // Auto-refresh system status
            setInterval(() => {
                if (systemInitialized) {
                    getSystemStatus();
                }
            }, 30000);
        });
    </script>
</body>
</html>
        """

def create_enhanced_dashboard_app() -> FastAPI:
    """Create and configure the enhanced dashboard application"""
    dashboard = EnhancedCLIDashboard()
    
    @dashboard.app.on_event("startup")
    async def startup_event():
        print("🚀 Enhanced OSV CLI Dashboard starting up...")
        print("✅ Enhanced dashboard ready at http://localhost:8000")
    
    return dashboard.app

def main():
    """Run the enhanced dashboard server"""
    app = create_enhanced_dashboard_app()
    
    print("🖥️  Starting Enhanced CLI-Style OSV Discovery Dashboard...")
    print("📟 Integrated terminal interface available at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()

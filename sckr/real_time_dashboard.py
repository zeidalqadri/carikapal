#!/usr/bin/env python3
"""
Real-time OSV Discovery Dashboard
FastAPI-based dashboard with WebSocket support for live monitoring
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
import asyncpg
from pydantic import BaseModel

# Supabase connection
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

@dataclass
class DashboardStats:
    """Real-time dashboard statistics"""
    total_companies: int = 0
    total_vessels: int = 0
    vessels_with_photos: int = 0
    vessels_with_specs: int = 0
    active_crawl_sessions: int = 0
    avg_data_quality: float = 0.0
    last_update: datetime = None
    
    # Performance metrics
    crawl_success_rate: float = 0.0
    avg_processing_time: float = 0.0
    media_collection_rate: float = 0.0
    
    # Recent activity
    vessels_added_today: int = 0
    media_collected_today: int = 0
    errors_today: int = 0

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📱 Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"📱 Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

class OSVDashboard:
    """Main dashboard application"""
    
    def __init__(self):
        self.app = FastAPI(title="OSV Discovery Dashboard", version="1.0.0")
        self.connection_manager = ConnectionManager()
        self.supabase_client = None
        self.setup_supabase()
        self.setup_routes()
        self.setup_middleware()
        
        # Background task for real-time updates
        self.update_task = None
    
    def setup_supabase(self):
        """Initialize Supabase connection"""
        if SUPABASE_AVAILABLE:
            try:
                url = "https://juvqqrsdbruskleodzip.supabase.co"
                key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw"
                self.supabase_client = create_client(url, key)
                print("✅ Supabase connected to dashboard")
            except Exception as e:
                print(f"⚠️ Supabase connection failed: {e}")
    
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
            return self.get_dashboard_html()
        
        @self.app.get("/api/stats")
        async def get_dashboard_stats():
            """Get current dashboard statistics"""
            try:
                stats = await self.calculate_dashboard_stats()
                return JSONResponse(content=asdict(stats))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/vessels")
        async def get_vessels(
            limit: int = 50, 
            offset: int = 0,
            search: Optional[str] = None,
            vessel_type: Optional[str] = None
        ):
            """Get vessel list with filtering and pagination"""
            try:
                return await self.get_vessels_data(limit, offset, search, vessel_type)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/companies")
        async def get_companies(limit: int = 50, offset: int = 0):
            """Get company list"""
            try:
                return await self.get_companies_data(limit, offset)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/crawl-sessions")
        async def get_crawl_sessions(limit: int = 20):
            """Get recent crawl sessions"""
            try:
                return await self.get_crawl_sessions_data(limit)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/source-performance")
        async def get_source_performance():
            """Get source performance metrics"""
            try:
                return await self.get_source_performance_data()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/start-crawl")
        async def start_crawl():
            """Start a new crawl session"""
            try:
                # This would trigger the main crawler
                message = {
                    "type": "crawl_started",
                    "message": "New crawl session initiated",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.connection_manager.broadcast(message)
                return {"status": "success", "message": "Crawl started"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    # Keep connection alive and handle client messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await self.connection_manager.send_personal_message(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                            websocket
                        )
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
    
    async def calculate_dashboard_stats(self) -> DashboardStats:
        """Calculate current dashboard statistics"""
        stats = DashboardStats()
        stats.last_update = datetime.utcnow()
        
        if not self.supabase_client:
            return stats
        
        try:
            # Total companies
            companies_result = self.supabase_client.table('companies').select('id').execute()
            stats.total_companies = len(companies_result.data)
            
            # Total vessels
            vessels_result = self.supabase_client.table('vessels').select('id, data_quality_score').execute()
            stats.total_vessels = len(vessels_result.data)
            
            # Average data quality
            if vessels_result.data:
                quality_scores = [v.get('data_quality_score', 0) for v in vessels_result.data if v.get('data_quality_score')]
                stats.avg_data_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Vessels with photos
            photos_result = self.supabase_client.table('vessel_media')\
                .select('vessel_id')\
                .eq('media_type', 'photo')\
                .execute()
            unique_vessels_with_photos = set(photo['vessel_id'] for photo in photos_result.data)
            stats.vessels_with_photos = len(unique_vessels_with_photos)
            
            # Vessels with specifications
            specs_result = self.supabase_client.table('vessel_specifications')\
                .select('vessel_id')\
                .execute()
            unique_vessels_with_specs = set(spec['vessel_id'] for spec in specs_result.data)
            stats.vessels_with_specs = len(unique_vessels_with_specs)
            
            # Active crawl sessions
            active_sessions_result = self.supabase_client.table('crawl_sessions')\
                .select('id')\
                .eq('status', 'running')\
                .execute()
            stats.active_crawl_sessions = len(active_sessions_result.data)
            
            # Today's activity
            today = datetime.utcnow().date()
            
            # Vessels added today
            vessels_today_result = self.supabase_client.table('vessels')\
                .select('id')\
                .gte('created_at', today.isoformat())\
                .execute()
            stats.vessels_added_today = len(vessels_today_result.data)
            
            # Media collected today
            media_today_result = self.supabase_client.table('vessel_media')\
                .select('id')\
                .gte('created_at', today.isoformat())\
                .execute()
            stats.media_collected_today = len(media_today_result.data)
            
            # Crawl performance
            recent_sessions_result = self.supabase_client.table('crawl_sessions')\
                .select('*')\
                .gte('started_at', (datetime.utcnow() - timedelta(days=7)).isoformat())\
                .order('started_at', desc=True)\
                .execute()
            
            if recent_sessions_result.data:
                completed_sessions = [s for s in recent_sessions_result.data if s.get('status') == 'completed']
                if completed_sessions:
                    success_count = len(completed_sessions)
                    total_count = len(recent_sessions_result.data)
                    stats.crawl_success_rate = (success_count / total_count) * 100
                    
                    # Average processing time
                    durations = [s.get('duration_seconds', 0) for s in completed_sessions if s.get('duration_seconds')]
                    if durations:
                        stats.avg_processing_time = sum(durations) / len(durations)
            
        except Exception as e:
            print(f"Error calculating dashboard stats: {e}")
        
        return stats
    
    async def get_vessels_data(self, limit: int, offset: int, search: Optional[str], vessel_type: Optional[str]):
        """Get vessels data with filtering"""
        if not self.supabase_client:
            return {"vessels": [], "total": 0}
        
        query = self.supabase_client.table('vessels').select('*')
        
        if search:
            query = query.or_(f'vessel_name.ilike.%{search}%,owner_company.ilike.%{search}%,imo_number.ilike.%{search}%')
        
        if vessel_type:
            query = query.eq('vessel_type', vessel_type)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data)
        
        # Get paginated results
        result = query.range(offset, offset + limit - 1).order('created_at', desc=True).execute()
        
        return {
            "vessels": result.data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_companies_data(self, limit: int, offset: int):
        """Get companies data"""
        if not self.supabase_client:
            return {"companies": [], "total": 0}
        
        # Get total count
        count_result = self.supabase_client.table('companies').select('id').execute()
        total = len(count_result.data)
        
        # Get paginated results
        result = self.supabase_client.table('companies')\
            .select('*')\
            .range(offset, offset + limit - 1)\
            .order('created_at', desc=True)\
            .execute()
        
        return {
            "companies": result.data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_crawl_sessions_data(self, limit: int):
        """Get recent crawl sessions"""
        if not self.supabase_client:
            return {"sessions": []}
        
        result = self.supabase_client.table('crawl_sessions')\
            .select('*')\
            .order('started_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return {"sessions": result.data}
    
    async def get_source_performance_data(self):
        """Get source performance metrics"""
        if not self.supabase_client:
            return {"sources": []}
        
        result = self.supabase_client.table('source_performance')\
            .select('*')\
            .order('success_rate', desc=True)\
            .execute()
        
        return {"sources": result.data}
    
    def get_dashboard_html(self) -> str:
        """Generate dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSV Discovery Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .dashboard-container {
            display: grid;
            grid-template-columns: 250px 1fr;
            grid-template-rows: 60px 1fr;
            height: 100vh;
            gap: 1px;
        }
        
        .header {
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        
        .logo {
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .sidebar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            overflow-y: auto;
        }
        
        .main-content {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            padding: 20px;
            overflow-y: auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .activity-log {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .log-item {
            padding: 12px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .log-icon {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4CAF50;
        }
        
        .log-icon.warning { background: #FF9800; }
        .log-icon.error { background: #F44336; }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
            margin-bottom: 10px;
            width: 100%;
        }
        
        .btn:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        
        .nav-item {
            padding: 10px 0;
            color: #666;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        
        .nav-item:hover {
            color: #667eea;
        }
        
        .nav-item.active {
            color: #667eea;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header">
            <div class="logo">🚢 OSV Discovery Dashboard</div>
            <div class="status-indicator">
                <div class="status-dot" id="connection-status"></div>
                <span id="connection-text">Connected</span>
                <span id="last-update"></span>
            </div>
        </header>
        
        <aside class="sidebar">
            <button class="btn" onclick="startCrawl()">🚀 Start New Crawl</button>
            <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
            
            <div class="nav-item active" onclick="showSection('overview')">📊 Overview</div>
            <div class="nav-item" onclick="showSection('vessels')">🚢 Vessels</div>
            <div class="nav-item" onclick="showSection('companies')">🏢 Companies</div>
            <div class="nav-item" onclick="showSection('sessions')">⏱️ Crawl Sessions</div>
            <div class="nav-item" onclick="showSection('sources')">🔗 Source Performance</div>
            <div class="nav-item" onclick="showSection('media')">📸 Media Collection</div>
        </aside>
        
        <main class="main-content">
            <div id="overview-section">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="total-companies">0</div>
                        <div class="stat-label">Total Companies</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-vessels">0</div>
                        <div class="stat-label">Total Vessels</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="vessels-with-photos">0</div>
                        <div class="stat-label">Vessels with Photos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="vessels-with-specs">0</div>
                        <div class="stat-label">Vessels with Specs</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="avg-quality">0.0</div>
                        <div class="stat-label">Avg Data Quality</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="success-rate">0%</div>
                        <div class="stat-label">Crawl Success Rate</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Discovery Progress Over Time</h3>
                    <div id="progress-chart" style="height: 400px;"></div>
                </div>
                
                <div class="activity-log">
                    <h3 style="padding: 20px;">Recent Activity</h3>
                    <div id="activity-log-content">
                        <div class="log-item">
                            <div class="log-icon"></div>
                            <span>Dashboard initialized and ready</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Other sections would be dynamically loaded here -->
        </main>
    </div>

    <script>
        let ws = null;
        let stats = {};
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                console.log('WebSocket connected');
                updateConnectionStatus(true);
                // Send ping to keep connection alive
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
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }
        
        function updateConnectionStatus(connected) {
            const dot = document.getElementById('connection-status');
            const text = document.getElementById('connection-text');
            
            if (connected) {
                dot.style.background = '#4CAF50';
                text.textContent = 'Connected';
            } else {
                dot.style.background = '#F44336';
                text.textContent = 'Disconnected';
            }
        }
        
        function handleWebSocketMessage(message) {
            console.log('Received message:', message);
            
            switch(message.type) {
                case 'stats_update':
                    updateDashboardStats(message.data);
                    break;
                case 'vessel_processed':
                    addActivityLog(`Vessel processed: ${message.vessel_name}`, 'success');
                    break;
                case 'crawl_started':
                    addActivityLog('New crawl session started', 'info');
                    break;
                case 'error':
                    addActivityLog(`Error: ${message.message}`, 'error');
                    break;
            }
        }
        
        async function loadDashboardStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                updateDashboardStats(data);
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
        
        function updateDashboardStats(data) {
            stats = data;
            
            document.getElementById('total-companies').textContent = data.total_companies || 0;
            document.getElementById('total-vessels').textContent = data.total_vessels || 0;
            document.getElementById('vessels-with-photos').textContent = data.vessels_with_photos || 0;
            document.getElementById('vessels-with-specs').textContent = data.vessels_with_specs || 0;
            document.getElementById('avg-quality').textContent = (data.avg_data_quality || 0).toFixed(2);
            document.getElementById('success-rate').textContent = (data.crawl_success_rate || 0).toFixed(1) + '%';
            
            // Update last update time
            const lastUpdate = new Date(data.last_update);
            document.getElementById('last-update').textContent = `Last updated: ${lastUpdate.toLocaleTimeString()}`;
            
            // Update progress chart
            updateProgressChart();
        }
        
        function updateProgressChart() {
            const trace1 = {
                x: ['Companies', 'Vessels', 'Photos', 'Specifications'],
                y: [stats.total_companies, stats.total_vessels, stats.vessels_with_photos, stats.vessels_with_specs],
                type: 'bar',
                marker: {
                    color: ['#667eea', '#764ba2', '#f093fb', '#f5576c']
                }
            };
            
            const layout = {
                title: 'Discovery Progress',
                xaxis: { title: 'Category' },
                yaxis: { title: 'Count' },
                margin: { t: 50, r: 30, b: 50, l: 50 }
            };
            
            Plotly.newPlot('progress-chart', [trace1], layout, {responsive: true});
        }
        
        function addActivityLog(message, type = 'info') {
            const logContent = document.getElementById('activity-log-content');
            const logItem = document.createElement('div');
            logItem.className = 'log-item';
            
            const icon = document.createElement('div');
            icon.className = `log-icon ${type}`;
            
            const timestamp = new Date().toLocaleTimeString();
            logItem.innerHTML = `
                <div class="log-icon ${type}"></div>
                <span>[${timestamp}] ${message}</span>
            `;
            
            logContent.insertBefore(logItem, logContent.firstChild);
            
            // Keep only last 20 items
            while (logContent.children.length > 20) {
                logContent.removeChild(logContent.lastChild);
            }
        }
        
        async function startCrawl() {
            try {
                const response = await fetch('/api/start-crawl', { method: 'POST' });
                const result = await response.json();
                addActivityLog(result.message, 'success');
            } catch (error) {
                addActivityLog(`Failed to start crawl: ${error.message}`, 'error');
            }
        }
        
        function refreshData() {
            loadDashboardStats();
            addActivityLog('Data refreshed manually', 'info');
        }
        
        function showSection(sectionName) {
            // Hide all sections
            const sections = document.querySelectorAll('[id$="-section"]');
            sections.forEach(section => section.style.display = 'none');
            
            // Show selected section
            const targetSection = document.getElementById(`${sectionName}-section`);
            if (targetSection) {
                targetSection.style.display = 'block';
            }
            
            // Update navigation
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            loadDashboardStats();
            
            // Auto-refresh stats every 30 seconds
            setInterval(loadDashboardStats, 30000);
            
            addActivityLog('Dashboard initialized successfully', 'success');
        });
    </script>
</body>
</html>
        """
    
    async def start_background_updates(self):
        """Start background task for real-time updates"""
        async def update_loop():
            while True:
                try:
                    stats = await self.calculate_dashboard_stats()
                    message = {
                        "type": "stats_update",
                        "data": asdict(stats),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.connection_manager.broadcast(message)
                    await asyncio.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    print(f"Error in update loop: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
        
        self.update_task = asyncio.create_task(update_loop())

def create_dashboard_app() -> FastAPI:
    """Create and configure the dashboard application"""
    dashboard = OSVDashboard()
    
    @dashboard.app.on_event("startup")
    async def startup_event():
        print("🚀 OSV Dashboard starting up...")
        await dashboard.start_background_updates()
        print("✅ Dashboard ready at http://localhost:8000")
    
    @dashboard.app.on_event("shutdown")
    async def shutdown_event():
        print("🛑 OSV Dashboard shutting down...")
        if dashboard.update_task:
            dashboard.update_task.cancel()
    
    return dashboard.app

def main():
    """Run the dashboard server"""
    app = create_dashboard_app()
    
    print("🌐 Starting OSV Discovery Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
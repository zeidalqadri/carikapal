#!/usr/bin/env python3
"""
Minimal Carikapal OSV Discovery System for Railway
Simplified version that focuses on core functionality
"""

import os
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Carikapal OSV Discovery System", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def dashboard():
    """Main dashboard interface"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚢 Carikapal OSV Discovery System</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
            color: #00ff41;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            padding: 20px;
            border: 2px solid #00ff41;
            margin-bottom: 20px;
            background: rgba(0, 255, 65, 0.05);
        }
        .ascii-art {
            font-size: 12px;
            line-height: 1;
            color: #00aaff;
            margin-bottom: 15px;
        }
        .title {
            font-size: 24px;
            color: #00ff88;
            font-weight: bold;
            text-shadow: 0 0 10px #00ff88;
        }
        .subtitle {
            font-size: 14px;
            color: #666;
            margin-top: 10px;
        }
        .status-panel {
            background: rgba(0, 255, 65, 0.05);
            border: 2px solid #00ff41;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }
        .status-good { color: #00ff88; }
        .status-warning { color: #ffaa00; }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .feature-card {
            background: rgba(0, 255, 65, 0.05);
            border: 1px solid #00ff41;
            padding: 15px;
        }
        .feature-title {
            color: #00aaff;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .btn {
            background: linear-gradient(135deg, #003300 0%, #006600 100%);
            border: 1px solid #00ff41;
            color: #00ff41;
            padding: 10px 20px;
            cursor: pointer;
            font-family: inherit;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: linear-gradient(135deg, #006600 0%, #00aa00 100%);
            box-shadow: 0 0 10px #00ff41;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="ascii-art">
  ██████╗ █████╗ ██████╗ ██╗██╗  ██╗ █████╗ ██████╗  █████╗ ██╗     
 ██╔════╝██╔══██╗██╔══██╗██║██║ ██╔╝██╔══██╗██╔══██╗██╔══██╗██║     
 ██║     ███████║██████╔╝██║█████╔╝ ███████║██████╔╝███████║██║     
 ██║     ██╔══██║██╔══██╗██║██╔═██╗ ██╔══██║██╔═══╝ ██╔══██║██║     
 ╚██████╗██║  ██║██║  ██║██║██║  ██╗██║  ██║██║     ██║  ██║███████╗
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝
            </div>
            <div class="title">🚢 OSV DISCOVERY SYSTEM 🚢</div>
            <div class="subtitle">Integrated Maritime Intelligence Platform v2.0</div>
            <div class="subtitle">🌊 Malaysian Offshore Vessel Association (MOSVA) 🌊</div>
        </div>

        <div class="status-panel">
            <h3 style="color: #00aaff; margin-top: 0;">🚀 System Status</h3>
            <div class="status-item">
                <span>🌐 Web Interface</span>
                <span class="status-good">✅ ONLINE</span>
            </div>
            <div class="status-item">
                <span>🐳 Railway Deployment</span>
                <span class="status-good">✅ ACTIVE</span>
            </div>
            <div class="status-item">
                <span>🚢 Vessel Discovery</span>
                <span class="status-warning">⚠️ STANDBY</span>
            </div>
            <div class="status-item">
                <span>📊 Database Connection</span>
                <span class="status-warning">⚠️ INITIALIZING</span>
            </div>
        </div>

        <div class="features">
            <div class="feature-card">
                <div class="feature-title">🔍 Vessel Discovery</div>
                <p>Automatically discovers and tracks Malaysian offshore vessels from MOSVA member websites.</p>
                <button class="btn" onclick="alert('Discovery system ready for initialization!')">Start Discovery</button>
            </div>
            
            <div class="feature-card">
                <div class="feature-title">📸 Media Collection</div>
                <p>Collects vessel photos and specifications from maritime databases and company websites.</p>
                <button class="btn" onclick="alert('Media collection module available!')">View Media</button>
            </div>
            
            <div class="feature-card">
                <div class="feature-title">⚓ IMO Integration</div>
                <p>Enriches vessel data using International Maritime Organization (IMO) databases.</p>
                <button class="btn" onclick="alert('IMO search engine ready!')">IMO Search</button>
            </div>
            
            <div class="feature-card">
                <div class="feature-title">🏪 Marketplace Sync</div>
                <p>Synchronizes vessel data with OSV marketplace platforms for commercial intelligence.</p>
                <button class="btn" onclick="alert('Marketplace integration available!')">Sync Data</button>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #333;">
            <div style="color: #666; font-size: 12px;">
                🚢 Carikapal OSV Discovery System - Successfully deployed on Railway! ⚓<br>
                Malaysian Maritime Intelligence Platform | MOSVA Integration Active
            </div>
        </div>
    </div>

    <script>
        // Simple status updates
        console.log('🚢 Carikapal OSV Discovery System loaded successfully!');
        
        // Add some interactivity
        setInterval(() => {
            const timestamp = new Date().toLocaleTimeString();
            document.title = `🚢 Carikapal OSV Discovery System - ${timestamp}`;
        }, 1000);
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "Carikapal OSV Discovery System", "version": "2.0.0"}

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Carikapal OSV Discovery System", 
        "version": "2.0.0",
        "description": "Malaysian Maritime Intelligence Platform",
        "status": "online",
        "deployment": "railway",
        "features": [
            "Vessel Discovery Engine",
            "Media Collection System", 
            "IMO Database Integration",
            "Marketplace Synchronization"
        ]
    }

@app.get("/api/status")
async def system_status():
    """System status endpoint"""
    return {
        "web_interface": "online",
        "deployment": "railway_active", 
        "vessel_discovery": "standby",
        "database": "initializing",
        "timestamp": "live"
    }

def main():
    """Main entry point"""
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"🚢 Starting Carikapal OSV Discovery System")
    logger.info(f"🌐 Server starting on {host}:{port}")
    logger.info(f"🚀 Railway deployment active")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
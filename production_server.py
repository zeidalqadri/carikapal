#!/usr/bin/env python3
"""
Production Server for Carikapal OSV Discovery System
Optimized for Railway deployment
"""

import os
import sys
import logging
from pathlib import Path

# Add sckr directory to Python path
sys.path.append(str(Path(__file__).parent / "sckr"))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Import the enhanced dashboard
from enhanced_cli_dashboard import EnhancedCLIDashboard

def create_production_app() -> FastAPI:
    """Create production-ready FastAPI application"""
    
    # Create enhanced dashboard
    dashboard = EnhancedCLIDashboard()
    app = dashboard.app
    
    # Update CORS for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add health check endpoint for Railway
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "Carikapal OSV Discovery System"}
    
    # Root endpoint info
    @app.get("/api/info")
    async def api_info():
        return {
            "name": "Carikapal OSV Discovery System",
            "version": "2.0.0",
            "description": "Integrated Maritime Intelligence Platform",
            "endpoints": {
                "dashboard": "/",
                "api": "/api/*",
                "websocket": "/ws",
                "health": "/health"
            }
        }
    
    return app

def main():
    """Main entry point for production server"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Get port from environment (Railway provides this)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"🚂 Starting Carikapal OSV Discovery System on Railway")
    logger.info(f"🌐 Server will be available on port {port}")
    
    # Create production app
    app = create_production_app()
    
    # Start server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=False,
        access_log=True
    )

if __name__ == "__main__":
    main()
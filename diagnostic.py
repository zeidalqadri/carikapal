#!/usr/bin/env python3
"""
Railway-specific diagnostic version
"""

import os
import sys
import logging
import signal
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

# Force immediate output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

logger.info("🚂 RAILWAY DIAGNOSTIC STARTING")
logger.info(f"Python: {sys.version}")
logger.info(f"PORT env: {os.environ.get('PORT', 'NOT_SET')}")

# Create app
app = FastAPI(title="Railway Diagnostic", docs_url=None, redoc_url=None)

@app.get("/")
async def root():
    return PlainTextResponse("Railway Diagnostic Online - Carikapal OSV System")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/healthz")  # Kubernetes-style health check
async def healthz():
    return PlainTextResponse("OK")

@app.get("/ping")
async def ping():
    return PlainTextResponse("pong")

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}")
    sys.exit(0)

def main():
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get port - Railway provides this
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting on 0.0.0.0:{port}")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=False,  # Reduce logging
            timeout_keep_alive=5,
            timeout_graceful_shutdown=5
        )
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
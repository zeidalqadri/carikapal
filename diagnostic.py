#!/usr/bin/env python3
"""
Diagnostic version to identify Railway startup issues
"""

import os
import sys
import logging
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup sequence
logger.info("=" * 50)
logger.info("🚢 CARIKAPAL DIAGNOSTIC STARTUP")
logger.info("=" * 50)

# Log environment
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"PORT env var: {os.environ.get('PORT', 'NOT SET')}")
logger.info(f"All env vars: {list(os.environ.keys())}")

# Create minimal FastAPI app
logger.info("Creating FastAPI app...")
app = FastAPI(title="Carikapal Diagnostic")

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Carikapal Diagnostic Online", "status": "ok"}

@app.get("/health")
async def health():
    logger.info("Health endpoint called")
    return {"status": "healthy", "diagnostic": "working"}

@app.get("/debug")
async def debug():
    logger.info("Debug endpoint called")
    return {
        "port": os.environ.get('PORT', 'not_set'),
        "host": "0.0.0.0",
        "python": sys.version,
        "cwd": os.getcwd(),
        "env_count": len(os.environ)
    }

def main():
    try:
        # Get port from environment
        port = int(os.environ.get("PORT", 8000))
        host = "0.0.0.0"
        
        logger.info(f"Attempting to start server on {host}:{port}")
        
        # Log before startup
        logger.info("About to call uvicorn.run...")
        
        # Start server with minimal config
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="debug",
            access_log=True,
            timeout_keep_alive=30,
            timeout_graceful_shutdown=10
        )
        
    except Exception as e:
        logger.error(f"STARTUP FAILED: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Script started, calling main()...")
    main()
    logger.info("main() returned (this shouldn't happen)")
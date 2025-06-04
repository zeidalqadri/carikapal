#!/usr/bin/env python3
"""
Diagnostic entry point
"""

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("🔍 Starting diagnostic version...")

from diagnostic import main

if __name__ == "__main__":
    main()
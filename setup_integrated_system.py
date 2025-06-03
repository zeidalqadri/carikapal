#!/usr/bin/env python3
"""
Setup Script for Integrated OSV Discovery System
Automatically installs and configures all dependencies and components
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json
import requests

def print_header():
    """Print setup header"""
    print("=" * 80)
    print("🌊 INTEGRATED OSV DISCOVERY SYSTEM - AUTOMATIC SETUP")
    print("=" * 80)
    print("This script will set up the complete integrated system with all components")
    print()

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """Install all required packages"""
    print("\n📦 Installing required packages...")
    
    packages = [
        "requests>=2.31.0",
        "aiohttp>=3.9.0", 
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "pandas>=2.1.0",
        "supabase>=2.0.0",
        "PyMuPDF>=1.23.0",
        "Pillow>=10.0.0",
        "pyyaml>=6.0.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "asyncpg>=0.29.0",
        "tqdm>=4.65.0",
        "colorama>=0.4.6",
        "websockets>=12.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        try:
            print(f"📦 Installing {package.split('>=')[0]}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"  ✅ {package.split('>=')[0]} installed")
        except subprocess.CalledProcessError:
            print(f"  ❌ {package.split('>=')[0]} failed")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️ Some packages failed to install: {failed_packages}")
        print("You may need to install them manually")
    else:
        print("✅ All packages installed successfully")
    
    return len(failed_packages) == 0

def create_directory_structure():
    """Create required directory structure"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "osv_data",
        "osv_data/vessels", 
        "osv_data/companies",
        "osv_data/media",
        "logs",
        "cache",
        "cache/photos",
        "cache/documents", 
        "cache/registry",
        "vessel_media",
        "vessel_media/photos",
        "vessel_media/documents",
        "imo_search_cache",
        "config"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 {directory}")
    
    print("✅ Directory structure created")
    return True

def test_supabase_connection():
    """Test Supabase database connection"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from supabase import create_client
        
        url = "https://juvqqrsdbruskleodzip.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw"
        
        client = create_client(url, key)
        result = client.table('vessels').select('id').limit(1).execute()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"⚠️ Database connection test failed: {e}")
        print("The system will still work, but database features may be limited")
        return True  # Continue setup anyway

def create_startup_scripts():
    """Create platform-specific startup scripts"""
    print("\n🔧 Creating startup scripts...")
    
    # Get current directory
    current_dir = Path.cwd()
    python_exe = sys.executable
    
    if platform.system() == "Windows":
        # Windows batch files
        dashboard_script = f"""@echo off
title Enhanced OSV Discovery System Dashboard
echo Starting Enhanced OSV Discovery System Dashboard...
cd /d "{current_dir}"
"{python_exe}" enhanced_cli_dashboard.py
pause
"""
        
        integrated_script = f"""@echo off
title Integrated OSV Discovery System
echo Starting Integrated OSV Discovery System...
cd /d "{current_dir}"
"{python_exe}" integrated_osv_system.py full-system
pause
"""
        
        with open("start_enhanced_dashboard.bat", "w") as f:
            f.write(dashboard_script)
        
        with open("start_integrated_system.bat", "w") as f:
            f.write(integrated_script)
        
        print("  ✅ Windows batch files created")
        print("    - start_enhanced_dashboard.bat")
        print("    - start_integrated_system.bat")
    
    else:
        # Unix shell scripts
        dashboard_script = f"""#!/bin/bash
echo "Starting Enhanced OSV Discovery System Dashboard..."
cd "{current_dir}"
"{python_exe}" enhanced_cli_dashboard.py
"""
        
        integrated_script = f"""#!/bin/bash
echo "Starting Integrated OSV Discovery System..."
cd "{current_dir}"
"{python_exe}" integrated_osv_system.py full-system
"""
        
        with open("start_enhanced_dashboard.sh", "w") as f:
            f.write(dashboard_script)
        os.chmod("start_enhanced_dashboard.sh", 0o755)
        
        with open("start_integrated_system.sh", "w") as f:
            f.write(integrated_script)
        os.chmod("start_integrated_system.sh", 0o755)
        
        print("  ✅ Unix shell scripts created")
        print("    - start_enhanced_dashboard.sh")
        print("    - start_integrated_system.sh")

def create_configuration_files():
    """Create configuration files"""
    print("\n⚙️ Creating configuration files...")
    
    # Create config.yaml
    config_content = {
        'system': {
            'name': 'Integrated OSV Discovery System',
            'version': '2.0.0',
            'environment': 'production'
        },
        'database': {
            'supabase_url': 'https://juvqqrsdbruskleodzip.supabase.co',
            'supabase_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw'
        },
        'crawler': {
            'max_workers': 4,
            'rate_limit_delay': 1.5,
            'enable_media_collection': True,
            'enable_specification_parsing': True,
            'max_photos_per_vessel': 5
        },
        'dashboard': {
            'host': '0.0.0.0',
            'port': 8000,
            'auto_refresh_interval': 30
        }
    }
    
    import yaml
    with open("config/system_config.yaml", "w") as f:
        yaml.dump(config_content, f, default_flow_style=False, indent=2)
    
    # Create .env file
    env_content = """# Integrated OSV Discovery System Environment Variables
SUPABASE_URL=https://juvqqrsdbruskleodzip.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1dnFxcnNkYnJ1c2tsZW9kemlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNzYyOTUsImV4cCI6MjA1OTc1MjI5NX0.lEP07y-D7S70hpd-Ob62v4VyDx9ZyaaLN7yUK-3tvIw

# System Configuration
OSV_MAX_WORKERS=4
OSV_RATE_LIMIT=1.5
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000
LOG_LEVEL=INFO
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("  ✅ Configuration files created")
    print("    - config/system_config.yaml")
    print("    - .env")

def test_system_components():
    """Test all system components"""
    print("\n🧪 Testing system components...")
    
    # Test imports
    test_imports = [
        "requests", "aiohttp", "beautifulsoup4", "pandas",
        "supabase", "fastapi", "uvicorn", "yaml", "PIL"
    ]
    
    failed_imports = []
    for module in test_imports:
        try:
            if module == "beautifulsoup4":
                import bs4
            elif module == "PIL":
                import PIL
            else:
                __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"⚠️ Failed imports: {failed_imports}")
        return False
    
    print("✅ All component tests passed")
    return True

def create_readme():
    """Create comprehensive README"""
    print("\n📖 Creating README...")
    
    readme_content = f"""# Integrated OSV Discovery System v2.0

## 🌊 Overview
Complete integrated vessel discovery and tracking system for Malaysian maritime industry, specifically focused on MOSVA (Malaysian Offshore Vessel Association) members.

## 🚀 Quick Start

### Option 1: Enhanced CLI Dashboard
```bash
# Windows
start_enhanced_dashboard.bat

# Linux/Mac
./start_enhanced_dashboard.sh

# Or directly with Python
python enhanced_cli_dashboard.py
```

### Option 2: Full Integrated System
```bash
# Windows
start_integrated_system.bat

# Linux/Mac  
./start_integrated_system.sh

# Or directly with Python
python integrated_osv_system.py full-system
```

### Dashboard Access
Open your browser and go to: **http://localhost:8000**

## 🔧 System Components

### Core Modules
- **Vessel Discovery**: Automated crawling of MOSVA member websites
- **Media Collection**: Photos and specification document collection
- **IMO Search**: Advanced search across maritime databases
- **Marketplace Integration**: Synchronization with OSV marketplace
- **Real-time Dashboard**: Web-based monitoring interface
- **Database Integration**: Supabase database with comprehensive vessel data

### Integrated Features
- ✅ Comprehensive vessel data collection
- ✅ Automated photo and document collection
- ✅ IMO-based vessel enrichment
- ✅ Real-time progress monitoring
- ✅ CLI-style terminal interface
- ✅ Marketplace synchronization
- ✅ Data quality scoring
- ✅ Component health monitoring

## 📁 Directory Structure
```
{Path.cwd().name}/
├── sckr/                    # Core system modules
├── osv_data/               # Vessel data storage
├── logs/                   # System logs
├── cache/                  # Temporary cache files
├── vessel_media/           # Downloaded photos and documents
├── config/                 # Configuration files
├── integrated_osv_system.py       # Main integrated system
├── enhanced_cli_dashboard.py      # Enhanced CLI dashboard
└── setup_integrated_system.py    # This setup script
```

## ⚙️ Configuration
- **Main Config**: `config/system_config.yaml`
- **Environment**: `.env`
- **Database**: Pre-configured Supabase connection

## 🎯 Usage Examples

### Initialize and Run Full Discovery
```python
python integrated_osv_system.py discovery --enable-media --enable-imo
```

### Start Dashboard Only
```python
python enhanced_cli_dashboard.py
```

### Check System Status
```python
python integrated_osv_system.py status
```

### Install/Reinstall System
```python
python integrated_osv_system.py install
```

## 🔍 Features in Detail

### 1. Vessel Discovery
- Parses MOSVA member data
- Discovers company websites automatically
- Extracts vessel information from web pages
- Validates and scores data quality

### 2. Media Collection
- Searches multiple maritime photo databases
- Downloads vessel photos and specifications
- Processes and optimizes media files
- Extracts text from PDF documents

### 3. IMO Enhancement
- Searches comprehensive IMO databases
- Enriches vessel data with additional information
- Calculates confidence scores
- Tracks source reliability

### 4. Real-time Monitoring
- CLI-style terminal interface
- Live progress tracking
- Component health monitoring
- WebSocket-based updates

## 🏪 Marketplace Integration
Seamlessly integrates with OSV marketplace platform for:
- Automated listing creation
- Data synchronization
- Commercial information processing
- Availability status tracking

## 📊 Database Schema
- **Vessels**: Comprehensive vessel information
- **Companies**: MOSVA member company data
- **Vessel Media**: Photos and documents
- **Vessel Specifications**: Technical specifications
- **Crawl Sessions**: Discovery session tracking

## 🛠️ Troubleshooting

### Common Issues
1. **Import Errors**: Run `python setup_integrated_system.py` again
2. **Database Connection**: Check internet connection and Supabase status
3. **Port 8000 in Use**: Change port in configuration or kill existing process

### Logs
- System logs: `logs/`
- Component logs: Check dashboard for real-time status

## 📈 Performance
- **Concurrent Processing**: Multi-threaded vessel discovery
- **Rate Limiting**: Respectful website crawling
- **Caching**: Intelligent caching of search results
- **Progress Tracking**: Real-time progress monitoring

## 🔐 Security
- Environment variable configuration
- Rate limiting to prevent abuse
- Data validation and sanitization
- Secure database connections

## 🎉 Setup Complete!
Installation date: {Path('setup_integrated_system.py').stat().st_mtime}
Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
Platform: {platform.system()} {platform.release()}

Ready to discover and track OSV fleet data! 🚢
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("  ✅ README.md created")

def main():
    """Main setup function"""
    print_header()
    
    success = True
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Python version incompatible")
        return False
    
    # Install requirements
    if not install_requirements():
        print("\n⚠️ Some packages failed to install, but continuing...")
    
    # Create directory structure
    if not create_directory_structure():
        success = False
    
    # Test database connection
    test_supabase_connection()
    
    # Create configuration files
    create_configuration_files()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Test system components
    if not test_system_components():
        print("\n⚠️ Some components failed tests, but system may still work")
    
    # Create README
    create_readme()
    
    # Final summary
    print("\n" + "=" * 80)
    if success:
        print("🎉 INTEGRATED OSV DISCOVERY SYSTEM SETUP COMPLETE!")
        print("=" * 80)
        print("🚀 Quick Start Options:")
        print()
        if platform.system() == "Windows":
            print("   1. Double-click 'start_enhanced_dashboard.bat' for CLI dashboard")
            print("   2. Double-click 'start_integrated_system.bat' for full system")
        else:
            print("   1. Run './start_enhanced_dashboard.sh' for CLI dashboard")
            print("   2. Run './start_integrated_system.sh' for full system")
        print("   3. Open http://localhost:8000 in your browser")
        print()
        print("📖 See README.md for complete documentation")
        print("🌊 Ready to discover maritime intelligence!")
    else:
        print("❌ SETUP ENCOUNTERED ISSUES")
        print("=" * 80)
        print("Check the error messages above and try running setup again")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

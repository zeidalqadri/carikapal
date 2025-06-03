# Integrated OSV Discovery System v2.0

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
app/
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
Installation date: 1748968307.3630614
Python version: 3.11.12
Platform: Linux 6.6.72+

Ready to discover and track OSV fleet data! 🚢

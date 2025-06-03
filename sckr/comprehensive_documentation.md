# OSV Discovery System - Comprehensive Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [System Architecture](#system-architecture)
4. [Installation & Deployment](#installation--deployment)
5. [Configuration](#configuration)
6. [API Documentation](#api-documentation)
7. [User Guide](#user-guide)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)
10. [Maintenance](#maintenance)

---

## System Overview

### What is the OSV Discovery System?

The OSV (Offshore Support Vessel) Discovery System is a comprehensive, automated platform for discovering, collecting, analyzing, and managing vessel data from Malaysian maritime companies, specifically focusing on MOSVA (Malaysian Offshore Vessel Association) members.

### Key Features

🚢 **Comprehensive Vessel Discovery**
- Automated crawling of MOSVA member websites
- Smart website discovery and validation
- Multi-source vessel data collection

📸 **Media Collection**
- Automated photo collection from multiple maritime databases
- Specification document download and parsing
- Image processing and optimization

🗄️ **Database Integration**
- Real-time sync with Supabase database
- Comprehensive vessel data schema
- Performance tracking and analytics

📊 **Real-time Dashboard**
- Live monitoring of discovery operations
- Interactive data visualization
- Real-time statistics and progress tracking

🔍 **Advanced Search**
- IMO-based vessel search across multiple sources
- Intelligent data merging and quality scoring
- Reliable source performance tracking

🏪 **Marketplace Integration**
- Seamless integration with OSV marketplace platform
- Automated listing creation and management
- Commercial data processing

### System Components

1. **MOSVA Data Parser** - Extracts company information from MOSVA member data
2. **Website Discovery Engine** - Finds and validates company websites
3. **Vessel Discovery Module** - Locates vessel pages on company websites
4. **Data Extraction Engine** - Extracts structured vessel data
5. **Media Collector** - Downloads photos and specification documents
6. **IMO Search Engine** - Advanced search across maritime databases
7. **Database Manager** - Handles Supabase integration and data persistence
8. **Real-time Dashboard** - Web-based monitoring and control interface
9. **Marketplace Sync** - Integration with marketplace platform

---

## Quick Start Guide

### Prerequisites
- Python 3.8 or higher
- 5GB free disk space
- Internet connection
- Supabase account (provided)

### Installation
```bash
# 1. Download and extract the system
git clone <repository-url>
cd osv-discovery-system

# 2. Run automated deployment
python deployment_manager.py

# 3. Start the dashboard
./start_dashboard.sh  # Linux/Mac
# OR
start_dashboard.bat   # Windows

# 4. Open browser
http://localhost:8000
```

### First Run
1. Access the dashboard at http://localhost:8000
2. Click "Start New Crawl" to begin discovery
3. Monitor progress in real-time
4. View discovered vessels in the Vessels section
5. Check data quality scores and media collection

---

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Sources   │────│  OSV Discovery  │────│   Supabase DB   │
│  (MOSVA, etc.)  │    │     System      │    │   (Vessels)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                       ┌─────────────────┐
                       │  Dashboard UI   │
                       │ (Real-time web) │
                       └─────────────────┘
```

### Component Architecture
```
OSV Discovery System
├── Data Collection Layer
│   ├── MOSVA Parser
│   ├── Website Discovery
│   ├── Vessel Page Discovery
│   ├── Data Extraction
│   └── Media Collection
├── Processing Layer
│   ├── Data Validation
│   ├── Quality Scoring
│   ├── Specification Parsing
│   └── Image Processing
├── Storage Layer
│   ├── Supabase Integration
│   ├── Local Cache
│   └── Media Storage
├── API Layer
│   ├── RESTful APIs
│   ├── WebSocket Events
│   └── Real-time Updates
└── Presentation Layer
    ├── Web Dashboard
    ├── Real-time Monitoring
    └── Data Visualization
```

### Data Flow
1. **Discovery Phase**: Parse MOSVA data → Find company websites → Discover vessel pages
2. **Extraction Phase**: Extract vessel data → Download media → Parse specifications
3. **Processing Phase**: Validate data → Calculate quality scores → Merge duplicates
4. **Storage Phase**: Save to database → Cache locally → Update marketplace
5. **Presentation Phase**: Real-time dashboard updates → API responses

---

## Installation & Deployment

### Automated Deployment
The system includes a comprehensive deployment manager that handles the complete setup process.

```bash
python deployment_manager.py
```

### Manual Installation Steps

#### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

#### 2. Install Dependencies
```bash
# Install from requirements file
pip install -r requirements.txt

# Or install manually
pip install requests aiohttp beautifulsoup4 pandas supabase PyMuPDF Pillow fastapi uvicorn
```

#### 3. Directory Structure
```
osv-discovery-system/
├── osv_data/
│   ├── vessels/
│   ├── companies/
│   └── media/
├── logs/
├── cache/
│   ├── photos/
│   ├── documents/
│   └── registry/
├── config/
├── vessel_media/
│   ├── photos/
│   └── documents/
└── scripts/
```

#### 4. Configuration Files
Create `config/osv_config.yaml`:
```yaml
system:
  name: "OSV Discovery System"
  version: "1.0.0"
  environment: "production"

database:
  supabase_url: "https://juvqqrsdbruskleodzip.supabase.co"
  supabase_key: "your_supabase_key_here"

crawler:
  max_workers: 4
  rate_limit_delay: 1.5
  enable_media_collection: true
  max_photos_per_vessel: 5

dashboard:
  host: "0.0.0.0"
  port: 8000
  auto_refresh_interval: 30
```

Create `.env` file:
```bash
SUPABASE_URL=https://juvqqrsdbruskleodzip.supabase.co
SUPABASE_KEY=your_supabase_key_here
OSV_MAX_WORKERS=4
DASHBOARD_PORT=8000
LOG_LEVEL=INFO
```

---

## Configuration

### Main Configuration File: `config/osv_config.yaml`

#### System Settings
```yaml
system:
  name: "OSV Discovery System"
  version: "1.0.0"
  environment: "production"  # development, staging, production
```

#### Database Configuration
```yaml
database:
  supabase_url: "https://your-project.supabase.co"
  supabase_key: "your-anon-key"
```

#### Crawler Settings
```yaml
crawler:
  max_workers: 4                    # Number of concurrent workers
  rate_limit_delay: 1.5            # Delay between requests (seconds)
  request_timeout: 30              # Request timeout (seconds)
  retry_attempts: 3                # Number of retry attempts
  enable_media_collection: true    # Enable photo/document collection
  enable_specification_parsing: true  # Enable spec document parsing
  max_photos_per_vessel: 5         # Maximum photos to collect per vessel
  min_quality_score: 0.1           # Minimum data quality to save
```

#### Dashboard Settings
```yaml
dashboard:
  host: "0.0.0.0"                  # Dashboard host (0.0.0.0 for all interfaces)
  port: 8000                       # Dashboard port
  auto_refresh_interval: 30        # Auto-refresh interval (seconds)
  max_log_entries: 100            # Maximum log entries to display
```

#### Logging Configuration
```yaml
logging:
  level: "INFO"                    # DEBUG, INFO, WARNING, ERROR
  file_rotation: true              # Enable log file rotation
  max_file_size_mb: 50            # Maximum log file size
  backup_count: 5                 # Number of backup log files
  console_output: true            # Enable console logging
```

### Environment Variables
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Crawler
OSV_MAX_WORKERS=4
OSV_RATE_LIMIT=1.5
OSV_ENABLE_PATCHING=true

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

---

## API Documentation

### REST API Endpoints

#### Dashboard Statistics
```http
GET /api/stats
```
Returns current system statistics.

**Response:**
```json
{
  "total_companies": 47,
  "total_vessels": 156,
  "vessels_with_photos": 89,
  "vessels_with_specs": 67,
  "avg_data_quality": 0.75,
  "crawl_success_rate": 82.5,
  "last_update": "2024-12-03T10:30:00Z"
}
```

#### Vessel List
```http
GET /api/vessels?limit=50&offset=0&search=Perdana&vessel_type=OSV
```
Returns paginated vessel list with optional filtering.

**Parameters:**
- `limit`: Number of results (default: 50)
- `offset`: Starting position (default: 0)
- `search`: Search term for vessel name/owner
- `vessel_type`: Filter by vessel type

**Response:**
```json
{
  "vessels": [
    {
      "id": "uuid",
      "vessel_name": "Perdana Express",
      "imo_number": "1234567",
      "vessel_type": "OSV",
      "owner_company": "Perdana Petroleum Berhad",
      "data_quality_score": 0.85
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

#### Company List
```http
GET /api/companies?limit=50&offset=0
```
Returns paginated company list.

#### Crawl Sessions
```http
GET /api/crawl-sessions?limit=20
```
Returns recent crawl session history.

#### Source Performance
```http
GET /api/source-performance
```
Returns performance metrics for external data sources.

#### Start Crawl
```http
POST /api/start-crawl
```
Initiates a new crawl session.

### WebSocket Events

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

#### Events Received
- `stats_update`: Real-time statistics updates
- `vessel_processed`: Individual vessel processing completion
- `crawl_started`: New crawl session initiated
- `crawl_complete`: Crawl session completed
- `error`: Error notifications

#### Events Sent
- `ping`: Keep-alive ping (responds with `pong`)

### Python API Usage

#### Direct System Integration
```python
from complete_osv_system import OSVSystemConfig, ComprehensiveVesselDiscovery

# Initialize system
config = OSVSystemConfig()
system = ComprehensiveVesselDiscovery(config)

# Run discovery
await system.initialize_system()
results = await system.run_comprehensive_discovery()
```

#### Marketplace Integration
```python
from marketplace_integration import MarketplaceIntegrationManager

# Initialize marketplace manager
manager = MarketplaceIntegrationManager(supabase_url, supabase_key)

# Run full integration cycle
results = await manager.full_integration_cycle()
```

---

## User Guide

### Dashboard Overview

#### Main Dashboard Sections
1. **Overview**: System statistics and key metrics
2. **Vessels**: Complete vessel database with search/filter
3. **Companies**: MOSVA member companies
4. **Sessions**: Crawl session history and performance
5. **Sources**: External source performance monitoring
6. **Media**: Photo and document collection status

#### Starting a Discovery Session
1. Access dashboard at http://localhost:8000
2. Click "🚀 Start New Crawl" in the sidebar
3. Monitor progress in real-time on the Overview section
4. View activity log for detailed progress information

#### Monitoring Progress
- **Real-time Statistics**: Updated every 30 seconds
- **Activity Log**: Live feed of system operations
- **Progress Charts**: Visual representation of discovery progress
- **Error Tracking**: Real-time error notifications

### Data Management

#### Vessel Data Quality
- **Quality Score**: 0.0 - 1.0 based on data completeness
- **Verification Status**: Unverified, Pending, Verified
- **Source Tracking**: Multiple sources per vessel for reliability

#### Photo Management
- **Automatic Collection**: Photos from maritime databases
- **Quality Filtering**: Confidence-based photo selection
- **Local Storage**: Downloaded and optimized for fast access
- **Thumbnail Generation**: Automatic thumbnail creation

#### Document Processing
- **Specification Sheets**: Automatic download and parsing
- **Text Extraction**: OCR and text processing
- **Structured Data**: Extraction of technical specifications

### Search and Filtering

#### Vessel Search
- **Text Search**: Vessel name, owner, IMO number
- **Type Filtering**: Filter by vessel type/category
- **Quality Filtering**: Filter by data quality score
- **Availability**: Filter by availability status

#### Advanced Filtering
- **Date Ranges**: Filter by build year, last update
- **Specifications**: Filter by size, capacity, equipment
- **Location**: Filter by flag state, home port
- **Commercial**: Filter by day rate, availability

---

## Troubleshooting

### Common Issues

#### 1. Installation Problems

**Issue**: "Python version not supported"
**Solution**: 
```bash
# Check Python version
python --version
# Install Python 3.8+ from python.org
```

**Issue**: "Permission denied during installation"
**Solution**:
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**Issue**: "Dependencies failed to install"
**Solution**:
```bash
# Update pip first
pip install --upgrade pip
# Install dependencies one by one
pip install requests beautifulsoup4 pandas
```

#### 2. Database Connection Issues

**Issue**: "Supabase connection failed"
**Solution**:
1. Verify Supabase URL and key in configuration
2. Check internet connectivity
3. Verify Supabase project status
4. Check firewall settings

**Issue**: "Database schema not found"
**Solution**:
1. Apply database schema from `supabase_schema_setup.sql`
2. Verify table creation in Supabase dashboard
3. Check user permissions

#### 3. Crawler Issues

**Issue**: "No vessels found"
**Solution**:
1. Check MOSVA data files existence
2. Verify website accessibility
3. Review rate limiting settings
4. Check network connectivity

**Issue**: "Rate limiting errors"
**Solution**:
```yaml
# Increase delays in config
crawler:
  rate_limit_delay: 3.0  # Increase from 1.5
  request_timeout: 60    # Increase from 30
```

**Issue**: "Memory errors during crawling"
**Solution**:
```yaml
# Reduce worker count
crawler:
  max_workers: 2  # Reduce from 4
```

#### 4. Dashboard Issues

**Issue**: "Dashboard not accessible"
**Solution**:
1. Check if port 8000 is available
2. Verify dashboard process is running
3. Check firewall settings
4. Try different port in configuration

**Issue**: "Real-time updates not working"
**Solution**:
1. Check WebSocket connection in browser console
2. Verify no proxy blocking WebSockets
3. Restart dashboard service

### Log Analysis

#### Log Locations
- **System Logs**: `logs/osv_discovery_YYYYMMDD_HHMMSS.log`
- **Deployment Logs**: `deployment_logs/deployment_YYYYMMDD_HHMMSS.log`
- **Error Logs**: Included in main system logs

#### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning messages (non-critical)
- **ERROR**: Error messages (critical issues)

#### Common Log Messages
```
[INFO] Starting MOSVA vessel discovery
[INFO] Found 47 companies from MOSVA data
[INFO] Website found: https://company.com
[WARNING] No working website found for Company XYZ
[ERROR] Failed to extract vessels from https://example.com: Timeout
```

### Performance Monitoring

#### System Metrics
- **Memory Usage**: Monitor via dashboard or system tools
- **Disk Space**: Check available space in data directories
- **Network Usage**: Monitor for rate limiting issues
- **Database Performance**: Check Supabase dashboard

#### Performance Optimization
1. **Reduce Worker Count**: If memory issues occur
2. **Increase Rate Limits**: If getting blocked by websites
3. **Disable Media Collection**: To reduce bandwidth usage
4. **Increase Cache Duration**: To reduce redundant requests

---

## Performance Optimization

### Crawler Performance

#### Optimal Configuration
```yaml
# For development/testing
crawler:
  max_workers: 2
  rate_limit_delay: 2.0
  enable_media_collection: false

# For production
crawler:
  max_workers: 4
  rate_limit_delay: 1.5
  enable_media_collection: true
```

#### Memory Optimization
- **Batch Processing**: Process vessels in smaller batches
- **Cache Management**: Regular cache cleanup
- **Image Optimization**: Reduce image sizes for storage
- **Database Indexing**: Proper indexing for fast queries

#### Network Optimization
- **Connection Pooling**: Reuse HTTP connections
- **Compression**: Enable gzip compression
- **CDN Usage**: Use CDN for static assets
- **Rate Limiting**: Respect website rate limits

### Database Performance

#### Query Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_vessels_owner ON vessels(owner_company);
CREATE INDEX idx_vessels_type ON vessels(vessel_type);
CREATE INDEX idx_vessels_updated ON vessels(updated_at);
```

#### Data Archiving
- **Old Records**: Archive vessels not updated in 6+ months
- **Log Rotation**: Automatic log file rotation
- **Cache Cleanup**: Regular cleanup of temporary files

### System Monitoring

#### Key Metrics to Monitor
1. **Discovery Rate**: Vessels processed per hour
2. **Success Rate**: Percentage of successful discoveries
3. **Data Quality**: Average quality score
4. **Error Rate**: Number of errors per session
5. **Response Time**: Average API response time

#### Alerting
- **High Error Rate**: > 20% errors in session
- **Low Success Rate**: < 50% successful discoveries
- **System Resources**: > 80% memory/disk usage
- **Database Issues**: Connection failures or timeouts

---

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor dashboard for errors
- Check system logs for issues
- Verify data quality metrics
- Review crawl session results

#### Weekly
- Clean up cache directories
- Review source performance metrics
- Update vessel data quality scores
- Check disk space usage

#### Monthly
- Archive old log files
- Review and update configuration
- Performance optimization review
- Database maintenance (indexing, cleanup)

#### Quarterly
- System backup and recovery testing
- Dependency updates
- Security review
- Performance benchmarking

### Backup and Recovery

#### Database Backup
- **Automated**: Supabase automatic backups
- **Manual**: Export critical data regularly
- **Testing**: Verify backup restoration procedures

#### System Backup
```bash
# Backup configuration and data
tar -czf osv_backup_$(date +%Y%m%d).tar.gz \
  config/ osv_data/ logs/ deployment_summary.json
```

#### Recovery Procedures
1. **System Recovery**: Restore from backup and reconfigure
2. **Database Recovery**: Use Supabase backup restoration
3. **Configuration Recovery**: Restore configuration files
4. **Data Recovery**: Re-run discovery if needed

### System Updates

#### Updating Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Update all packages
pip install --upgrade -r requirements.txt

# Or update specific packages
pip install --upgrade supabase requests beautifulsoup4
```

#### System Configuration Updates
1. Update configuration files
2. Test changes in development
3. Deploy to production
4. Monitor for issues

#### Database Schema Updates
1. Apply schema changes to Supabase
2. Update application code
3. Test data migration
4. Deploy updates

---

## Support and Resources

### Getting Help
1. **Check Logs**: Review system logs for error details
2. **Documentation**: Refer to this comprehensive guide
3. **Configuration**: Verify all configuration settings
4. **Community**: Reach out for community support

### Useful Resources
- **Supabase Documentation**: https://supabase.com/docs
- **MOSVA Website**: https://mosva.org.my
- **Python Documentation**: https://docs.python.org
- **FastAPI Documentation**: https://fastapi.tiangolo.com

### System Information
- **Version**: 1.0.0
- **Last Updated**: December 2024
- **Python Requirement**: 3.8+
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML5 + JavaScript
- **Architecture**: Modular Python system

---

*This documentation covers the complete OSV Discovery System. For specific implementation details, refer to the individual module documentation and source code comments.*
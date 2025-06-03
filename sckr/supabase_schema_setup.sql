-- Supabase Database Schema for OSV Marketplace
-- Complete schema for vessel data, companies, and media

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Companies table (MOSVA members and operators)
CREATE TABLE IF NOT EXISTS companies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    phone TEXT,
    fax TEXT,
    website TEXT,
    email TEXT,
    member_type TEXT CHECK (member_type IN ('ordinary', 'associate', 'other')),
    country TEXT DEFAULT 'Malaysia',
    verified BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    data_source TEXT DEFAULT 'mosva_crawler'
);

-- Vessels table (main vessel registry)
CREATE TABLE IF NOT EXISTS vessels (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Basic identification
    vessel_name TEXT NOT NULL,
    imo_number TEXT UNIQUE,
    mmsi_number TEXT,
    call_sign TEXT,
    official_number TEXT,
    
    -- Company relationships
    owner_company_id UUID REFERENCES companies(id),
    owner_company TEXT, -- Fallback text field
    operator_company_id UUID REFERENCES companies(id),
    operator_company TEXT, -- Fallback text field
    company_website TEXT,
    
    -- Registration and legal
    flag_state TEXT,
    port_of_registry TEXT,
    classification_society TEXT,
    class_notation TEXT,
    
    -- Vessel type and category
    vessel_type TEXT,
    vessel_subtype TEXT,
    operational_category TEXT,
    
    -- Construction details
    builder_shipyard TEXT,
    builder_location TEXT,
    build_year INTEGER,
    delivery_date DATE,
    
    -- Physical dimensions
    length_overall_m DECIMAL(8,2),
    length_between_perpendiculars_m DECIMAL(8,2),
    beam_m DECIMAL(6,2),
    depth_m DECIMAL(6,2),
    draft_design_m DECIMAL(6,2),
    draft_maximum_m DECIMAL(6,2),
    
    -- Tonnage and capacity
    gross_tonnage DECIMAL(10,2),
    net_tonnage DECIMAL(10,2),
    deadweight_tonnage DECIMAL(10,2),
    cargo_capacity_cbm DECIMAL(10,2),
    fuel_capacity_cbm DECIMAL(10,2),
    freshwater_capacity_cbm DECIMAL(10,2),
    ballast_capacity_cbm DECIMAL(10,2),
    
    -- Propulsion and performance
    main_engine_make TEXT,
    main_engine_model TEXT,
    main_engine_power_kw DECIMAL(10,2),
    propulsion_type TEXT,
    max_speed_knots DECIMAL(4,1),
    service_speed_knots DECIMAL(4,1),
    fuel_consumption_tonnes_day DECIMAL(6,2),
    
    -- OSV-specific equipment
    crane_capacity_tonnes DECIMAL(8,2),
    crane_details TEXT,
    deck_area_sqm DECIMAL(8,2),
    deck_load_capacity_tonnes DECIMAL(8,2),
    accommodation_persons INTEGER,
    helicopter_deck BOOLEAN DEFAULT FALSE,
    moon_pool BOOLEAN DEFAULT FALSE,
    
    -- Dynamic positioning and offshore capabilities
    dynamic_positioning_system TEXT,
    dp_class TEXT,
    working_depth_m DECIMAL(8,2),
    rov_capability BOOLEAN DEFAULT FALSE,
    diving_support BOOLEAN DEFAULT FALSE,
    
    -- Commercial and operational
    home_port TEXT,
    current_location TEXT,
    current_status TEXT,
    employment_status TEXT,
    availability_status TEXT,
    day_rate_usd DECIMAL(12,2),
    
    -- Maintenance and certification
    last_drydock_date DATE,
    next_drydock_due DATE,
    last_survey_date DATE,
    next_survey_due DATE,
    
    -- Environmental
    marpol_annexes TEXT[],
    ballast_water_treatment TEXT,
    green_passport BOOLEAN DEFAULT FALSE,
    
    -- Data quality and provenance
    source_url TEXT,
    source_company TEXT,
    data_quality_score DECIMAL(3,2),
    verification_status TEXT DEFAULT 'unverified',
    external_sources TEXT[],
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vessel media table (photos, documents, specifications)
CREATE TABLE IF NOT EXISTS vessel_media (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    vessel_id UUID REFERENCES vessels(id) ON DELETE CASCADE,
    
    -- Media details
    media_type TEXT NOT NULL CHECK (media_type IN ('photo', 'specification', 'brochure', 'manual', 'certificate', 'drawing')),
    title TEXT NOT NULL,
    description TEXT,
    
    -- File information
    original_url TEXT NOT NULL,
    local_path TEXT,
    file_size BIGINT,
    file_format TEXT,
    mime_type TEXT,
    
    -- Source and quality
    source TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- Extracted content (for documents)
    extracted_text TEXT,
    extracted_specifications JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vessel specifications extracted from documents
CREATE TABLE IF NOT EXISTS vessel_specifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    vessel_id UUID REFERENCES vessels(id) ON DELETE CASCADE,
    media_id UUID REFERENCES vessel_media(id) ON DELETE SET NULL,
    
    -- Specification data (JSONB for flexibility)
    specifications JSONB NOT NULL,
    
    -- Source information
    source_document TEXT,
    extraction_method TEXT,
    confidence_score DECIMAL(3,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vessel features and capabilities
CREATE TABLE IF NOT EXISTS vessel_features (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    vessel_id UUID REFERENCES vessels(id) ON DELETE CASCADE,
    
    feature_name TEXT NOT NULL,
    feature_value TEXT,
    feature_category TEXT,
    confidence_score DECIMAL(3,2),
    
    -- Source information
    source_type TEXT, -- 'extracted', 'manual', 'verified'
    source_reference TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(vessel_id, feature_name)
);

-- Crawl sessions and logs
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    session_type TEXT NOT NULL, -- 'full_crawl', 'company_update', 'vessel_update'
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'paused')),
    
    -- Statistics
    companies_processed INTEGER DEFAULT 0,
    vessels_found INTEGER DEFAULT 0,
    vessels_updated INTEGER DEFAULT 0,
    media_collected INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    
    -- Configuration
    config JSONB,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Results
    results JSONB,
    error_log TEXT[]
);

-- Source performance tracking
CREATE TABLE IF NOT EXISTS source_performance (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL, -- 'vessel_tracking', 'photo_source', 'specification_source'
    
    -- Performance metrics
    attempts INTEGER DEFAULT 0,
    successes INTEGER DEFAULT 0,
    failures INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(8,2),
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    
    -- Calculated fields
    success_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN attempts > 0 THEN (successes::decimal / attempts::decimal) * 100 ELSE 0 END
    ) STORED,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_name, source_type)
);

-- Marketplace listings (for future marketplace functionality)
CREATE TABLE IF NOT EXISTS vessel_listings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    vessel_id UUID REFERENCES vessels(id) ON DELETE CASCADE,
    
    -- Listing details
    listing_type TEXT NOT NULL CHECK (listing_type IN ('charter', 'sale', 'services')),
    title TEXT NOT NULL,
    description TEXT,
    
    -- Commercial terms
    price_usd DECIMAL(15,2),
    price_type TEXT, -- 'day_rate', 'fixed_price', 'negotiable'
    currency TEXT DEFAULT 'USD',
    
    -- Availability
    available_from DATE,
    available_until DATE,
    minimum_charter_period TEXT,
    
    -- Contact information
    contact_company_id UUID REFERENCES companies(id),
    contact_person TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    
    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'expired', 'chartered')),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vessels_imo ON vessels(imo_number);
CREATE INDEX IF NOT EXISTS idx_vessels_mmsi ON vessels(mmsi_number);
CREATE INDEX IF NOT EXISTS idx_vessels_name ON vessels(vessel_name);
CREATE INDEX IF NOT EXISTS idx_vessels_owner ON vessels(owner_company);
CREATE INDEX IF NOT EXISTS idx_vessels_type ON vessels(vessel_type);
CREATE INDEX IF NOT EXISTS idx_vessels_updated ON vessels(updated_at);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_member_type ON companies(member_type);

CREATE INDEX IF NOT EXISTS idx_vessel_media_vessel_id ON vessel_media(vessel_id);
CREATE INDEX IF NOT EXISTS idx_vessel_media_type ON vessel_media(media_type);
CREATE INDEX IF NOT EXISTS idx_vessel_media_source ON vessel_media(source);

CREATE INDEX IF NOT EXISTS idx_vessel_features_vessel_id ON vessel_features(vessel_id);
CREATE INDEX IF NOT EXISTS idx_vessel_features_category ON vessel_features(feature_category);

CREATE INDEX IF NOT EXISTS idx_crawl_sessions_status ON crawl_sessions(status);
CREATE INDEX IF NOT EXISTS idx_crawl_sessions_started ON crawl_sessions(started_at);

-- Create GIN index for JSONB columns
CREATE INDEX IF NOT EXISTS idx_vessel_specifications_data ON vessel_specifications USING GIN (specifications);

-- Update triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vessels_updated_at BEFORE UPDATE ON vessels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vessel_media_updated_at BEFORE UPDATE ON vessel_media
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vessel_specifications_updated_at BEFORE UPDATE ON vessel_specifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_source_performance_updated_at BEFORE UPDATE ON source_performance
    FOR EACH ROW EXECUTE FUNCTION update_source_performance_updated_at_column();

CREATE TRIGGER update_vessel_listings_updated_at BEFORE UPDATE ON vessel_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for easier data access

-- Complete vessel information view
CREATE OR REPLACE VIEW vessel_complete AS
SELECT 
    v.*,
    oc.name as owner_company_name,
    oc.website as owner_website,
    opc.name as operator_company_name,
    opc.website as operator_website,
    COUNT(vm.id) as media_count,
    COUNT(CASE WHEN vm.media_type = 'photo' THEN 1 END) as photo_count,
    COUNT(CASE WHEN vm.media_type = 'specification' THEN 1 END) as specification_count
FROM vessels v
LEFT JOIN companies oc ON v.owner_company_id = oc.id
LEFT JOIN companies opc ON v.operator_company_id = opc.id
LEFT JOIN vessel_media vm ON v.id = vm.vessel_id
GROUP BY v.id, oc.name, oc.website, opc.name, opc.website;

-- Recent crawl activity view
CREATE OR REPLACE VIEW recent_crawl_activity AS
SELECT 
    cs.id,
    cs.session_type,
    cs.status,
    cs.companies_processed,
    cs.vessels_found,
    cs.vessels_updated,
    cs.media_collected,
    cs.errors_count,
    cs.started_at,
    cs.completed_at,
    cs.duration_seconds,
    CASE 
        WHEN cs.vessels_found > 0 THEN (cs.vessels_updated::decimal / cs.vessels_found::decimal) * 100 
        ELSE 0 
    END as success_rate
FROM crawl_sessions cs
ORDER BY cs.started_at DESC;

-- Source performance summary
CREATE OR REPLACE VIEW source_performance_summary AS
SELECT 
    source_name,
    source_type,
    attempts,
    successes,
    success_rate,
    avg_response_time_ms,
    last_success_at,
    CASE 
        WHEN last_success_at > NOW() - INTERVAL '24 hours' THEN 'healthy'
        WHEN last_success_at > NOW() - INTERVAL '7 days' THEN 'warning'
        ELSE 'critical'
    END as health_status
FROM source_performance
ORDER BY source_type, success_rate DESC;

-- Row Level Security (RLS) policies
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE vessels ENABLE ROW LEVEL SECURITY;
ALTER TABLE vessel_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE vessel_specifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE vessel_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE vessel_listings ENABLE ROW LEVEL SECURITY;

-- Allow read access to all authenticated users
CREATE POLICY "Public read access" ON companies FOR SELECT USING (true);
CREATE POLICY "Public read access" ON vessels FOR SELECT USING (true);
CREATE POLICY "Public read access" ON vessel_media FOR SELECT USING (true);
CREATE POLICY "Public read access" ON vessel_specifications FOR SELECT USING (true);
CREATE POLICY "Public read access" ON vessel_features FOR SELECT USING (true);
CREATE POLICY "Public read access" ON vessel_listings FOR SELECT USING (true);

-- Allow insert/update for service role (crawler)
CREATE POLICY "Service role full access" ON companies FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON vessels FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON vessel_media FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON vessel_specifications FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON vessel_features FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON crawl_sessions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON source_performance FOR ALL USING (auth.role() = 'service_role');

-- Insert some initial configuration data
INSERT INTO source_performance (source_name, source_type) VALUES
('VesselFinder', 'vessel_tracking'),
('MarineTraffic', 'vessel_tracking'),
('FleetMon', 'vessel_tracking'),
('ShipSpotting', 'photo_source'),
('Maritime Connector', 'photo_source'),
('Marine21 Malaysia', 'specification_source'),
('MISR Malaysia', 'specification_source'),
('ClassNK Database', 'specification_source')
ON CONFLICT (source_name, source_type) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE companies IS 'MOSVA member companies and vessel operators';
COMMENT ON TABLE vessels IS 'Main vessel registry with comprehensive vessel data';
COMMENT ON TABLE vessel_media IS 'Photos, documents, and media files related to vessels';
COMMENT ON TABLE vessel_specifications IS 'Extracted specifications from documents';
COMMENT ON TABLE vessel_features IS 'Vessel features and capabilities';
COMMENT ON TABLE crawl_sessions IS 'Tracking of crawler sessions and performance';
COMMENT ON TABLE source_performance IS 'Performance metrics for external data sources';
COMMENT ON TABLE vessel_listings IS 'Marketplace listings for charter/sale';

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
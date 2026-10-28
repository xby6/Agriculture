CREATE TABLE IF NOT EXISTS agri_device (
    id SERIAL PRIMARY KEY,
    base_id VARCHAR(64),
    plot_id VARCHAR(64),
    vendor_name VARCHAR(64) NOT NULL DEFAULT '0531yun',
    vendor_device_addr VARCHAR(128) NOT NULL,
    device_name VARCHAR(255),
    device_code VARCHAR(128),
    group_id VARCHAR(128),
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    device_status VARCHAR(32),
    save_data_interval INTEGER,
    offline_interval INTEGER,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uk_agri_device_vendor_addr UNIQUE (vendor_name, vendor_device_addr)
);

CREATE INDEX IF NOT EXISTS idx_agri_device_base_plot
    ON agri_device (base_id, plot_id);

CREATE TABLE IF NOT EXISTS agri_metric_mapping (
    id SERIAL PRIMARY KEY,
    vendor_device_addr VARCHAR(128) NOT NULL,
    node_id VARCHAR(64) NOT NULL,
    register_id VARCHAR(64) NOT NULL,
    factor_id VARCHAR(128),
    factor_name VARCHAR(255),
    metric_code VARCHAR(64) NOT NULL,
    source_unit VARCHAR(32),
    standard_unit VARCHAR(32),
    coefficient NUMERIC(18, 6),
    "offset" NUMERIC(18, 6),
    digits INTEGER,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_agri_metric_mapping_device_node_reg UNIQUE (vendor_device_addr, node_id, register_id)
);

CREATE TABLE IF NOT EXISTS agri_sensor_observation (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES agri_device(id) ON DELETE CASCADE,
    plot_id VARCHAR(64),
    node_id VARCHAR(64) NOT NULL,
    register_id VARCHAR(64) NOT NULL,
    metric_code VARCHAR(64) NOT NULL,
    metric_value NUMERIC(18, 6),
    metric_unit VARCHAR(32),
    alarm_level INTEGER,
    alarm_info VARCHAR(255),
    observed_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    quality_flag VARCHAR(32) NOT NULL DEFAULT 'normal',
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uk_agri_sensor_observation_unique_point UNIQUE (device_id, node_id, register_id, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_agri_sensor_device_time
    ON agri_sensor_observation (device_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_agri_sensor_plot_time
    ON agri_sensor_observation (plot_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_agri_sensor_metric_time
    ON agri_sensor_observation (metric_code, observed_at);

CREATE TABLE IF NOT EXISTS agri_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(32) NOT NULL,
    device_addr VARCHAR(128),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    total_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_agri_sync_log_type_time
    ON agri_sync_log (sync_type, started_at);

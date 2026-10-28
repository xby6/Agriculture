UPDATE agri_sensor_observation
SET metric_code = CASE
        WHEN node_id = '1' AND register_id = '1' THEN 'air_temperature'
        WHEN node_id = '1' AND register_id = '2' THEN 'relative_humidity'
        WHEN node_id = '2' AND register_id = '5' THEN 'illuminance'
        WHEN node_id = '3' AND register_id = '1' THEN 'soil_temperature'
        WHEN node_id = '3' AND register_id = '2' THEN 'soil_moisture'
        WHEN node_id = '4' AND register_id = '2' THEN 'co2_concentration'
        WHEN node_id = '5' AND register_id = '1' THEN 'battery_level'
        ELSE metric_code
    END,
    quality_flag = CASE
        WHEN quality_flag = 'unmapped'
             AND (node_id, register_id) IN (('1', '1'), ('1', '2'), ('2', '5'), ('3', '1'), ('3', '2'), ('4', '2'), ('5', '1'))
        THEN 'normal'
        ELSE quality_flag
    END
WHERE metric_code = 'unmapped'
  AND (node_id, register_id) IN (('1', '1'), ('1', '2'), ('2', '5'), ('3', '1'), ('3', '2'), ('4', '2'), ('5', '1'));

INSERT INTO agri_metric_mapping (
    vendor_device_addr,
    node_id,
    register_id,
    factor_name,
    metric_code,
    source_unit,
    standard_unit,
    coefficient,
    "offset",
    digits,
    enabled
)
SELECT DISTINCT
    d.vendor_device_addr,
    o.node_id,
    o.register_id,
    o.raw_payload ->> 'registerName',
    CASE
        WHEN o.node_id = '1' AND o.register_id = '1' THEN 'air_temperature'
        WHEN o.node_id = '1' AND o.register_id = '2' THEN 'relative_humidity'
        WHEN o.node_id = '2' AND o.register_id = '5' THEN 'illuminance'
        WHEN o.node_id = '3' AND o.register_id = '1' THEN 'soil_temperature'
        WHEN o.node_id = '3' AND o.register_id = '2' THEN 'soil_moisture'
        WHEN o.node_id = '4' AND o.register_id = '2' THEN 'co2_concentration'
        WHEN o.node_id = '5' AND o.register_id = '1' THEN 'battery_level'
        ELSE o.metric_code
    END,
    o.metric_unit,
    o.metric_unit,
    1,
    0,
    2,
    TRUE
FROM agri_sensor_observation o
JOIN agri_device d ON d.id = o.device_id
WHERE (o.node_id, o.register_id) IN (('1', '1'), ('1', '2'), ('2', '5'), ('3', '1'), ('3', '2'), ('4', '2'), ('5', '1'))
ON CONFLICT (vendor_device_addr, node_id, register_id) DO UPDATE
SET factor_name = EXCLUDED.factor_name,
    metric_code = EXCLUDED.metric_code,
    source_unit = EXCLUDED.source_unit,
    standard_unit = EXCLUDED.standard_unit,
    enabled = TRUE;

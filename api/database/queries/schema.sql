-- Tabla de dispositivos
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de lecturas de los dispositivos
CREATE TABLE readings (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    temp NUMERIC(5, 2),        
    humidity NUMERIC(5, 2),    
    pm10 NUMERIC(7, 2),
    gas NUMERIC(7, 2),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Relación con la tabla de dispositivos
    CONSTRAINT fk_device
        FOREIGN KEY(device_id) 
        REFERENCES devices(id)
        ON DELETE CASCADE
);

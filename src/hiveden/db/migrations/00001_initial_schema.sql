-- Initial schema migration
-- depends:

-- migrate: apply

CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    short_name TEXT UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE configs (
    id SERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(module_id) REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TABLE service_templates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('docker', 'lxc')),
    description TEXT,
    logo TEXT,
    default_config JSONB DEFAULT '{}',
    maintainer TEXT DEFAULT 'hiveden',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE managed_services (
    id SERIAL PRIMARY KEY,
    identifier TEXT NOT NULL, -- Docker ID or Name
    name TEXT NOT NULL,       -- User friendly name
    type TEXT NOT NULL CHECK(type IN ('docker', 'lxc')),
    template_id INTEGER,
    category TEXT DEFAULT 'general',
    icon TEXT,
    config JSONB DEFAULT '{}',
    is_managed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY(template_id) REFERENCES service_templates(id) ON DELETE SET NULL,
    UNIQUE(identifier, type)
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL,
    log TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(module_id) REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TABLE explorer_config (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE filesystem_locations (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE,
    label TEXT NOT NULL,
    path TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'user_bookmark',
    description TEXT,
    is_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE explorer_operations (
    id TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    source_paths TEXT,
    destination_path TEXT,
    error_message TEXT,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE setup_state (
    step_key TEXT PRIMARY KEY,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    meta_data TEXT
);

-- Seed System Module
INSERT INTO modules (name, short_name, enabled) 
VALUES ('System Core', 'core', true)
ON CONFLICT (name) DO NOTHING;

-- Seed Default Filesystem Locations
INSERT INTO filesystem_locations (key, label, path, type, is_editable, description) VALUES
('apps', 'Applications', '/hiveden-temp-root/apps', 'system_root', false, 'Root directory for managed applications and their data'),
('movies', 'Movies', '/hiveden-temp-root/movies', 'system_root', false, 'Storage for movie files'),
('tvshows', 'TV Shows', '/hiveden-temp-root/tvshows', 'system_root', false, 'Storage for TV show series'),
('pictures', 'Pictures', '/hiveden-temp-root/pictures', 'system_root', false, 'Storage for personal photos and images'),
('documents', 'Documents', '/hiveden-temp-root/documents', 'system_root', false, 'Storage for personal documents'),
('ebooks', 'E-Books', '/hiveden-temp-root/ebooks', 'system_root', false, 'Storage for digital books'),
('music', 'Music', '/hiveden-temp-root/music', 'system_root', false, 'Storage for music and audio files'),
('backups', 'Backups', '/hiveden-temp-root/backups', 'system_root', false, 'Storage for system and application backups');


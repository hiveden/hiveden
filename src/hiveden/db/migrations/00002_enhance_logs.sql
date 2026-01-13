-- Enhancing logs table for system audit
-- depends: 00001_initial_schema

-- migrate: apply
ALTER TABLE logs RENAME COLUMN log TO message;
ALTER TABLE logs ADD COLUMN actor TEXT DEFAULT 'system';
ALTER TABLE logs ADD COLUMN action TEXT;
ALTER TABLE logs ADD COLUMN level TEXT DEFAULT 'info';
ALTER TABLE logs ADD COLUMN module TEXT;
ALTER TABLE logs ADD COLUMN metadata JSONB DEFAULT '{}';

-- Attempt to populate module from FK if data exists
UPDATE logs SET module = COALESCE((SELECT short_name FROM modules WHERE modules.id = logs.module_id), 'unknown');

-- Drop old foreign key column
ALTER TABLE logs DROP COLUMN module_id;

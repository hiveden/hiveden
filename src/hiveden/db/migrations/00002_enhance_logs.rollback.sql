-- migrate: rollback

ALTER TABLE logs ADD COLUMN module_id INTEGER;
-- Note: Rolling back module_id is lossy if we dropped the mapping, but we do best effort.
ALTER TABLE logs DROP COLUMN metadata;
ALTER TABLE logs DROP COLUMN module;
ALTER TABLE logs DROP COLUMN level;
ALTER TABLE logs DROP COLUMN action;
ALTER TABLE logs DROP COLUMN actor;
ALTER TABLE logs RENAME COLUMN message TO log;

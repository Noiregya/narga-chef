ALTER TABLE rewards ADD COLUMN r_name text NOT NULL DEFAULT 'unset';
alter table rewards RENAME COLUMN reward TO r_role;
ALTER TABLE rewards ALTER COLUMN r_role DROP NOT NULL;

UPDATE metanarga SET data_model_version = '1.0.9';
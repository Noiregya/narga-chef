ALTER TABLE achievements ADD COLUMN description text NOT NULL DEFAULT 'unset';

UPDATE metanarga SET data_model_version = '1.0.10';
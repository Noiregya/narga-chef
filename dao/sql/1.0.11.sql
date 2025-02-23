ALTER TABLE members ADD COLUMN theme numeric NOT NULL DEFAULT 0;

UPDATE metanarga SET data_model_version = '1.0.11';
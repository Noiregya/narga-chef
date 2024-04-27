alter table members RENAME COLUMN last_submission_time TO next_submission_time;
UPDATE metanarga SET data_model_version = '1.0.1';

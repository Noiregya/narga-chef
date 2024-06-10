ALTER TABLE achievements DROP CONSTRAINT achievements_a_name_key;
ALTER TABLE achievements ALTER COLUMN icon TYPE bytea USING icon::bytea;

ALTER TABLE rewards DROP CONSTRAINT rewards_pkey;
ALTER TABLE requests DROP CONSTRAINT requests_pkey;
ALTER TABLE achievements DROP CONSTRAINT achievements_pkey;

ALTER TABLE rewards ADD PRIMARY KEY (ident);
ALTER TABLE requests ADD PRIMARY KEY (ident);
ALTER TABLE achievements ADD PRIMARY KEY (ident);

ALTER TABLE reward_attr ALTER COLUMN reward type INTEGER;
ALTER TABLE request_attr ALTER COLUMN request type INTEGER;
ALTER TABLE achievement_attr ALTER COLUMN achievement type INTEGER;

ALTER TABLE reward_attr ADD FOREIGN KEY (reward) REFERENCES rewards(ident) ON DELETE CASCADE;
ALTER TABLE request_attr ADD FOREIGN KEY (request) REFERENCES requests(ident) ON DELETE CASCADE;
ALTER TABLE achievement_attr ADD FOREIGN KEY (achievement) REFERENCES achievements(ident) ON DELETE CASCADE;

UPDATE metanarga SET data_model_version = '1.0.8';
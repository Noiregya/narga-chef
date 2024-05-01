CREATE TABLE rewards (
    guild numeric NOT NULL, 
    condition text NOT NULL, 
    nature text NOT NULL, 
    reward numeric NOT NULL,
    points_required numeric NOT NULL,
    PRIMARY KEY(guild, condition, nature, reward)
);
UPDATE metanarga SET data_model_version = '1.0.2';

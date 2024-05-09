ALTER TABLE members ADD spent NUMERIC DEFAULT 0;

CREATE TABLE reward_attr (
    guild numeric NOT NULL, 
    member numeric NOT NULL, 
    nature text NOT NULL, 
    reward numeric NOT NULL,
    PRIMARY KEY(guild, member, nature, reward)
);

UPDATE metanarga SET data_model_version = '1.0.4';
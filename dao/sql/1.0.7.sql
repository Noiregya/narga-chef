CREATE TABLE achievements (
    ident SERIAL NOT NULL,
    guild NUMERIC NOT NULL, 
    a_name TEXT NOT NULL UNIQUE,
    icon TEXT NOT NULL,
    condition TEXT NOT NULL,
    PRIMARY KEY(guild, ident)
);

CREATE TABLE achievement_attr (
    guild NUMERIC NOT NULL, 
    member NUMERIC NOT NULL,
    achievement NUMERIC NOT NULL,
    PRIMARY KEY(guild, member, achievement)
);

UPDATE metanarga SET data_model_version = '1.0.7';
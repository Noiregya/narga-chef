CREATE TABLE guilds (
    id numeric NOT NULL, 
    guild_name text NOT NULL, 
    currency text NOT NULL, 
    submission_channel numeric NOT NULL, 
    review_channel numeric NOT NULL, 
    info_channel numeric NOT NULL, 
    leaderboard numeric,
    cooldown numeric,
    PRIMARY KEY(id)
);
CREATE TABLE members (
    guild numeric NOT NULL, 
    id numeric NOT NULL, 
    nickname text NOT NULL, 
    points numeric NOT NULL,
    last_submission_time timestamp NOT NULL,
    last_submission text,
    PRIMARY KEY(guild, id)
);
CREATE TABLE requests (
    guild numeric NOT NULL, 
    request_name text NOT NULL, 
    requirements text NOT NULL,
    comment text,
    PRIMARY KEY(guild, request_name)
);
CREATE TABLE options (
    guild numeric NOT NULL, 
    request_name text NOT NULL, 
    option_name text NOT NULL, 
    remuneration numeric NOT NULL,
    PRIMARY KEY(guild, request_name, option_name)
);
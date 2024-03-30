CREATE TABLE guilds (
    id numeric NOT NULL, 
    guild_name text NOT NULL, 
    currency numeric NOT NULL, 
    submission_channel numeric NOT NULL, 
    review_channel numeric NOT NULL, 
    info_channel numeric NOT NULL, 
    leaderboard numeric) 
    CONSTRAINT pk_guilds PRIMARY KEY REFERENCES id;
CREATE TABLE members (
    guild numeric NOT NULL, 
    id numeric NOT NULL, 
    nickname text NOT NULL, 
    points numeric NOT NULL)
    CONSTRAINT pk_members PRIMARY KEY REFERENCES guild, id;
CREATE TABLE requests (
    guild numeric NOT NULL, 
    request_name text NOT NULL, 
    requirements text NOT NULL,
    comment text)
    CONSTRAINT pk_requests PRIMARY KEY REFERENCES guild, request_name;
CREATE TABLE options (
    guild numeric NOT NULL, 
    request_name text NOT NULL, 
    option_name text NOT NULL, 
    remuneration numeric NOT NULL)
    CONSTRAINT pk_options PRIMARY KEY REFERENCES guild, request_name, option_name;
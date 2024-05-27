
ALTER TABLE rewards ADD COLUMN ident SERIAL;
ALTER TABLE requests ADD COLUMN ident SERIAL;
ALTER TABLE reward_attr RENAME COLUMN reward to role_id;
ALTER TABLE reward_attr ADD COLUMN reward NUMERIC;
UPDATE reward_attr SET reward = (SELECT ident FROM rewards WHERE reward_attr.role_id = rewards.reward);
ALTER TABLE reward_attr DROP CONSTRAINT reward_attr_pkey;
ALTER TABLE reward_attr ALTER nature DROP NOT NULL, 
    ALTER role_id DROP NOT NULL, 
    ALTER reward SET NOT NULL;
ALTER TABLE reward_attr
    ADD CONSTRAINT reward_attr_pkey 
    PRIMARY KEY (guild, member, reward);

CREATE TABLE request_attr (
    guild numeric NOT NULL, 
    member numeric NOT NULL,
    request numeric NOT NULL,
    PRIMARY KEY(guild, member, request)
);

UPDATE metanarga SET data_model_version = '1.0.6';
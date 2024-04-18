# Getting started
clone the repository then cd inside nargaChef
## Initialize python environment
* python -m narga .
* source bin/activate
* pip install -r requirements.txt
## Initialize the database
You will need a postgresql database for this. Copy sql/createDatabase.sql to the server hosting the postgres database. Log in to the server with shell and input the following commands to create the user and schema:
* sudo -u postgres psql
* postgres=# create database narga;
* postgres=# create user narga with encrypted password '==your password==';
* postgres=# grant all privileges on database narga to narga;
* psql -U narga -d narga < ==/path/to/==createDatabase.sql
## Configure the settings
-
## Start the bot

## Register the commands
This should be done after every update.
## Run the bot
-

## More
* [The bot needs message content intents](https://discord.com/developers/docs/topics/gateway#message-content-intent)
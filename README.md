# Abstract
Narga chef is a bot that aim to streamline organizing challenges for server members. Members will be able to send a screenshot with information and moderators will be able to review the screenshot and its associated information to award points to the players.

# Getting started
## Initialize the database
You will need a postgresql database for this. Copy sql/createDatabase.sql to the server hosting the postgres database. Log in to the server with shell and input the following commands to create the user and schema:
* sudo -u postgres psql
* postgres=# create database narga;
* postgres=# create user narga with encrypted password '==your password==';
* postgres=# grant all privileges on database narga to narga;
* psql -U narga -d narga < ==/path/to/==createDatabase.sql
## Configure the settings 
-
## Register the commands
This should be done after every update.
## Run the bot
-

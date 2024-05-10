# Getting started
clone the repository then cd inside narga-chef
## Initialize python environment
./bin/install
## Initialize the database
You will need a postgresql database called narga for this. Make sure you create a user that has full access to it. 
## Configure the settings
The settings can be setup two ways, environment variables, or a .env file using a key=value format with one per line.
The values you must provide are:
* token
* application_id
* host
* password
* db_user
## Start the bot
./bin/start

## More
* [The bot needs message content intents](https://discord.com/developers/docs/topics/gateway#message-content-intent)

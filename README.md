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
## Install Image Magick 7
Image Magick is used to render SVG into png for discord. I couldn't find a way around it.
### Linux: 
sudo apt-get install libmagickwand-dev
### MacOS
brew install imagemagick
### Windows: 
* Download and install Image Magick https://imagemagick.org/script/download.php#windows
 * Don't forget to tick the "Install development headers and libraries for X and C++" box
* Set the environment variable MAGICK_HOME with the install folder ex: C:\Program Files\ImageMagick-7.1.1-Q16-HDRI
### Other
https://www.cairographics.org/download/

## Start the bot
./bin/start

## More
* [The bot needs message content intents](https://discord.com/developers/docs/topics/gateway#message-content-intent)

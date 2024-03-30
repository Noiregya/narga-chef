import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["token"]
APPLICATION_ID = os.environ["application_id"]
URL = os.environ["command_url"]

print(f"TOKEN: {TOKEN},APPLICATION_ID: {APPLICATION_ID},URL: {URL}")

commandFile = open("commands/slashCommands.json", "r", encoding="utf-8")
commands = json.load(commandFile)
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

for command in commands:
    response = requests.post(URL, json=command, headers=headers)
    commandName = command["name"];
    print(f"Command {commandName} created: {response.status_code}")
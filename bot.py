# This example requires the 'message_content' intent.
import os
import datetime
import calendar
from interactions import (Client, Intents, 
    listen, slash_command, slash_option, OptionType, SlashContext, 
    Embed, EmbedField, StringSelectMenu, Button, ButtonStyle, ActionRow, spread_to_rows,
    Permissions, Member, ChannelType, BaseChannel, CallbackType)
from interactions.api.events import MessageCreate, Component
import logging
import json
import dao.dao
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["token"]
PURPLE = "#7f03fc"
AQUAMARINE = "#00edd9"
ONE_HOUR = 3600

intents = Intents.MESSAGE_CONTENT | Intents.GUILD_MESSAGES | Intents.GUILDS
bot = Client(intents=intents)

eventDictionnary = {}

@listen()
async def on_message_create(ctx: MessageCreate):
    image = get_first_image_attachement(ctx.message)
    if(image != None):
        # Check input and fetch from database
        guild_error = check_in_guild(ctx.message)
        if(guild_error != None):
            return await ctx.message.reply(guild_error, ephemeral=True)
        is_setup, db_guild = check_guild_setup(ctx.message.guild.id)
        if(is_setup == False):
            return await ctx.message.reply(db_guild, ephemeral=True)
        if(ctx.message.channel.id == db_guild[3]): #Message is in the submission channel
            # return await ctx.message.reply(f"Received your submission {image.url}") # TODO: prompt form and submit for review
            # Persist url in database + read interactions and persist answers
            eventDictionnary[f"request,image,{ctx.message.id},{ctx.message.author.id}"] = image.url
            db_requests = dao.dao.requestPerColumn(ctx.message.guild.id)
            return await ctx.message.reply("Please tell us about your request", 
                components=ask_info_request_component(db_requests, ctx.message.author.id, ctx.message.id))

@listen(Component)
async def on_component(event: Component):
    ctx = event.ctx
    event_type,event_context,unique,data1 = ctx.custom_id.split(",")
    response_type = CallbackType.UPDATE_MESSAGE
    match [event_type,event_context,unique,data1]: #Read component event id
        # Name field has been set
        case ["request","name",*_]:
            image = eventDictionnary.get(f"{event_type},image,{unique},{ctx.member.id}")
            if(image != None): # An image URL have been saved   
                name = ctx.values[0]
                effect = eventDictionnary.get(f"{event_type},effect,{unique},{ctx.member.id}")
                if(effect != None): # Every element has been set
                    response = await send_to_review(ctx, image, name, effect, unique)
                    # Delete event from the event dictionnary
                else: # Effect isn't set yet
                    eventDictionnary[f"{event_type},name,{unique},{ctx.member.id}"] = name
                    db_requests = dao.dao.requestPerColumn(ctx.guild.id, name=name)
                    return await ctx.edit_origin(content="Please tell us about your request", 
                        components=ask_info_request_component(db_requests, ctx.message.author.id, unique, name=name))
            else:
                response = "Sorry, we lost your image... Please submit your request again"
        # Effect field has been set
        case ["request","effect",*_]:
            image = eventDictionnary.get(f"{event_type},image,{unique},{ctx.member.id}")
            if(image != None):
                effect = ctx.values[0]
                name = eventDictionnary.get(f"{event_type},name,{unique},{ctx.member.id}")
                if(name != None): # Every element has been set
                    response = await send_to_review(ctx, image, name, effect, unique)
                else: # Name isn't set yet
                    eventDictionnary[f"{event_type},effect,{unique},{ctx.member.id}"] = effect
                    db_requests = dao.dao.requestPerColumn(ctx.guild.id, effect=effect)
                    return await ctx.edit_origin(content="Please tell us about your request", 
                        components=ask_info_request_component(db_requests, ctx.message.author.id, unique, effect=effect))
            else:
                response = "Sorry, we lost your image... Please submit your request again"
        case ["accept",*_]:
            value = data1
            request_member = event_context
            image = eventDictionnary.get(f"request,image,{unique},{event_context}")
            dao.dao.add_points(ctx.guild.id, request_member, value)
            clear_events(unique, request_member)
            await notify_member(ctx, request_member, unique, value, fulfilled = True)
            return await ctx.edit_origin(content=f"{image} Request accepted by <@{ctx.member.id}> and {value} points awarded to <@{request_member}>", components=[])
        case ["deny",*_]:
            value = data1
            request_member = event_context
            image = eventDictionnary.get(f"request,image,{unique},{event_context}")
            dao.dao.add_points(ctx.guild.id, request_member, value)
            clear_events(unique, request_member)
            await notify_member(ctx, request_member, unique, value, fulfilled = False)
            return await ctx.edit_origin(content=f"{image} Request from <@{request_member}> denied by <@{ctx.member.id}>", components=[])
        case _:
            response = f"Something went wrong, unknown interaction {ctx.custom_id}"
    return await ctx.edit_origin(content=response, components=[])

def clear_events(unique, member):
    # Delete event from the event dictionnary
    try:
        del eventDictionnary[f"request,name,{unique},{member}"]
        del eventDictionnary[f"request,effect,{unique},{member}"]
        del eventDictionnary[f"request,image,{unique},{member}"]
    except:
        logging.info("Unable to delete event from the dictionnary")

@slash_command(name="setup",
    description="Set up the bot for this server",
    default_member_permissions=Permissions.MANAGE_GUILD)
@slash_option(name="currency",
    description="Name of the points to be collected",
    opt_type=OptionType.STRING,
    required=True)
@slash_option(name="cooldown",
    description="Delay before the member is allowed to submit again (in hours)",
    opt_type=OptionType.INTEGER,
    required=True)
@slash_option(name="submission_channel",
    description="Channel you want members to submit to",
    opt_type=OptionType.CHANNEL,
    required=True)
@slash_option(name="review_channel",
    description="Channel you want moderators to review submissions in",
    opt_type=OptionType.CHANNEL,
    required=True)
@slash_option(name="info_channel",
    description="Channel you want the leaderboard to be displayed in",
    opt_type=OptionType.CHANNEL,
    required=True)
async def setup(ctx: SlashContext, currency: str, cooldown: int, submission_channel: BaseChannel, review_channel: BaseChannel, info_channel: BaseChannel):
     # Check input and fetch from database
    guild_error = check_in_guild(ctx)
    if(guild_error != None):
        return await ctx.send(guild_error)
    if submission_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("submission_channel is not a text channel",ephemeral=True)
    if review_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("review_channel is not a text channel",ephemeral=True)
    if info_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("info_channel is not a text channel",ephemeral=True)
    # Business
    dao.dao.setup(ctx.guild.id, ctx.guild.name, currency, submission_channel.id, review_channel.id, info_channel.id, cooldown)
    return await ctx.send("Setup complete. Enjoy!")

@slash_command(name="card",
    description="Show the guild card for the specified member",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS)
@slash_option(name="member",
    description="Member to show the card of",
    opt_type=OptionType.USER,
    required=False)
async def card(ctx: SlashContext, member: Member = None):
    # Check input and fetch from database
    guild_error = check_in_guild(ctx)
    if(guild_error != None):
        return await ctx.send(guild_error)
    is_setup, db_guild = check_guild_setup(ctx.guild.id)
    if(is_setup == False):
        return await ctx.send(db_guild) #db_guild is a polymorph, either guild or error message
    if(member == None):
        member = ctx.member
    db_member = dao.dao.getMember(ctx.guild.id, member.id, member.display_name)
    # Business
    rank = dao.dao.getRank(ctx.guild.id, member.id)
    return await ctx.send(embed=guild_card_embed(db_member, db_guild, rank))

@slash_command(name="request_register",
    description="Register a request and set its value",
    default_member_permissions=Permissions.ADMINISTRATOR)
@slash_option(name="name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    required=True)
@slash_option(name="effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    required=True)
@slash_option(name="value",
    description="Reward for making the request",
    opt_type=OptionType.INTEGER,
    required=True)
async def request_register(ctx: SlashContext, name: str, effect: str, value: str):
    # Check input and fetch from database
    guild_error = check_in_guild(ctx)
    if(guild_error != None):
        return await ctx.send(guild_error)
    is_setup, error = check_guild_setup(ctx.guild.id)
    if(is_setup == False):
        return await ctx.send(error)
    dao.dao.requestRegister(ctx.guild.id, name, effect, value)
    return await ctx.send(f"Request {name} with effect {effect} and value {value} added")

@slash_command(name="request_delete",
    description="Delete a request",
    default_member_permissions=Permissions.ADMINISTRATOR)
@slash_option(name="name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    required=True)
@slash_option(name="effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    required=True)
async def request_delete(ctx: SlashContext, name: str, effect: str):
    # Check input and fetch from database
    guild_error = check_in_guild(context)
    if(guild_error != None):
        return await ctx.send(guild_error)
    is_setup, error = check_guild_setup(ctx.guild.id)
    if(is_setup == False):
        return await ctx.send(error)
    #Business
    dao.dao.requestDelete(ctx.guild.id, name, effect)
    return await ctx.send(f"Request {name} with effect {effect} removed")

@slash_command(name="request_list",
    description="List all the requests",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS)
async def request_list(ctx: SlashContext):
    # Check input and fetch from database
    guild_error = check_in_guild(ctx)
    if(guild_error != None):
        return await ctx.send(guild_error)
    is_setup, error = check_guild_setup(ctx.guild.id)
    if(is_setup == False):
        return await ctx.send(error)
    # Business
    db_requests = dao.dao.requests(ctx.guild.id, None, None)
    return await ctx.send(embed=requests_embed(db_requests))

def check_in_guild(context):
    if(context.guild == None):
        return "This command isn\'t available outside of a server"

def check_guild_setup(guild_id):
    db_guild = dao.dao.getGuild(guild_id)
    if(db_guild == None):
        return [False, "Please register this server by using the /setup command"]
    return [True, db_guild]

def guild_card_embed(member, guild, rank):
    points = EmbedField(name=guild[2], value=str(member[3]), inline=True)
    rank = EmbedField(name="Rank", value=str(rank[2]), inline=True)
    target_time = member[4].timestamp() + float(guild[7]) * ONE_HOUR
    cooldown = EmbedField(name="Cooldown", value=f"<t:{int(target_time)}:R>", inline=True)
    embed = Embed(color=PURPLE, title=f"Guild card for {member[2]}", fields=[points, rank, cooldown])
    return embed

def requests_embed(requests):
    fields = []
    for request in requests:
        fields.append(EmbedField(name=request[1], value=f"**Effect:** {request[2]}, **Value:** {request[3]}"))
    return Embed(color=AQUAMARINE, title="Available requests:", fields=fields)

def get_first_image_attachement(message):
    for attachement in message.attachments:
        if(attachement.content_type.startswith("image")):
            return attachement
    return None

def ask_info_request_component(db_requests, member_id, message_id, name="Request name", effect="Request effect"):
    res: list[ActionRow] = spread_to_rows(
        StringSelectMenu(
        db_requests[0],
        placeholder=name,
        min_values=1,
        max_values=1,
        custom_id=f"request,name,{message_id},{member_id}",
        ),
        StringSelectMenu(
        db_requests[1],
        placeholder=effect,
        min_values=1,
        max_values=1,
        custom_id=f"request,effect,{message_id},{member_id}",
        )
    )
    logging.info(res)
    return res

async def send_to_review(ctx, image, name, effect, unique):
    guild = ctx.guild.id
    member = ctx.user.id
    db_request = dao.dao.getRequest(guild, name, effect)
    if(len(db_request) == 0):
        return f"{name} with effect {effect} doesn't exist. Please select a possible combination."
    db_guild =  dao.dao.getGuild(guild)
    if(len(db_guild) == 0):
        return "Please setup the guild again"
    await send_review_message(ctx, image, db_guild, db_request, unique)
    return f"You have fulfilled the request for {name} with effect {effect}, review is in progress"

async def send_review_message(ctx, image, db_guild, db_request, unique):
    member = ctx.user.id
    channel = await ctx.guild.fetch_channel(db_guild[4])
    if(channel == None):
        return await ctx.channel.send(f"Error, I cannot see channel <#{db_guild[4]}>, check the setup and bot rights")
    components = generate_review_component(member, unique, db_request[3])
    return await channel.send(f"{image}\n<@{member}> submitted {db_request[1]} with effect {db_request[2]} and value {db_request[3]}",components=components, attachements=image)

def generate_review_component(member, unique, value):
    return [
        ActionRow(
            Button(
                style=ButtonStyle.RED,
                label="Deny",
                custom_id = f"deny,{member},{unique},{value}",
            ),
            Button(
                style=ButtonStyle.GREEN,
                label="Accept",
                custom_id = f"accept,{member},{unique},{value}",
            )
        )
    ]

async def notify_member(ctx, member, message, points, fulfilled = False):
    db_guild = dao.dao.getGuild(ctx.guild.id)
    channel = await ctx.guild.fetch_channel(db_guild[3])
    message = await channel.fetch_message(message)
    if(fulfilled):
        content = f"Congratulations, your request have been accepted by <@{ctx.user.id}> and you have been awarded {points} points"
    else:
        content = f"<@{ctx.user.id}> denied your request."
    if(message == None): # The request message can't be fetched
        await channel.send(f"<@{member}> {content}")
    else:
        await message.reply(content)

bot.start(TOKEN)
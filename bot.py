# This example requires the 'message_content' intent.
import os
import calendar
import logging
import json
import dao.dao
from dotenv import load_dotenv
from datetime import datetime
from interactions import (Client, Intents, 
    listen, slash_command, slash_option, OptionType, SlashContext, 
    Modal, ParagraphText, spread_to_rows,
    Embed, EmbedField, StringSelectMenu, Button, ButtonStyle, ActionRow, 
    Permissions, Member, ChannelType, BaseChannel, CallbackType)
from interactions.api.events import MessageCreate, Component

load_dotenv()
TOKEN = os.environ.get("token")
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
        is_setup, db_guild = check_guild_setup(ctx.message.guild.id)
        is_right_channel = ctx.message.channel.id == db_guild[3]
        # Check input and fetch from database
        guild_error = check_in_guild(ctx.message)
        if(guild_error != None or is_setup == False or is_right_channel == False):
            return
        # Make sure that the member exists and update its nickname in the database
        db_member = dao.dao.getMember(ctx.message.guild.id, ctx.message.author.id, ctx.message.author.display_name)

        if(db_member[4] != datetime.min): # The user submitted before
            timestamp_next_request = db_member[4].timestamp() + float(db_guild[7]) * ONE_HOUR
            timestamp_string = f"<t:{int(timestamp_next_request)}>"
            if(datetime.utcnow().timestamp() < timestamp_next_request):
                return await ctx.message.reply(f"You will be able to submit your next request on: <t:{int(timestamp_next_request)}>")
        eventDictionnary[f"image,{ctx.message.author.id},{ctx.message.id}"] = image.url
        type_list = dao.dao.requestPerColumn(ctx.message.guild.id)["type"]
        if(len(type_list)==0):
            return await ctx.send(f"Please start by registering requests")
        return await ctx.message.reply("Please tell us about your request", 
            components=ask_info_request_component(
                type_list, 
                ctx.message.author.id, 
                ctx.message.id, name="Request Type", variation="type")
            )

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
                eventDictionnary[f"{event_type},name,{unique},{ctx.member.id}"] = name
                db_requests = dao.dao.requestPerColumn(ctx.guild.id, name=name)
                return await ctx.edit_origin(content="Please tell us about your request", 
                components=ask_info_request_component(db_requests[1], ctx.message.author.id, unique, name="Request Effect", variation="effect"))
            else:
                response = "Sorry, we lost your image... Please submit your request again"
        # Effect field has been set
        case ["request","effect",*_]:
            image = eventDictionnary.get(f"{event_type},image,{unique},{ctx.member.id}")
            if(image != None):
                effect = ctx.values[0]
                name = eventDictionnary.get(f"{event_type},name,{unique},{ctx.member.id}")
                response = await send_to_review(ctx, image, name, effect, unique)
            else:
                response = "Sorry, we lost your image... Please submit your request again"
        case ["accept",*_]:
            value = data1
            image = eventDictionnary.get(f"image,{req_member},{unique}")
            request_type = eventDictionnary.get(f"type,{req_member},{unique}")
            name = eventDictionnary.get(f"name,{req_member},{unique}")
            effect = eventDictionnary.get(f"effect,{req_member},{unique}")
            # Update member
            dao.dao.add_points(ctx.guild.id, req_member, value)
            last_request = "I forgor 💀"
            if(request_type != None):
                last_request = f"{request_type.capitalize()} {name} {effect}"
            dao.dao.update_member_submission(ctx.guild.id, req_member, last_request)
            clear_events(unique, req_member)
            # Send messages
            await notify_member(ctx, req_member, unique, value, fulfilled = True)
            return await ctx.edit_origin(content=f"{image}\nRequest accepted by <@{ctx.member.id}> and {value} points awarded to <@{req_member}>", components=[])
        case ["deny",*_]:
            custom_id = f"reason,{event_context},{unique},{data1}"
            modal = getDenialReasonModal()
            value = data1
            request_member = event_context
            image = eventDictionnary.get(f"request,image,{unique},{event_context}")
            await ctx.send_modal(modal=modal)
            # Response received
            modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal)
            paragraph = modal_ctx.responses["reason"]
            dao.dao.add_points(ctx.guild.id, request_member, value)
            clear_events(unique, request_member)
            await notify_member(ctx, request_member, unique, value, reason = paragraph, fulfilled = False)
            await modal_ctx.send(content="Processing", ephemeral=True, delete_after=1.0)
            return await ctx.message.edit(content=f"{image}\nRequest from <@{req_member}> denied by <@{ctx.member.id}> for reason:\n{paragraph}", components=[])
        case _:
            response = f"Something went wrong, unknown interaction {ctx.custom_id}"
    return await ctx.edit_origin(content=response, components=[])


def getDenialReasonModal():
    return Modal(
        ParagraphText(
            label="Reason for denial",
            custom_id="reason",
            placeholder="Help the member understand the reason of the denial",
            max_length=255
        ),
        title="Bounty denial",
    )

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
    guild_error = check_in_guild(ctx)
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
    return await ctx.send(content=requests_content(db_requests))

def check_in_guild(context):
    if(context.guild == None):
        return "This command isn\'t available outside of a server"

def check_guild_setup(guild_id):
    db_guild = dao.dao.getGuild(guild_id)
    if(db_guild == None):
        return [False, "Please register this server by using the /setup command"]
    return [True, db_guild]

def guild_card_embed(db_member, db_guild, rank):
    points = EmbedField(name=db_guild[2], value=str(db_member[3]), inline=True)
    rank = EmbedField(name="Rank", value=str(rank[2]), inline=True)
    if(db_member[4] == datetime.min):
        timestamp_string = "No submission yet"
    else:
        timestamp_next_request = db_member[4].timestamp() + float(db_guild[7]) * ONE_HOUR
        timestamp_string = f"<t:{int(timestamp_next_request)}>"
    cooldown = EmbedField(name="Cooldown", value=timestamp_string, inline=True)
    embed = Embed(color=PURPLE, title=f"Guild card for {db_member[2]}", fields=[points, rank, cooldown])
    return embed

#def requests_embed(requests):
#    fields = []
#    for request in requests:
#        fields.append(EmbedField(name=request[1], value=f"**Effect:** {request[2]}, **Value:** {request[3]}"))
#    return Embed(color=AQUAMARINE, title="Available requests:", fields=fields)

def requests_content(requests):
    res = "```csv\nName; Effect; Value\n"
    for request in requests:
        res = f"{res}{request[1]};{request[2]};{request[3]}\n"
    return f"{res}```"

def get_first_image_attachement(message):
    for attachement in message.attachments:
        if(attachement.content_type.startswith("image")):
            return attachement
    return None

def ask_info_request_component(options, member_id, message_id, name="Request name", variation="name"):
    res: list[ActionRow] = spread_to_rows( # TODO: check size limit
        StringSelectMenu(
        options,
        placeholder=name,
        min_values=1,
        max_values=1,
        custom_id=f"request,{variation},{message_id},{member_id}",
        ),
    )
    logging.info(res)
    return res

async def send_to_review(ctx, image, name, effect, unique):
    guild = ctx.guild.id
    member = ctx.user.id
    db_request = dao.dao.getRequest(guild, name, effect)
    if(db_request == None or len(db_request) == 0):
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

async def notify_member(ctx, member, message, points, reason = None, fulfilled = False):
    db_guild = dao.dao.getGuild(ctx.guild.id)
    channel = await ctx.guild.fetch_channel(db_guild[3])
    message = await channel.fetch_message(message)
    if(fulfilled):
        content = f"Congratulations, your request have been accepted by <@{ctx.user.id}> and you have been awarded {points} points"
    else:
        content = f"<@{ctx.user.id}> denied your request"
    if(reason != None):
        content = f"{content} here's why:\n{reason}"
    if(message == None): # The request message can't be fetched
        await channel.send(f"<@{member}> {content}")
    else:
        await message.reply(content)

bot.start(TOKEN)
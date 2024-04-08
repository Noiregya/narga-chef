# This example requires the 'message_content' intent.
import os
import datetime
import calendar
from interactions import (Client, Intents, 
    listen, slash_command, slash_option, OptionType, SlashContext, 
    Embed, EmbedField,
    Permissions, Member, ChannelType, BaseChannel )
from interactions.api.events import MessageCreate
import logging
import json
import dao.dao
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["token"]
PURPLE = "#7f03fc"
AQUAMARINE = "#00edd9"
ONE_HOUR = 3600

bot = Client(intents=Intents.DEFAULT)

@listen()
async def on_message_create(event: MessageCreate):
    event.message  # actual message

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
    db_requests = dao.dao.requestAll(ctx.guild.id)
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

bot.start(TOKEN)
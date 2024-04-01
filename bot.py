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
    if submission_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("submission_channel is not a text channel",ephemeral=True)
    if review_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("review_channel is not a text channel",ephemeral=True)
    if info_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("info_channel is not a text channel",ephemeral=True)
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
    if(member == None):
        member = ctx.member
    dbMember = dao.dao.getMember(ctx.guild.id, member.id, member.display_name)
    dbGuild = dao.dao.getGuild(ctx.guild.id)
    rank = dao.dao.getRank(ctx.guild.id, member.id)
    return await ctx.send(embed=guildCardEmbed(dbMember, dbGuild, rank))

def guildCardEmbed(member, guild, rank):
    points = EmbedField(name=guild[2], value=str(member[3]), inline=True)
    rank = EmbedField(name="Rank", value=str(rank[2]), inline=True)
    #test = calendar.timegm(member[4])
    targetTime = member[4].timestamp() + float(guild[7]) * ONE_HOUR
    cooldown = EmbedField(name="Cooldown", value=f"<t:{int(targetTime)}:R>", inline=True)
    embed = Embed(color=PURPLE, title=f"Guild card for {member[2]}", fields=[points, rank, cooldown])
    return embed
bot.start(TOKEN)
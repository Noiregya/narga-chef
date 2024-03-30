# This example requires the 'message_content' intent.
import os
from interactions import (Client, Intents, listen, slash_command, slash_option, OptionType, SlashContext,
    Member, ChannelType, BaseChannel )
from interactions.api.events import MessageCreate
import logging
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["token"]

bot = Client(intents=Intents.DEFAULT)

@listen()
async def on_message_create(event: MessageCreate):
    event.message  # actual message

@slash_command(name="card",
    description="Show the member's clan card")
@slash_option(
    name="member",
    description="The member you want to see the card of",
    opt_type=OptionType.USER,
    required=False
)  # for slash commands
async def card(ctx: SlashContext, member: Member = None):
    if member == None:
        member = ctx.member
    await ctx.send(f"Member: {member}")

@slash_command(name="setup",
    description="Set up the bot for this server")
@slash_option(name="currency",
    description="Name of the points to be collected",
    opt_type=OptionType.STRING,
    required=True
)
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
async def setup(ctx: SlashContext, currency: str, submission_channel: BaseChannel, review_channel: BaseChannel, info_channel: BaseChannel):
    if submission_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("submission_channel is not a text channel",ephemeral=True)
    if review_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("review_channel is not a text channel",ephemeral=True)
    if info_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("info_channel is not a text channel",ephemeral=True)
    dao.setup(ctx.server.id, ctx.server.name, currency, submission_channel.id, review_channel.id, info_channel.id)
    return await ctx.send("Setup complete. Enjoy!")


bot.start(TOKEN)
import discord
from discord.ext import commands, tasks
import logging
import aiofiles
import asyncio
import aiofiles.os

import dill as pickle
from os import path
from util import get_config
from objects import TOBot

config = get_config('./config.json')
logging.basicConfig(level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format='[{asctime}] [{levelname:<8}] {name}: {message}',
                    style='{')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = TOBot(config, command_prefix=('!', '```!'), case_insensitive=True, intents=intents)

initial_extensions = ['cogs.TournamentManager', 'cogs.Tables',
                      'cogs.Registration', 'cogs.Results',
                      'cogs.TeamManagement', 'cogs.mkc_tournaments',
                      'cogs.lounge', 'cogs.MKCentral']

if path.exists('tournament_data.pkl'):
    with open('tournament_data.pkl', 'rb') as backupFile:
        bot.tournaments = pickle.load(backupFile)
        print("loaded backup file successfully")
else:
    bot.tournaments = {}

@tasks.loop(minutes=1)
async def backup_tournament_data():
    if len(bot.tournaments) == 0:
        return
    # write to a temporary file first in case bot is taken offline while writing
    temp_file_name = 'tournament_data_temp.pkl'
    async with aiofiles.open(temp_file_name, 'wb') as backupFile:
        await backupFile.write(pickle.dumps(bot.tournaments, pickle.HIGHEST_PROTOCOL))
    permanent_file_name = 'tournament_data.pkl'
    await aiofiles.os.replace(temp_file_name, permanent_file_name)
    
@bot.event
async def on_command_error(ctx: commands.Context[TOBot], error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await(await ctx.send("Your command is missing an argument: `%s`" %
                       str(error.param))).delete(delay=10)
        return
    if isinstance(error, commands.CommandOnCooldown):
        await(await ctx.send("This command is on cooldown; try again in %.0fs"
                       % error.retry_after)).delete(delay=5)
        return
    if isinstance(error, commands.MissingAnyRole):
        missing_roles = [str(role) for role in error.missing_roles]
        await(await ctx.send("You need one of the following roles to use this command: `%s`"
                             % (", ".join(missing_roles)))
              ).delete(delay=10)
        return
    if isinstance(error, commands.BadArgument):
        await(await ctx.send("BadArgument Error: `%s`" % error.args)).delete(delay=10)
        return
    if isinstance(error, commands.BotMissingPermissions):
        await(await ctx.send("I need the following permissions to use this command: %s"
                       % ", ".join(error.missing_permissions))).delete(delay=10)
        return
    if isinstance(error, commands.NoPrivateMessage):
        await(await ctx.send("You can't use this command in DMs!")).delete(delay=5)
        return
    if isinstance(error, commands.MissingPermissions):
        await(await ctx.send(f"You need the following permissions to use this command: {', '.join(error.missing_permissions)}")).delete(delay=10)
        return
    if isinstance(error, commands.MaxConcurrencyReached):
        assert ctx.command is not None
        await ctx.send(f"The command `!{ctx.command.name}` can only be used once at a time!", delete_after=20)
        return
    raise error

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))

async def main():
    async with bot:
        for extension in initial_extensions:
            await bot.load_extension(extension)
        backup_tournament_data.start()
        await bot.start(bot.config.token)

asyncio.run(main())

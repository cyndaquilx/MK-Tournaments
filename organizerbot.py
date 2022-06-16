import discord
from discord.ext import commands, tasks
import json
import logging
import aiofiles
import asyncio

import dill as pickle
from os import path

logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)

initial_extensions = ['cogs.TournamentManager', 'cogs.Tables',
                      'cogs.Registration', 'cogs.Results',
                      'cogs.TeamManagement']

with open('./config.json', 'r') as cjson:
    bot.config = json.load(cjson)

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
    async with aiofiles.open('tournament_data.pkl', 'wb') as backupFile:
        await backupFile.write(pickle.dumps(bot.tournaments, pickle.HIGHEST_PROTOCOL))
#backup_tournament_data.start()
    
@bot.event
async def on_command_error(ctx, error):
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
                       % ", ".join(error.missing_perms))).delete(delay=10)
        return
    if isinstance(error, commands.NoPrivateMessage):
        await(await ctx.send("You can't use this command in DMs!")).delete(delay=5)
        return
    if isinstance(error, commands.MissingPermissions):
        await(await ctx.send(f"You need the following permissions to use this command: {', '.join(error.missing_permissions)}")).delete(delay=10)
        return
    raise error

##if __name__ == '__main__':
##    for extension in initial_extensions:
##        bot.load_extension(extension)

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    
##bot.run(bot.config["token"])

async def main():
    async with bot:
        for extension in initial_extensions:
            await bot.load_extension(extension)
        backup_tournament_data.start()
        await bot.start(bot.config["token"])

asyncio.run(main())

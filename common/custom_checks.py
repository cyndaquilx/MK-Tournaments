import discord
from discord.ext import commands, tasks

#ROLE CHECKS

async def has_organizer_role(ctx, tournament):
    check = commands.has_guild_permissions(manage_guild=True).predicate
    try:
        await check(ctx)
        return True
    except Exception as e:
        pass
    for role in ctx.author.roles:
        for orgrole in tournament.organizer_roles:
            if role.id == orgrole:
                return True
    organizer_roles = []
    for role in tournament.organizer_roles:
        organizer_roles.append(ctx.guild.get_role(role))
    await ctx.send("You need one of these roles to use this command:\n"
                   + f"{', '.join([r.name for r in organizer_roles])}")
    return False

async def has_host_role(ctx, tournament):
    check = commands.has_guild_permissions(manage_guild=True).predicate
    try:
        await check(ctx)
        return True
    except Exception as e:
        pass
    if len(tournament.host_roles) == 0:
        return True
    for role in ctx.author.roles:
        for orgrole in tournament.organizer_roles:
            if role.id == orgrole:
                return True
        for hostrole in tournament.host_roles:
            if role.id == hostrole:
                return True
    host_roles = []
    for role in tournament.organizer_roles:
        host_roles.append(ctx.guild.get_role(role))
    for role in tournament.host_roles:
        host_roles.append(ctx.guild.get_role(role))   
    await ctx.send("You need one of these roles to use this command:\n"
                   + f"{', '.join([r.name for r in host_roles])}")
    return False

#BOT.WAIT_FOR CHECKS

async def basic_check(ctx):
    def check(m: discord.Message):
        if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
            return False
        return True
    resp = await ctx.bot.wait_for('message', check=check, timeout=60.0)
    return resp

async def yes_no_check(ctx):
    def check(m: discord.Message):
        if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
            return False
        if m.content.lower() == "yes" or m.content.lower() == "no":
            return True
    resp = await ctx.bot.wait_for('message', check=check, timeout=60.0)
    return resp

async def num_exit_check(ctx):
    def check(m: discord.Message):
        if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
            return False
        if m.content.lower() == "exit":
            return True
        if m.content.isdigit():
            return True
    resp = await ctx.bot.wait_for('message', check=check, timeout=60.0)
    return resp

async def optionCheck(ctx):
    def check(m: discord.Message):
        if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
            return False
        if m.content.lower() in ["back", "exit"]:
            return True
        if m.content.isdigit():
            return True
    resp = await ctx.bot.wait_for('message', check=check, timeout=60.0)
    return resp

async def number_check(ctx):
    def check(m: discord.Message):
        if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
            return False
        if m.content.isdigit():
            return True
    resp = await ctx.bot.wait_for('message', check=check, timeout=60.0)
    return resp


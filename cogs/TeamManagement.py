import discord
from discord.ext import commands, tasks
from objects import Tournament
from common import has_organizer_role, basic_check, yes_no_check, number_check
import common
from algorithms import parsing
import asyncio
import math

class TeamManagement(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.command()
    async def addMKB(self, ctx, *, text:str):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        teams = parsing.parseMKB(tournament.size, text)
        send = ""
        tournament.addTeamsFromLists(teams)
        await ctx.send(f'Added {len(teams)} teams to the tournament from input')

    @commands.command(aliases=['registered'])
    async def registeredTeams(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        i = 1
        msg = f"Registered Teams [{len(tournament.teams)}]\n```"
        for team in tournament.teams:
            msg += f"{i}. "
            if team.tag is not None:
                msg += f"{team.tag} | "
            msg += f"{', '.join(str(player) for player in team)}\n"
            i += 1
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)

    @commands.command()
    async def seed(self, ctx, teamid:int, seednum:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        teams = tournament.teams
        if teamid < 1 or teamid > len(teams):
            await ctx.send(f"Invalid team index; valid numbers are 1-{len(teams)}")
            return
        team = teams[teamid-1]
        team.seed = seednum
        await ctx.send(f"Successfully seeded {str(team)} at {seednum}")

    @commands.command()
    async def toggleHost(self, ctx, teamid:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if teamid < 1:
            await ctx.send("Please enter a number greater than 0")
            return
        if teamid > len(tournament.teams):
            await ctx.send(f"Please enter a number inside the range of the number of teams registered {len(tournament.teams)}")
            return
        team = tournament.teams[teamid-1]
        playersMsg = "Which player do you want to change?\n"
        for i, player in enumerate(team.players):
            if player.canHost:
                playerHost = "(can host)"
            else:
                playerHost = ""
            playersMsg += f"`{i+1})` {str(player)} {playerHost}\n"
        await ctx.send(playersMsg)
        try:
            resp = await number_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled host change")
            return
        choice = int(resp.content)
        if choice < 1 or choice > len(team.players):
            await ctx.send("Invalid player ID; try using this command again")
            return
        player = team.players[choice-1]
        player.canHost = not (player.canHost)
        await ctx.send(f"Set player {str(player)} host field to {player.canHost}")

    @commands.command(aliases=['editMii'])
    async def editMiiName(self, ctx, teamid:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if teamid < 1:
            await ctx.send("Please enter a number greater than 0")
            return
        if teamid > len(tournament.teams):
            await ctx.send(f"Please enter a number inside the range of the number of teams registered {len(tournament.teams)}")
            return
        team = tournament.teams[teamid-1]
        playersMsg = "Which player do you want to change?\n"
        for i, player in enumerate(team.players):
            playersMsg += f"`{i+1})` {str(player)} - {player.miiName}\n"
        await ctx.send(playersMsg)
        try:
            resp = await number_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled name change")
            return
        choice = int(resp.content)
        if choice < 1 or choice > len(team.players):
            await ctx.send("Invalid player ID; try using this command again")
            return
        player = team.players[choice-1]
        await ctx.send("What would you like to change the name to?")
        try:
            resp = await basic_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled name change")
            return
        player.miiName = resp.content
        await ctx.send(f"Successfully changed {str(player)}'s name to {resp.content}")

    @commands.command()
    async def editFC(self, ctx, teamid:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if teamid < 1:
            await ctx.send("Please enter a number greater than 0")
            return
        if teamid > len(tournament.teams):
            await ctx.send(f"Please enter a number inside the range of the number of teams registered {len(tournament.teams)}")
            return
        team = tournament.teams[teamid-1]
        playersMsg = "Which player do you want to change?\n"
        for i, player in enumerate(team.players):
            playersMsg += f"`{i+1})` {str(player)} - {player.miiName}\n"
        await ctx.send(playersMsg)
        try:
            resp = await number_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled FC change")
            return
        choice = int(resp.content)
        if choice < 1 or choice > len(team.players):
            await ctx.send("Invalid player ID; try using this command again")
            return
        player = team.players[choice-1]
        await ctx.send("What would you like to change their FC to?")
        try:
            resp = await basic_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled FC change")
            return
        player.fc = resp.content
        await ctx.send(f"Successfully changed {str(player)}'s FC to {resp.content}")

    @commands.command(aliases=['r'])
    async def remove(self, ctx, id:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if id > len(tournament.teams):
            await ctx.send(f"There are only {len(tournament.teams)} teams in this tournamnet.")
            return
        team = tournament.teams[id-1]
        if team is not None:
            tournament.teams.remove(team)
            await ctx.send(f"Removed {str(team)} from the tournament")
            return


async def setup(bot):
    await bot.add_cog(TeamManagement(bot))

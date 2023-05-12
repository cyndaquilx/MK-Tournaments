import discord
from discord.ext import commands
import aiohttp, asyncio
from common import has_organizer_role, yes_no_check, number_check
from objects import Tournament

class lounge(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.command()
    async def getmmr(self, ctx, season=None):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return False
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        base_url = "https://www.mk8dx-lounge.com" + '/api/player?'
        if season is not None:
            base_url += f"season={int(season)}&"
        headers = {'Content-type': 'application/json'}
        progress = await ctx.send("Working...")
        async with aiohttp.ClientSession() as session:
            not_found = []
            for i, team in enumerate(tournament.teams):
                for player in team.players:
                    await asyncio.sleep(0.05)
                    request_text = f"discordId={player.discordTag}"
                    request_url = base_url + request_text
                    async with session.get(request_url,headers=headers) as resp:
                        if resp.status != 200:
                            player.mmr = 0
                            not_found.append(player)
                            continue
                        player_data = await resp.json()
                        if 'maxMmr' not in player_data.keys():
                            player.mmr = 0
                            #not_found.append(player)
                            continue
                        player.mmr = player_data['maxMmr']
                if i > 0 and i % 10 == 0:
                    await progress.edit(f"Working... ({i}/{len(tournament.teams)})")
        not_found_msg = "\n".join([f"{str(player)} - {player.miiName}" for player in not_found])
        await ctx.send(f"done\nMMR for these players was not found:\n{not_found_msg}")

    @commands.command()
    async def editmmr(self, ctx, teamid:int):
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
            playersMsg += f"`{i+1})` {str(player)} - {player.miiName} - {player.mmr} MMR\n"
        await ctx.send(playersMsg)
        try:
            resp = await number_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled MMR change")
            return
        choice = int(resp.content)
        if choice < 1 or choice > len(team.players):
            await ctx.send("Invalid player ID; try using this command again")
            return
        player = team.players[choice-1]
        await ctx.send("What would you like to change their MMR to?")
        try:
            resp = await number_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled MMR change")
            return
        player.mmr = int(resp.content)
        await ctx.send(f"Successfully changed {str(player)}'s MMR to {resp.content}")

    @commands.command()
    async def printmmrs(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return False
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        msg = f"Team MMRs [{len(tournament.teams)}]\n```"
        i = 1
        for team in tournament.teams:
            msg += f"{i}. "
            if team.tag is not None:
                msg += f"{team.tag} | "
            msg += f"{', '.join(str(player) for player in team)} ({team.avg_mmr()})\n"
            i += 1
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)

    @commands.command()
    async def floatmmr(self, ctx, mmr:int, round:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return False
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.started is False:
            await ctx.send("The tournament must be started to use this command; use `!start`")
            return False
        if tournament.currentRoundNumber() > 0:
            await ctx.send("The tournament has rooms for R1 made already, so this command cannot be used.")
            return
        if round <= 1:
            await ctx.send("Round must be higher than 1")
            return
        await ctx.send(f"Do you want to float teams with over {mmr} MMR to Round {round}? (yes/no)")
        try:
            resp = await yes_no_check(ctx)
            if resp.content.lower() == "no":
                await ctx.send("Cancelled floating teams")
                return
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        teams = tournament.get_unfloated_teams()
        floated_teams = []
        for team in teams:
            if team.avg_mmr() >= mmr:
                floated_teams.append(team)
        if len(tournament.floated_teams) < round:
            for i in range(len(tournament.floated_teams), round):
                tournament.floated_teams.append([])
        tournament.floated_teams[round-1] = floated_teams
        await ctx.send("Done")

    @commands.command()
    async def floated(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return False
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        msg = "```"
        for i, round in enumerate(tournament.floated_teams):
            if len(round) == 0:
                continue
            msg += f"***Round {i+1}**\n"
            for team in round:
                if team.tag is not None:
                    msg += f"{team.tag} | "
                msg += f"{', '.join(str(player) for player in team)} ({team.avg_mmr()})\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(lounge(bot))
import discord
from discord.ext import commands, tasks
from objects import Tournament, TOBot
from common import has_organizer_role
from io import StringIO
import csv

class Results(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def placements(self, ctx: commands.Context[TOBot], arg=""):
        assert ctx.guild is not None
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.finished is False:
            await ctx.send("The tournament must be finished to use this command")
            return
        teams, placements = tournament.getPlacements()
        msg = "```"
        for i in range(len(teams)):
            if arg.lower() == "fc":
                team = " ".join(str(p.fc) for p in teams[i].players)
            elif arg.lower() == "reg":
                team = " ".join(str(p.mkcID) for p in teams[i].players)
            elif arg.lower() == "loungeid":
                team = " ".join(str(p.loungeID) for p in teams[i].players)
            elif arg.lower() == "mkc":
                team = str(teams[i].mkcID)
            else:
                team = str(teams[i])
            msg += f"{team} {placements[i]}\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)

    # used for SUMMIT finale FFA
    #@commands.command()
    async def loungePrizes(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.finished is False:
            await ctx.send("The tournament must be finished to use this command")
            return
        teams = []
        placements = []
        bonuses = []
        final_bonuses = {
            1: 1000,
            2: 900,
            3: 850,
            4: 800,
            5: 750,
            6: 700,
            7: 700,
            8: 700,
            9: 700,
            10: 700,
            11: 700,
            12: 700
        }
        for i in range(len(tournament.rounds)-1, -1, -1):
            currRound = tournament.rounds[i]
            sortableTeams = []
            for room in currRound.rooms:
                sortableTeams.extend(room.table.getSortableTeams(tournament))
            sortableTeams = [s for s in sortableTeams if s.team not in teams]
            sortableTeams.sort(reverse=True)
            roundPlacements = []
            for team in sortableTeams:
                if len(roundPlacements) > 0:
                    if team.rank == sortableTeams[len(roundPlacements)-1].rank:
                        roundPlacements.append(roundPlacements[len(roundPlacements)-1])
                        continue
                roundPlacements.append(len(roundPlacements)+1)
            for placement in roundPlacements:
                if placement + len(placements) <= 12:
                    bonuses.append(final_bonuses[placement+len(placements)])
                else:
                    bonuses.append(int(i*100))
            teams.extend([s.team for s in sortableTeams])
            placements.extend([p + len(placements) for p in roundPlacements])
        output = StringIO()
        writer = csv.writer(output)
        for i in range(len(teams)):
            writer.writerow([p.loungeID for p in teams[i].players] + [placements[i], bonuses[i]])
        output.seek(0)
        f = discord.File(output, filename="bonuses.csv")
        await ctx.send(file=f)
        

    @commands.command()
    async def archiveTables(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.finished is False:
            await ctx.send("The tournament must be finished to use this command")
            return
        txt = ""
        for currRound in tournament.rounds:
            txt += f"***ROUND {currRound.roundNum}***\n\n"
            for room in currRound.rooms:
                txt += f"**ROOM {room.roomNum}**\n"
                for team in room.teams:
                    txt += f"{team.mkcID} - {str(team)} - {team.tableName()}\n"
                txt += f"\nTABLE:\n{room.table.scoreboard()}\n"
            txt += "\n"
        f = discord.File(StringIO(txt), filename="TournamentData.txt")
        await ctx.send(file=f)
        
async def setup(bot):
    await bot.add_cog(Results(bot))

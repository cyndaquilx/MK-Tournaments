import discord
from discord.ext import commands, tasks
from objects import Tournament
from common import has_organizer_role
from io import StringIO

class Results(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.command()
    async def placements(self, ctx, arg=""):
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
            if arg == "fc":
                team = " ".join(p.fc for p in teams[i].players)
            else:
                team = str(teams[i])
            msg += f"{team} {placements[i]}\n"
            #msg += f"{teams[i].mkcID} {placements[i]}\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)
        #await ctx.send(placements)

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

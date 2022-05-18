import discord
from discord.ext import commands, tasks
#from Tournament import Tournament
from objects import Tournament
from algorithms import parsing
#from parsing import parseLorenzi
from common import (has_organizer_role, has_host_role,
                    get_expected_points)
import urllib
import io
import aiohttp

class Tables(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.command()
    async def scoreboard(self, ctx, roomNum:int, roundNum=0):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if roundNum == 0:
            table = tournament.getRoomTableNumber(roomNum)
            if table is None:
                await ctx.send("Invalid room number")
                return
        else:
            if roundNum < 1 or roundNum > len(tournament.rounds):
                await ctx.send("Invalid round number")
                return
            tRound = tournament.rounds[roundNum-1]
            if roomNum < 1 or roomNum > len(tRound.rooms):
                await ctx.send("Invalid room number")
                return
            table = tRound.rooms[roomNum-1].table
        sb = table.scoreboard()
        msg = f"```{sb}```\nPaste the above into https://hlorenzi.github.io/mk8d_ocr/table.html for the table."
        await ctx.send(msg)

    async def tableEmbed(self, ctx, tournament, tround, room, data):
        names, scores = parsing.parseLorenzi(data)
        pNum = int(len(room.teams) * tournament.size)
        
        if len(names) != pNum:
            await ctx.send(f"Your table does not contain {pNum} valid score lines, try again!")
            return None, None, None, None
        if len(set(names)) != len(names):
            await ctx.send("Duplicate names are not allowed! Try again")
            return None, None, None, None
        players = room.getPlayersFromMiiNames(names)
        err_str = ""
        for i in range(len(players)):
            if players[i] is None:
                if len(err_str) == 0:
                    err_str += f"The following players cannot be found in Room {room.roomNum}:\n"
                err_str += f"{names[i]}\n"
        if len(err_str) > 0:
            await ctx.send(err_str)
            return None, None, None, None
        sb = room.sampleScoreboard(players, scores)
        
        base_url_lorenzi = "https://gb.hlorenzi.com/table.png?data="
        url_table_text = urllib.parse.quote(sb)
        image_url = base_url_lorenzi + url_table_text

        connector=aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    f = None
                    imgData = None
                else:
                    imgData = io.BytesIO(await resp.read())
                    f = discord.File(imgData, filename="MogiTable.png")
        
        e = discord.Embed(title="Table")
        e.add_field(name="Round", value=f"Round {room.roundNum}")
        e.add_field(name="Room", value=f"Room {room.roomNum}")
        adv, tie, extra = room.checkAdvanced(tournament, players, scores)
              
        if len(adv) > 0:
            advMsg = ""
            for team in adv:
                advMsg += f"{team.tableName()}\n"
            e.add_field(name="Advancing", value=advMsg, inline=False)
        if len(tie) > 0:
            tieMsg = ""
            for team in tie:
                tieMsg += f"{team.team.tableName()}\n"
            e.add_field(name="Tiebreaker", value=tieMsg, inline=False)
        if len(extra) > 0:
            extraMsg = ""
            n = tournament.getNthPlace()
            for team in extra:
                extraMsg += f"{team.team.tableName()}\n"
            e.add_field(name=f"{n} Place Teams", value=extraMsg,inline=False)

        if hasattr(tround, 'races'):          
            exp_points = get_expected_points(tournament.game, pNum, tround.races)
            total_score = sum(scores)
            if total_score != exp_points:
                e.add_field(name="Warning", value=f"This table has {total_score} points but this round expects"
                            + f" {exp_points} points! This may be an error")
        
        e.set_image(url="attachment://MogiTable.png")
        return e, f, players, scores

    @commands.command()
    async def submit(self, ctx, roomid:int, *, data):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_host_role(ctx, tournament) is False:
            return
        currRound = tournament.currentRound()
        room = tournament.getRoomNumber(roomid)
        if room is None:
            await ctx.send("Invalid room number")
            return
        
        e, f, players, scores = await self.tableEmbed(ctx, tournament, currRound, room, data)
        if e is None:
            return
        content = f"{ctx.author.mention} Please react to this message with \U00002611 within the next 30 seconds to confirm the table is correct"
        embedded = await ctx.send(file=f, content=content, embed=e)
        #ballot box with check emoji
        CHECK_BOX = "\U00002611"
        X_MARK = "\U0000274C"
        await embedded.add_reaction(CHECK_BOX)
        await embedded.add_reaction(X_MARK)

        def check(reaction, user):
            if user != ctx.author:
                return False
            if reaction.message != embedded:
                return False
            if str(reaction.emoji) == X_MARK:
                return True
            if str(reaction.emoji) == CHECK_BOX:
                return True
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except:
            await embedded.delete()
            return

        if str(reaction.emoji) == X_MARK:
            await embedded.delete()
            return
        room.updateTable(tournament, players, scores)
        await embedded.delete()
        await ctx.send("Table updated")
        await self.sendResults(ctx, roomid, e)

    @commands.command(aliases=['fix'])
    async def fixOldTable(self, ctx, roomid:int, *, data):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        lastRound = tournament.lastRound()
        if lastRound is None:
            return
        if roomid < 1 or roomid > len(lastRound.rooms):
            await ctx.send(f"Invalid room number; valid numbers are 1-{len(lastRound.rooms)}")
            return
        room = lastRound.rooms[roomid-1]
        e, f, players, scores = await self.tableEmbed(ctx, tournament, lastRound, room, data)
##        names, scores = parsing.parseLorenzi(data)
##        pNum = tournament.playersPerRoom
##        if len(names) != pNum:
##            await ctx.send(f"Your table does not contain {pNum} valid score lines, try again!")
##            return
##        if len(set(names)) != len(names):
##            await ctx.send("Duplicate names are not allowed! Try again")
##            return
##        players = room.getPlayersFromMiiNames(names)
##        err_str = ""
##        for i in range(len(players)):
##            if players[i] is None:
##                if len(err_str) == 0:
##                    err_str += f"The following players cannot be found in Room {room.roomNum}:\n"
##                err_str += f"{names[i]}\n"
##        if len(err_str) > 0:
##            await ctx.send(err_str)
##            return
##        sb = room.sampleScoreboard(players, scores)
##        
##        
##        base_url_lorenzi = "https://gb.hlorenzi.com/table.png?data="
##        url_table_text = urllib.parse.quote(sb)
##        image_url = base_url_lorenzi + url_table_text
##
##        async with aiohttp.ClientSession() as session:
##            async with session.get(image_url) as resp:
##                if resp.status != 200:
##                    f = None
##                    imgData = None
##                else:
##                    imgData = io.BytesIO(await resp.read())
##                    f = discord.File(imgData, filename="MogiTable.png")
##        
##        e = discord.Embed(title="Table")
##        adv, tie, extra = room.checkAdvanced(tournament, players, scores)
##              
##        if len(adv) > 0:
##            advMsg = ""
##            for team in adv:
##                advMsg += f"{team.tableName()}\n"
##            e.add_field(name="Advancing", value=advMsg)
##        if len(tie) > 0:
##            tieMsg = ""
##            for team in tie:
##                tieMsg += f"{team.tableName()}\n"
##            e.add_field(name="Tiebreaker", value=tieMsg, inline=False)
##        if len(extra) > 0:
##            extraMsg = ""
##            n = tournament.getNthPlace()
##            for team in extra:
##                extraMsg += f"{team.team.tableName()}\n"
##            e.add_field(name=f"{n} Place Teams", value=extraMsg,inline=False)
##        
##        e.set_image(url="attachment://MogiTable.png")
        #e.set_image(url=image_url)
        content = f"{ctx.author.mention} **WARNING:** The rooms in the current round may be affected by this change. Make sure this is okay before confirming"
        embedded = await ctx.send(file=f, content=content, embed=e)
        #ballot box with check emoji
        CHECK_BOX = "\U00002611"
        X_MARK = "\U0000274C"
        await embedded.add_reaction(CHECK_BOX)
        await embedded.add_reaction(X_MARK)

        def check(reaction, user):
            if user != ctx.author:
                return False
            if reaction.message != embedded:
                return False
            if str(reaction.emoji) == X_MARK:
                return True
            if str(reaction.emoji) == CHECK_BOX:
                return True
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except:
            await embedded.delete()
            return

        if str(reaction.emoji) == X_MARK:
            await embedded.delete()
            return
        room.updateTable(tournament, players, scores)
        lastExtra = tournament.adv_path[tournament.currentRoundNumber()-2].topscorers
        newAdv, scores = lastRound.getAdvanced(lastExtra)
        currRound = tournament.currentRound()
        currTeams = currRound.teams
        new = [t for t in newAdv if t not in currTeams]
        old = [t for t in currTeams if t not in newAdv]
        msg = ""
        for i in range(len(new)):
            room = currRound.replaceTeam(old[i], new[i])
            if room is not None:
                msg += f"Room {room} - "
            msg += f"{str(old[i])} -> {str(new[i])}\n"
        if len(msg) > 0:
            msg = "The following changes have been made to the current round:\n" + msg
            await ctx.send(msg)
        await self.sendResults(ctx, roomid, e, lastRound.roundNum)
        #await ctx.send("Table updated")
        

    #@commands.command()
    async def sendResults(self, ctx, room:int, embed, roundNum=0):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if roundNum == 0:
            currRound = tournament.currentRound()
            roundNum = tournament.currentRoundNumber()
        else:
            currRound = tournament.rounds[roundNum-1]
        if tournament.results_channel is None:
            return
        channel = ctx.guild.get_channel(tournament.results_channel)
        if channel is None:
            return
        table = currRound.rooms[room-1].table
        sb = table.scoreboard()
        base_url_lorenzi = "https://gb.hlorenzi.com/table.png?data="
        url_table_text = urllib.parse.quote(sb)
        image_url = base_url_lorenzi + url_table_text
        connector=aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    f = None
                    imgData = None
                else:
                    imgData = io.BytesIO(await resp.read())
                    f = discord.File(imgData, filename="MogiTable.png")
        #e = discord.Embed(title="Room Results")
        embed.title = "Room Results"
        embed.set_image(url="attachment://MogiTable.png")
        await channel.send(embed=embed, file=f)

##    @commands.command()
##    async def view(self, ctx, room:int, roundNum=0):
##        if ctx.guild.id not in ctx.bot.tournaments:
##            return
##        tournament = ctx.bot.tournaments[ctx.guild.id]
##        if roundNum == 0:
##            t_round = 
        

async def setup(bot):
    await bot.add_cog(Tables(bot))

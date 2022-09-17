import discord
from discord.ext import commands, tasks
from objects import Tournament
from common import (has_organizer_role, basic_check, yes_no_check,
                    number_check, num_exit_check, optionCheck, getNthPlace)
import common
from algorithms import parsing
import aiohttp
import asyncio
import math

class TournamentManager(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self._progress_task = self.update_progress_channels.start()

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def tournament(self, ctx, size:int):
        valid_sizes = [1, 2, 3, 4]
        if size not in valid_sizes:
            await ctx.send(f"Invalid size: Valid sizes are: {', '.join([str(i) for i in valid_sizes])}")
            return
        await ctx.send(f"{ctx.author.mention} Before starting the tournament, there's a few steps that need to be completed.\n")
        await ctx.send("`1.` What game is this tournament for (MKW, MK7, MK8, MK8DX, MKT)?")

        try:
            resp = await basic_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        valid_games = ["MKW", "MK7", "MK8", "MK8DX", "MKT"]
        if resp.content.upper() not in valid_games:
            await ctx.send(f"Invalid game. Valid games are: {', '.join(valid_games)}")
            return
        game = resp.content.upper()
        #since mk7/mkt are 8 players, only ffa and 2v2 are supported
        if size > 2 and game in ["MK7", "MKT"]:
            await ctx.send("Only FFA and 2v2 are supported for MK7/MKTour tournaments, try again")
            return
        await ctx.send("`2.` What is the name of your tournament?")
        try:
            resp = await basic_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        name = resp.content
        await ctx.send("`3.` Please mention your server's **Tournament Organizer** role")
        #RoleConverter object converts a string to a role, useful for when you need a reply with a role
        c = commands.RoleConverter()
        
        #getting the tournament organizer role
        try:
            resp = await basic_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        try:
            orgRole = await c.convert(ctx, resp.content)
        except Exception as e:
            await ctx.send("You didn't type a valid role! Try this command again")
            return
        await ctx.send("`4.` Please mention your server's **host** role (type `None` if you want everyone to have host permissions)")
        #getting the host role
        try:
            resp = await basic_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        if resp.content.lower() == "none":
            hostRoles = []
        else:
            try:
                hostRole = await c.convert(ctx, resp.content)
                hostRoles = [hostRole.id]
            except Exception as e:
                await ctx.send("You didn't type a valid role! Try this command again")
                return
        await ctx.send("`5.` Do you want to use tiebreakers for teams who tie for an advancing spot? (yes/no)")
        try:
            resp = await yes_no_check(ctx)
            if resp.content.lower() == "yes":
                tiebreakerRule = True
            else:
                tiebreakerRule = False
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        e = discord.Embed(title="Tournament Settings")
        e.add_field(name="Tournament Name", value=name, inline=False)
        e.add_field(name="Game", value=game)
        e.add_field(name="Organizer Role", value=orgRole.mention)
        if len(hostRoles) > 0:
            e.add_field(name="Host Role", value=hostRole.mention)
        e.add_field(name="1 race tiebreaker rule", value=tiebreakerRule)
        await ctx.send(embed=e, content=f"{ctx.author.mention} Are these settings correct? (yes/no)")
        
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled creating tournament")
            return
        if resp.content.lower() == "no":
            await ctx.send("Cancelled creating tournament")
            return
        ctx.bot.tournaments[ctx.guild.id] = Tournament(size, name, game, [orgRole.id], hostRoles)
        ctx.bot.tournaments[ctx.guild.id].tiebreakRule = tiebreakerRule
        await ctx.send("Successfully created the tournament!")

    @commands.command()
    async def addHostRole(self, ctx, role:discord.Role):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if role.id in self.host_roles:
            await ctx.send("This role already has host privileges")
            return
        tournament.host_roles.append(role.id)
        await ctx.send("Successfully gave host permissions")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addOrganizerRole(self, ctx, role:discord.Role):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if role.id in tournament.organizer_roles:
            await ctx.send("This role already has organizer privileges")
            return
        tournament.organizer_roles.append(role.id)
        await ctx.send("Successfully gave organizer permissions")
        
    @commands.command(aliases=['check'])
    async def checkTournamentInfo(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        await ctx.send(tournament.signups)

    @commands.command()
    async def start(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.started is True:
            await ctx.send("Tournament is already started")
            return
        await ctx.send("**WARNING:** You will not be able to re-open registrations or add new players once the tournament has started. Are you sure you want to begin the tournament? (yes/no)")
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled starting tournament")
            return
        if resp.content.lower() == "no":
            await ctx.send("Cancelled starting tournament")
            return
        tournament.started = True
        tournament.signups = False
        await ctx.send("Successfully started the tournament")

    async def customCap(self, ctx, tournament, numTeams):
        players = tournament.playersPerRoom
        size = tournament.size
        while True:
            capEmbed = discord.Embed(title="Custom setup")
            capEmbed.add_field(name="Team Cap", value=f"How many teams would you like to cap the event at? ({numTeams} registered) (type `exit` to exit)")
            await ctx.send(embed=capEmbed)
            try:
                resp = await num_exit_check(ctx)
            except asyncio.TimeoutError:
                await ctx.send("Timed out: Use `!adv` to restart")
                return False
            if resp.content.lower() == "exit":
                await ctx.send("Cancelled creating advancements; use `!adv` to restart")
                return False
            if int(resp.content) < (players / size) or int(resp.content) > numTeams:
                await ctx.send(f"Invalid cap; valid number of teams are between {int(players/size)} and {numTeams}")
                continue
            cap = int(resp.content)
            finished = await self.customNumRooms(ctx, tournament, cap)
            if finished is True:
                tournament.cap = cap
                return True
            if finished is False:
                return False

    async def customNumRooms(self, ctx, tournament, cap):
        players = tournament.playersPerRoom
        size = tournament.size
        if size == 1:
            change = 2
        else:
            change = size
        minRooms = math.ceil(cap / (players/size))
        maxRooms = int(cap / ((players-change)/size))
        while True:
            newRoomsEmbed = discord.Embed(title="Custom setup")
            newRoomsEmbed.add_field(name="Rooms", value=f"How many rooms would you like there to be? (min: {minRooms}, max: {maxRooms}) (type `back` to go back, type `exit` to exit)")
            await ctx.send(embed=newRoomsEmbed)
            try:
                resp = await num_exit_check(ctx)
            except asyncio.TimeoutError:
                await ctx.send("Timed out: Use `!r1config` to restart")
                return False
            if resp.content.lower() == "exit":
                await ctx.send("Cancelled creating advancements; use `!adv` to restart")
                return False
            if resp.content.lower() == "back":
                return
            if int(resp.content) < (minRooms) or int(resp.content) > maxRooms:
                await ctx.send(f"Invalid # of rooms; valid number of teams are between {minRooms} and {maxRooms}")
                continue
            tournament.numRound1Rooms = int(resp.content)
            return True
        
    @commands.command(aliases=['r1config'])
    async def configureFirstRound(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return False
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.started is False:
            await ctx.send("The tournament must be started to use this command; use `!start`")
            return False
        numTeams = tournament.numTeams()
        size = tournament.size
        players = tournament.playersPerRoom
        rooms = int(numTeams / (players/size))
        cap = int(rooms * (players/size))
        def yes_no_check(m: discord.Message):
            if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
                return False
            if m.content.lower() == "yes" or m.content.lower() == "no":
                return True
        await ctx.send("Would you like to guarantee hosts a place in Round 1? (yes/no)")
        try:
            response = await ctx.bot.wait_for('message', check=yes_no_check, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Use `!r1config` to restart")
            return False
        if response.content.lower() == "yes":
            tournament.prioritizeHosts = True
        if response.content.lower() == "no":
            tournament.prioritizeHosts = False
        roomsEmbed = discord.Embed(title="Number of rooms")
        roomsEmbed.add_field(name="Recommended", value=rooms)
        capMsg = f"This would run the tournament with **{cap}** teams, cutting off the last **{numTeams-cap}** teams"
        roomsEmbed.add_field(name="Team Cap", value=capMsg, inline=False)
        confirm = f"Would you like to use this recommended setting? (yes/no)"
        roomsEmbed.add_field(name="Confirmation", value=confirm, inline=False)
        roomsMsg = await ctx.send(embed=roomsEmbed)
        
        try:
            response = await ctx.bot.wait_for('message', check=yes_no_check, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Use `!r1config` to restart")
            return False
        if response.content.lower() == "yes":
            tournament.cap = cap
            tournament.numRound1Rooms = rooms
        if response.content.lower() == "no":
            finished = await self.customCap(ctx, tournament, numTeams)
            if finished is False:
                return False
        
        finalEmbed = discord.Embed(title="Finished configuring settings for Round 1")
        finalEmbed.add_field(name="# of teams", value=tournament.cap)
        finalEmbed.add_field(name="# of rooms", value=tournament.numRound1Rooms)
        finalEmbed.add_field(name="Prioritize hosts", value=tournament.prioritizeHosts)
        await ctx.send(embed=finalEmbed)
        return True

    async def customRooms(self, ctx, tournament, rooms, roundNum):
        teamsPerRoom = int(tournament.playersPerRoom/tournament.size)
        
        minRooms = math.ceil(1 / teamsPerRoom * rooms)
        #maxRooms = math.floor((teamsPerRoom - 1) / teamsPerRoom * rooms)
        maxRooms = math.floor((teamsPerRoom) / teamsPerRoom * rooms)
        await ctx.send(f"Please enter the number of rooms you want (min: {minRooms}, max: {maxRooms})")
        
        def roomCheck(m: discord.Message):
            if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
                return False
            if m.content.isdigit():
                if int(m.content) >= minRooms and int(m.content) <= maxRooms:
                    return True
        try:
            resp = await ctx.bot.wait_for('message', check=roomCheck, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Use `!advConfig` to restart")
            return False
        newRooms = int(resp.content)
        numAdvancing = int(newRooms * teamsPerRoom / rooms)
        numExtra = int((newRooms * teamsPerRoom) % rooms)
        confirmEmbed = discord.Embed(title="Confirmation",
                                     description="Please confirm that these settings are correct (yes/no)")
        confirmEmbed.add_field(name=f"Round {roundNum} rooms", value=rooms)
        confirmEmbed.add_field(name="Teams advancing", value=f"{numAdvancing}/{teamsPerRoom}", inline=False)
        if numExtra > 0:
            confirmEmbed.add_field(name=f"{common.getNthPlace(numAdvancing+1)} place teams", value=numExtra)
        confirmEmbed.add_field(name=f"# of Round {roundNum+1} rooms", value=newRooms, inline=False)
        await ctx.send(embed=confirmEmbed)
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Use `!advConfig` to restart")
            return False
        if resp.content.lower() == "no":
            await ctx.send("Cancelled creating advancements; use `!advConfig` to restart")
            return False
        return tournament.createCustomAdvancement(rooms, newRooms, numAdvancing, numExtra)
                
    @commands.command(aliases=['advConfig'])
    async def configureAdvancements(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.started is False:
            await ctx.send("The tournament must be started to use this command; use `!start`")
            return False
        if tournament.cap is None:
            success = await self.configureFirstRound(ctx)
            if success is False:
                return False
        size = tournament.size
        if tournament.currentRound() is None:
            rooms = tournament.numRound1Rooms
            startingRound = 1
        else:
            rooms = tournament.currentRoundRooms()
            startingRound = tournament.currentRoundNumber()
        roundNum = startingRound
        path = []
            
        while rooms > 1:
            nxt = tournament.calcAdvancements(rooms)
            advEmbed = discord.Embed(title=f"Round {roundNum} advancements ({rooms} rooms)")
            optionStr = ""
            i = 1
            for adv in nxt:
                optionStr += f"**{i})** Top {adv.adv} + {adv.topscorers} -> {adv.newRooms} rooms\n"
                i += 1
            optionStr += f"**{i})** Custom\n"
            optionStr += "type `back` to go back, type `exit` to exit"
            advEmbed.add_field(name="Please respond with your chosen option", value=optionStr)
            await ctx.send(embed=advEmbed)
            try:
                resp = await optionCheck(ctx)
            except asyncio.TimeoutError:
                await ctx.send("Timed out: Use `!advConfig` to restart")
                return False
            if resp.content == "back":
                if len(path) == 0:
                    continue
                rooms = path[len(path)-1].oldRooms
                del path[len(path)-1]
                roundNum -= 1
                continue
            if resp.content == "exit":
                await ctx.send("Cancelled creating advancements; use `!advConfig` to restart")
                return False
            opt = int(resp.content)
            if opt > 0 and opt <= len(nxt):
                chosenAdv = nxt[opt-1]
            else:
                custom = await self.customRooms(ctx, tournament, rooms, roundNum)
                if custom is False:
                    return False
                chosenAdv = custom
            roundNum += 1
            path.append(chosenAdv)
            rooms = chosenAdv.newRooms
        finalAdv = tournament.createCustomAdvancement(1, 0, 0, 0)
        path.append(finalAdv)
        
        confirmStr = ""
        roundNum = startingRound
        teamsPerRoom = int(tournament.playersPerRoom/tournament.size)
        for adv in path:
            if roundNum == 1:
                teams = tournament.cap
            else:
                teams = int(teamsPerRoom * adv.oldRooms)
            if adv.oldRooms > 1:
                confirmStr += f"Round {roundNum} | {teams} teams **({adv.oldRooms} rooms)** | Top {adv.adv} + {adv.topscorers} advance\n"
            else:
                confirmStr += f"Finals | {teamsPerRoom} teams **(1 room)**\n"
            roundNum += 1
                
        confirmEmbed = discord.Embed(title="Confirmation",
                                     description="Please confirm that these settings are correct (yes/no)")
        confirmEmbed.add_field(name="Tournament Advancements", value=confirmStr)
        await ctx.send(embed=confirmEmbed)
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Use `!advConfig` to restart")
            return False
        if resp.content.lower() == "no":
            await ctx.send("Cancelled creating advancements; use `!advConfig` to restart")
            return False
        tournament.editPath(path, startingRound)
        await ctx.send("Successfully created advancements")
        return True
        
    @commands.command()
    async def nextRound(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if tournament.started is False:
            await ctx.send("The tournament must be started to use this command; use `!start`")
            return False
        if tournament.finished is True:
            await ctx.send("The tournament has already been finished")
            return
        if len(tournament.adv_path) == 0:
            success = await self.configureAdvancements(ctx)
            if success is False:
                return
        currentRound = tournament.currentRound()
        if currentRound is not None:
            if currentRound.randomized is False:
                await ctx.send("The current round has not been finished yet!")
                return
            notFinished = []
            tiebreaks = []
            for room in currentRound.rooms:
                if room.table.finished is False:
                    notFinished.append(room.roomNum)
                if len(room.tieTeams) > 0:
                    tiebreaks.append(room.roomNum)
            if len(notFinished) > 0:
                missingRooms = ", ".join(notFinished)
                await ctx.send(f"The following rooms need to be updated: {missingRooms}")
                return
            if len(tiebreaks) > 0:
                missingTies = ", ".join([str(t) for t in tiebreaks])
                await ctx.send(f"The following tiebreakers need to be resolved: {missingTies}")
                return
        if tournament.currentRoundNumber() == len(tournament.adv_path):
            tournament.finished = True
            await ctx.send("The tournament has now been completed!")
            return
        await ctx.send("How many races would you like there to be this round?")
        try:
            resp = await number_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Cancelled creating next round")
            return
        races = int(resp.content)
        newRound = tournament.nextRound(races)
        await ctx.send(f"Successfully advanced to round {newRound.roundNum}")

    @commands.command()
    async def prevRound(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if len(currentRound.rooms) > 0:
            await ctx.send("Rooms have already been made for this round, so you can't use this command. "
                           + "Use `!deleterooms` if you really need to delete the rooms.")
            return
        tournament.rounds.remove(currentRound)

    @commands.command(aliases=['mr'])
    async def makeRooms(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if currentRound is None:
            await ctx.send("There are currently no rounds in the tournament; use `!nextRound`")
            return
        if currentRound.randomized is True:
            await ctx.send("Rooms have already been randomized for this round!")
            return
        hosts = currentRound.getHostTeams()
        numRooms = tournament.currentRoundRooms()
        if len(hosts) < numRooms:
            await ctx.send(f"There are only {len(hosts)} hosting teams but {numRooms} rooms planned for next round. "
                           + f"Use `!togglehost` to add more hosts or `!advconfig` to reduce the number of rooms.")
            return
        numTeams = currentRound.numTeams()
        players = tournament.playersPerRoom
        size = tournament.size
        if size == 1:
            change = 2
        else:
            change = size
        minRooms = math.ceil(numTeams / (players/size))
        maxRooms = int(numTeams / ((players-change)/size))
        # runs if somehow you advanced too many or too little players for this round's num of rooms
        if numRooms < minRooms or numRooms > maxRooms:
            await ctx.send(f"The number of teams in this round ({numTeams}) is not compatible with the number of rooms configured ({numRooms}). "
                           + f"Either change the number of rooms using `!advConfig` or use `!prevRound` "
                           + f"to go to the previous round to fix the number of players advancing.")
            return
        rng_url = f"https://www.random.org/sequences/?min=0&max={numTeams-1}&format=plain&rnd=new&col=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(rng_url) as resp:
                rngText = await resp.text()
        rngList = [int(num) for num in rngText.split()]
        rooms = currentRound.seedRooms(numRooms, rngList, tournament)
        await ctx.send("Successfully randomized rooms; use `!printRooms` or `!pr` to view")

    @commands.command()
    async def printFormat(self, ctx, pformat):
        if pformat.lower() not in common.print_formats:
            await ctx.send("Invalid print format")
            return
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if pformat.lower() == "none":
            tournament.print_format = None
        else:
            tournament.print_format = pformat.lower()
        await ctx.send("Successfully changed print format")
        return

    @commands.command(aliases=['pr'])
    async def printRooms(self, ctx, roomnum=0):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if currentRound is None:
            await ctx.send("There are currently no rounds in the tournament; use `!nextRound`")
            return
        rngd = currentRound.randomized
        if rngd is False:
            await ctx.send("Rooms have not been created yet; use `!makeRooms` / `!mr`")
            return
        rooms = currentRound.rooms
        if roomnum > 0:
            if roomnum > len(rooms):
                await ctx.send("invalid room number")
                return
        await common.printRooms(ctx, tournament.print_format, rooms, roomnum)
        
    @commands.command()
    async def deleteRooms(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if currentRound is None:
            await ctx.send("There are currently no rounds in the tournament; use `!nextRound`")
            return
        for room in currentRound.rooms:
            if room.table.finished is True:
                await ctx.send("Rooms have already been finished in this round, so you can't delete the rooms.")
                return
        currentRound.rooms = []
        currentRound.randomized = False
        await ctx.send("Are you SURE you want to delete this round's rooms? (yes/no)")
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled deletion")
            return
        if resp.content.lower() == "no":
            await ctx.send("Cancelled deletion")
            return
        await ctx.send("Successfully deleted this round's rooms")

    @commands.command()
    async def replace(self, ctx, id1:int, id2:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if currentRound is None:
            await ctx.send("There are currently no rounds in the tournament; use `!nextRound`")
            return
        numTeams = len(tournament.teams)
        if id1 < 1 or id2 < 1:
            await ctx.send("Please enter a number greater than 0; use `!registered` to see the valid teams")
            return
        if id1 > numTeams or id2 > numTeams:
            await ctx.send("One of your team IDs is greater than the number of registered teams; use `!registered` to see the valid teams")
            return
        if id1 == id2:
            await ctx.send("The two IDs you entered are identical; try again")
            return
        t1 = tournament.teams[id1-1]
        t2 = tournament.teams[id2-1]
        if t1 not in currentRound.teams:
            await ctx.send(f"The team `{id1}. {str(t1)}` is not in the current round, so you can't replace them!")
            return
        if t2 in currentRound.teams:
            await ctx.send(f"The team `{id2}. {str(t2)}` is already in the current round!")
            return
        await ctx.send(f"Are you sure you want to replace this team:\n"
                       + f"`{id1}. {str(t1)}`"
                       + f"\nwith this team:\n`{id2}. {str(t2)}`\n"
                       + f"in round {currentRound.roundNum}? (yes/no)")
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled replacement")
            return
        if resp.content.lower() == "no":
            await ctx.send("Cancelled replacement")
            return
        room = currentRound.replaceTeam(t1, t2)
        await ctx.send(f"Replaced `{id1}. {str(t1)}` with `{id2}. {str(t2)}` in room {room}")
        return

    @commands.command()
    async def swap(self, ctx, id1:int, id2:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if currentRound is None:
            await ctx.send("There are currently no rounds in the tournament; use `!nextRound`")
            return
        numTeams = len(tournament.teams)
        if id1 < 1 or id2 < 1:
            await ctx.send("Please enter a number greater than 0; use `!registered` to see the valid teams")
            return
        if id1 > numTeams or id2 > numTeams:
            await ctx.send("One of your team IDs is greater than the number of registered teams; use `!registered` to see the valid teams")
            return
        if id1 == id2:
            await ctx.send("The two IDs you entered are identical; try again")
            return
        t1 = tournament.teams[id1-1]
        t2 = tournament.teams[id2-1]
        if t1 not in currentRound.teams:
            await ctx.send(f"The team `{id1}. {str(t1)}` is not in the current round, so you can't replace them!")
            return
        if t2 not in currentRound.teams:
            await ctx.send(f"The team `{id2}. {str(t2)}` is not in the current round, so you can't replace them!")
            return
        await ctx.send(f"Are you sure you want to swap this team:\n"
                       + f"`{id1}. {str(t1)}`"
                       + f"\nand this team:\n`{id2}. {str(t2)}`\n"
                       + f"in round {currentRound.roundNum}? (yes/no)")
        try:
            resp = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled replacement")
            return
        if resp.content.lower() == "no":
            await ctx.send("Cancelled replacement")
            return
        room = currentRound.swapTeam(t1, t2)
        await ctx.send(f"Swapped `{id1}. {str(t1)}` with `{id2}. {str(t2)}`")
        return

    @commands.command()
    async def reseed(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if hasattr(tournament, 'reseed'):
            tournament.reseed = not tournament.reseed
        else:
            tournament.reseed = True
        if tournament.reseed:
            await ctx.send("Teams will now be reseeded in rooms after each round")
        else:
            await ctx.send("Teams will no longer be reseeded in rooms after each round")

    @commands.command()
    async def roundProgress(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        currentRound = tournament.currentRound()
        if currentRound is None:
            await ctx.send("There are currently no rounds in the tournament; use `!nextRound`")
            return
        if currentRound.numRooms() == 0:
            await ctx.send("Rooms have not yet been made for this round, check again later")
            return
        msg = f"`Round {tournament.currentRoundNumber()} Progress`\n"
        finishCount = 0
        for room in currentRound.rooms:
            if room.table.finished:
                msg += f"\t{room.roomNum} ✓\n"
                finishCount += 1
            else:
                msg += f"\t{room.roomNum} ✘\n"
        msg += f"`{finishCount}/{currentRound.numRooms()} finished`"
        await ctx.send(msg)
        

    @commands.command()
    async def roomAdvanced(self, ctx, roomnum:int):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        #table = tournament.getRoomTableNumber(roomnum)
        room = tournament.getRoomNumber(roomnum)
        advancement = tournament.adv_path[tournament.currentRoundNumber()-1]
        numAdv = advancement.adv
        xExtra = advancement.topscorers
        #adv, tied, extra = table.getAdvanced(tournament)
        adv = room.advanced
        tied = room.tieTeams
        extra = room.extraTeams
        advstr = "**Advanced:**\n"
        for team in adv:
            advstr += f"{str(team)}\n"
        if len(tied) > 0:
            advstr += "**Tiebreaker:**\n"
            for team in tied:
                advstr += f"{str(team.team)}\n"
        if xExtra > 0 and len(extra) > 0:
            advstr += "**Potentially advancing:**\n"
            for team in extra:
                advstr += f"{str(team.team)}\n"
        await ctx.send(advstr)

    @commands.command()
    async def advanced(self, ctx, roundNum=0):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if roundNum == 0:
            currRound = tournament.currentRound()
            roundNum = tournament.currentRoundNumber()
        else:
            currRound = tournament.rounds[roundNum-1]
        for room in currRound.rooms:
            if room.table.finished is False:
                await ctx.send("Round isnt finished yet")
                return
        extra = tournament.adv_path[roundNum-1].topscorers
        #print(extra)
        adv, scores = currRound.getAdvanced(extra)
        msg = f"```ADVANCING FROM ROUND {roundNum}\n"
        for index, team in enumerate(adv):
            #print(scores[index])
            if scores[index] > 0:
                msg += f"{scores[index]} - "
            msg += f"{team.tableName()}\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)

    @commands.command()
    async def topscorers(self, ctx, roundNum=0):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if roundNum == 0:
            currRound = tournament.currentRound()
            roundNum = tournament.currentRoundNumber()
        else:
            currRound = tournament.rounds[roundNum-1]
        adv = tournament.adv_path[roundNum-1]
        x = []
        for room in currRound.rooms:
            x.extend(room.extraTeams)
        #print(len(x))
        x.sort(reverse=True)
        if len(x) == 0:
            await ctx.send("Either this round doesn't have the top-scorers rule or no tables have been submitted")
            return
        nth = common.getNthPlace(adv.adv + 1)
        msg = f"```Top-scoring {nth} teams in Round {roundNum}\n"
        for i, team in enumerate(x):
            if i == adv.topscorers:
                msg += "--------\n"
            tscore = 0
            for player in team.team:
                tscore += team.playerScores[player]
            if team.rank <= adv.adv:
                rank = f" ({common.getNthPlace(team.rank)})"
            else:
                rank = ""
            msg += f"{tscore}{rank} - {team.team.tableName()}\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)

    @commands.command(aliases=['rr'])
    async def roundRanking(self, ctx, roundNum=0):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        if roundNum == 0:
            currRound = tournament.currentRound()
            roundNum = tournament.currentRoundNumber()
        else:
            currRound = tournament.rounds[roundNum-1]
        extra = tournament.adv_path[roundNum-1].topscorers
        adv, scores = currRound.getAdvanced(extra)
        sortable_teams = []
        for room in currRound.rooms:
            sortable_teams.extend(room.table.getSortableTeams(tournament))
        adv_sortable = [t for t in sortable_teams if t.team in adv]
        elim_sortable = [t for t in sortable_teams if t not in adv_sortable]

        adv_sortable.sort(reverse=True)
        elim_sortable.sort(reverse=True)
        msg = f"```Round {currRound.roundNum} team ranking\n"
        msg += f"TID  | Rank | Score | Players \n"
        for t in adv_sortable:
            t_score = sum([t.playerScores[p] for p in t.team])
            msg += f"{tournament.teams.index(t.team)+1:<4} | {t.rank:<4} | {t_score:<5} | {t.team.tableName()}\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        msg += "--------\n"
        for t in elim_sortable:
            t_score = sum([t.playerScores[p] for p in t.team])
            msg += f"{tournament.teams.index(t.team)+1:<4} | {t.rank:<4} | {t_score:<5} | {t.team.tableName()}\n"
            if len(msg) > 1500:
                msg += "```"
                await ctx.send(msg)
                msg = "```"
        if len(msg) > 3:
            msg += "```"
            await ctx.send(msg)

    @commands.command()
    async def progressChannel(self, ctx, channel:discord.TextChannel):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        tournament.progress_channel = channel.id
        await ctx.send(f"Successfully set progress channel to {channel.mention}")

    @commands.command()
    async def resultsChannel(self, ctx, channel:discord.TextChannel):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        tournament.results_channel = channel.id
        await ctx.send(f"Successfully set results channel to {channel.mention}")

    @commands.command()
    async def tiebreak(self, ctx, roomNum:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        room = tournament.getRoomNumber(roomNum)
        if room is None:
            await ctx.send("Room could not be found in the current round")
            return
        if len(room.tieTeams) == 0:
            await ctx.send("There are no tied teams in this room")
            return
        roundNum = tournament.currentRoundNumber()
        numAdv = tournament.adv_path[roundNum-1].adv
        numExtra = tournament.adv_path[roundNum-1].topscorers
        numTiebreak = numAdv - len(room.advanced)
        #await ctx.send(f"Please enter {numTiebreak} teams to tiebreak")
        advanced_teams = []
        while numTiebreak > 0:
            msg = f"Please choose a team to advance to the next round ({numTiebreak} more needed)\n"
            for i, team in enumerate(room.tieTeams):
                if team in advanced_teams:
                    continue
                msg += f"`{i+1})` {str(team.team)}\n"
            await ctx.send(msg)
            try:
                resp = await number_check(ctx)
            except asyncio.TimeoutError:
                await ctx.send("Timed out: please try this command again")
                return
            choice = int(resp.content)
            # basically a check to make sure you don't select duplicate teams
            valid_choices = [i+1 for i in range(len(room.tieTeams)) if room.tieTeams[i] not in advanced_teams]
            if choice not in valid_choices:
                await ctx.send(f"You didn't select a valid choice! {valid_choices} please try this command again")
                return
            numTiebreak -= 1
            advanced_teams.append(room.tieTeams[choice-1])
        msg = "`Advanced the following teams:`\n"
        room.advanced.extend([t.team for t in advanced_teams])
        for team in advanced_teams:
            msg += f"- {str(team.team)}\n"
            room.tieTeams.remove(team)
        if numExtra > 0:
            msg += f"`Added the following teams to {getNthPlace(numAdv+1)} place teams:`\n"
            for team in room.tieTeams:
                msg += f"- {str(team.team)}\n"
            room.extraTeams.extend(room.tieTeams)
        room.tieTeams = []
        await ctx.send(msg)

    @commands.command()
    async def lookup(self, ctx, *, query):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        results = []
        query = query.lower().strip()
        if parsing.checkFC(query):
            for team in tournament.teams:
                for player in team.players:
                    if player.fc == query:
                        results.append(team)
        elif query.isdigit():
            if len(tournament.teams) >= int(query):
                results.append(tournament.teams[int(query)-1])
            for team in tournament.teams:
                if team.seed == int(query):
                    results.append(team)
                if team.mkcID == int(query):
                    results.append(team)
                for player in team:
                    if player.mkcID == int(query):
                        results.append(team)
        for team in tournament.teams:
            if team.tag is not None and team.tag.lower() == query:
                results.append(team)
            for player in team.players:
                if player.username is not None and player.username.lower() == query:
                    results.append(team)
                if player.miiName is not None and player.miiName.lower() == query:
                    results.append(team)
        results = list(set(results))
        e = discord.Embed(title="Search Results")
        for team in results:
            teamid = tournament.teams.index(team) + 1
            e.add_field(name=f"ID {teamid}", value=team.teamDetails(), inline=False)
        if len(e.fields) > 0:
            await ctx.send(embed=e)
            
        

    @tasks.loop(seconds=30)
    async def update_progress_channels(self):
        for tournament in self.bot.tournaments.values():
            if tournament.progress_channel is None:
                continue
            channel = self.bot.get_channel(tournament.progress_channel)
            if channel is None:
                continue
            currRound = tournament.currentRound()
            if currRound is None:
                continue
            if currRound.numRooms() == 0:
                continue
            msgs = []
            currMsg = ""
            roundNum = tournament.currentRoundNumber()
            currMsg += f"**ROUND {roundNum} PROGRESS**\n"
            finishCount = 0
            for room in currRound.rooms:
                finished, status = room.getProgressStr()
                if finished is True:
                    finishCount += 1
                currMsg += status
                if len(currMsg) > 1500:
                    msgs.append(currMsg)
                    currMsg = ""
            currMsg += f"`{finishCount}/{len(currRound.rooms)} finished`"
            msgs.append(currMsg)
            discordMsgs = []
            invalidMsgs = []
            for msgid in currRound.progress_msgs:
                try:
                    msg = await channel.fetch_message(msgid)
                    discordMsgs.append(msg)
                except Exception as e:
                    invalidMsgs.append(msgid)
                    continue
            for msgid in invalidMsgs:
                currRound.progress_msgs.remove(msgid)
            try:
                for i, msg in enumerate(discordMsgs):
                    if len(msgs) > 0:
                        messageText = msgs.pop(0)
                        if msg.content == messageText:
                            continue
                        await msg.edit(content=messageText)
                    else:
                        await msg.delete()
                for messageText in msgs:
                    message = await channel.send(messageText)
                    currRound.progress_msgs.append(message.id)
            except Exception as e:
                pass

async def setup(bot):
    await bot.add_cog(TournamentManager(bot))

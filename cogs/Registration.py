import discord
from discord.ext import commands, tasks
#from Tournament import Tournament
from objects import Tournament
#import parsing
from algorithms import parsing
from common import yes_no_check, basic_check

class Registration(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.msg_queue = {}
        self._msgqueue_task = self.send_queued_messages.start()

    async def queue(self, ctx, msg):
        if ctx.channel.id not in self.msg_queue.keys():
            self.msg_queue[ctx.channel.id] = []
        self.msg_queue[ctx.channel.id].append(msg)

    @tasks.loop(seconds=2)
    async def send_queued_messages(self):
        for channelid in self.msg_queue.keys():
            channel = self.bot.get_channel(channelid)
            if channel is None:
                continue
            queue = self.msg_queue[channelid]
            if len(queue) > 0:
                sentmsgs = []
                sentmsg = ""
                for i in range(len(queue)-1, -1, -1):
                    sentmsg = queue.pop(i) + "\n" + sentmsg
                    if len(sentmsg) > 1500:
                        sentmsgs.append(sentmsg)
                        sentmsg = ""
                if len(sentmsg) > 0:
                    sentmsgs.append(sentmsg)
                for i in range(len(sentmsgs)-1, -1, -1):
                    await channel.send(sentmsgs[i])

    @commands.command(aliases=['open'])
    async def openRegistrations(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]

        tag = False
        miiName = False
        fc = False
        host = False
        
        if tournament.size > 1:
            tagQuestion = await ctx.send("Do you want to require tags for team registrations? (yes/no)")
            try:
                response = await yes_no_check(ctx)
            except asyncio.TimeoutError:
                await ctx.send("Timed out: Cancelled opening registrations")
                return
            if response.content.lower() == "yes":
                tag = True

        miiQuestion = await ctx.send("Do you want to require Mii Names for registrations? (yes/no)")
        try:
            response = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled opening registrations")
            return
        if response.content.lower() == "yes":
            miiName = True
            
        fcQuestion = await ctx.send("Do you want to require FCs for registrations? (yes/no)")
        try:
            response = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled opening registrations")
            return
        if response.content.lower() == "yes":
            fc = True

##        hostQuestion = await ctx.send("Do you want to enabled the `!ch` command for players to say if they can host? (yes/no)")
##        try:
##            response = await yes_no_check(ctx)
##        except asyncio.TimeoutError:
##            await ctx.send("Timed out: Cancelled opening registrations")
##            return
##        if response.content.lower() == "yes":
##            host = True
##        else:
##            host = False
            

        e = discord.Embed(title="Confirmation")
        settings = f"Tag required (team formats only): **{tag}**\nMii name required: **{miiName}**\nFC required: **{fc}**"
        e.add_field(name="Requested settings", value=settings)
        content = "Please confirm that you would like to open up registrations with the following settings (yes/no):"
        confirmEmbed = await ctx.send(content=content, embed=e)

        try:
            response = await yes_no_check(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Timed out: Cancelled opening registrations")
            return
        
        if response.content.lower() == "no":
            try:
                await confirmEmbed.delete()
                await ctx.message.delete()
            except Exception as e:
                pass
            return
        
        tournament.signups = True
        tournament.required_tag = tag
        tournament.required_miiName = miiName
        tournament.required_fc = fc
        tournament.can_channel = ctx.channel.id
        
        await ctx.send("Successfully opened Discord registrations for this tournament")

    @commands.command(aliases=['close'])
    async def closeRegistrations(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        tournament.signups = False
        await ctx.send("Closed registrations")
                
    @commands.command(aliases=['c'])
    #async def can(self, ctx, members: commands.Greedy[discord.Member]):
    async def can(self, ctx, *, args=""):
        await self.process_can(ctx, args, False)

    @commands.command(aliases=['ch'])
    async def canHost(self, ctx, *, args=""):
        await self.process_can(ctx, args, True)

    async def process_can(self, ctx, args, canHost):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if ctx.channel.id != tournament.can_channel:
            return
        if tournament.signups is False:
            await ctx.send("This tournament does not support Discord registrations")
            return
        size = tournament.size
        team = tournament.getRegisteredTeamFromDiscord(ctx.author)
        if team is not None:
            if canHost and tournament.required_host:
                for player in team:
                    if player.discordObj == ctx.author.id:
                        player.toggleHost()
                        await self.queue(ctx, f"{ctx.author.display_name} successfully changed host to {player.canHost}")
                        return
            reggedMsg = (f"{ctx.author.display_name} is already registered for the tournament `({str(team)})`")
            await self.queue(ctx, reggedMsg)
            return
        members, miiName, fc = await parsing.parseCanArgs(ctx, args)
        for member in members:
            team = tournament.getRegisteredTeamFromDiscord(member)
            if team is not None:
                reggedMsg = (f"{member.display_name} is already registered for the tournament `({str(team)})`")
                await self.queue(ctx, reggedMsg)
                return
        if len(members) == 0 and tournament.size > 1:
            await self.confirmForSquad(ctx, size, miiName, fc, canHost)
        else:
            await self.createSquad(ctx, size, members, miiName, fc, canHost)

    async def createSquad(self, ctx, size, members, miiName, fc, host):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if len(members) != (size - 1):
            await self.queue(ctx, f"{ctx.author.display_name} didn't tag the correct number of people for this format ({size-1}).")
            return
        team = tournament.getUnregisteredTeamFromDiscord(ctx.author)
        if team is not None:
            if host and tournament.required_host:
                for player in team:
                    if player.discordObj == ctx.author.id:
                        player.toggleHost()
                        await self.queue(ctx, f"{ctx.author.display_name} successfully changed host to {player.canHost}")
                        return
            reggedMsg = (f"{ctx.author.display_name} is already confirmed for a unregistered squad for this tournament `({str(team)})`")
            await self.queue(ctx, reggedMsg)
            return
        for member in members:
            team = tournament.getUnregisteredTeamFromDiscord(member)
            if team is not None:
                reggedMsg = (f"{member.display_name} is already confirmed for a unregistered squad for this tournament `({str(team)})`")
                await self.queue(ctx, reggedMsg)
                return
        tag=None
        if tournament.required_tag is True:
            tag = await self.getTag(ctx)
            if tag is None:
                return
        squad = tournament.createEmptyTeam(tag)
        captain = squad.addFromDiscord(ctx.author)
        detailsGot = await self.getPlayerDetails(ctx, captain, tag, miiName, fc, host)
        if detailsGot is False:
            return
        if tournament.size > 1:
            for member in members:
                squad.addFromDiscord(member)
            tournament.addUnregisteredSquad(squad)
            await self.queue(ctx, f"{ctx.author.display_name} has created a squad with {', '.join(member.display_name for member in members)}; "
                             + f"each player must type `!c` to join the queue `[1/{size}]`")
        else:
            tournament.registerTeam(squad)
            await self.queue(ctx, f"{ctx.author.display_name} has successfully registered for the tournament")

    async def confirmForSquad(self, ctx, size, miiName, fc, host):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        squad = tournament.getUnregisteredTeamFromDiscord(ctx.author)
        if squad is None:
            await self.queue(ctx, f"{ctx.author.display_name} is not currently in a team for this tournament; type `!c @partnerNames`")
            return
        tag = squad.tag
        player = tournament.getUnregisteredPlayerFromDiscord(ctx.author)
        if player.confirmed is True:
            if host and tournament.required_host:
                player.toggleHost()
                await self.queue(ctx, f"{ctx.author.display_name} successfully changed host to {player.canHost}")
                return
            await self.queue(ctx, f"{ctx.author.display_name} is already confirmed for this event; type !d to drop")
            return
        detailsGot = await self.getPlayerDetails(ctx, player, tag, miiName, fc, host)
        if detailsGot is False:
            return
        numConfirmed = squad.numConfirmed()
        await self.queue(ctx, f"{ctx.author.display_name} has confirmed for their squad [{numConfirmed}/{size}]")
        if numConfirmed == size:
            tournament.pending_teams.remove(squad)
            tournament.registerTeam(squad)
            regMsg = (f"`Squad successfully registered for the tournament "
                      + f"[{tournament.numTeams()} teams]`:\n")
            i = 1
            for player in squad:
                regMsg += f"`{i}.` {player.username}\n"
                i += 1
            await self.queue(ctx, regMsg)
            
    async def getTag(self, ctx):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        await self.queue(ctx, f"{ctx.author.mention} what is your team's tag?")
        try:
            msg = await basic_check(ctx)
        except asyncio.TimeoutError:
            await self.queue(ctx, f"{ctx.author.mention} timed out, try again")
            return None
        if len(msg.content) > 10:
            await self.queue(ctx, f"{ctx.author.mention} your tag is too long")
            return None
        teamWithTag = tournament.getTeamWithTag(msg.content)
        if teamWithTag is not None:
            await self.queue(ctx, f"{ctx.author.mention} that tag is taken by the following team: {str(teamWithTag)}")
            return None
        return str(msg.content)

    async def getPlayerDetails(self, ctx, player, tag, miiName, fc, host):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if tournament.required_miiName is True:
            if len(miiName) == 0:
                await self.queue(ctx, f"{ctx.author.mention} you didn't include your Mii Name/Ingame Name in your registration!")
                return False
            if len(miiName) > 10:
                await self.queue(ctx, f"{ctx.author.mention} your Mii Name/Ingame Name is above 10 characters, try again")
                return False
            if tag is not None:
                if tag not in miiName:
                    await self.queue(ctx, f"{ctx.author.mention} your team's tag is not in your name! Try typing !c again")
                    return False
            player.miiName = miiName
        if tournament.required_fc is True:
            if fc is None:
                await self.queue(ctx, f"{ctx.author.mention} you didn't include your FC in your registration!")
                return False
            playerWithFC = tournament.getPlayerFromFC(fc)
            if playerWithFC is not None:
                await self.queue(ctx, f"The FC {fc} is already in use by the following player: {str(playerWithFC)}")
                return False
            player.fc = fc
        if tournament.required_host is True:
            player.canHost = host
        player.confirmed = True
        return True

    async def getPlayerDetails_old(self, ctx, player, tag):
        tournament = ctx.bot.tournaments[ctx.guild.id]
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        
        #asking the player for their Mii Name, if needed
        if tournament.required_miiName is True:
            await self.queue(ctx, f"{ctx.author.mention} what is your in-game nickname/Mii Name for this tournament?")
            try:
                msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await self.queue(ctx, f"{ctx.author.mention} timed out, try again")
                return False
            if len(msg.content) > 10:
                await self.queue(ctx, f"{ctx.author.mention} your Mii Name is above 10 characters, try typing !c again")
                return False
            if tag is not None:
                if tag not in msg.content:
                    await self.queue(ctx, f"{ctx.author.mention} your team's tag is not in your name! Try typing !c again")
                    return False
            player.miiName = str(msg.content)
        #asking the player for their FC, if needed
        if tournament.required_fc is True:
            await self.queue(ctx, f"{ctx.author.mention} what is your FC? (format: 0000-0000-0000)")
            try:
                msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await self.queue(ctx, f"{ctx.author.mention} timed out, try again")
                return False
            if parsing.checkFC(msg.content) is False:
                await self.queue(ctx, f"{ctx.author.mention} your FC format is invalid, try typing !c again (format: 0000-0000-0000)")
                return False
            playerWithFC = tournament.getPlayerFromFC(msg.content)
            if playerWithFC is not None:
                await self.queue(ctx, f"The FC {msg.content} is already in use by the following player: {str(playerWithFC)}")
                return False
            player.fc = str(msg.content)
        if tournament.required_host is True:
            await self.queue(ctx, f"{ctx.author.mention} can you host? (yes/no)")
            def yes_no_check(m: discord.Message):
                if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
                    return False
                if m.content.lower() == "yes" or m.content.lower() == "no":
                    return True
            try:
                msg = await ctx.bot.wait_for('message', check=yes_no_check, timeout=60.0)
            except asyncio.TimeoutError:
                await self.queue(ctx, f"{ctx.author.mention} timed out, try again")
                return False
            if msg.content.lower() == "yes":
                player.canHost = True
        player.confirmed = True
        return True

    @commands.command(aliases=['d'])
    async def drop(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if ctx.channel.id != tournament.can_channel:
            return
        team = tournament.getUnregisteredTeamFromDiscord(ctx.author)
        if team is not None:
            tournament.pending_teams.remove(team)
            await self.queue(ctx, f"Removed {str(team)} from unregistered squads")
            return
        team = tournament.getRegisteredTeamFromDiscord(ctx.author)
        if team is not None:
            tournament.teams.remove(team)
            await self.queue(ctx, f"Removed {str(team)} from registered list")
        else:
            await self.queue(ctx, f"{ctx.author.display_name} is not registered for this event")

    @commands.command(aliases=['reg', 'squad', 'team'])
    async def registration(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if ctx.channel.id != tournament.can_channel:
            return
        team = tournament.getUnregisteredTeamFromDiscord(ctx.author)
        if team is None:
            team = tournament.getRegisteredTeamFromDiscord(ctx.author)
        if team is None:
            await ctx.send("You are not in a squad for this event")
            return
        numConfirmed = team.numConfirmed()
        numPlayers = team.numPlayers()
        if numConfirmed != numPlayers:
            teamDescription = f"{numConfirmed}/{numPlayers} confirmed\n"
        else:
            teamDescription = f"**Registered**\n"
        if team.tag is not None:
            teamDescription += f"Tag: {team.tag}"
        if tournament.size > 1:
            teamOrPlayer = "Team"
        else:
            teamOrPlayer = "Player"
        e = discord.Embed(title=teamOrPlayer, description=teamDescription)
        for player in team.players:
            if player.confirmed is False:
                playerDescription = "**✘ Unconfirmed**"
            else:
                playerDescription = "**✓ Confirmed**\n"
                if tournament.required_miiName is True:
                    playerDescription += f"Mii Name: {player.miiName}\n"
                if tournament.required_fc is True:
                    playerDescription += f"FC: {player.fc}\n"
                if player.canHost:
                    playerDescription += "**Can host**\n"
            e.add_field(name=player.username, value=playerDescription,inline=False)
        await ctx.send(embed=e)
                
    @commands.command()
    async def unregisteredTeams(self, ctx):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if len(tournament.pending_teams) == 0:
            await self.queue(ctx, "There are no pending teams for this tournament")
            return
        send = "`Unregistered Teams`\n"
        i = 1
        for team in tournament.pending_teams:
            send += f"`{i}.` {str(team)} `[{team.numConfirmed()}/{tournament.size}]`\n"
            if len(send) > 1500:
                await self.queue(send)
                send = ""
        if len(send) > 0:
            await self.queue(send)

async def setup(bot):
    await bot.add_cog(Registration(bot))

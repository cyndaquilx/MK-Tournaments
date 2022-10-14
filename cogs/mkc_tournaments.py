import discord
from discord.ext import commands
import aiohttp, asyncio
from common import has_organizer_role, yes_no_check
from objects import Team, Player

class mkc_tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['site'])
    async def addFromMKCTournaments(self, ctx, tid:int):
        if ctx.guild.id not in ctx.bot.tournaments:
            await ctx.send("no tournament started yet")
            return
        tournament = ctx.bot.tournaments[ctx.guild.id]
        if await has_organizer_role(ctx, tournament) is False:
            return
        tournament_info_url = f'https://mkc-tournaments.com/tournamentData/{tid}'
        connector=aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(tournament_info_url) as resp:
                if int(resp.status / 100) != 2:
                    await ctx.send("Tournament ID not found")
                    return
                tinfo = await resp.json()
                if tournament.size == 1 and int(tinfo["size"]) != 1:
                    print(tournament.size)
                    print(tinfo['size'])
                    await ctx.send("Event size on MKC does not correspond with the size of this tournament")
                    return
                e = discord.Embed(title="MKCentral Tournament")
                e.add_field(name="Tournament Name", value=tinfo['name'])
                await ctx.send(content="Would you like to add the players from this tournament? (yes/no)",
                               embed=e)
                try:
                    resp = await yes_no_check(ctx)
                except asyncio.TimeoutError:
                    await ctx.send("Timed out: Cancelled adding players")
                    return
                if resp.content.lower() == "no":
                    await ctx.send("Cancelled adding players")
                    return
                if tournament.size == 1:
                    players = parse_ffa(tinfo)
                    tournament.teams = []
                    tournament.addFFAPlayersFromList(players)
                else:
                    teams = parse_squads(tinfo)
                    tournament.teams = teams
                await ctx.send("Successfully imported players")

def parse_ffa(json):
    players = []
    for s in json['squads']:
        for player in s['players']:
            username = player['name']
            mii_name = player['mii_name']
            fc = player['switch_fc']
            can_host = player['can_host']
            registry_id = player['registry_id']
            discord_id = player['discord_id']
            country = player['country_code']
            p = Player(username=username, miiName=mii_name, fc=fc, canHost=can_host,
            mkcID=registry_id, discordTag=discord_id, country=country)
            players.append(p)
    return players
                
def parse_squads(json):
    teams = []
    for team in json['squads']:
        if not team['is_confirmed']:
            continue
        mkcID = team['id']
        tag = team['tag']
        players = []
        t = Team([], tag=tag, mkcID=mkcID)
        for player in team['players']:
            username = player['name']
            mii_name = player['mii_name']
            fc = player['switch_fc']
            can_host = player['can_host']
            registry_id = player['registry_id']
            discord_id = player['discord_id']
            country = player['country_code']
            p = Player(username=username, miiName=mii_name, fc=fc, canHost=can_host,
            mkcID=registry_id, discordTag=discord_id, country=country)
            t.addPlayer(p)
        teams.append(t)
    return teams
        
async def setup(bot):
    await bot.add_cog(mkc_tournaments(bot))
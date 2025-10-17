import discord
from discord.ext import commands
import aiohttp, asyncio
from common import has_organizer_role, yes_no_check
from objects import Team, Player, TOBot
import json
import msgspec
from dataclasses import dataclass

@dataclass
class MKCTournament:
    id: int
    name: str
    game: str
    mode: str
    series_id: int | None
    is_squad: bool
    registrations_open: bool
    date_start: int
    date_end: int
    use_series_description: bool
    series_stats_include: bool
    use_series_logo: bool
    url: str | None
    registration_deadline: int | None
    registration_cap: int | None
    teams_allowed: bool
    teams_only: bool
    team_members_only: bool
    min_squad_size: int | None
    max_squad_size: int | None
    squad_tag_required: bool
    squad_name_required: bool
    mii_name_required: bool
    host_status_required: bool
    checkins_enabled: bool
    checkins_open: bool
    min_players_checkin: int | None
    verification_required: bool
    verified_fc_required: bool
    is_viewable: bool
    is_public: bool
    is_deleted: bool
    show_on_profiles: bool
    require_single_fc: bool
    min_representatives: int | None
    bagger_clause_enabled: bool
    use_series_ruleset: bool
    organizer: str
    location: str | None
    description: str
    ruleset: str
    is_deleted: bool
    logo: str | None
    series_name: str | None = None
    series_url: str | None = None
    series_description: str | None = None
    series_ruleset: str | None = None

@dataclass
class MKCDiscord:
    discord_id: str
    username: str
    discriminator: str
    global_name: str | None
    avatar: str | None

@dataclass
class MKCFriendCode:
    id: int
    fc: str
    type: str
    player_id: int
    is_verified: bool
    is_primary: bool
    creation_date: int
    description: str | None = None
    is_active: bool = True

@dataclass
class MKCTournamentPlayerDetails:
    id: int
    player_id: int
    registration_id: int
    timestamp: int
    is_checked_in: bool
    is_approved: bool
    mii_name: str | None
    can_host: bool
    name: str
    country_code: str | None
    discord: MKCDiscord | None
    selected_fc_id: int | None
    friend_codes: list[MKCFriendCode]
    is_squad_captain: bool
    is_representative: bool
    is_invite: bool
    is_bagger_clause: bool

@dataclass
class MKCRosterBasic:
    team_id: int
    team_name: str
    team_tag: str
    team_color: int
    roster_id: int
    roster_name: str | None
    roster_tag: str | None

@dataclass
class MKCTournamentSquadDetails():
    id: int
    name: str | None
    tag: str | None
    color: int
    timestamp: int
    is_registered: bool
    is_approved: bool
    players: list[MKCTournamentPlayerDetails]
    rosters: list[MKCRosterBasic]

class MKCentral(commands.Cog):
    def __init__(self, bot: TOBot):
        self.bot = bot

    @commands.command(name='mkc')
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def add_teams_from_mkc(self, ctx: commands.Context[TOBot], tournament_id: int):
        assert ctx.guild is not None
        tournament = ctx.bot.tournaments.get(ctx.guild.id, None)
        if tournament is None:
            await ctx.send("There is no tournament ongoing in this server")
            return
        if await has_organizer_role(ctx, tournament) is False:
            return
        tournament_info_url = f'https://mkcentral.com/api/tournaments/{tournament_id}'
        connector=aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(tournament_info_url) as resp:
                if int(resp.status / 100) != 2:
                    await ctx.send("Tournament ID not found")
                    return
                tinfo = await resp.json()
                mkc_tournament = msgspec.convert(tinfo, MKCTournament, strict=False)
                if tournament.size == 1 and mkc_tournament.is_squad:
                    await ctx.send("Event size on MKC does not correspond with the size of this tournament")
                    return
                if tournament.size > 1:
                    if not mkc_tournament.is_squad:
                        await ctx.send("Event on MKC is not listed as a squad tournament")
                        return
                    if mkc_tournament.min_squad_size != tournament.size:
                        await ctx.send(f"Minimum squad size on MKC is {mkc_tournament.min_squad_size} but this tournament is of size {tournament.size}")
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
            tournament_registrations_url = f'https://mkcentral.com/api/tournaments/{tournament_id}/registrations?eligible_only=true'
            async with session.get(tournament_registrations_url) as resp:
                if int(resp.status / 100) != 2:
                    await ctx.send("Tournament ID not found")
                    return
                reg_info = await resp.json()
                registrations = msgspec.convert(reg_info, list[MKCTournamentSquadDetails], strict=False)
            teams: list[Team] = []
            for squad in registrations:
                team = Team([], tag=squad.tag, mkcID=squad.id)
                for mkc_player in squad.players:
                    if mkc_player.is_invite:
                        continue
                    friend_code: str | None = None
                    for fc in mkc_player.friend_codes:
                        if not mkc_player.selected_fc_id:
                            friend_code = fc.fc
                            break
                        if fc.id == mkc_player.selected_fc_id:
                            friend_code = fc.fc
                    discord_tag = None
                    discord_id = None
                    if mkc_player.discord:
                        discord_tag = mkc_player.discord.username
                        discord_id = int(mkc_player.discord.discord_id)
                    player = Player(mkc_player.name, mkc_player.mii_name, friend_code, discord_id,
                                    discord_tag, mkc_player.can_host, mkc_player.player_id,
                                    not mkc_player.is_invite, mkc_player.country_code)
                    team.addPlayer(player)
                teams.append(team)
            tournament.addTeams(teams)
            await ctx.send(f"Added {len(teams)} teams to the tournament")

async def setup(bot):
    await bot.add_cog(MKCentral(bot))
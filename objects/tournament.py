from algorithms import advanceAlg
from .round import Round
from .team import Team

class Tournament:
    def __init__(self, size:int, name, game, organizerRoles, hostRoles):
        self.size = size
        self.name = name
        self.game = game
        if game in ["MK7", "MKT"]:
            self.playersPerRoom = 8
        else:
            self.playersPerRoom = 12
        
        self.started = False
        self.finished = False
        self.teams = []
        self.pending_teams = []

        self.organizer_roles = organizerRoles
        self.host_roles = hostRoles
        self.print_format = None
        
        self.cap = None
        self.prioritizeHosts = False
        self.numRound1Rooms = 0

        self.adv_path = []
        self.rounds = []
        
        self.signups = False
        self.required_tag = False
        self.required_miiName = False
        self.required_fc = False
        if game == "MK7":
            self.required_host = False
        else:
            self.required_host = True
        
        self.can_channel = 0
        self.progress_channel = None
        self.results_channel = None

        self.tiebreakRule = False
        self.hostRule = True
        self.mostPtsRule = True
        self.registrationRule = True
        self.reseed = False
        
    def currentRound(self):
        if len(self.rounds) == 0:
            return None
        return self.rounds[-1]

    def currentRoundNumber(self):
        return len(self.rounds)

    def currentRoundRooms(self):
        roundNum = self.currentRoundNumber()
        currAdv = self.adv_path[roundNum-1]
        return currAdv.oldRooms

    def lastRound(self):
        if len(self.rounds) < 2:
            return None
        return self.rounds[-2]

    def getRoomNumber(self, num):
        currRound = self.currentRound()
        if currRound is None:
            return None
        if num > len(currRound.rooms):
            return None
        room = currRound.rooms[num-1]
        return room

    def getRoomTableNumber(self, num):
        currRound = self.currentRound()
        if currRound is None:
            return None
        if num > len(currRound.rooms):
            return None
        room = currRound.rooms[num-1]
        return room.table

    def getNthPlace(self, num=0):
        ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
        if num == 0:
            num = self.currentRoundNumber()
        return ordinal(self.adv_path[num-1].adv + 1)

    def getHostTeams(self):
        hosts = []
        for team in self.teams:
            if team.hasHost():
                hosts.append(team)
        return hosts

    def getNonHostTeams(self):
        teams = []
        for team in self.teams:
            if team.hasHost() is False:
                teams.append(team)
        return teams

    def numTeams(self):
        return len(self.teams)

    def addTeams(self, teams:list):
        self.teams.extend(teams)

    def addTeamsFromLists(self, teams:list):
        for players in teams:
            self.teams.append(Team(players))

    def addFFAPlayersFromList(self, players:list):
        for player in players:
            newTeam = Team([player])
            newTeam.mkcID = player.mkcID
            self.teams.append(newTeam)

    def createEmptyTeam(self, tag=None):
        return Team(players=[], tag=tag)

    def createPlayer(self, username=None, miiName=None, fc=None,
                 discordObj=None, discordTag=None, canHost=False,
                 mkcID=None, confirmed=False):
        return Player(username, miiName, fc, discordObj, discordTag,
                      canHost, mkcID, confirmed)

    def getUnregisteredTeamFromDiscord(self, member):
        for team in self.pending_teams:
            for player in team.players:
                #if player.discordObj == member:
                if player.discordObj == member.id:
                    return team
        return None

    def getUnregisteredPlayerFromDiscord(self, member):
        for team in self.pending_teams:
            for player in team.players:
                #if player.discordObj == member:
                if player.discordObj == member.id:
                    return player
        return None

    def getRegisteredTeamFromDiscord(self, member):
        for team in self.teams:
            for player in team:
                if player.discordObj == member.id:
                    return team
        return None

    def getPlayerFromFC(self, fc):
        for team in self.teams:
            for player in team:
                if player.fc == fc:
                    return player
        for team in self.pending_teams:
            for player in team:
                if player.fc == fc:
                    return player
        return None

    def getTeamWithTag(self, tag):
        for team in self.teams:
            if team.tag == tag:
                return team
        for team in self.pending_teams:
            if team.tag == tag:
                return team
        return None

    def registerTeam(self, team):
        self.teams.append(team)

    def registeredPlayers(self):
        players = []
        for team in self.teams:
            players.extend(team.players)
        return players

    def addUnregisteredSquad(self, squad):
        self.pending_teams.append(squad)

    def getR1Teams(self):
        if self.prioritizeHosts is False:
            return self.teams[0:self.cap]
        orderedTeams = self.getHostTeams() + self.getNonHostTeams()
        return orderedTeams[0:self.cap]

    def nextRound(self, races:int):
        if len(self.rounds) == 0:
            #teams = self.teams[0:self.cap]
            teams = self.getR1Teams()
        else:
            extra = self.adv_path[self.currentRoundNumber()-1].topscorers
            teams, scores = self.currentRound().getAdvanced(extra)
        newRound = Round(teams, self.currentRoundNumber()+1, races)
        self.rounds.append(newRound)
        return newRound

    def editPath(self, newPath, startingRound):
        currIndex = startingRound-1
        del self.adv_path[currIndex:]
        self.adv_path.extend(newPath)

    def calcAdvancements(self, num:int):
        return advanceAlg.nextRoomNumbers(num, self.size, self.playersPerRoom)

    def createCustomAdvancement(self, oldRooms:int, newRooms:int, adv:int, topscorers:int):
        return advanceAlg.Advancement(oldRooms, newRooms, adv, topscorers)

    def getPlacements(self):
        teams = []
        placements = []
        for i in range(len(self.rounds)-1, -1, -1):
            currRound = self.rounds[i]
            sortableTeams = []
            for room in currRound.rooms:
                sortableTeams.extend(room.table.getSortableTeams(self))
            sortableTeams = [s for s in sortableTeams if s.team not in teams]
            sortableTeams.sort(reverse=True)
            roundPlacements = []
            for team in sortableTeams:
                if len(roundPlacements) > 0:
                    if team.rank == sortableTeams[len(roundPlacements)-1].rank:
                        roundPlacements.append(roundPlacements[len(roundPlacements)-1])
                        continue
                roundPlacements.append(len(roundPlacements)+1)
            teams.extend([s.team for s in sortableTeams])
            placements.extend([p + len(placements) for p in roundPlacements])
        return teams, placements

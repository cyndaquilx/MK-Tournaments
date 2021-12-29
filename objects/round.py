from .room import Room

class Round:
    def __init__ (self, teams:list, num:int, races:int):
        self.teams = teams
        self.rooms = []
        self.progress_msgs = []
        self.randomized = False
        self.finished = False
        self.roundNum = num
        self.races = races

    def optimalAdvancements(self):
        if len(self.rooms) < 1:
            return None
        return

    def numRooms(self):
        return len(self.rooms)

    def numTeams(self):
        return len(self.teams)

    def getAdvanced(self, extraTeams):
        adv = []
        extra = []
        scores = []
        for room in self.rooms:
            adv.extend(room.advanced)
            for t in room.advanced:
                scores.append(0)
            extra.extend(room.extraTeams)
        extra.sort(reverse=True)
        for t in extra[0:extraTeams]:
            tscore = 0
            for player in t.team:
                tscore += t.playerScores[player]
            scores.append(tscore)
        adv.extend([t.team for t in extra[0:extraTeams]])
        return adv, scores

    def reseed(self, tournament):
        lastRound = tournament.lastRound()
        if lastRound is None:
            return
        sortableTeams = []
        for room in lastRound.rooms:
            sortableTeams.extend(room.table.getSortableTeams(tournament))
        sortableTeams = [s for s in sortableTeams if s.team in self.teams]
        sortableTeams.sort(reverse=True)
        for i, team in enumerate(sortableTeams):
            team.team.currSeed = i+1

    def resetSeeds(self):
        for team in self.teams:
            team.currSeed = team.seed

    def randomList(self, rngList:list):
        randomizedTeams = [self.teams[i] for i in rngList]
        randomizedTeams.sort(reverse=True)
        return randomizedTeams

    def orderHosts(self, numRooms:int, teams:list):
        hosts = []
        nonHosts = []
        for team in teams:
            if len(hosts) == numRooms:
                nonHosts.append(team)
                continue
            if team.hasHost():
                hosts.append(team)
            else:
                nonHosts.append(team)
        newTeams = hosts + nonHosts
        return newTeams

    def seedRooms(self, numRooms:int, rngList:list, tournament):
        size = tournament.size
        if tournament.reseed:
            self.reseed(tournament)
        else:
            self.resetSeeds()
        teams = self.randomList(rngList)
        roomLists = [[] for i in range(numRooms)]
        teams = self.orderHosts(numRooms, teams)
        #snake-style seeding
        i = 0
        inc = 1
        for team in teams:
            roomLists[i].append(team)
            if (i == 0 and inc == -1) or (i == numRooms-1 and inc == 1):
                inc *= -1
            else:
                i += inc
        rooms = []
        roomNum = 1
        for teamList in roomLists:
            rooms.append(Room(teamList, self.roundNum, roomNum, size))
            roomNum += 1
        self.rooms = rooms
        self.randomized = True
        return roomLists

    def replaceTeam(self, old, new):
        for i in range(len(self.teams)):
            if self.teams[i] == old:
                self.teams[i] = new
                break
        for room in self.rooms:
            for i in range(len(room.teams)):
                if room.teams[i] == old:
                    room.teams[i] = new
                    room.reset()
                    return room.roomNum
        return None

    def swapTeam(self, old, new):
        for i in range(len(self.teams)):
            if self.teams[i] == old:
                self.teams[i] = new
                continue
            if self.teams[i] == new:
                self.teams[i] = old
                continue
        for room in self.rooms:
            for i in range(len(room.teams)):
                if room.teams[i] == old:
                    room.teams[i] = new
                    room.reset()
                    continue
                if room.teams[i] == new:
                    room.teams[i] = old
                    room.reset()
                    continue
                    #return room.roomNum

    def getHostTeams(self):
        hosts = []
        for team in self.teams:
            if team.hasHost():
                hosts.append(team)
        return hosts

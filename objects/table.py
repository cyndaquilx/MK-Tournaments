class Table:
    def __init__(self, teams, roundNum, roomNum, size):
        self.teams = teams
        self.playerScores = {}
        self.roundNum = roundNum
        self.roomNum = roomNum
        self.size = size
        self.finished = False
        for team in teams:
            for player in team:
                self.playerScores[player] = None

    def update(self, players, scores):
        for i in range(len(players)):
            self.playerScores[players[i]] = scores[i]
        for team in self.teams:
            score = 0
            for player in team:
                if self.playerScores[player] is not None:
                    score += self.playerScores[player]
            if len(team.roundScores) < self.roundNum:
                team.roundScores.append(score)
            else:
                team.roundScores[self.roundNum-1] = score

    def getTeamScores(self, playerScores=None):
        if playerScores is None:
            playerScores = self.playerScores
        teamScores = []
        for team in self.teams:
            score = 0
            for player in team:
                if playerScores[player] is not None:
                    #return None
                    score += playerScores[player]
            teamScores.append(score)
        return teamScores
                

    def scoreboard(self, playerScores=None):
        if playerScores is None:
            playerScores = self.playerScores
        sb = f"#title ROUND {self.roundNum} ROOM {self.roomNum}.\n"
        i = 0
        if self.size == 1:
            sb += "FFA - Free for All\n"
        for team in self.teams:
            if self.size > 1:
                #A + 1 = B
                letter = chr(ord('A')+i)
                if team.tag is not None:
                    tag = team.tag
                    if tag.startswith("#"):
                        tag = "." + tag
                else:
                    tag = letter
                sb += f"\n{tag} - {letter}\n"
            for player in team:
                score = playerScores[player]
                if score is None:
                    score = 0
                if player.country is not None:
                    country = player.country
                else:
                    country = ""
                sb += f"{self.getTableName(player)} [{country}] {score}\n"
            i += 1
        return sb


    def getTableName(self, player):
        players = list(self.playerScores.keys())
        for index, playerObj in enumerate(players):
            if player == playerObj:
                duplicates = [p for p in players[0:index] if p.tableName() == playerObj.tableName()]
                name = playerObj.tableName()
                if len(duplicates) > 0:
                    name += f" ({len(duplicates)+1})"
                return name
        return None

    def getPlayerFromName(self, name):
        for player in self.playerScores.keys():
            condition = (self.getTableName(player).lower() == name.lower())
            if self.getTableName(player) == name:
                return player
        return None

    def getRank(self, team, playerScores=None):
        teamScores = self.getTeamScores(playerScores)
        teamScore = teamScores[self.teams.index(team)]
        rank = 1
        for score in teamScores:
            if score > teamScore:
                rank += 1
        return rank

    def getAdvanced(self, tournament, playerScores=None):
        if playerScores is None:
            playerScores = self.playerScores
        advancement = tournament.adv_path[self.roundNum-1]
        numAdvance = advancement.adv
        extra = advancement.topscorers
        tournamentTeams = tournament.teams
        tiebreakRule = tournament.tiebreakRule
        hostRule = tournament.hostRule
        mostPtsRule = tournament.mostPtsRule
        registrationRule = tournament.registrationRule
        
        #teamScores = self.getTeamScores()
        sortableTeams = []
        for team in self.teams:
            s = SortableTeam(team, tournamentTeams, playerScores, self.getRank(team, playerScores),
                             self.roundNum, hostRule, mostPtsRule, registrationRule)
            sortableTeams.append(s)
        #sortedTeams = [x for _, x in sorted(zip(teamScores, sortableTeams), reverse=True)]
        sortedTeams = sorted(sortableTeams, reverse=True)
        advancingTeams = [t.team for t in sortedTeams][0:numAdvance]
        tieTeams = []
        extraTeams = []
        if numAdvance > 0:
            tieRank = sortedTeams[numAdvance-1].rank
        else:
            tieRank = 0

        #gets all the teams with a rank of tieRank
        potentialTieTeams = [t for t in sortedTeams if t.rank == tieRank]
        if tiebreakRule is True:
                #print(len(potentialTieTeams))
            if tieRank - 1 + len(potentialTieTeams) > numAdvance:
                tieTeams = [t for t in potentialTieTeams]
                for team in tieTeams:
                    if team.team in advancingTeams:
                        advancingTeams.remove(team.team)
        #we keep extraTeams as a list of SortableTeam objects
        #as opposed to Team objects, since we want to compare
        #them all at the end of the round
        elif extra > 0:
            #print('a')
            extraTeams.extend([t for t in potentialTieTeams if t.team not in advancingTeams])
        if extra > 0:
            #print('b')
            extraTeams.extend([t for t in sortedTeams if t.rank == numAdvance+1])
        #print(len(advancingTeams))
        return advancingTeams, tieTeams, extraTeams

    def getSortableTeams(self, tournament):
        sortableTeams = []
        lastRoundTeams = []
        for team in self.teams:
            rank = self.getRank(team, self.playerScores)
            s = SortableTeam(team, tournament.teams, self.playerScores, rank, self.roundNum)
            sortableTeams.append(s)
        return sortableTeams
            
class SortableTeam:
    def __init__ (self, team, tournamentTeams, playerScores, rank, roundNum, hostRule=True, mostPtsRule=True, registrationRule=True):
        self.team = team
        self.tournamentTeams = tournamentTeams
        self.playerScores = playerScores
        self.rank = rank
        self.roundNum = roundNum
        self.hostRule = hostRule
        self.mostPtsRule = mostPtsRule
        self.registrationRule = registrationRule
        
    def __lt__ (self, other):
        #checking the room ranks of the 2 teams
        if self.rank < other.rank:
            #print(f"team {str(self.team)} has a higher rank ({self.rank}>{other.rank}) than {str(other.team)}")
            return False
        if other.rank < self.rank:
            #print(f"team {str(other.team)} has a higher rank ({other.rank}>{self.rank}) than {str(self.team)}")
            return True

        #next, comparing the total scores of the 2 teams
        sum1 = 0
        sum2 = 0
        for player in self.team:
            sum1 += self.playerScores[player]
        for player in other.team:
            sum2 += other.playerScores[player]
        if sum1 < sum2:
            return True
        if sum2 < sum1:
            return False

        #checking the host rule
        #(hosts get advancement priority)
        if self.hostRule is True:
            #print(self.team.hasHost())
            #print(other.team.hasHost())
            if self.team.hasHost() is False and other.team.hasHost() is True:
                #print(f"team {str(other.team)} wins tiebreak due to host rule")
                return True
            if self.team.hasHost() is True and other.team.hasHost() is False:
                #print(f"team {str(self.team)} wins tiebreak due to host rule")
                return False
        #checking most pts rule
        #(team with highest scoring player advances)
        if self.mostPtsRule is True:
            max1 = 0
            max2 = 0
            for player in self.team:
                if self.playerScores[player] > max1:
                    max1 = self.playerScores[player]
            for player in other.team:
                if other.playerScores[player] > max2:
                    max2 = other.playerScores[player]
            if max1 < max2:
                #print(f"team {str(other.team)} wins tiebreak due to indivs rule")
                return True
            if max2 < max1:
                #print(f"team {str(self.team)} wins tiebreak due to indivs rule")
                return False

        #checking new last round rule
        #(team that scored higher last round advances)
        if self.roundNum > 1:
            t1_last_round = self.team.roundScores[self.roundNum-2]
            t2_last_round = other.team.roundScores[self.roundNum-2]
            if t1_last_round < t2_last_round:
                return True
            if t1_last_round > t2_last_round:
                return False
            
        #checking registration rule
        #(team that registered first advances)
        if self.registrationRule is True:
            index1 = self.tournamentTeams.index(self.team)
            index2 = self.tournamentTeams.index(other.team)
            #print(index1)
            #print(index2)
            
            if index1 > index2:
                #print(f"team {str(other.team)} wins tiebreak due to registration rule ({index2} vs {index1})")
                return True
            if index2 < index1:
                #print(f"team {str(self.team)} wins tiebreak due to registration rule ({index1} vs {index2})")
                return False
        return False

    def __gt__ (self, other):
        return other.__lt__(self)

from .player import Player

class Team:
    def __init__ (self, players:list, tag=None, seed=None, mkcID=None, mkcHost=False):
        self.players = players
        self.tag = tag
        self.seed = seed
        self.currSeed = seed
        self.mkcID = mkcID
        self.mkcHost = mkcHost
        self.roundScores = []

    def __str__ (self):
        return ", ".join(str(player) for player in self.players)

    #less than
    def __lt__ (self, other):
        if self.currSeed is None and other.currSeed is not None:
            return True
        if self.currSeed is None or other.currSeed is None:
            return False
        return self.currSeed > other.currSeed

    #greater than
    def __gt__ (self, other):
        return other.__lt__(self)

    def __iter__ (self):
        self.index = 0
        return self

    def __next__ (self):
        if self.index >= len(self.players):
            raise StopIteration
        else:
            currPlayer = self.players[self.index]
            self.index += 1
            return currPlayer

    def hasHost(self):
        for player in self.players:
            if player.canHost:
                return True
        return False

    def getHost(self):
        if self.hasHost is False:
            return None
        for player in self.players:
            if player.canHost:
                return player

    def addMKCPlayer(self, player):
        if self.mkcHost is True:
            if len(self.players) == 0:
                player.canHost = True         
        self.players.append(player)

    def addPlayer(self, player):
        self.players.append(player)

    def addFromDiscord(self, account):
        player = Player(username = account.display_name,
                        discordObj = account.id, confirmed=False)
        self.addPlayer(player)
        return player

    def numPlayers(self):
        return len(self.players)

    def numConfirmed(self):
        num = 0
        for player in self.players:
            if player.confirmed:
                num += 1
        return num

    def tableName(self):
        return ", ".join([p.tableName() for p in self.players])

    def mkcStr(self):
        return " + ".join([p.mkcStr() for p in self.players])

    def teamDetails(self):
        details = ""
        if self.tag is not None:
            details += f"`Tag:` {self.tag}\n"
        if self.seed is not None:
            details += f"`Seed:` {self.seed}\n"
        if self.mkcID is not None:
            details += f"`MKC Squad:` {self.mkcID}\n"
        details += "`Players`\n"
        for player in self.players:
            player_details = ""
            if player.username is not None:
                player_details += f"\t`Username`: {player.username}\n"
            if player.miiName is not None:
                player_details += f"\t`Mii Name:` {player.miiName}\n"
            if player.fc is not None:
                player_details += f"\t`FC:` {player.fc}\n"
            if player.canHost:
                player_details += "\t`can host`\n"
            if player.mkcID is not None:
                player_details += f"\t`MKC ID:` {player.mkcID}\n"
            details += f"{player_details}\n"
        return details

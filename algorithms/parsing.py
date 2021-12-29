import re
from objects import Player, Team
from discord.ext import commands

def checkFC(text:str):
    fcFormat = re.compile(r'^\d{4}-\d{4}-\d{4}$')
    if fcFormat.match(text):
        return True
    return False

def parseLorenzi(data):
    #functions for parsing lorenzi table data
    def isGps(scores:str):
        gps = re.split("[|+]", scores)
        for gp in gps:
            if gp.strip().isdigit() == False:
                return False
    def sumGps(scores:str):
        gps = re.split("[|+]", scores)
        sum = 0
        for gp in gps:
            if gp == "":
                continue
            sum += int(gp.strip())
        return sum
    def removeExtra(line):
        splitLine = line.split()
        if line.startswith("#"):
            return False
        if line.strip() == "":
            return False
        if len(splitLine) == 1:
            return False
        scores = splitLine[len(splitLine)-1]
        if scores.isdigit() == False and isGps(scores) == False:
            return False
        else:
            return True
    lines = filter(removeExtra, data.split("\n"))
    names = []
    scores = []
    for line in lines:
        # removes country flag brackets and other unnecessary things
        line = line.strip()
        if line.endswith('```'):
            line = line[:-3]
        # this .split(" ") is actually necessary since it includes spaces
        # (if name has 2 spaces in a row for some reason, which i found
        #  during testing)
        newline = re.sub("[\[].*?[\]]", "", line).split(" ")
        names.append(" ".join(newline[0:len(newline)-1]).strip())
        #print(names[len(names)-1])
        gps = newline[len(newline)-1]
        scores.append(sumGps(gps))
    return names, scores

async def parseCanArgs(ctx, text):
    args = text.split()
    c = commands.MemberConverter()
    members = []
    name_args = []
    fc = None
    for arg in args:
        #this is what mentions in discord start with
        if arg.startswith('<@'):
            try:
                member = await c.convert(ctx, arg)
                members.append(member)
                continue
            except Exception as e:
                pass
            continue
        if checkFC(arg):
            if fc is None:
                fc = arg
            continue
        name_args.append(arg)
    name = " ".join(name_args)
    return members, name, fc
    

def parseMKB(size:int, text:str):
    lines = text.splitlines()
    def isMKBformat(line):
        mkbFormat = re.compile(r'[^)）]*\s?[（(]\d{4}-\d{4}-\d{4}[）)]')
        match = mkbFormat.search(line)
        if match:
            return True
        return False

    def getPlayers(line):
        mkbFormat = re.compile(r'[^)）]*\s?[（(]\d{4}-\d{4}-\d{4}[）)]')
        players = mkbFormat.findall(line)
        return players

    def isHost(player):
        hostFormat = re.compile(r'★進\s?[(（]\d{4}-\d{4}-\d{4}[)）]')
        match = hostFormat.search(player)
        if match:
            return True
        return False
        
    def getMiiName(player):
        toRemove = re.compile(r'(★進)?\s?[(（]\d{4}-\d{4}-\d{4}[)）]')
        name = toRemove.sub("", player).strip()
        return name

    def getFC(player):
        fcFormat = re.compile(r'\d{4}-\d{4}-\d{4}')
        fc = fcFormat.findall(player)[0]
        return fc
    teams = []
    for line in lines:
        #print(line)
        if isMKBformat(line) is False:
            continue
        playersInLine = getPlayers(line)
        if len(playersInLine) != size:
            continue
        team = []
        for player in playersInLine:
            name = getMiiName(player)
            fc = getFC(player)
            canHost = isHost(player)
            team.append(Player(miiName=name, fc=fc, canHost=canHost))
        teams.append(team)
    return teams


#can add other parsing functions here if needed

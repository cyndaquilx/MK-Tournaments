import math

class Advancement:
    def __init__ (self, oldRooms, newRooms, adv, topscorers):
        self.oldRooms = oldRooms
        self.newRooms = newRooms
        self.adv = adv
        self.topscorers = topscorers
        self.next = []

    def __str__ (self):
        string = f"{self.newRooms} | {self.adv} | {self.topscorers}"
        return string
        #return str(self.newRooms)

    def __eq__ (self, other):
        if self.oldRooms != other.oldRooms:
            return False
        if self.newRooms != other.newRooms:
            return False
        if self.adv != other.adv:
            return False
        if self.topscorers != other.topscorers:
            return False
        return True

def canAdvance(num:int, size:int, playersPerRoom=12):
    if num == 1:
        return True
    teams = playersPerRoom/size
    adv1 = math.ceil((teams) * 1 / 2)
    adv2 = math.floor((teams) * 1 / 2)

    num2 = float(num * adv1 / teams)
    if num2.is_integer() and canAdvance(int(num2), size, playersPerRoom):
        return True
    if adv2 != adv1:
        num2 = float(num * adv2 / teams)
        if num2.is_integer() and canAdvance(int(num2), size, playersPerRoom):
            return True
    return False

def isGoodNumber(num:int, size:int, playersPerRoom=12):
    teams = (playersPerRoom/size)
    adv = math.ceil(teams * 1 / 2)
    if size == 1:
        change = 2
    else:
        change = 1
    if canAdvance(num, size, playersPerRoom) is True:
        return True
    numMinus = num * (adv-change) / teams
    if numMinus.is_integer():
        if int(numMinus) == 1:
            return True
    if adv + 1 < teams:
        numPlus = num * (adv+change) / teams
        if numPlus.is_integer() and isGoodNumber(int(numPlus), size, playersPerRoom):
            return True
    return False
    

def goodWithHighScores(num:int, size:int, playersPerRoom=12):
    def getNext(num:int, size:int):
        adv = math.ceil((playersPerRoom/size) * 1 / 2)
        nextnum = num * adv / (12/size)
        if nextnum.is_integer():
            return int(nextnum)
        return False
    nn = getNext(num, size)
    if nn is not False:
        if getNext(nn, size) is not False:
            return True
    return False

def nextGoodRooms(num:int, size:int, playersPerRoom=12):
    advancements = []
    if num == 1:
        return advancements
    teams = playersPerRoom/size
    adv = math.ceil(teams * 1 / 2)
    change = 1
    if size == 1:
        change += 1
    numNext = num * adv / teams
    if numNext.is_integer():
        if isGoodNumber(int(numNext), size, playersPerRoom):
            #return int(numNext)
            advancements.append(Advancement(num, int(numNext), adv, 0))
    if adv + change < teams:
        numNext = num * (adv+change) / teams
        if numNext.is_integer() and isGoodNumber(int(numNext), size, playersPerRoom):
            advancements.append(Advancement(num, int(numNext), adv+change, 0))
    numNext = num * (adv-change) / teams
    if numNext.is_integer() and isGoodNumber(int(numNext), size, playersPerRoom):
        advancements.append(Advancement(num, int(numNext), adv-change, 0))
    return advancements

def nextDecentRooms(num:int, size:int, playersPerRoom=12):
    advancements = []
    teams = playersPerRoom/size
    adv = math.ceil(teams * 1 / 2)
    change = 1
    if size == 1:
        change += 1
        
    def calcAdvances(numNext:int, adv:int):
        if(isGoodNumber(numNext, size, playersPerRoom)):
            return
        roomsNext = nextGoodRooms(int(numNext), size, playersPerRoom)
        if len(roomsNext) > 0:
            advancements.append(Advancement(num, int(numNext), adv, 0))
     
    numNext = num * adv / teams
    if numNext.is_integer():
        calcAdvances(numNext, adv)
    numNext = num * (adv+change) / teams
    if numNext.is_integer():
        calcAdvances(numNext, adv)
    numNext = num * (adv-change) / teams
    if numNext.is_integer():
        calcAdvances(numNext, adv)
    return advancements
    
def nextAnyRooms(num:int, size:int, playersPerRoom=12):
    advancements = []
    teams = playersPerRoom/size
    adv = math.ceil(teams * 1 / 2)
    change = 1
    if size == 1:
        change += 1

    numNext = num * adv / teams
    if numNext.is_integer():
        advancements.append(Advancement(num, int(numNext), adv, 0))
    if adv + change < teams:
        numNext = num * (adv+change) / teams
        if numNext.is_integer():
            advancements.append(Advancement(num, int(numNext), adv+change, 0))
    if adv - change > 0:
        numNext = num * (adv - change) / teams
        if numNext.is_integer():
            advancements.append(Advancement(num, int(numNext), adv-change, 0))
    return advancements

def nextHighScoreDecentRooms(num:int, size:int, playersPerRoom=12):
    advancements = []
    teamsPerRoom = playersPerRoom/size
    adv = math.ceil(teamsPerRoom * 1 / 2)
    change = 1
    if size == 1:
        change += 1
    if adv - change > 0:
        minTeams = (adv - change) * num
    else:
        minTeams = adv * num
    if adv + change < teamsPerRoom:
        maxTeams = (adv + change) * num
    else:
        maxTeams = adv * num

    #room = math.ceil(minTeams / teams)
    teams = math.ceil(minTeams / teamsPerRoom) * teamsPerRoom
    while teams <= maxTeams:
        rooms = int(teams/teamsPerRoom)
        numAdvancing = int(teams/num)
        numExtra = int(teams % num)
        #if len(nextDecentRooms(rooms, size)) > 0 or len(nextGoodRooms(rooms, size)) > 0:
        if (len(nextDecentRooms(rooms, size, playersPerRoom)) > 0
            or isGoodNumber(rooms, size, playersPerRoom)):
            advancements.append(Advancement(num, rooms, numAdvancing, numExtra))
        teams += teamsPerRoom
    return advancements
            
def nextHighScoreAnyRoom(num:int, size:int, playersPerRoom=12):
    advancements = []
    teamsPerRoom = playersPerRoom/size
    change = 1
    if size == 1:
        change += 1
    rooms = math.ceil(1 / 2 * num)
    numAdvancing = int(rooms * teamsPerRoom / num)
    numExtra = int((rooms * teamsPerRoom) % num)
    advancements.append(Advancement(num, rooms, numAdvancing, numExtra))
    return advancements

def nextRoomNumbers(num:int, size:int, playersPerRoom=12):
    advancements = []
    if num == 1:
        return advancements
    
    advancements.extend(nextGoodRooms(num, size, playersPerRoom))
    temp = nextDecentRooms(num, size, playersPerRoom)
    advancements.extend([x for x in temp if x not in advancements])
    temp = nextAnyRooms(num, size, playersPerRoom)
    advancements.extend([x for x in temp if x not in advancements])
    if len(advancements) > 2:
        return advancements
    temp = nextHighScoreDecentRooms(num, size, playersPerRoom)
    advancements.extend([x for x in temp if x not in advancements])
    if len(advancements) > 2:
        return advancements
    temp = nextHighScoreAnyRoom(num, size, playersPerRoom)
    advancements.extend([x for x in temp if x not in advancements])
    return advancements
        

def printAllGoodNumbers():
    for size in [1, 2, 3, 4]:
        goodNums = []
        for i in range(1, 101):
            if isGoodNumber(i, size):
                goodNums.append(i)
        print(f"{size}: {goodNums}")

def printAllGoodNumbersPlus():
    for size in [1, 2, 3, 4]:
        goodNums = []
        for i in range(1, 101):
            if isGoodNumber(i, size):
                goodNums.append(i)
            elif goodWithHighScores(i, size):
                goodNums.append(i)
        print(f"{size}: {goodNums}")
    
def getAllNextRooms(size, num):
    print(f"All possible advancements (2-{num} rooms) for {size}v{size}")
    for i in range(2, num+1):
        nextNum = nextRoomNumbers(i, size)
        #if i == nextNum:
        #    print(i)
        if nextNum is not None:
            #print(f"{i}: {[str(adv) for adv in nextNum]}")
            print(f"{i}: {[adv.newRooms for adv in nextNum]}")
    #print(nextRoomNumber(9, size))

def pathFind():
    size = int(input("size?\n"))
    rooms = int(input("# of rooms?\n"))
    path = []
    path.append(rooms)
    while rooms > 1:
        nxt = nextRoomNumbers(rooms, size)
        print(f"Here are your options for advancements for {rooms} rooms:")
        i = 0
        for adv in nxt:
            print(f"{i+1}) Top {adv.adv} + {adv.topscorers} -> {adv.newRooms}")
            i+=1
        print(f"{i+1}) Custom")
        index = int(input("What option do you choose?\n"))
        if index > 0 and index <= len(nxt):
            rooms = nxt[index-1].newRooms
        else:
            rooms = int(input("How many rooms do you want next round?\n"))
        path.append(rooms)
    print(f"Tournament progression: {path}")
    

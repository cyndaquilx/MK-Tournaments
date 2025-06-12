from discord.ext import commands
from objects import TOBot, Room, Player, Team

#all lower case
print_formats = ['mkc', 'mkb', 'summit', 'mkw', 'none']

async def printSummit(ctx, rooms: list[Room], roomnum=0):
    def playerStr(player: Player):
        if player.canHost:
            host = "★進"
        else:
            host = ""
        return(f"{player.miiName}{host} ({player.fc})")
    def teamStr(team: Team):
        return(" ".join([playerStr(p) for p in team.players]))
    def roomStr(room: Room):
        msg = f"### {room.roomNum}組\n"
        hostTeam = room.teams[0]
        hostPlayer = hostTeam.getHost()
        if hostPlayer is not None:
            msg += f"**{playerStr(hostPlayer)}** "
        otherPlayers = []
        for player in hostTeam.players:
            if player == hostPlayer:
                continue
            otherPlayers.append(player)
        msg += " ".join([playerStr(p) for p in otherPlayers])
        msg += "  \n"
        for i in range(1, len(room.teams)):
            msg += f"{teamStr(room.teams[i])}  \n"
        msg += "\n"
        return msg
    if roomnum > 0:
        await ctx.send("```" + roomStr(rooms[roomnum-1]) + "```")
        return
    send = "```"
    for i in range(len(rooms)):
        room_str = roomStr(rooms[i])
        if len(send) + len(room_str) > 1500:
            send += "```"
            await ctx.send(send)
            send = "```"
        send += room_str
    if len(send) > 3:
        send += "```"
        await ctx.send(send)

async def printMKC(ctx: commands.Context[TOBot], rooms: list[Room], roomnum=0):
    def playerStr(player: Player):
        return(f"[{player.username}](https://mkcentral.com/registry/players/profile?id={player.mkcID}) | {player.miiName} ({player.fc})")
    def teamStr(team: Team):
        return " + ".join([playerStr(p) for p in team.players]) + "  "
    def roomStr(room: Room):
        msg = f"### Room {room.roomNum}\n"
        hostTeam = room.teams[0]
        hostPlayer = hostTeam.getHost()
        if hostPlayer is not None:
            msg += f"**{playerStr(hostPlayer)}**"
        otherPlayers: list[Player] = []
        for player in hostTeam.players:
            if player == hostPlayer:
                continue
            otherPlayers.append(player)
        if len(otherPlayers):
            msg += " + ".join([playerStr(p) for p in otherPlayers])
        msg += "  \n"
        for i in range(1, len(room.teams)):
            msg += f"{teamStr(room.teams[i])}\n"
        msg += "\n"
        return msg
    
    if roomnum > 0:
        await ctx.send("```" + roomStr(rooms[roomnum-1]) + "```")
        return
    send = "```"
    for i in range(len(rooms)):
        room_str = roomStr(rooms[i])
        for line in room_str.splitlines():
            if len(send) + len(line) > 1500:
                send += "```"
                await ctx.send(send)
                send = "```"
            send += f"{line}\n"
    if len(send) > 0:
        send += "```"
        await ctx.send(send)

async def printMKW(ctx, rooms, roomnum=0):
    def playerStr(player):
        return(f"{player.tableName()} ({player.fc})")
    def teamStr(team):
        return(" ".join([playerStr(p) for p in team.players]))
    def roomStr(room):
        msg = f"**Room {room.roomNum}**\n"
        hostTeam = room.teams[0]
        hostPlayer = hostTeam.getHost()
        if hostPlayer is not None:
            msg += f"**{playerStr(hostPlayer)}** "
        otherPlayers = []
        for player in hostTeam.players:
            if player == hostPlayer:
                continue
            otherPlayers.append(player)
        msg += " ".join([playerStr(p) for p in otherPlayers])
        msg += "\n"
        for i in range(1, len(room.teams)):
            msg += f"{teamStr(room.teams[i])}\n"
        msg += "-\n"
        return msg
    if roomnum > 0:
        await ctx.send("```" + roomStr(rooms[roomnum-1]) + "```")
        return
    send = "```"
    for i in range(len(rooms)):
        send += roomStr(rooms[i])
        if len(send) > 1500:
            send += "```"
            await ctx.send(send)
            send = "```"
    if len(send) > 3:
        send += "```"
        await ctx.send(send)

async def printDefault(ctx, rooms, roomnum=0):
    if roomnum > 0:
        await ctx.send(str(rooms[roomnum-1]))
        return
    send = ""
    for i in range(len(rooms)):
        send += str(rooms[i])
        if len(send) > 1500:
            await ctx.send(send)
            send = ""
    if len(send) > 0:
        await ctx.send(send)

async def printRooms(ctx, print_format, rooms, roomNum):
    if print_format == "mkc":
        await printMKC(ctx, rooms, roomNum)
    elif print_format == "summit":
        await printSummit(ctx, rooms, roomNum)
    elif print_format == "mkw":
        await printMKW(ctx, rooms, roomNum)
    else:
        await printDefault(ctx, rooms, roomNum)

#all lower case
print_formats = ['mkc', 'mkb', 'summit', 'none']

async def printSummit(ctx, rooms, roomnum=0):
    def playerStr(player):
        if player.canHost:
            host = "★進"
        else:
            host = ""
        return(f"{player.miiName}{host} ({player.fc})")
    def teamStr(team):
        return(" ".join([playerStr(p) for p in team.players]))
    def roomStr(room):
        msg = f"[b]{room.roomNum}組[/b]\n"
        hostTeam = room.teams[0]
        hostPlayer = hostTeam.getHost()
        if hostPlayer is not None:
            msg += f"[B]{playerStr(hostPlayer)}[/B] "
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

async def printMKC(ctx, rooms, roomnum=0):
    if roomnum > 0:
        await ctx.send("```" + rooms[roomnum-1].mkcStr() + "```")
        return
    send = "```"
    for i in range(len(rooms)):
        send += rooms[i].mkcStr()
        if len(send) > 1500:
            send += "```"
            await ctx.send(send)
            send = "```"
    if len(send) > 0:
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
    else:
        await printDefault(ctx, rooms, roomNum)

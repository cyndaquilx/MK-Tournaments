#returns 1st, 2nd, 3rd, etc.
def getNthPlace(num=1):
    ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
    return ordinal(num)        

def get_expected_points(game: str, numPlayers:int, races:int):
    pts = {
        "mk8": {
            2: 4,
            3: 7,
            4: 11,
            5: 16,
            6: 22,
            7: 31,
            8: 39,
            9: 48,
            10: 58,
            11: 69,
            12: 82
        },
        "mkw": {
            2: 22,
            3: 25,
            4: 29,
            5: 32,
            6: 35,
            7: 41,
            8: 47,
            9: 50,
            10: 61,
            11: 66,
            12: 73
        },
        "mkworld": {
            2: 3,
            3: 7,
            4: 11,
            5: 16,
            6: 22,
            7: 29,
            8: 37,
            9: 46,
            10: 56,
            11: 67,
            12: 82,
            13: 84,
            14: 87,
            15: 90,
            16: 94,
            17: 98,
            18: 103,
            19: 108,
            20: 114,
            21: 120,
            22: 127,
            23: 135,
            24: 144,
        }
    }
    if game.lower() == "mkw":
        return int(pts['mkw'][numPlayers] * races)
    elif game.lower() == "mkworld":
        return int(pts['mkworld'][numPlayers] * races)
    return int(pts['mk8'][numPlayers] * races)

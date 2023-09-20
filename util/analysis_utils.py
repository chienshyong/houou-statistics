import math
import re
from collections import Counter

# Analysis tools from https://github.com/Euophrys/phoenix-logs/tree/develop
# Log format https://github.com/ApplySci/tenhou-log#log-format
# Tiles number from 0 to 135, going from souzu, pinzu, manzu, wind and dragon. 16 : 5s0, 52 : 5p0, 88 : 5m0 are the akadora (Applysci notation)
# DEFG = Discard by player 0123 respectively, TSUV = Tsumo by player 0123 respectively, m = meld, N = call
# Melds are encoded, just call print(tenhou_decoder.Meld.decode(47178)) to view it, and getTilesFromCall() for analysis

tile_dict = {0: '1s0', 1: '1s1', 2: '1s2', 3: '1s3', 4: '2s0', 5: '2s1', 6: '2s2', 7: '2s3', 8: '3s0', 9: '3s1', 10: '3s2', 11: '3s3', 12: '4s0', 13: '4s1', 14: '4s2', 15: '4s3', 16: '5s0',
        17: '5s1', 18: '5s2', 19: '5s3', 20: '6s0', 21: '6s1', 22: '6s2', 23: '6s3', 24: '7s0', 25: '7s1', 26: '7s2', 27: '7s3', 28: '8s0', 29: '8s1', 30: '8s2', 31: '8s3', 32: '9s0',
        33: '9s1', 34: '9s2', 35: '9s3', 36: '1p0', 37: '1p1', 38: '1p2', 39: '1p3', 40: '2p0', 41: '2p1', 42: '2p2', 43: '2p3', 44: '3p0', 45: '3p1', 46: '3p2', 47: '3p3', 48: '4p0',
        49: '4p1', 50: '4p2', 51: '4p3', 52: '5p0', 53: '5p1', 54: '5p2', 55: '5p3', 56: '6p0', 57: '6p1', 58: '6p2', 59: '6p3', 60: '7p0', 61: '7p1', 62: '7p2', 63: '7p3', 64: '8p0',
        65: '8p1', 66: '8p2', 67: '8p3', 68: '9p0', 69: '9p1', 70: '9p2', 71: '9p3', 72: '1m0', 73: '1m1', 74: '1m2', 75: '1m3', 76: '2m0', 77: '2m1', 78: '2m2', 79: '2m3', 80: '3m0',
        81: '3m1', 82: '3m2', 83: '3m3', 84: '4m0', 85: '4m1', 86: '4m2', 87: '4m3', 88: '5m0', 89: '5m1', 90: '5m2', 91: '5m3', 92: '6m0', 93: '6m1', 94: '6m2', 95: '6m3', 96: '7m0',
        97: '7m1', 98: '7m2', 99: '7m3', 100: '8m0', 101: '8m1', 102: '8m2', 103: '8m3', 104: '9m0', 105: '9m1', 106: '9m2', 107: '9m3', 108: 'ew0', 109: 'ew1', 110: 'ew2', 111: 'ew3',
        112: 'sw0', 113: 'sw1', 114: 'sw2', 115: 'sw3', 116: 'ww0', 117: 'ww1', 118: 'ww2', 119: 'ww3', 120: 'nw0', 121: 'nw1', 122: 'nw2', 123: 'nw3', 124: 'wd0', 125: 'wd1', 126: 'wd2',
        127: 'wd3', 128: 'gd0', 129: 'gd1', 130: 'gd2', 131: 'gd3', 132: 'rd0', 133: 'rd1', 134: 'rd2'}

# For analysis use amber notation. 1-9 souzu, 11-19 pinzu, 21-29 manzu, 31-34 winds, 35-37 dragons
# Hand format: Counter({16: 2, 17: 1, 14: 1, 32: 1, 19: 1, 18: 1, 33: 1, 34: 1, 15: 1, 11: 0, 37: 0, 24: 0, 8: 0, 6: 0, 2: 0, 27: 0, 21: 0, 29: 0, 36: 0})

tenhou_tile_to_array_index_lookup = [1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,9,9,9,9,
    11,11,11,11,12,12,12,12,13,13,13,13,14,14,14,14,15,15,15,15,16,16,16,16,17,17,17,17,18,18,18,18,19,19,19,19,
    21,21,21,21,22,22,22,22,23,23,23,23,24,24,24,24,25,25,25,25,26,26,26,26,27,27,27,27,28,28,28,28,29,29,29,29,
    31,31,31,31,32,32,32,32,33,33,33,33,34,34,34,34,35,35,35,35,36,36,36,36,37,37,37,37
]

discards = ['D', 'E', 'F', 'G']
draws = ['T', 'U', 'V', 'W']
suit_characters = ['s', 'p', 'm', 'z']
yaku_names = ["Tsumo", "Riichi", "Ippatsu", "Chankan", "Rinshan", "Haitei", "Houtei", "Pinfu", "Tanyao", "Iipeikou",
    "Yakuhai Wind", "Yakuhai Wind", "Yakuhai Wind", "Yakuhai Wind", "Yakuhai Wind", "Yakuhai Wind", "Yakuhai Wind", "Yakuhai Wind",
    "Yakuhai Dragon", "Yakuhai Dragon", "Yakuhai Dragon", "Double Riichi", "Chiitoitsu", "Chanta", "Itsu", "Doujun", "Doukou",
    "Sankantsu", "Toitoi", "Sanankou", "Shousangen", "Honroutou", "Ryanpeikou", "Junchan", "Honitsu", "Chinitsu",
    "Renhou", "Tenhou", "Chihou", "Daisangen", "Suuankou", "Suuankou", "Tsuuiisou", "Ryuuiisou", "Chinroutou", "Chuuren", "Chuuren",
    "Kokushi", "Kokushi", "Daisuushi", "Shousuushi", "Suukantsu", "Dora", "Uradora", "Akadora"
]

def convertTile(tile):
    return tenhou_tile_to_array_index_lookup[int(tile)]

def convertHand(hand):
    return Counter(hand)

def convertHandToTenhouString(hand):
    handString = ""
    valuesInSuit = ""

    for suit in range(4):
        for i in range(suit * 10 + 1, suit * 10 + 10):
            if i > 37: continue
            value = i % 10

            if value == 5 and hand[i - 5] > 0:
                for j in range(hand[i - 5]):
                    valuesInSuit += 0

            for j in range(hand[i]):
                valuesInSuit += str(value)

        if valuesInSuit != "":
            handString += valuesInSuit + suit_characters[suit]
            valuesInSuit = ""

    return handString

def convertHai(hai):
    converted = list(map(convertTile, hai.split(',')))
    return convertHand(converted)

def getTilesFromCall(call):
    meldInt = int(call)
    meldBinary = format(meldInt, "016b")

    if meldBinary[-3] == '1':
        # Chii
        tile = meldBinary[0:6]
        tile = int(tile, 2)
        order = tile % 3
        tile = tile // 3
        tile = 9 * (tile // 7) + (tile % 7)
        tile = convertTile(tile * 4)

        if order == 0:
            return [tile, tile + 1, tile + 2]
        
        if order == 1:
            return [tile + 1, tile, tile + 2]

        return [tile + 2, tile, tile + 1]
    
    elif meldBinary[-4] == '1':
        # Pon
        tile = meldBinary[0:7]
        tile = int(tile, 2)
        tile = tile // 3
        tile = convertTile(tile * 4)

        return [tile, tile, tile]
    
    elif meldBinary[-5] == '1':
        # Added kan
        tile = meldBinary[0:7]
        tile = int(tile, 2)
        tile = tile // 3
        tile = convertTile(tile * 4)

        return [tile]
    
    elif meldBinary[-6] == '1':
        # Nuki
        return [34]
    
    else:
        # Kan
        tile = meldBinary[0:8]
        tile = int(tile, 2)
        tile = tile // 4
        tile = convertTile(tile * 4)
        return [tile, tile, tile, tile]

def GetWhoTileWasCalledFrom(call):
    meldInt = int(call.attrib["m"])
    meldBinary = format(meldInt, "016b")
    return int(meldBinary[-2:], 2)

round_names = [
    "East 1", "East 2", "East 3", "East 4",
    "South 1", "South 2", "South 3", "South 4",
    "West 1", "West 2", "West 3", "West 4"
]

def GetRoundName(init):
    seed = init.attrib["seed"].split(",")
    return "%s-%s" % (round_names[int(seed[0])], seed[1])

def GetRoundNameWithoutRepeats(init):
    seed = init.attrib["seed"].split(",")
    return round_names[int(seed[0])]

seats_by_oya = [
    [ "East", "South", "West", "North" ],
    [ "North", "East", "South", "West" ],
    [ "West", "North", "East", "South" ],
    [ "South", "West", "North", "East" ]
]

def CheckSeat(who, oya):
    return seats_by_oya[int(oya)][int(who)]

def GetPlacements(ten, starting_oya):
    points = list(map(int, ten.split(",")))
    # For tiebreaking
    points[0] -= (4 - starting_oya) % 4
    points[1] -= (5 - starting_oya) % 4
    points[2] -= (6 - starting_oya) % 4
    points[3] -= (7 - starting_oya) % 4
    ordered_points = points.copy()
    ordered_points.sort(reverse=True)

    return [
        ordered_points.index(points[0]),
        ordered_points.index(points[1]),
        ordered_points.index(points[2]),
        ordered_points.index(points[3])
    ]

def GetNextRealTag(element):
    next_element = element.getnext()

    while next_element is not None and (next_element.tag == "UN" or next_element.tag == "BYE"):
        next_element = next_element.getnext()
    
    return next_element

def GetPreviousRealTag(element):
    next_element = element.getprevious()

    while next_element is not None and (next_element.tag == "UN" or next_element.tag == "BYE"):
        next_element = next_element.getprevious()
    
    return next_element
    
def CheckIfWinIsClosed(agari):
    if "m" not in agari.attrib:
        return True

    calls = agari.attrib["m"].split(",")

    for call in calls:
        meldInt = int(call)
        meldBinary = format(meldInt, "016b")
        last_nums = meldBinary[-2:]

        if int(last_nums, 2) != 0:
            return False
    
    return True

def CheckIfWinWasRiichi(agari):
    if "yaku" in agari.attrib:
        yaku = agari.attrib["yaku"].split(",")[0::2]
        if "1" in yaku or "21" in yaku:
            return True
        else:
            return False
    
    winner = agari.attrib["who"]

    previous = agari.getprevious()

    while previous is not None:
        if previous.tag == "INIT":
            return False
        
        if previous.tag == "REACH" and previous.attrib["who"] == winner:
            return True
        
        previous = previous.getprevious()
    
    return False

def CheckIfWinWasDealer(agari):
    winner = agari.attrib["who"]
    previous = agari.getprevious()

    while previous is not None:
        if previous.tag == "INIT":
            return previous.attrib["oya"] == winner
        previous = previous.getprevious()
    
    return False # ???

def CheckDoubleRon(element):
    next_element = GetNextRealTag(element)

    if next_element is not None and next_element.tag == "AGARI":
        return True
    
    return False

def GetStartingHands(init, players = 4):
    hands = []
    for i in range(players):
        hands.append(convertHai(init.attrib["hai%d" % i]))
    return hands

dora_indication = [
     6, 2, 3, 4, 5, 6, 7, 8, 9, 1,
    16,12,13,14,15,16,17,18,19,11,
    26,22,23,24,25,26,27,28,29,21,
    30,32,33,34,31,36,37,35
]

def GetDora(indicator):
    return dora_indication[indicator]

# Convert amber notation hand into readable form
def parseAmberNotation(hand):
    res = ""
    for i in range(0,10):
        res += str(i) * hand[i]
    if len(res) > 0:
        res += 's '

    for i in range(11,20):
        res += str(i%10) * hand[i]
    if len(res) > 0:
        if res[-1].isdigit():
            res += 'p '

    for i in range(21,30):
        res += str(i%10) * hand[i]
    if len(res) > 0:
        if res[-1].isdigit():
            res += 'm '

    honor_map = ['E', 'S', 'W', 'N', 'Wh', 'G', 'R']
    for i in range(31,38):
        res += honor_map[i%10 - 1] * hand[i]

    return res

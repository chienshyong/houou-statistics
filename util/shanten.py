# Hand shanten calculator.
# Use amber notation: myhand = Counter({1:1, 2:1, 3:1, 5:1, 6:1, 7:1, 12:1, 13:2, 17:2, 21:1, 22:1}). calls = [[23,24,25],[33,33,33]]

hand = []
completeSets = 0
pair = 0
partialSets = 0
bestShanten = 0
mininumShanten = 0

def calculateMinimumShanten(handToCheck, mininumShanten = -1):
    if sum(handToCheck.values()) < 13: #If melds are present, skip chiitoi
        return calculateStandardShantenOptimized(handToCheck, mininumShanten)
    
    chiitoiShanten = calculateChiitoitsuShanten(handToCheck)
    if chiitoiShanten == -1:
        return -1
    
    standardShanten = calculateStandardShantenOptimized(handToCheck, mininumShanten)
    return min(standardShanten, chiitoiShanten)

# Original algorithm from Euophrys
def calculateStandardShanten(handToCheck, mininumShanten_ = -1):
    global hand
    global mininumShanten
    global completeSets
    global pair
    global partialSets
    global bestShanten

    hand = handToCheck.copy()
    mininumShanten = mininumShanten_

    def removeCompletedSets(i):
        global hand
        global mininumShanten
        global completeSets
        global pair
        global partialSets
        global bestShanten

        if bestShanten <= mininumShanten: return

        # Skip to the next tile that exists in the hand.
        while i < 39 and hand[i] == 0: i += 1

        if i >= 39:
            # We've gone through the whole hand, now check for partial sets.
            removePotentialSets(1)
            return

        # Pung
        if hand[i] >= 3:
            completeSets += 1
            hand[i] -= 3
            removeCompletedSets(i)
            hand[i] += 3
            completeSets -= 1

        # Chow
        if i < 30 and hand[i + 1] != 0 and hand[i + 2] != 0:
            completeSets += 1
            hand[i] -= 1
            hand[i + 1] -= 1
            hand[i + 2] -= 1
            removeCompletedSets(i)
            hand[i] += 1
            hand[i + 1] += 1
            hand[i + 2] += 1
            completeSets -= 1
        
        # Check all alternative hand configurations
        removeCompletedSets(i + 1)

    def removePotentialSets(i):
        global hand
        global mininumShanten
        global completeSets
        global pair
        global partialSets
        global bestShanten

        if bestShanten <= mininumShanten: return
        #if completeSets < 2: return

        # Skip to the next tile that exists in the hand
        while i < 39 and hand[i] == 0: i += 1

        if i >= 39:
            # We've checked everything. See if this shanten is better than the current best.
            currentShanten = 8 - (completeSets * 2) - partialSets - pair
            if currentShanten < bestShanten:
                bestShanten = currentShanten
            
            return
        
        # A standard hand will only ever have four groups plus a pair.
        if completeSets + partialSets < 4:
            # Pair
            if hand[i] == 2:
                partialSets += 1
                hand[i] -= 2
                removePotentialSets(i)
                hand[i] += 2
                partialSets -= 1
            
            # Edge or Side wait protorun
            if i < 30 and hand[i + 1] != 0:
                partialSets += 1
                hand[i] -= 1
                hand[i + 1] -= 1
                removePotentialSets(i)
                hand[i] += 1
                hand[i + 1] += 1
                partialSets -= 1
            
            # Closed wait protorun
            if i < 30 and i % 10 <= 8 and hand[i + 2] != 0:
                partialSets += 1
                hand[i] -= 1
                hand[i + 2] -= 1
                removePotentialSets(i)
                hand[i] += 1
                hand[i + 2] += 1
                partialSets -= 1

        # Check all alternative hand configurations
        removePotentialSets(i + 1)

    # Initialize variables
    completeSets = (14 - sum(handToCheck.values())) // 3
    pair = 0
    partialSets = 0
    bestShanten = 8

    # Loop through hand, removing all pair candidates and checking their shanten
    for i in range(1, 38):
        if hand[i] >= 2:
            pair += 1
            hand[i] -= 2
            removeCompletedSets(1)
            hand[i] += 2
            pair -= 1

    # Check shanten when there's nothing used as a pair
    removeCompletedSets(1)

    return bestShanten

# Takes some shortcuts but gets 99% correct. Almost twice as fast.
def calculateStandardShantenOptimized(handToCheck, mininumShanten_ = -1):
    global hand
    global mininumShanten
    global completeSets
    global pair
    global partialSets
    global bestShanten

    hand = handToCheck.copy()
    mininumShanten = mininumShanten_
    tilesinhand = [key for key, count in hand.items() if count != 0]

    # Initialize variables
    completeSets = (14 - sum(handToCheck.values())) // 3
    pair = 0
    partialSets = 0
    bestShanten = 8

    # Attempt to lock in pair. Start with trying to find lone pair, if not, take it from a joint (neighbors < 2)
    pairLocked = False
    for i in range(31,38):
        if pairLocked: break
        if hand[i] == 2:
            pair = 1
            hand[i] -= 2
            pairLocked = True

    for i in range(1,30):
        if pairLocked: break
        if hand[i] == 2 and hand[i-2] + hand[i-1] + hand[i+1] + hand[i+2] == 0:
            pair = 1
            hand[i] -= 2
            pairLocked = True

    for i in range(1,30):
        if pairLocked: break
        if hand[i] == 2 and hand[i-2] + hand[i-1] + hand[i+1] + hand[i+2] == 1:
            pair = 1
            hand[i] -= 2
            pairLocked = True

    #Remove any ankou of honors
    for i in range(31,38):
        if hand[i] >= 3:
            completeSets += 1
            hand[i] -= 3

    #If a triplet has no neighbors, it is always be correct to use it as a triple. If pair locked, 1 neighbor can also.
    for i in range(1,30):
        if hand[i] >= 3:
            if hand[i-1] + hand[i+1] == 0:
                completeSets += 1
                hand[i] -= 3
            if hand[i-1] + hand[i+1] == 1 and pairLocked:
                completeSets += 1
                hand[i] -= 3
        
    #If a sequence has no neighbors and cannot be a triplet
    #Not always correct eg. 134457 can be 3 blocks. But functionally, will rarely use it as 3 blocks so its OK
    if pairLocked:
        for i in range(1,28):
            if hand[i-1] == 0 and hand[i] != 0 and hand[i+1] != 0 and hand[i+2] != 0 and hand[i+3] == 0:
                if hand[i] < 3 and hand[i+1] < 3 and hand[i+2] < 3:
                    completeSets += 1
                    hand[i] -= 1
                    hand[i + 1] -= 1
                    hand[i + 2] -= 1
                    if hand[i-1] != 0 and hand[i] != 0 and hand[i+1] != 0:
                        completeSets += 1
                        hand[i] -= 1
                        hand[i + 1] -= 1
                        hand[i + 2] -= 1
    else:
        for i in range(1,28):
            if hand[i-1] == 0 and hand[i] == 1 and hand[i+1] == 1 and hand[i+2] == 1 and hand[i+3] == 0:
                completeSets += 1
                hand[i] -= 1
                hand[i + 1] -= 1
                hand[i + 2] -= 1

    def removeCompletedSets(i):
        global hand
        global mininumShanten
        global completeSets
        global pair
        global partialSets
        global bestShanten

        if bestShanten <= mininumShanten: return
        # Skip to the next tile that exists in the hand.
        while i < 39 and hand[i] == 0: i += 1

        if i >= 39:
            # We've gone through the whole hand, now check for partial sets.
            removePotentialSets(1)
            return

        # Pung
        if hand[i] >= 3:
            completeSets += 1
            hand[i] -= 3
            removeCompletedSets(i)
            hand[i] += 3
            completeSets -= 1

        # Chow
        if i < 30 and hand[i + 1] != 0 and hand[i + 2] != 0:
            completeSets += 1
            hand[i] -= 1
            hand[i + 1] -= 1
            hand[i + 2] -= 1
            removeCompletedSets(i)
            hand[i] += 1
            hand[i + 1] += 1
            hand[i + 2] += 1
            completeSets -= 1
        
        # Check all alternative hand configurations
        removeCompletedSets(i + 1)

    def removePotentialSets(i):
        global hand
        global mininumShanten
        global completeSets
        global pair
        global partialSets
        global bestShanten

        if bestShanten <= mininumShanten: return

        # Skip to the next tile that exists in the hand
        while i < 39 and hand[i] == 0: i += 1

        if i >= 39:
            # We've checked everything. See if this shanten is better than the current best.
            currentShanten = 8 - (completeSets * 2) - partialSets - pair
            if currentShanten < bestShanten:
                bestShanten = currentShanten
            
            return
        
        # A standard hand will only ever have four groups plus a pair.
        if completeSets + partialSets < 4:
            # Pair
            if hand[i] == 2:
                partialSets += 1
                hand[i] -= 2
                removePotentialSets(i)
                hand[i] += 2
                partialSets -= 1
            
            # Edge or Side wait protorun
            if i < 30 and hand[i + 1] != 0:
                partialSets += 1
                hand[i] -= 1
                hand[i + 1] -= 1
                removePotentialSets(i)
                hand[i] += 1
                hand[i + 1] += 1
                partialSets -= 1
            
            # Closed wait protorun
            if i < 30 and i % 10 <= 8 and hand[i + 2] != 0:
                partialSets += 1
                hand[i] -= 1
                hand[i + 2] -= 1
                removePotentialSets(i)
                hand[i] += 1
                hand[i + 2] += 1
                partialSets -= 1

        # Check all alternative hand configurations
        removePotentialSets(i + 1)

    # 1 iteration is enough if pair is found.
    if pairLocked:
        removeCompletedSets(1)
        return bestShanten

    # Fallback. Hopefully hand is very small at this point without many sets left.
    # Loop through hand, removing all pair candidates and checking their shanten.
    for i in tilesinhand:
        if hand[i] >= 2:
            pair += 1
            hand[i] -= 2
            removeCompletedSets(1)
            hand[i] += 2
            pair -= 1

    # Check shanten when there's nothing used as a pair.
    removeCompletedSets(1)
    return bestShanten

def calculateChiitoitsuShanten(handToCheck):
    hand = handToCheck
    pairCount = 0
    uniqueTiles = 0

    for i in range(1, 38):
        if hand[i] == 0:
            continue

        uniqueTiles += 1

        if hand[i] >= 2:
            pairCount += 1
        
    shanten = 6 - pairCount

    if uniqueTiles < 7:
        shanten += 7 - uniqueTiles
    
    return shanten

def calculateKokushiShanten(handToCheck):
    uniqueTiles = 0
    hasPair = 0

    for i in range(1, 38):
        if i % 10 == 1 or i % 10 == 9 or i > 30:
            if handToCheck[i] != 0:
                uniqueTiles += 1

                if handToCheck[i] >= 2:
                    hasPair = 1
               
    return 13 - uniqueTiles - hasPair

def calculateUkeire(hand, calls = [], baseShanten = -2):
    if baseShanten == -2:
        baseShanten = calculateMinimumShanten(hand)
    
    value = 0
    tiles = []

    # Optimization to only check tiles which can potentially reduce shanten.
    # If tenpai, tiles 2 away from existing hand cannot reduce shanten.
    # Else, (almost all) tiles 3 away from existing hand, or honors that you have 0, 1 or 4 cannot reduce shanten.
    # The exception is NNN EEE WWW SSSS, where any tile draw gives tanki tenpai, but I will ignore this case.

    potentialTiles = []
    if baseShanten == 0:
        for tile in range(30):
            if tile % 10 == 0: continue
            if hand[tile-1] == 0 and hand[tile] == 0 and hand[tile+1] == 0: continue
            potentialTiles.append(tile)
        for tile in range(31,38):
            if hand[tile] == 1 or hand[tile] == 2:
                potentialTiles.append(tile)
    else:
        for tile in range(30):
            if tile % 10 == 0: continue
            if hand[tile-2] == 0 and hand[tile-1] == 0 and hand[tile] == 0 and hand[tile+1] == 0 and hand[tile+2] == 0: continue
            potentialTiles.append(tile)
        for tile in range(31,38):
            if hand[tile] == 1 or hand[tile] == 2:
                potentialTiles.append(tile)

    flatcalls = [item for row in calls for item in row]

    for addedTile in potentialTiles:
        hand[addedTile] += 1
        if calculateMinimumShanten(hand, mininumShanten = baseShanten - 1) < baseShanten:
            #Improves shanten. Add the number of remaining tiles to the ukeire count
            value += 5 - hand[addedTile] - flatcalls.count(addedTile)
            tiles.append(addedTile)
        hand[addedTile] -= 1

    if tiles == []:
        tiles = [38] #Fifth tile case tenpai, eg. 345s GGGG

    return value, tiles

def isTenpai(hand):
    return calculateMinimumShanten(hand, mininumShanten = 0) == 0

# from collections import Counter
# from tqdm import tqdm
# import analysis_utils as u

# myhand = Counter({17: 2, 14: 2, 2: 1, 19: 1, 13: 1, 4: 1, 28: 1, 3: 1, 11: 1, 7: 1, 15: 1, 36: 0, 33: 0, 31: 0, 21: 0})
# print(u.parseAmberNotation(myhand))
# print(calculateStandardShanten(myhand))
# print(calculateStandardShantenOptimized(myhand))
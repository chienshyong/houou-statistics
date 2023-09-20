# Hand shanten calculator. Would like to expand this so that it also gives ukeire.
# Use amber notation: myhand = Counter({1:1, 2:1, 3:1, 5:1, 6:1, 7:1, 12:1, 13:2, 17:2, 21:1, 22:1})

hand = []
completeSets = 0
pair = 0
partialSets = 0
bestShanten = 0
mininumShanten = 0

def calculateMinimumShanten(handToCheck, mininumShanten = -1, considerKokushi = False):
    chiitoiShanten = calculateChiitoitsuShanten(handToCheck)
    if considerKokushi:
        kokushiShanten = calculateKokushiShanten(handToCheck)
    else:
        kokushiShanten = 13

    if chiitoiShanten == -1 or kokushiShanten == -1:
        return -1

    standardShanten = calculateStandardShanten(handToCheck, mininumShanten)
    return min(standardShanten, chiitoiShanten, kokushiShanten)

def calculateStandardShanten(handToCheck, mininumShanten_ = -1):
    global hand
    global mininumShanten
    global completeSets
    global pair
    global partialSets
    global bestShanten

    hand = handToCheck
    mininumShanten = mininumShanten_

    # Initialize variables
    completeSets = 0
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

def removeCompletedSets(i):
    global hand
    global mininumShanten
    global completeSets
    global pair
    global partialSets
    global bestShanten

    if bestShanten <= mininumShanten: return
    # Skip to the next tile that exists in the hand.
    while i < 38 and hand[i] == 0: i += 1

    if i >= 38:
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
    if completeSets < 2: return

    # Skip to the next tile that exists in the hand
    while i < 38 and hand[i] == 0: i += 1

    if i >= 38:
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

def calculateUkeire(hand, baseShanten = -2):
    if baseShanten == -2:
        baseShanten = calculateMinimumShanten(hand)
    
    value = 0
    tiles = []

    for addedTile in range(38):
        if addedTile % 10 == 0: continue
        
        hand[addedTile] += 1

        if calculateMinimumShanten(hand, baseShanten - 1) < baseShanten:
            #Improves shanten. Add the number of remaining tiles to the ukeire count
            value += 5 - hand[addedTile];
            tiles.append(addedTile);

        hand[addedTile] -= 1

    return value, tiles

# Hand shanten calculator.
# Use amber notation: myhand = Counter({1:1, 2:1, 3:1, 5:1, 6:1, 7:1, 12:1, 13:2, 17:2, 21:1, 22:1}). calls = [[23,24,25],[33,33,33]]

from collections import Counter

hand = []
completeSets = 0
pair = 0
partialSets = 0
bestShanten = 0
mininumShanten = 0

def calculateMinimumShanten(handToCheck, mininumShanten = -1):
    if sum(handToCheck.values()) < 13: #If melds are present, skip chiitoi
        return calculateStandardShantenBacktrack(handToCheck, mininumShanten)
    
    chiitoiShanten = calculateChiitoitsuShanten(handToCheck)
    if chiitoiShanten == -1: return -1
    
    standardShanten = calculateStandardShantenBacktrack(handToCheck, mininumShanten)
    return min(standardShanten, chiitoiShanten)

def calculateUkeire(hand, calls = [], baseShanten = -2):
    if sum(hand.values()) % 3 != 1: #Must be 1, 4, 7, 10 or 13
        raise Exception("Ukeire can only be calculated for hands after discard")
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

# Original algorithm from Euophrys
def calculateStandardShanten(handToCheck, mininumShanten_ = -1):
    global hand
    global mininumShanten
    global completeSets
    global pair
    global partialSets
    global bestShanten

    hand = Counter({k: v for k, v in handToCheck.items() if v != 0})
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

# Backtrack algortihm, 7x faster
def calculateStandardShantenBacktrack(handToCheck, mininumShanten_ = -1):
    global hand
    global mininumShanten
    global completeSets
    global pair
    global partialSets
    global bestShanten

    hand = Counter({k: v for k, v in handToCheck.items() if v != 0})
    mininumShanten = mininumShanten_

    # Initialize variables
    completeSets = (14 - sum(handToCheck.values())) // 3
    pair = 0
    partialSets = 0
    bestShanten = 8
    
    # Step 1: Attempt to lock pair. Algo is totally different (simpler) if pair is locked.
    # Attempt to lock in pair. Start with trying to find lone pair, if not, take it from a joint (neighbors < 2)
    pairLocked = False
    for i in range(31,38):
        if hand[i] == 2:
            if not pairLocked:
                pair = 1
                hand[i] -= 2
                pairLocked = True
            else:
                partialSets += 1
                hand[i] -= 2

    for i in range(1,30):
        if hand[i] == 2 and (0 if i%10 == 1 else hand[i-2]) + hand[i-1] + hand[i+1] + (0 if i%10 == 9 else hand[i+2]) == 1:
            if not pairLocked:
                pair = 1
                hand[i] -= 2
                pairLocked = True
            else:
                partialSets += 1
                hand[i] -= 2

    # print(f"\nHand after s1: {u.parseAmberNotation(hand)}")
    # print('completeSets: ', completeSets)
    # print('pair: ', pair)
    # print('partialSets: ', partialSets)

    # Step 2: Trimming.
    # Remove any ankou of honors and loose honors (1 or 4)
    for i in range(31,38):
        if hand[i] >= 3:
            completeSets += 1
        hand[i] = 0

    # If a triplet has no neighbors, it is always be correct to use it as a triple.
    for i in range(1,30):
        if hand[i] >= 3:
            if hand[i-1] + hand[i+1] == 0:
                completeSets += 1
                hand[i] -= 3

    # If a sequence has no neighbors and cannot be a triplet. Watch for edge case 134457.
        for i in range(1,28):
            if hand[i-1] == 0 and hand[i] != 0 and hand[i+1] == 1 and hand[i+2] != 0 and hand[i+3] == 0:
                if hand[i] < 3 and hand[i+2] < 3:
                    completeSets += 1
                    hand[i] -= 1
                    hand[i + 1] -= 1
                    hand[i + 2] -= 1

    hand = Counter({k: v for k, v in hand.items() if v != 0})

    # print(f"\nHand after s2: {u.parseAmberNotation(hand)}")
    # print('completeSets: ', completeSets)
    # print('pair: ', pair)
    # print('partialSets: ', partialSets)
        
    # Step 3: Backtracking.
    # For each tile from 1, see possible options. 

    # Init queue to (0, 'nil') to start at pointer 1
    # (pointer, action, hand, completeSets, partialSets, pair)
    # useJoint always uses the lowest number tile (446-> use 44). Using as a pair counts as useJoint as it takes priority anyway.
    queue = [(0, 4, hand.copy(), completeSets, partialSets, pair)]
    actions = ["useTriplet", "useRun", "useJoint", "skip", "nil"]

    # Backtracking until all branches are explored.
    while queue:
        pointer, action, hand, completeSets, partialSets, pair = queue.pop()
        lastpointer = pointer
        if action == 0:
            hand[pointer] -= 3
            completeSets += 1
        if action == 1:
            hand[pointer] -= 1
            hand[pointer+1] -= 1
            hand[pointer+2] -= 1
            completeSets += 1
        if action == 2:
            if hand[pointer] >= 2:
                hand[pointer] -= 2
                if not pair:
                    pair += 1
                else:
                    partialSets += 1
            elif hand[pointer+1] >= 1:
                hand[pointer] -= 1
                hand[pointer+1] -= 1
                partialSets += 1
            elif hand[pointer+2] >= 1:
                hand[pointer] -= 1
                hand[pointer+2] -= 1
                partialSets += 1
        if action == 3:
            hand[pointer] -= 1
            pointer += 1

        # Counts sets until the end of the hand
        while pointer < 30:
            if hand[pointer] == 0:
                pointer += 1
                continue

            # print(f"\nHand after {actions[action]} on {lastpointer}: {u.parseAmberNotation(hand)}")
            # print('completeSets: ', completeSets)
            # print('pair: ', pair)
            # print('partialSets: ', partialSets)
            # print('queue: ' + str(queue))
            
            # If we have a pair, less branches to consider and logic is simpler
            if pair:
                # If 3 or 4, try use as triplet
                if hand[pointer] >= 3:      # Triplet case when pair is locked. Always use unless set + pair is possible (11123)
                    if hand[pointer+1] == 0 or hand[pointer+2] == 0:
                        completeSets += 1
                        hand[pointer] -= 3
                        continue
                    else:
                        queue.append((pointer, 0, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair)) # useJoint will imply using the set too (set+pair) except for 1112233
                        if hand[pointer+1] == 2 and hand[pointer+2] == 2:
                            queue.append((pointer, 1, hand.copy(), completeSets, partialSets, pair))
                        break

                # If 1 or 2 and can use as run, try use as run
                if hand[pointer] >= 1 and hand[pointer+1] >= 1 and hand[pointer+2] >= 1:        # Since pair is locked, always use unless middle can form a triplet. eg 1222345
                    if hand[pointer] == 2:  # If can be a pair need to consider, but will never skip. eg 11234
                        queue.append((pointer, 1, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        break
                    if hand[pointer+1] < 3:
                        completeSets += 1
                        hand[pointer] -= 1
                        hand[pointer + 1] -= 1
                        hand[pointer + 2] -= 1
                        continue
                    else:       # Skip is possible if there is triplet possibility
                        queue.append((pointer, 1, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 3, hand.copy(), completeSets, partialSets, pair))
                        break
                
                # If not, check if a joint is possible.
                # Always use it unless the other tile is part of a set. 1222, 1333 or 1345.
                if hand[pointer] == 2:
                    hand[pointer] -= 2
                    partialSets += 1
                    continue
                elif hand[pointer+1] >= 1:
                    if hand[pointer+1] == 3:
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 3, hand.copy(), completeSets, partialSets, pair))
                        break
                    else:
                        hand[pointer] -= 1
                        hand[pointer+1] -= 1
                        partialSets += 1
                        continue
                elif pointer%10 != 9 and hand[pointer+2] >= 1:
                    if hand[pointer+2] == 3 or (hand[pointer+3] >= 1 and hand[pointer+4] >= 1):
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 3, hand.copy(), completeSets, partialSets, pair))
                        break
                    else:
                        hand[pointer] -= 1
                        hand[pointer+2] -= 1
                        partialSets += 1
                        continue

                #If no set posisble, no joint possible, it's a float so just remove it.
                hand[pointer] = 0

            # Will not be touched if Step 1 found a clear pair
            if not pair:
                # If 3 or 4, try use as a triplet or pair, or run if that's possible. eg 11112233.
                # Lock as triplet only if there is no neighbor.
                if hand[pointer] >= 3:
                    if hand[pointer+1] == 0:
                        completeSets += 1
                        hand[pointer] -= 3
                        continue
                    elif hand[pointer+2] >= 1:
                        queue.append((pointer, 0, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 1, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair)) 
                        break
                    else:
                        queue.append((pointer, 0, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        break

                # If 1 or 2 and can use as run, try use as run
                if hand[pointer] >= 1 and hand[pointer+1] >= 1 and hand[pointer+2] >= 1:
                    if hand[pointer] == 1 and hand[pointer+1] == 1:         # Lock run only if all but last is 1.
                        completeSets += 1
                        hand[pointer] -= 1
                        hand[pointer + 1] -= 1
                        hand[pointer + 2] -= 1
                        continue
                    elif hand[pointer] == 2:  # If can be a pair need to consider, but will never skip. eg 112334
                        queue.append((pointer, 1, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        break
                    if hand[pointer] == 1 and hand[pointer+1] > 1:  # Possible to skip only if ptr is 1 and ptr+1 is >1. eg 122345
                        queue.append((pointer, 1, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 3, hand.copy(), completeSets, partialSets, pair))
                        break
                
                # If no set or run, check if a joint is possible.
                # If can pair, lock pair. For kanchan and ryanmen, if the other side forms a pair or set, need to consider skip case. eg 244 where 44 is pair.
                if hand[pointer] == 2:
                    hand[pointer] -= 2
                    pair += 1
                    continue
                elif hand[pointer+1] >= 1:
                    if hand[pointer+1] == 1:
                        hand[pointer] -= 1
                        hand[pointer+1] -= 1
                        partialSets += 1
                        continue
                    else:
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 3, hand.copy(), completeSets, partialSets, pair))
                        break
                elif hand[pointer+2] >= 1 and pointer%10 != 9:
                    if hand[pointer+2] == 1 and (hand[pointer+3] == 0 or hand[pointer+4] == 0):
                        hand[pointer] -= 1
                        hand[pointer+2] -= 1
                        partialSets += 1
                        continue
                    else:
                        queue.append((pointer, 2, hand.copy(), completeSets, partialSets, pair))
                        queue.append((pointer, 3, hand.copy(), completeSets, partialSets, pair))
                        break
                    
                #If no set posisble, no joint possible, it's a float so just remove it.
                hand[pointer] = 0

        # Count shanten after reaching end of the hand. Then backtrack and explore next branch.
        if completeSets + partialSets > 4:
            partialSets = 4 - completeSets

        currentShanten = 8 - (completeSets * 2) - partialSets - pair

        if currentShanten <= mininumShanten: return mininumShanten
        if currentShanten < bestShanten:
            bestShanten = currentShanten

        # print(f"\nShanten after {actions[action]} on {lastpointer}: {currentShanten}")
        # print('completeSets: ', completeSets)
        # print('pair: ', pair)
        # print('partialSets: ', partialSets)
        # print('queue: ' + str(queue))

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


from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Discard reading from the Riichi tile, for first riichi
# Turn? Tedashi or tsumogiri?
# Safe tile, terminal, 28, middle tile or dora? What about safe tile after dropping a joint?
# What if the tile is connected to something in the discards?

output = "./results/RiichiTile.csv"
joints = [(1,1), (2,2), (3,3), (4,4), (5,5),                            # Pair Drop 
        (1,2), (2,1), (2,4), (4,2), (1,3), (3,1), (3,5), (5,3),         # Kanchan Drop
        (2,3), (3,2), (3,4), (4,3), (4,5), (5,4)]                       # Ryanmen Drop
combos = [(1,7), (7,1), (2,8), (1,9),                                   # 6 gap and 7 gap for good measure
        (1,6), (6,1), (2,7), (7,2),                                     # Aida yon ken
        (1,4), (4,1), (2,5), (5,2), (3,6), (6,3)]                       # Suji drop

class RiichiTile(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.hand_before = None
        self.tedashi = [[], [], [], []]

        self.riichitile_correlation_df = pd.DataFrame(0,index=[1,2,3,4,5,6,7,8,9],columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"count"]) #Given riichi on X, chance Y is in the discards
        self.riichitile_df = pd.DataFrame(0, index = [1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor","count"]) #Given riichi on X, relative danger of Y
        self.riichitile_jointdrop_df = pd.DataFrame(0,index = joints,
                                columns = [1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor","count"]) #Given riichi on X2 and X1 in discards, relative danger of tiles
        self.riichitile_combos_df = pd.DataFrame(0,index = combos,
                                columns = [1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor","count"]) #Given riichi on X2 and X1 in discards, relative danger of tiles
        self.riichitile_urawait_df = pd.DataFrame(0, index = [1,2,3,4,5,6,7,8,9], columns=["matagisuji", "urasuji","urakanchan","uratanki","urashanpon","uracomplex", "not ura", "count"]) #Chance of type of wait around riichi tile, given riichi tile
        self.turn_urawait_df = pd.DataFrame(0, index = range(0,18), columns=["matagisuji", "urasuji","urakanchan", "uratanki","urashanpon","uracomplex", "not ura", "count"]) #Chance of type of wait around riichi tile, given turn
        self.riichitile_firstrow_df = pd.DataFrame(0, index = [1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor","count"]) #Given riichi on X, relative danger of Y
        self.riichitile_secondrow_df = pd.DataFrame(0, index = [1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor","count"]) #Given riichi on X, relative danger of Y
        self.riichitile_thirdrow_df = pd.DataFrame(0, index = [1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor","count"]) #Given riichi on X, relative danger of Y

    def RoundStarted(self, init):
        self.tedashi = [[], [], [], []]
        return super().RoundStarted(init)
    
    def TileDiscarded(self, who, tile, tsumogiri, element):
        self.tedashi[who].append(not tsumogiri)
        super().TileDiscarded(who, tile, tsumogiri, element)

    def RiichiCalled(self, who, step, element):
        if step == 1:
            self.hand_before = self.hands[who].copy()
            self.hand_before[self.last_draw[who]] -= 1

        if step == 2:
            if self.turn > 17:
                self.end_round = True
                return
            
            ### Discard pool
            discarded_joints = []
            for i in range(len(self.discards[who])):
                d = self.discards[who][i]
                if d > 30: continue
                if d % 10 <= 5: 
                    for j in joints:
                        if j in discarded_joints: continue
                        if j[0] == d % 10:
                            for ii in range(i+1, len(self.discards[who])-1): # Attempt to find other side of the joint
                                dd = self.discards[who][ii]
                                if j[1] == dd % 10 and d // 10 == dd // 10 and self.tedashi[who][ii]: # Joint found.
                                    discarded_joints.append(j)

            ### Before riichi
            hand_before_shanten = sh.calculateMinimumShanten(self.hand_before)
            uke_before, wait_before = sh.calculateUkeire(self.hand_before, baseShanten=hand_before_shanten)
            shape_before = ut.GroupShanten(hand_before_shanten, uke_before)

            ### Wait
            hand = self.hands[who]
            uke, wait = sh.calculateWait(hand)
            wait_class = WaitClass(uke, wait, hand)

            tanyao = True
            for tile in hand:
                if hand[tile] > 0:
                    if tile % 10 == 1 or tile % 10 == 9 or tile > 30:
                        tanyao = False
                        break

            ## Dora & Dora discarded
            aka_drawn = [i*10 + 5 for i, x in enumerate(self.aka) if x == who]
            aka = []
            aka_discarded = []
            for a_d in aka_drawn:
                if hand[a_d] > 0:
                    aka.append(a_d)
                else:
                    aka_discarded.append(a_d)

            dora = 0
            dora_discarded = 0
            for d in self.dora:
                dora += hand[d]
                dora_discarded += self.discards[who].count(d)

            dsoba_wait = False
            for w in wait:
                for d in self.dora:
                    if w // 10 == d // 10:
                        if w >= d-2 and w <= d+2:
                            dsoba_wait = True
                            break

            ### Riichi tile
            riichi_tile = self.discards[who][-1]
            riichi_tile_class = RiichiTileClass(riichi_tile, self.dora, aka_discarded)
            ura_wait_class = UraWaitSorter(riichi_tile, wait, wait_class)
            tsumogiri = self.discards[who][-1] == self.last_draw[who]

            # First joint that is +- 2 of riichi tile 
            riichi_joint = []
            if riichi_tile < 30 and riichi_tile % 10 <= 5:
                for i in range(len(self.discards[who])-1,-1,-1):
                    d = self.discards[who][i]
                    if d > 30: continue
                    if d % 10 <= 5: 
                        for j in joints:
                            if j[0] == d % 10:
                                if j[1] == riichi_tile % 10 and d // 10 == riichi_tile // 10 and not tsumogiri: # Joint found.
                                    riichi_joint.append(j)
                                    break

            riichi_combos = []
            if riichi_tile < 30:
                for i in range(len(self.discards[who])-1):
                    d = self.discards[who][i]
                    if d > 30: continue
                    for c in combos:
                        if c[0] == d % 10:
                            if c[1] == riichi_tile % 10 and d // 10 == riichi_tile // 10 and not tsumogiri: # Joint found.
                                riichi_combos.append(c)

            ### Record data
            if riichi_tile < 30 and self.turn <= 6:
                self.riichitile_firstrow_df.loc[riichi_tile%10, "count"] += 1
                for w in wait:
                    if w > 30:
                        waittile_class = "Honor"
                    elif riichi_tile // 10 == w // 10:
                        waittile_class = w % 10
                    else:
                        waittile_class = w % 10 + 10 
                    self.riichitile_firstrow_df.loc[riichi_tile%10, waittile_class] += 1

            elif riichi_tile < 30 and self.turn >= 12:
                self.riichitile_thirdrow_df.loc[riichi_tile%10, "count"] += 1
                for w in wait:
                    if w > 30:
                        waittile_class = "Honor"
                    elif riichi_tile // 10 == w // 10:
                        waittile_class = w % 10
                    else:
                        waittile_class = w % 10 + 10 
                    self.riichitile_thirdrow_df.loc[riichi_tile%10, waittile_class] += 1

            elif riichi_tile < 30:
                self.riichitile_secondrow_df.loc[riichi_tile%10, "count"] += 1
                for w in wait:
                    if w > 30:
                        waittile_class = "Honor"
                    elif riichi_tile // 10 == w // 10:
                        waittile_class = w % 10
                    else:
                        waittile_class = w % 10 + 10 
                    self.riichitile_secondrow_df.loc[riichi_tile%10, waittile_class] += 1

            if riichi_tile < 30:
                self.riichitile_urawait_df.loc[riichi_tile%10, ura_wait_class] += 1
                self.riichitile_urawait_df.loc[riichi_tile%10, "count"] += 1
                self.turn_urawait_df.loc[self.turn, ura_wait_class] += 1
                self.turn_urawait_df.loc[self.turn, "count"] += 1
                
            # Log
            # print(f"Riichi turn {self.turn} Round {self.round[0]}")
            # print(f"Hand before: {ut.parseAmberNotation(self.hand_before)}, Shanten/Shape: {shape_before}, Drawn tile: {ut.parseAmberNotation(list=[self.last_draw[who]])}")
            # print(f"Discards: {ut.parseAmberNotation(list=self.discards[who])}")
            # print(f"Tenpai: {ut.parseAmberNotation(hand)}, Riichi on: {ut.parseAmberNotation(list=[riichi_tile])}, Class: {riichi_tile_class}, Tsumogiri: {tsumogiri}")
            # print(f"Wait on: {ut.parseAmberNotation(list=wait)}, Ura Wait class: {ura_wait_class}, Tanyao: {tanyao}")
            # print(f"Dora: {ut.parseAmberNotation(list=self.dora)}, Have # dora: {dora}, Have # aka: {ut.parseAmberNotation(list=aka)}, Dorasoba wait: {dsoba_wait}")
            # print(f"Aka discarded: {aka_discarded}, Dora discarded: {dora_discarded}")
            # input()

            self.end_round = True

    def PrintResults(self):
        self.riichitile_firstrow_df.to_csv(output, mode='a', index_label='first row')
        self.riichitile_secondrow_df.to_csv(output, mode='a', index_label='second row')
        self.riichitile_thirdrow_df.to_csv(output, mode='a', index_label='third row')

        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi count,{self.riichi_counts}\n")
            f.write(f"Total riichi tanyao,{self.riichi_tanyao}\n")
            f.write(f"Total riichi dorawait,{self.riichi_dorawait}\n")
            f.write(f"Total riichi turn,{self.riichi_turn}\n")


def WaitClass(uke, wait, hand):
    if len(wait) == 1:
        if wait[0] < 30:
            if hand[wait[0]]>0 and hand[wait[0]-1] + hand[wait[0]+1] < 3: #Cases where you have the tile and waiting on it, but it's kanchan eg 22344, 12234
                return "tanki"
            else:
                return "kanchan"
        else:
            return "tanki"

    if len(wait) == 2:
        if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and uke >= 5:
            return "ryanmen"
        else:
            if uke > 4:
                return "complex"
            else:
                return "shanpon"
            
    if len(wait) == 3:
        if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and wait[1] + 3 == wait[2]:
            return "sanmenchan"
        
    if len(wait) >= 3:
        return "complex"

def RiichiTileClass(tile, dora, aka_discarded):
    if tile in aka_discarded: 
        return "Aka"
    if tile in dora:
        return "Dora"
    if tile > 30:
        return "Honor"
    if tile % 10 == 1 or tile % 10 == 9:
        return "19"
    if tile % 10 == 2 or tile % 10 == 8:
        return "28"
    else:
        return "34567"
    
def TsumogiriSorter(hand, uke, wait, wait_class, tanyao, who, round, oya):
    if wait_class == "tanki":
        return "tanki"
    
    #Check for sanshoku. At least 2 of 3 sanshokus present & 2 of the other tile
    for i in range(1,8):
        set = 0
        joint = 0
        for j in range(3):
            count = 0
            if hand[j*10+i] > 0:
                count += 1
            if hand[j*10+i+1] > 0:
                count += 1
            if hand[j*10+i+2] > 0:
                count += 1
            if count == 3:
                set += 1
            if count == 2:
                joint += 1
        if set + joint == 3 and set >= 1:
            return "sanshoku"
        
    #Check for san/suuankou chance. 2 triplets present.
    triplets = 0
    for i in range(38):
        if hand[i] >= 3:
            triplets += 1
        if triplets >= 2:
            return "sanankou"
    
    #Tanyao/iipeikou bad wait, too hard to check for pinfu
    if tanyao:
        return "tanyao"
    if len(wait) == 1:
        if hand[wait[0]-1] >= 2 and hand[wait[0]] >= 1 and hand[wait[0]+1] >= 2: #Common 33455 bad wait ippeikou
            return "iipeikou"
        
    #Yakuhai triplet or pair
    for i in range(31,38):
        if isYakuhai(i, who, round, oya):
            if hand[i] == 3:
                return "yakuhai triplet"
            if hand[i] == 2:
                return "yakuhai pair"

    if (wait_class == "ryanmen" or wait_class == "sanmenchan") and triplets == 0:
        return "pinfu" #Good wait probably pinfu, bad wait probably no yaku
    else:
        return "no yaku"
    
def isYakuhai(tile, who, round, oya):
    yaku = 0
    if tile >= 35:
        yaku += 1
    if round <= 3 and tile == 31:
        yaku += 1
    if round >= 4 and tile == 32:
        yaku += 1

    if tile - ((who-oya)%4) == 31:
        yaku += 1

    return yaku

def UraWaitSorter(riichi_tile, wait, wait_class):
    if wait_class == "tanki":
        if wait[0] // 10 == riichi_tile // 10:
            if wait[0] <= riichi_tile + 2 and wait[0] >= riichi_tile - 2:
                return "uratanki"
    elif wait_class == "shanpon":
        for w in wait:
            if w // 10 == riichi_tile // 10:
                if w <= riichi_tile + 2 and w >= riichi_tile - 2:
                    return "urashanpon"
    elif wait_class == "complex":
        for w in wait:
            if w // 10 == riichi_tile // 10:
                if w <= riichi_tile + 2 and w >= riichi_tile - 2:
                    return "uracomplex"
    elif wait_class == "kanchan":
        if wait[0] // 10 == riichi_tile // 10:
            if wait[0] <= riichi_tile + 2 and wait[0] >= riichi_tile - 2:
                return "urakanchan"
    else:
        if wait[0] < riichi_tile and wait[-1] > riichi_tile:
            return "matagisuji"
        if wait[0] == riichi_tile + 1 or wait[-1] == riichi_tile - 1:
            return "urasuji"
    return "not ura"
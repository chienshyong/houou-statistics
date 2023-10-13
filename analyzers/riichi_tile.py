from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Discard reading from the Riichi tile, for first riichi
# Turn?
# Tedashi or tsumogiri?
# Safe tile, terminal, 28, middle tile or dora? What about safe tile after dropping a joint?

# Distribution of hand shapes when getting into tenpai - perfect (17-24 uke), ryanmen ryanmen (13-16 uke), sticky
# Final wait good shape or bad shape
# Final wait matagi or ura suji
# Number of dora
# Tanyao %

output = "./results/RiichiTile.csv"
joints = [(1,1), (2,2), (3,3), (4,4), (5,5),                            # Pair Drop 
        (1,2), (2,1), (2,4), (4,2), (1,3), (3,1), (3,5), (5,3),         # Kanchan Drop
        (2,3), (3,2), (3,4), (4,3), (4,5), (5,4)]                       # Ryanmen Drop

class RiichiTile(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.hand_before = None
        self.tedashi = [[], [], [], []]

        # self.riichi_counts = 0
        # self.riichi_tanyao = 0
        # self.riichi_dorawait = 0
        # self.riichi_turn = 0
        # self.tsumogiri_counts = 0
        # self.tsumogiri_tanyao = 0
        # self.tsumogiri_dorawait = 0
        # self.tsumogiri_turn = 0
        # self.tsumogiri_df = pd.DataFrame(0,index = ["tanki", "sanshoku", "sanankou", "tanyao", "iipeikou", "yakuhai triplet", "yakuhai pair", "pinfu", "no yaku"],
        #                                  columns = ["sanmenchan", "ryanmen", "kanchan", "tanki", "shanpon", "complex", "tanyao", "dorasoba"])
        # self.tsumogiri_dora = 0
        # self.tsumogiri_2dora = 0
        # self.tsumogiri_totalwidth = 0

        # self.riichitile_df = pd.DataFrame(0,index = ["Aka", "Dora", "Honor", "19", "28", "34567"],
        #                             columns = ["sanmenchan", "ryanmen", "kanchan", "shanpon", "tanki", "complex", "tanyao", "dorawait", "dora",  "2dora", "totalwidth", "count"])

        # self.safetile_jointdrop_df = pd.DataFrame(0,index = joints,
        #                             columns = ["sanmenchan", "ryanmen", "kanchan", "shanpon", "tanki", "complex", "tanyao", "dorawait", "dora",  "2dora", "totalwidth", "count"])
        
        # self.jointdrop_df = pd.DataFrame(0,index = joints,
        #                             columns = ["sanmenchan", "ryanmen", "kanchan", "shanpon", "tanki", "complex", "tanyao", "dorawait", "dora",  "2dora", "totalwidth", "count"])
        
        # self.riichijoint_df = pd.DataFrame(0,index = joints,
        #                             columns = ["sanmenchan", "ryanmen", "kanchan", "shanpon", "tanki", "complex", "tanyao", "dorawait", "dora",  "2dora", "totalwidth", "count"])
        
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

            ### Record data

            # self.riichitile_df.loc[riichi_tile_class, "count"] += 1
            # self.riichitile_df.loc[riichi_tile_class, wait_class] += 1
            # if tanyao:
            #     self.riichitile_df.loc[riichi_tile_class, "tanyao"] += 1
            # if dsoba_wait:
            #     self.riichitile_df.loc[riichi_tile_class, "dorawait"] += 1
            # self.riichitile_df.loc[riichi_tile_class, "dora"] += dora + len(aka)
            # if dora + len(aka) >= 2:
            #     self.riichitile_df.loc[riichi_tile_class, "2dora"] += 1
            # self.riichitile_df.loc[riichi_tile_class, "totalwidth"] += uke

            # if riichi_tile_class == "Honor":
            #     self.safetile_jointdrop_df.loc[discarded_joints, "count"] += 1
            #     self.safetile_jointdrop_df.loc[discarded_joints, wait_class] += 1
            #     if tanyao:
            #         self.safetile_jointdrop_df.loc[discarded_joints, "tanyao"] += 1
            #     if dsoba_wait:
            #         self.safetile_jointdrop_df.loc[discarded_joints, "dorawait"] += 1
            #     self.safetile_jointdrop_df.loc[discarded_joints, "dora"] += dora + len(aka)
            #     if dora + len(aka) >= 2:
            #         self.safetile_jointdrop_df.loc[discarded_joints, "2dora"] += 1
            #     self.safetile_jointdrop_df.loc[discarded_joints, "totalwidth"] += uke

            # self.jointdrop_df.loc[discarded_joints, "count"] += 1
            # self.jointdrop_df.loc[discarded_joints, wait_class] += 1
            # if tanyao:
            #     self.jointdrop_df.loc[discarded_joints, "tanyao"] += 1
            # if dsoba_wait:
            #     self.jointdrop_df.loc[discarded_joints, "dorawait"] += 1
            # self.jointdrop_df.loc[discarded_joints, "dora"] += dora + len(aka)
            # if dora + len(aka) >= 2:
            #     self.jointdrop_df.loc[discarded_joints, "2dora"] += 1
            # self.jointdrop_df.loc[discarded_joints, "totalwidth"] += uke

            # self.riichijoint_df.loc[riichi_joint, "count"] += 1
            # self.riichijoint_df.loc[riichi_joint, wait_class] += 1
            # if tanyao:
            #     self.riichijoint_df.loc[riichi_joint, "tanyao"] += 1
            # if dsoba_wait:
            #     self.riichijoint_df.loc[riichi_joint, "dorawait"] += 1
            # self.riichijoint_df.loc[riichi_joint, "dora"] += dora + len(aka)
            # if dora + len(aka) >= 2:
            #     self.riichijoint_df.loc[riichi_joint, "2dora"] += 1
            # self.riichijoint_df.loc[riichi_joint, "totalwidth"] += uke

            # self.riichi_counts += 1
            # if tanyao:
            #     self.riichi_tanyao += 1
            # if dsoba_wait:
            #     self.riichi_dorawait += 1
            # self.riichi_turn += self.turn

            # if tsumogiri:
            #     self.tsumogiri_counts += 1
            #     if tanyao:
            #         self.tsumogiri_tanyao += 1
            #     if dsoba_wait:
            #         self.tsumogiri_dorawait += 1
            #     self.tsumogiri_turn += self.turn
            #     tsumogiri_reason = TsumogiriSorter(hand, uke, wait, wait_class, tanyao, who, self.round[0], self.oya)
            #     self.tsumogiri_df.loc[tsumogiri_reason, wait_class] += 1
            #     self.tsumogiri_totalwidth += uke
            #     self.tsumogiri_dora += dora + len(aka)
            #     if dora + len(aka) >= 2:
            #         self.tsumogiri_2dora += 1

            ## Log
            # if ((5, 5) in discarded_joints or (4,4) in discarded_joints or (3,3) in discarded_joints) and wait_class == "tanki":
            #     print(f"Riichi turn {self.turn} Round {self.round[0]}")
            #     print(f"Hand before: {ut.parseAmberNotation(self.hand_before)}, Shanten/Shape: {shape_before}, Drawn tile: {ut.parseAmberNotation(list=[self.last_draw[who]])}")
            #     print(f"Discards: {ut.parseAmberNotation(list=self.discards[who])}")
            #     print(f"Tenpai: {ut.parseAmberNotation(hand)}, Riichi on: {ut.parseAmberNotation(list=[riichi_tile])}, Class: {riichi_tile_class}, Tsumogiri: {tsumogiri}")
            #     print(f"Wait on: {ut.parseAmberNotation(list=wait)}, Class: {wait_class}, Tanyao: {tanyao}")
            #     print(f"Dora: {ut.parseAmberNotation(list=self.dora)}, Have # dora: {dora}, Have # aka: {ut.parseAmberNotation(list=aka)}, Dorasoba wait: {dsoba_wait}")
            #     print(f"Aka discarded: {aka_discarded}, Dora discarded: {dora_discarded}")
            #     input()

            self.end_round = True

    def PrintResults(self):

        print(self.riichitile_df)
        print(self.jointdrop_df)
        print(self.safetile_jointdrop_df)
        print(self.riichijoint_df)
        self.riichitile_df.to_csv(output, mode='w', index_label='riichitile')
        self.jointdrop_df.to_csv(output, mode='a', index_label='jointdrop')
        self.safetile_jointdrop_df.to_csv(output, mode='a', index_label='safetile jointdrop')
        self.riichijoint_df.to_csv(output, mode='a', index_label='riichi jointdrop')

        # with open(output, "a", encoding="utf8") as f:
        #     f.write(f"Total riichi count,{self.riichi_counts}\n")
        #     f.write(f"Total riichi tanyao,{self.riichi_tanyao}\n")
        #     f.write(f"Total riichi dorawait,{self.riichi_dorawait}\n")
        #     f.write(f"Total riichi turn,{self.riichi_turn}\n")
        #     f.write(f"Total tsumogiri count,{self.tsumogiri_counts}\n")
        #     f.write(f"Total tsumogiri tanyao,{self.tsumogiri_tanyao}\n")
        #     f.write(f"Total tsumogiri dorawait,{self.tsumogiri_dorawait}\n")
        #     f.write(f"Total tsumogiri turn,{self.tsumogiri_turn}\n")


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
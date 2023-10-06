from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# Gathers the usefulness of sotogawa combinations, eg aida yon ken, dropping a suji, dropping a pair or joint.
# For joints, have special case where the second tile thrown was tedashi.
# Differentiate between 1 -> 7 and 7 -> 1.
# Checks if those 2 tiles are in the discard pool, check the wait if they are.

output = "./results/SotogawaCombo.csv"
joints = [(1,1), (2,2), (3,3), (4,4), (5,5),                            # Pair Drop 
        (1,2), (2,1), (2,4), (4,2), (1,3), (3,1), (3,5), (5,3),         # Kanchan Drop
        (2,3), (3,2), (3,4), (4,3), (4,5), (5,4)]                       # Ryanmen Drop
combos = [(1,7), (7,1), (2,8), (1,9),                                   # 6 gap and 7 gap for good measure
        (1,6), (6,1), (2,7), (7,2),                                     # Aida yon ken
        (1,4), (4,1), (2,5), (5,2), (3,6), (6,3)]                       # Suji drop

class SotogawaCombo(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.tedashi = [[], [], [], []] #True if discard X is tedashi

        self.riichi_counts = 0
        self.joint_tsumogiri_counts = Counter({key: 0 for key in joints})
        self.joint_tedashi_counts = Counter({key: 0 for key in joints})
        self.combo_counts = Counter({key: 0 for key in combos})
        self.joint_tsumogiri_df = pd.DataFrame(0,index=pd.MultiIndex.from_tuples(joints),columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"]) #Let 11-19 rep. 1 to 9 in other suits
        self.joint_tedashi_df = pd.DataFrame(0,index=pd.MultiIndex.from_tuples(joints),columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"])
        self.combo_df = pd.DataFrame(0,index=pd.MultiIndex.from_tuples(combos),columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"])

    def RoundStarted(self, init):
        self.tedashi = [[], [], [], []]
        return super().RoundStarted(init)

    def TileDiscarded(self, who, tile, tsumogiri, element):
        self.tedashi[who].append(not tsumogiri)
        super().TileDiscarded(who, tile, tsumogiri, element)

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        self.riichi_counts += 1
        uke, wait = sh.calculateWait(self.hands[who])

        joints_sampled = []
        counts_sampled = []

        for i in range(len(self.discards[who])-1):
            d = self.discards[who][i]
            if d > 30: continue
            if d % 10 <= 5: 
                for j in joints:
                    if j in joints_sampled: continue
                    if j[0] == d % 10:
                        for ii in range(i+1, len(self.discards[who])-1): # Attempt to find other side of the joint
                            dd = self.discards[who][ii]
                            if j[1] == dd % 10 and d // 10 == dd // 10: # Joint found.
                                joints_sampled.append(j)
                                if self.tedashi[who][ii]:
                                    #Append to tedashi df
                                    self.joint_tedashi_counts[j] += 1
                                    for w in wait:
                                        if w > 30:
                                            wait_class = "Honor"
                                        elif d // 10 == w // 10:
                                            wait_class = w % 10
                                        else:
                                            wait_class = w % 10 + 10
                                        self.joint_tedashi_df.loc[j, wait_class] += 1  
                                else:
                                    #Append to tsumogiri df
                                    self.joint_tsumogiri_counts[j] += 1
                                    for w in wait:
                                        if w > 30:
                                            wait_class = "Honor"
                                        elif d // 10 == w // 10:
                                            wait_class = w % 10
                                        else:
                                            wait_class = w % 10 + 10
                                        self.joint_tsumogiri_df.loc[j, wait_class] += 1  
            if d % 10 <= 7:
                for c in combos:
                    if c in counts_sampled: continue
                    if c[0] == d % 10:
                        for ii in range(i+1, len(self.discards[who])-1): # Attempt to find other side of the joint
                            dd = self.discards[who][ii]
                            if c[1] == dd % 10 and d // 10 == dd // 10:
                                counts_sampled.append(c)
                                #Append to combo df
                                self.combo_counts[c] += 1
                                for w in wait:
                                    if w > 30:
                                        wait_class = "Honor"
                                    elif d // 10 == w // 10:
                                        wait_class = w % 10
                                    else:
                                        wait_class = w % 10 + 10
                                    self.combo_df.loc[c, wait_class] += 1       

    def PrintResults(self):
        print(self.joint_tedashi_counts)
        print(self.joint_tedashi_df)
        print(self.joint_tsumogiri_counts)
        print(self.joint_tsumogiri_df)
        print(self.combo_counts)
        print(self.combo_df)

        self.joint_tedashi_df.to_csv(output, mode='w', index_label='Tedashi joints')
        self.joint_tsumogiri_df.to_csv(output, mode='a', index_label='Tsumogiri joints')
        self.combo_df.to_csv(output, mode='a', index_label='Combos')

        with open(output, "a", encoding="utf8", newline='') as f:
            writer = csv.writer(f)

            writer.writerow(['Joint tedashi', 'Count'])
            for item, count in self.joint_tedashi_counts.items():
                writer.writerow([item, count])

            writer.writerow(['Joint tsmogiri', 'Count'])
            for item, count in self.joint_tsumogiri_counts.items():
                writer.writerow([item, count])

            writer.writerow(['Combos', 'Count'])
            for item, count in self.combo_counts.items():
                writer.writerow([item, count])

            writer.writerow(['Total riichi', self.riichi_counts])
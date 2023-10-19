from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Properties of oikake riichi hand.
# Turn against good wait % and score
# D vs ND/ND vs ND/ND vs D?

output = "./results/OikakeRiichi.csv"

class OikakeRiichi(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.riichis = 0
        self.who_first_riichi = -1
        self.who_oikake = -1
        self.oikake_turn = -1

        self.d_nd_oikake_df = pd.DataFrame(0, index=range(0,19),columns=["goodwait", "width", "ronscore", "tsumoscore", "roncount", "tsumocount", "count"])
        self.nd_nd_oikake_df = pd.DataFrame(0, index=range(0,19),columns=["goodwait", "width", "ronscore", "tsumoscore", "roncount", "tsumocount", "count"])
        self.nd_d_oikake_df = pd.DataFrame(0, index=range(0,19),columns=["goodwait", "width", "ronscore", "tsumoscore", "roncount", "tsumocount", "count"])

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.riichis = 0
        self.who_first_riichi = -1
        self.who_oikake = -1 
        self.oikake_turn = -1

    def RiichiCalled(self, who, step, element):
        if step == 2:
            if self.turn > 18:
                self.end_round = True
                return
            
            self.riichis += 1
            if self.riichis == 1:
                self.who_first_riichi = who

            if self.riichis == 2:
                self.who_oikake = who
                self.oikake_turn = self.turn
                uke, wait = sh.calculateWait(self.hands[who])
                
                if who == self.oya:
                    if uke > 4:
                        self.d_nd_oikake_df.loc[self.turn, "goodwait"] += 1
                    self.d_nd_oikake_df.loc[self.turn, "width"] += uke
                    self.d_nd_oikake_df.loc[self.turn, "count"] += 1
                else:
                    if self.who_first_riichi == self.oya:
                        if uke > 4:
                            self.nd_d_oikake_df.loc[self.turn, "goodwait"] += 1
                        self.nd_d_oikake_df.loc[self.turn, "width"] += uke
                        self.nd_d_oikake_df.loc[self.turn, "count"] += 1
                    else:
                        if uke > 4:
                            self.nd_nd_oikake_df.loc[self.turn, "goodwait"] += 1
                        self.nd_nd_oikake_df.loc[self.turn, "width"] += uke
                        self.nd_nd_oikake_df.loc[self.turn, "count"] += 1

    def Win(self, element):
        who = int(element.attrib["who"])
        isTsumo = who == int(element.attrib["fromWho"])
        score = int(element.attrib["ten"].split(',')[1])

        if who == self.who_oikake:
            if self.who_oikake == self.oya:
                if isTsumo:
                    self.d_nd_oikake_df.loc[self.oikake_turn, "tsumocount"] += 1
                    self.d_nd_oikake_df.loc[self.oikake_turn, "tsumoscore"] += score
                else:
                    self.d_nd_oikake_df.loc[self.oikake_turn, "roncount"] += 1
                    self.d_nd_oikake_df.loc[self.oikake_turn, "ronscore"] += score
            else:
                if self.who_first_riichi == self.oya:
                    if isTsumo:
                        self.nd_d_oikake_df.loc[self.oikake_turn, "tsumocount"] += 1
                        self.nd_d_oikake_df.loc[self.oikake_turn, "tsumoscore"] += score
                    else:
                        self.nd_d_oikake_df.loc[self.oikake_turn, "roncount"] += 1
                        self.nd_d_oikake_df.loc[self.oikake_turn, "ronscore"] += score
                else:
                    if isTsumo:
                        self.nd_nd_oikake_df.loc[self.oikake_turn, "tsumocount"] += 1
                        self.nd_nd_oikake_df.loc[self.oikake_turn, "tsumoscore"] += score
                    else:
                        self.nd_nd_oikake_df.loc[self.oikake_turn, "roncount"] += 1
                        self.nd_nd_oikake_df.loc[self.oikake_turn, "ronscore"] += score

    def PrintResults(self):
        self.d_nd_oikake_df["tsumoscore"] = self.d_nd_oikake_df["tsumoscore"] / self.d_nd_oikake_df["tsumocount"]
        self.d_nd_oikake_df["ronscore"] = self.d_nd_oikake_df["ronscore"] / self.d_nd_oikake_df["roncount"]
        self.nd_d_oikake_df["tsumoscore"] = self.nd_d_oikake_df["tsumoscore"] / self.nd_d_oikake_df["tsumocount"]
        self.nd_d_oikake_df["ronscore"] = self.nd_d_oikake_df["ronscore"] / self.nd_d_oikake_df["roncount"]
        self.nd_nd_oikake_df["tsumoscore"] = self.nd_nd_oikake_df["tsumoscore"] / self.nd_nd_oikake_df["tsumocount"]
        self.nd_nd_oikake_df["ronscore"] = self.nd_nd_oikake_df["ronscore"] / self.nd_nd_oikake_df["roncount"]

        self.d_nd_oikake_df.to_csv(output, mode='w', index_label='d v nd')
        self.nd_d_oikake_df.to_csv(output, mode='a', index_label='nd v d')
        self.nd_nd_oikake_df.to_csv(output, mode='a', index_label='nd v nd')
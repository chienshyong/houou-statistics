from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
from util.analysis_utils import convertHai, convertTile, convertTileCheckAka, discards, draws, GetNextRealTag, GetStartingHands, getTilesFromCall, GetDora
import pandas as pd
import numpy as np
import statistics

# Finding the mean of hand scores excluding riichi and honba sticks.
# Dealer or non dealer ✓
# By turn (Riichi-turn of riichi. Open/dama-turn of win) ✓
# By yaku (tanyao, yakuhai, honitsu) ✓
# By visible dora in calls ✓
# Dora discarded ✓
# By deal in tile (Terminal, honor, dorasoba, dora)

output = "./results/HandScore.csv"
cats = ["ippatsu tsumo", "ippatsu ron", "riichi tsumo", "riichi ron", "dama tsumo", "dama ron", "tanyao", "yakuhai", "honitsu", "chinitsu", "other open yaku"]
other_yaku_names = ["Chankan", "Rinshan", "Haitei", "Houtei", "Chanta", "Itsu", "Doujun", "Doukou", "Sankantsu", "Toitoi", "Sanankou", "Junchan"]

class HandScore(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.riichi_turn = [-1,-1,-1,-1]

        self.nondealer_turn_score_df = pd.DataFrame(0, index=range(19), columns=cats)
        self.dealer_turn_score_df = pd.DataFrame(0, index=range(19), columns=cats)
        self.nondealer_turn_count_df = pd.DataFrame(0, index=range(19), columns=cats)
        self.dealer_turn_count_df = pd.DataFrame(0, index=range(19), columns=cats)
        self.other_yaku = [0] * len(other_yaku_names)

        #Just do non dealer for everything else
        self.tanyao_doracalled_doratype = pd.DataFrame(0, index=[0,1,2,3,4,5], columns=[1,2,3,4,5,6,7,8,9,"Honor"])
        self.yakuhai_doracalled_doratype = pd.DataFrame(0, index=[0,1,2,3,4,5], columns=[1,2,3,4,5,6,7,8,9,"Honor"])
        self.tanyao_doracalled_doratype_count = pd.DataFrame(0, index=[0,1,2,3,4,5], columns=[1,2,3,4,5,6,7,8,9,"Honor"])
        self.yakuhai_doracalled_doratype_count = pd.DataFrame(0, index=[0,1,2,3,4,5], columns=[1,2,3,4,5,6,7,8,9,"Honor"])

        self.doradiscarded = pd.DataFrame(0, index=[0,1,2,3,4,5], columns=[cats])
        self.doradiscarded_count = pd.DataFrame(0, index=[0,1,2,3,4,5], columns=[cats])

        self.dealintile = pd.DataFrame(0, index=["19","28","34567","honor","dora","dorasoba"], columns=[cats])
        self.dealintile_count = pd.DataFrame(0, index=["19","28","34567","honor","dora","dorasoba"], columns=[cats])

    def RoundStarted(self, init):
        self.riichi_turn = [-1,-1,-1,-1]
        return super().RoundStarted(init)

    def RiichiCalled(self, who, step, element):
        self.riichi_turn[who] = self.turn
        return super().RiichiCalled(who, step, element)
    
    def Win(self, element):
        if "yakuman" in element.attrib: return

        who = int(element.attrib["who"])
        fromwho = int(element.attrib["fromWho"])
        winning_tile = ut.convertTile(int(element.attrib["machi"]))
        score = int(element.attrib["ten"].split(',')[1])
        yaku = element.attrib["yaku"].split(',')[0::2]

        isTsumo = who == fromwho
        isRiichi = "1" in yaku
        isIppatsu = "2" in yaku
        isTanyao = "8" in yaku
        isHonitsu  = "34" in yaku
        isChinitsu = "35" in yaku
        isYakuhai = False
        for y in yaku:
            if int(y) >= 10 and int(y) <= 20:
                isYakuhai = True
        isDama = len(self.calls[who]) == 0 and not isRiichi

        turn = self.riichi_turn[who] if isRiichi else self.turn
        turn = 18 if turn > 18 else turn

        if isIppatsu:
            if isTsumo:
                cat = "ippatsu tsumo"
            else:
                cat = "ippatsu ron"
        elif isRiichi:
            if isTsumo:
                cat = "riichi tsumo"
            else:
                cat = "riichi ron"
        elif isDama:
            if isTsumo:
                cat = "dama tsumo"
            else:
                cat = "dama ron"
        elif isTanyao:
            cat = "tanyao"
        elif isHonitsu:
            cat = "honitsu"
        elif isChinitsu:
            cat = "chinitsu"
        elif isYakuhai:
            cat = "yakuhai"
        else:
            cat = "other open yaku" #Sanshoku, ittsuu, chanta, toitoi... should count
            for y in yaku:
                if ut.yaku_names[int(y)] in other_yaku_names:
                    self.other_yaku[other_yaku_names.index(ut.yaku_names[int(y)])] += 1
        
        ## Turn

        # if who == self.oya:
        #     self.dealer_turn_count_df.loc[turn, cat] += 1
        #     self.dealer_turn_score_df.loc[turn, cat] += score
        #     return
        # else:
        #     self.nondealer_turn_count_df.loc[turn, cat] += 1
        #     self.nondealer_turn_score_df.loc[turn, cat] += score

        ## Dora called

        dora = self.dora[0] % 10 if self.dora[0] < 30 else "Honor"
        doracalled = 0

        aka_drawn = [i*10 + 5 for i, x in enumerate(self.aka) if x == who]
        aka_discarded = []
        for a_d in aka_drawn:
            akaincall = False
            for c in self.calls[who]:
                for tile in c:
                    if tile == a_d and not akaincall:
                        doracalled += 1
                        akaincall = True

            if self.hands[who][a_d] == 0 and not akaincall:
                aka_discarded.append(a_d)

        for c in self.calls[who]:
            for tile in c:
                if tile in self.dora:
                    doracalled += 1

        doracalled = 5 if doracalled > 5 else doracalled
            
        if isTanyao and len(self.calls[who]) != 0:
            self.tanyao_doracalled_doratype.loc[doracalled, dora] += score
            self.tanyao_doracalled_doratype_count.loc[doracalled, dora] += 1
        if isYakuhai and len(self.calls[who]) != 0:
            self.yakuhai_doracalled_doratype.loc[doracalled, dora] += score
            self.yakuhai_doracalled_doratype_count.loc[doracalled, dora] += 1

        ## Dora discarded

        # dora_discarded = len(aka_discarded)
        # for idx, d in enumerate(self.discards[who]):
        #     if isRiichi and idx == turn: break    #If riichi, only before riichi
        #     if d == self.dora[0]:
        #         dora_discarded += 1
        
        # self.doradiscarded.loc[dora_discarded, cat] += score
        # self.doradiscarded_count.loc[dora_discarded, cat] += 1

        # ## Deal in tile
        # if isTsumo: return

        # if winning_tile in self.dora:
        #     machicat = "dora"
        # elif winning_tile > 30:
        #     machicat = "honor"
        # elif winning_tile >= self.dora[0] - 2 and winning_tile <= self.dora[0] + 2 and winning_tile // 10 == self.dora[0] // 10:
        #     machicat = "dorasoba"
        # elif winning_tile % 10 == 1 or winning_tile % 10 == 9:
        #     machicat = "19"
        # elif winning_tile % 10 == 2 or winning_tile % 10 == 8:
        #     machicat = "28"
        # else:
        #     machicat = "34567"

        # self.dealintile.loc[machicat, cat] += score
        # self.dealintile_count.loc[machicat, cat] += 1
            
    def PrintResults(self):
        dealer_turn = self.dealer_turn_score_df / self.dealer_turn_count_df
        dealer_turn.to_csv(output, mode='w', index_label='turndealer')
        self.dealer_turn_count_df.to_csv(output, mode='a', index_label='turndealer')
        ndealer_turn = self.nondealer_turn_score_df / self.nondealer_turn_count_df
        ndealer_turn.to_csv(output, mode='a', index_label='turnnondealer')
        self.nondealer_turn_count_df.to_csv(output, mode='a', index_label='turnnondealer')

        with open(output, "a", encoding="utf8") as f:
            f.write(f"other yaku,{other_yaku_names}\n")
            f.write(f"other yaku,{self.other_yaku}\n")

        tanyao_doracalled = self.tanyao_doracalled_doratype / self.tanyao_doracalled_doratype_count
        yakuhai_doracalled = self.yakuhai_doracalled_doratype / self.yakuhai_doracalled_doratype_count
        tanyao_doracalled.to_csv(output, mode='a', index_label='tanyao doracalled')
        self.tanyao_doracalled_doratype_count.to_csv(output, mode='a', index_label='tanyao doracalled')
        yakuhai_doracalled.to_csv(output, mode='a', index_label='yakuhai doracalled')
        self.yakuhai_doracalled_doratype_count.to_csv(output, mode='a', index_label='yakuhai doracalled')

        doradiscarded = self.doradiscarded / self.doradiscarded_count
        doradiscarded.to_csv(output, mode='a', index_label='dora discarded')

        dealintile = self.dealintile / self.dealintile_count
        dealintile.to_csv(output, mode='a', index_label='dealin tile')
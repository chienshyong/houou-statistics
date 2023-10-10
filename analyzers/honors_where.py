from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# You have a pair of honors, but no one's thrown it yet. What are the odds it comes out eventually?
# What if you atozuke, obvious vs non obvious? You guest wind vs a dragon vs a double wind? What about dora yakuhai?
# Fresh vs once cut?

output = "./results/HonorsWhere.csv"
categories = ["Closed", "Closed1o", "Atozuke", "Atozuke1o", "TerminalAtozuke", "TerminalAtozuke1o",
              "Closed Guestwind", "Closed1o Guestwind", "Atozuke Guestwind", "Atozuke1o Guestwind", "TerminalAtozuke Guestwind", "TerminalAtozuke1o Guestwind",
              "Closed Doublewind", "Closed1o Doublewind", "Atozuke Doublewind", "Atozuke1o Doublewind", "TerminalAtozuke Doublewind", "TerminalAtozuke1o Doublewind",
              "Closed Dora", "Closed1o Dora", "Atozuke Dora", "Atozuke1o Dora", "TerminalAtozuke Dora", "TerminalAtozuke1o Dora"]

class HonorsWhere(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.honors_thrown = [None,0,0,0,0,0,0,0]
        self.waiting_honor = [] # (Player, which honor, since turn, cat). When honor is discarded, check the stack and remove all counts. Take atozuke category as when first waiting.

        self.honorswhere_df = pd.DataFrame(0,index=range(17),columns=categories) # Counts of honors that did come out eventually, by waiting turn and category
        self.honorswhere_selfdraw_df = pd.DataFrame(0,index=range(17),columns=categories) # Counts of third honors player drew themselves, by waiting turn and category
        self.honorswhere_count_df = pd.DataFrame(0,index=range(17),columns=categories) # Counts waiting on honor by waiting turn and category

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.honors_thrown = [None,0,0,0,0,0,0,0]
        self.waiting_honor = [] 

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        turn = len(self.discards[(self.oya-1)%4])
        if turn > 16:
            self.end_round = True
            return

        # If honor thrown, check the queue if anyone was waiting on it.
        if tile > 30:
            #print(f"Turn {turn}, {tile} thrown")
            self.honors_thrown[tile%10] += 1
            ind_to_pop = []
            for idx, w in enumerate(self.waiting_honor):
                if w[1] == tile:
                    ind_to_pop.append(idx)
                    self.honorswhere_df.loc[w[2], w[3]] += 1
            if len(ind_to_pop) > 0:
                for i in sorted(ind_to_pop, reverse=True):
                    self.waiting_honor.pop(i)
                #print(self.waiting_honor)

        # After each discard, check their hand and see if they are waiting yakuhai
        for i in range(31,38):
            if self.honors_thrown[i%10] >= 2: continue
            if self.hands[who][i] == 2:
                yaku = isYakuhai(i,who,self.round[0],self.oya,self.dora)
                if yaku != None:
                    if len(self.calls[who]) > 0: #Atozuke
                        has_terminal = False
                        terminals = [1,9,11,19,21,29]
                        for call in self.calls[who]:
                            for tilec in call:
                                if tilec in terminals:
                                    has_terminal = True
                                    break

                        if has_terminal:
                            cat = "TerminalAtozuke"
                        else:
                            cat = "Atozuke"
                    else:
                        cat = "Closed"
                        
                    if self.honors_thrown[i%10] == 1:
                        cat += "1o"
                    cat += yaku
                        
                    self.waiting_honor.append((who,i,turn,cat))
                    self.honorswhere_count_df.loc[turn, cat] += 1
                    #print(self.waiting_honor)

    def TileDrawn(self, who, tile, element):
        super().TileDrawn(who, tile, element)
        if tile > 30:
            if self.hands[who][tile] + self.discards[who].count(tile) == 3:
                ind_to_pop = []
                for idx, w in enumerate(self.waiting_honor):
                    if w[1] == tile:
                        ind_to_pop.append(idx)
                        self.honorswhere_selfdraw_df.loc[w[2], w[3]] += 1
                if len(ind_to_pop) > 0:
                    for i in sorted(ind_to_pop, reverse=True):
                        self.waiting_honor.pop(i)
                    #print(f"{who} self drew {tile}")

    def PrintResults(self):
        print(self.honorswhere_count_df)
        print(self.honorswhere_df)
        print(self.honorswhere_selfdraw_df)
        self.honorswhere_count_df.to_csv(output, mode='w', index_label='Waiting')
        self.honorswhere_df.to_csv(output, mode='a', index_label='Came out')
        self.honorswhere_selfdraw_df.to_csv(output, mode='a', index_label='Self draw')

def isYakuhai(tile, who, round, oya, dora):
    yaku = 0
    if tile >= 35:
        yaku += 1
    if round <= 3 and tile == 31:
        yaku += 1
    if round >= 4 and tile == 32:
        yaku += 1

    mywind = False
    if tile - ((who-oya)%4) == 31:
        yaku += 1
        mywind = True

    if yaku == 0:
        return None
    if tile in dora:
        return " Dora"
    if yaku == 1 and mywind:
        return " Guestwind"
    if yaku == 1:
        return ""
    if yaku == 2:
        return " Doublewind"
from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Non-furiten non-dora Dama winrate of a last place dama player by turn and wait. Get the rate of Ron, Tsumo, draw, opp tsumo, lateral movement, and dealin.
# Let's try look at East Round hands with at least dora 2, to minimize cases where they fold. This give a better comparison vs Riichi. Often, dama decision come from this kind of scenario.
# Let's also get the fold rate.

# Dora wait

output = "./results/DamaWinrate.csv"
wait_classes = ['147','258','369','14','25','36','47','58','69', # Sanmenchan and Ryanmen
                '19','28','37','46','5', # Single Wait
                'Zt0','Zt1','Zt2', # Honor Tanki - 0 out, 1 out, 2 out
                'ZZ','Z1','Z5','11','15','55', # Shanpon: Honor, terminal, simples
                'complex'] # Any other wait

class DamaWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.dama_tenpai = [{},{},{},{}]
        self.riichi_players = []
        self.winner = -1 #-1 if no winner
        self.dealedin = -1

        self.Ron = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Tsumo = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Draw = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.OppTsumo = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Lateral = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Dealin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.FoldCount = pd.DataFrame(0, index=range(19), columns=wait_classes) # Noten at the end of the hand
        self.Count = pd.DataFrame(0, index=range(19), columns=wait_classes)

    def PlayRound(self, round_):
        self.winner = -1
        self.dealedin = -1
        
        # Get eventual winner, who dealt in, or draw
        for element in round_.itersiblings():
            if element.tag == "AGARI":
                self.winner = int(element.attrib["who"])
                self.dealedin = int(element.attrib["fromWho"])
                break
            elif element.tag == "RYUUKYOKU":
                break

        super().PlayRound(round_)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.dama_tenpai = [{},{},{},{}]
        self.riichi_players = []

    def RiichiCalled(self, who, step, element):
        super().RiichiCalled(who, step, element)
        self.riichi_players.append(who)

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if self.turn > 18:
            self.end_round = True
            return
        
        if len(self.riichi_players) > 0: return
        if len(self.calls[who]) > 0: return

        dora = self.aka.count(who)
        for d in self.dora:
            dora += self.hands[who][d]
        
        if dora > 2:
            # Already dama tenpai and tsumogiri
            if tsumogiri and self.turn-1 in self.dama_tenpai[who]:
                self.dama_tenpai[who][self.turn] = self.dama_tenpai[who][self.turn-1]

            # Closed hand tedashi, check dama
            if not tsumogiri:
                shanten = sh.calculateMinimumShanten(self.hands[who])
                if shanten == 0:
                    uke, wait = sh.calculateWait(self.hands[who])
                    wait_class = self.GetWaitClass(who, uke, wait)
                    self.dama_tenpai[who][self.turn] = wait_class

    def RoundEnded(self, init):
        tenpai_at_end = []
        for i in range(4):
            if len(self.dama_tenpai[i]) > 0:
                if i in self.riichi_players:
                    shanten = 0
                else:
                    shanten = sh.calculateMinimumShanten(self.hands[i])
                if shanten == 0:
                    tenpai_at_end.append(i)

        for who in range(4):
            if len(self.dama_tenpai[who]) > 0:
                for turn, wait_class in self.dama_tenpai[who].items():
                    self.Count.loc[turn, wait_class] += 1
                    if self.winner == who:
                        if self.dealedin == who:
                            self.Tsumo.loc[turn, wait_class] += 1
                        else:
                            self.Ron.loc[turn, wait_class] += 1
                    else:
                        if not who in tenpai_at_end:
                            self.FoldCount.loc[turn, wait_class] += 1
                        if self.winner == -1:
                            self.Draw.loc[turn, wait_class] += 1
                        else:
                            if self.dealedin == who:
                                self.Dealin.loc[turn, wait_class] += 1
                            elif self.dealedin == self.winner:
                                self.OppTsumo.loc[turn, wait_class] += 1
                            else:
                                self.Lateral.loc[turn, wait_class] += 1
    
    def PrintResults(self):
        win = (self.Ron+self.Tsumo) / self.Count
        tsumo = self.Tsumo/(self.Ron+self.Tsumo)
        draw = self.Draw/self.Count
        opptsumo = self.OppTsumo/self.Count
        lateral = self.Lateral/self.Count
        dealin = self.Dealin/self.Count
        fold = self.FoldCount/self.Count

        win.to_csv(output, mode='w', index_label='win')
        tsumo.to_csv(output, mode='a', index_label='tsumo')
        draw.to_csv(output, mode='a', index_label='draw')
        opptsumo.to_csv(output, mode='a', index_label='opptsumo')
        lateral.to_csv(output, mode='a', index_label='lateral')
        dealin.to_csv(output, mode='a', index_label='dealin')
        fold.to_csv(output, mode='a', index_label='fold')

    def GetWaitClass(self, who, uke, wait):
        w0_num = wait[0] % 10
        w_suit = wait[0] // 10

        if len(wait) == 3:
            if all(i//10 == w_suit for i in wait) and wait[0] + 3 == wait[1] and wait[1] + 3 == wait[2]:
                # Sanmenchan
                if w0_num == 1:
                    return '147'
                if w0_num == 2:
                    return '258'
                if w0_num == 3:
                    return '369'
                
        if len(wait) >= 3:
            return 'complex'
        
        if len(wait) == 1:
            if wait[0] < 30:
                # Single wait
                if w0_num == 1 or w0_num == 9:
                    cat = '19'
                if w0_num == 2 or w0_num == 8:
                    cat = '28'
                if w0_num == 3 or w0_num == 7:
                    cat = '37'
                if w0_num == 4 or w0_num == 6:
                    cat = '46'
                if w0_num == 5:
                    cat = '5'
                return cat
            else:
                # Honor Tanki
                honor_out = 0
                for discards in self.discards:
                    honor_out += discards.count(wait[0])
                if honor_out == 0:
                    return 'Zt0'
                if honor_out == 1:
                    return 'Zt1'
                if honor_out >= 2:
                    return 'Zt2'

        if len(wait) == 2:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and uke >= 5:
                # Ryanmen
                if w0_num == 1:
                    return '14'
                if w0_num == 2:
                    return '25'
                if w0_num == 3:
                    return '36'
                if w0_num == 4:
                    return '47'
                if w0_num == 5:
                    return '58'
                if w0_num == 6:
                    return '69'
            elif uke <= 4:
                # Shanpon
                if wait[0] > 30:
                    w0 = 'Z'
                elif wait[0]%10 == 1 or wait[0]%10 == 9:
                    w0 = '1'
                else:
                    w0 = '5'

                if wait[1] > 30:
                    cat = 'Z' + w0
                elif wait[1]%10 == 1 or wait[1]%10 == 9:
                    if w0 != 'Z':
                        cat = '1' + w0
                    else:
                        cat = 'Z1'
                else:
                    cat = w0 + '5'
                return cat
            else:
                return 'complex'
        return 'complex'
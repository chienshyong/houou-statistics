from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# We only care about the situation when Riichi is called and the final result. Ignore double Ron for simplicity.
# Non-furiten non-dora Riichi winrate of a first Riichi by turn and wait. Get the rate of Ron, Tsumo, draw, opp tsumo, lateral movement, and dealin

# Furiten
# Dora wait
# Oya vs Non oya
# By position
# By number of open players

output = "./results/RiichiWinrate.csv"
wait_classes = ['147','258','369','14','25','36','47','58','69', # Sanmenchan and Ryanmen
                '19','28','37','46','5','19S','28S','37S','46S','5S', # Single Wait and Suji trap single wait
                'Zt0','Zt1','Zt2', # Honor Tanki - 0 out, 1 out, 2 out
                'ZZ','Z1','Z5','11','15','55', # Shanpon: Honor, terminal, simples
                'Z1S','Z5S','11S','15S','55S', # Shanpon suji trap
                'complex'] # Any other wait

class RiichiWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.winner = -1 #-1 if no winner
        self.dealedin = -1

        # Non furiten, non dora rates
        self.Ron = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Tsumo = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Draw = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.OppTsumo = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Lateral = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Dealin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Count = pd.DataFrame(0, index=range(19), columns=wait_classes)

        # Furiten
        self.FuritenCount = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.FuritenWin = pd.DataFrame(0, index=range(19), columns=wait_classes)

        # Dora wait
        self.DoraWaitCount = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.DoraWaitWin = pd.DataFrame(0, index=range(19), columns=wait_classes)

        # Oya/Non Oya
        self.DealerCount = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.NondealerCount = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.DealerWin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.NondealerWin = pd.DataFrame(0, index=range(19), columns=wait_classes)

        # 1st vs 4th in South round
        self.South1stCount = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.South4thCount = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.South1stWin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.South4thWin = pd.DataFrame(0, index=range(19), columns=wait_classes)

        # Number of open players
        self.Open0Count = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open1Count = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open2Count = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open3Count = pd.DataFrame(0, index=range(19), columns=wait_classes)

        self.Open0Win = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open1Win = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open2Win = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open3Win = pd.DataFrame(0, index=range(19), columns=wait_classes)

        self.Open0Dealin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open1Dealin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open2Dealin = pd.DataFrame(0, index=range(19), columns=wait_classes)
        self.Open3Dealin = pd.DataFrame(0, index=range(19), columns=wait_classes)

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

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if self.turn > 18:
            self.end_round = True
            return

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        self.end_round = True

        uke, wait = sh.calculateWait(self.hands[who])
        wait_class = self.GetWaitClass(who, uke, wait)
        #print(f"Final winner {self.winner} {self.dealin}, {who} riichi, wait {wait_class} ({wait})")

        furiten = False
        dora_wait = False
        for w in wait:
            if w in self.discards[who]:
                furiten = True
            if w in self.dora:
                dora_wait = True

        if not furiten and not dora_wait:
            self.Count.loc[self.turn, wait_class] += 1
            if self.winner == who:
                if self.dealedin == who:
                    self.Tsumo.loc[self.turn, wait_class] += 1
                else:
                    self.Ron.loc[self.turn, wait_class] += 1
            elif self.winner == -1:
                self.Draw.loc[self.turn, wait_class] += 1
            else:
                if self.dealedin == who:
                    self.Dealin.loc[self.turn, wait_class] += 1
                elif self.dealedin == self.winner:
                    self.OppTsumo.loc[self.turn, wait_class] += 1
                else:
                    self.Lateral.loc[self.turn, wait_class] += 1

        if furiten:
            self.FuritenCount.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.FuritenWin.loc[self.turn, wait_class] += 1

        if dora_wait:
            self.DoraWaitCount.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.DoraWaitWin.loc[self.turn, wait_class] += 1

        if self.oya == who:
            self.DealerCount.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.DealerWin.loc[self.turn, wait_class] += 1
        else:
            self.NondealerCount.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.NondealerWin.loc[self.turn, wait_class] += 1

        if self.round[0] >= 4:
            sorted_points = self.scores.copy()
            sorted_points.sort()
            if self.scores[who] == sorted_points[0]:
                self.South4thCount.loc[self.turn, wait_class] += 1
                if self.winner == who:
                    self.South4thWin.loc[self.turn, wait_class] += 1
            if self.scores[who] == sorted_points[3]:
                self.South1stCount.loc[self.turn, wait_class] += 1
                if self.winner == who:
                    self.South1stWin.loc[self.turn, wait_class] += 1

        open_players = 0
        for i in range(4):
            if i == who: continue
            if len(self.calls[i]) > 0:
                open_players += 1

        if open_players == 0:
            self.Open0Count.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.Open0Win.loc[self.turn, wait_class] += 1
            elif self.dealedin == who:
                self.Open0Dealin.loc[self.turn, wait_class] += 1
        elif open_players == 1:
            self.Open1Count.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.Open1Win.loc[self.turn, wait_class] += 1
            elif self.dealedin == who:
                self.Open1Dealin.loc[self.turn, wait_class] += 1
        elif open_players == 2:
            self.Open2Count.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.Open2Win.loc[self.turn, wait_class] += 1
            elif self.dealedin == who:
                self.Open2Dealin.loc[self.turn, wait_class] += 1
        else:
            self.Open3Count.loc[self.turn, wait_class] += 1
            if self.winner == who:
                self.Open3Win.loc[self.turn, wait_class] += 1
            elif self.dealedin == who:
                self.Open3Dealin.loc[self.turn, wait_class] += 1
        
    def PrintResults(self):
        win = (self.Ron+self.Tsumo) / self.Count
        tsumo = self.Tsumo/(self.Ron+self.Tsumo)
        draw = self.Draw/self.Count
        opptsumo = self.OppTsumo/self.Count
        lateral = self.Lateral/self.Count
        dealin = self.Dealin/self.Count

        win.to_csv(output, mode='w', index_label='win')
        tsumo.to_csv(output, mode='a', index_label='tsumo')
        draw.to_csv(output, mode='a', index_label='draw')
        opptsumo.to_csv(output, mode='a', index_label='opptsumo')
        lateral.to_csv(output, mode='a', index_label='lateral')
        dealin.to_csv(output, mode='a', index_label='dealin')

        furiten = self.FuritenWin/self.FuritenCount
        dorawait = self.DoraWaitWin/self.DoraWaitCount
        dealer = self.DealerWin/self.DealerCount
        nondealer = self.NondealerWin/self.NondealerCount
        south1st = self.South1stWin/self.South1stCount
        south4th = self.South4thWin/self.South4thCount

        furiten.to_csv(output, mode='a', index_label='furiten')
        dorawait.to_csv(output, mode='a', index_label='dorawait')
        dealer.to_csv(output, mode='a', index_label='dealer')
        nondealer.to_csv(output, mode='a', index_label='nondealer')
        south1st.to_csv(output, mode='a', index_label='south1st')
        south4th.to_csv(output, mode='a', index_label='south4th')

        open0 = self.Open0Win/self.Open0Count
        open0dealin = self.Open0Dealin/self.Open0Count
        open1 = self.Open1Win/self.Open1Count
        open1dealin = self.Open1Dealin/self.Open1Count
        open2 = self.Open2Win/self.Open2Count
        open2dealin = self.Open2Dealin/self.Open2Count
        open3 = self.Open3Win/self.Open3Count
        open3dealin = self.Open3Dealin/self.Open3Count

        open0.to_csv(output, mode='a', index_label='open0')
        open1.to_csv(output, mode='a', index_label='open1')
        open2.to_csv(output, mode='a', index_label='open2')
        open3.to_csv(output, mode='a', index_label='open3')
        open0dealin.to_csv(output, mode='a', index_label='open0dealin')
        open1dealin.to_csv(output, mode='a', index_label='open1dealin')
        open2dealin.to_csv(output, mode='a', index_label='open2dealin')
        open3dealin.to_csv(output, mode='a', index_label='open3dealin')

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
                if self.CheckSujiTrap(who, wait):
                    cat += 'S'
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

                if self.CheckSujiTrap(who, wait):
                    cat += 'S'
                return cat
            else:
                return 'complex'

    def CheckSujiTrap(self, who, wait):
        for w in wait:
            if w > 30: continue

            traps = []
            if w%10 <= 6:
                traps.append(w+3)
            if w%10 >= 4:
                traps.append(w-3)
            for d in self.discards[who]:
                if d in traps:
                    traps.remove(d)
            
            if len(traps) == 0:
                return True
        return False
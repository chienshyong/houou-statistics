from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# Judging tenpai chance of open & dama hands. Abort analysis once a riichi is called.
# Honitsu vs Yakuhai vs Tanyao vs Dama ✓
# What TYPE of call? ryanmen? kanchan? dora pon? ✓
# Safe tile tedashi ✓
# Dora discard ✓
# After a kan ✓
# Joint drops (and does it mean a pair wait?) ✓
# After continuous tsumogiri ✓

output = "./results/OpenTenpai.csv"

class OpenTenpai(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.tedashi = [[], [], [], []] #True if discard X is tedashi
        self.isTenpai = [False,False,False,False]
        self.didKakan = [False,False,False,False]
        self.just_called = False

        # Tenpai by yaku
        self.honitsu_turn_calls_df = pd.DataFrame(0,index=range(19),columns=range(1,4)) # Count as honitsu attempt if hand only has 1 suit
        self.honitsu_turn_calls_c_df = pd.DataFrame(0,index=range(19),columns=range(1,4)) # Kan and no kan counted
        self.yakuhai_turn_calls_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.yakuhai_turn_calls_c_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.other_turn_calls_df = pd.DataFrame(0,index=range(19),columns=range(4)) # Primarily open tanyao & dama
        self.other_turn_calls_c_df = pd.DataFrame(0,index=range(19),columns=range(4))

        # If a kan was called
        self.honitsu_kan_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.yakuhai_kan_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.other_kan_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.honitsu_kan_c_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.yakuhai_kan_c_df = pd.DataFrame(0,index=range(19),columns=range(1,4))
        self.other_kan_c_df = pd.DataFrame(0,index=range(19),columns=range(1,4))

        # 1 ryanmen call vs 1 kanchan call vs 1 pon (NOT yakuhai or honitsu)
        self.calltype_df = pd.DataFrame(0,index=range(19), columns =["ryanmen", "pon", "kanchan", "dora pon"])
        self.calltype_1sh_df = pd.DataFrame(0,index=range(19), columns =["ryanmen", "pon", "kanchan", "dora pon"])
        self.calltype_c_df = pd.DataFrame(0,index=range(19), columns =["ryanmen", "pon", "kanchan", "dora pon"])

        # Just called
        self.justcalled_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.justcalled_1sh_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.justcalled_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

        # Safe tile tedashi (Excluding honitsu since you hold honors anyway)
        self.safetile_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.safetile_1sh_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.safetile_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

        self.normaltile_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.normaltile_1sh_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.normaltile_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

        # Dora discard (Excluding honitsu)
        self.doradiscard_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.doradiscard_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

        # Aka discard (Excluding honitsu)
        self.akadiscard_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.akadiscard_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

        # Joint drop (Excluding honitsu)
        self.pairdrop_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.pairdrop_1sh_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.pairdrop_tanki_df = pd.DataFrame(0,index=range(19), columns=range(4)) # % of waits that are tanki, if tenpai
        self.kanchandrop_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.kanchandrop_1sh_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.kanchandrop_tanki_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.ryanmendrop_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.ryanmendrop_1sh_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.ryanmendrop_tanki_df = pd.DataFrame(0,index=range(19), columns=range(4))

        self.pairdrop_c_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.kanchandrop_c_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.ryanmendrop_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

        # Tsumogiri
        self.tsumogiri_3_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.tsumogiri_6_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.tsumogiri_3_c_df = pd.DataFrame(0,index=range(19), columns=range(4))
        self.tsumogiri_6_c_df = pd.DataFrame(0,index=range(19), columns=range(4))

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.tedashi = [[], [], [], []]
        self.isTenpai = [False,False,False,False]
        self.didKakan = [False,False,False,False]

    def RiichiCalled(self, who, step, element):
        self.end_round = True

    def TileDrawn(self, who, tile, element):
        super().TileDrawn(who, tile, element)
        self.just_called = False

    def TileCalled(self, who, tiles, element):
        super().TileCalled(who, tiles, element)
        length = len(tiles)
        if length == 1:
            self.didKakan[who] = True
        self.just_called = True

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        self.tedashi[who].append(not tsumogiri)

        if self.turn >= 19:
            self.end_round = True
            return
        
        # Analyse hands every turn (oya discard)
        if who == self.oya:
            for i in range(4):
                if len(self.calls[i]) == 4: continue

                # Categorize into honitsu or yakuhai. Other = open (mostly tanyao) or dama. And check if kan.
                did_kan = False
                if len(self.calls[i]) == 0:
                    cat = "other"
                else:
                    suits = [0,0,0]
                    for h in self.hands[i]:
                        if self.hands[i][h] == 0: continue
                        if h > 30: continue
                        suits[h//10] += self.hands[i][h]
                        
                    for c in self.calls[i]:
                        if len(c) == 4 and len(self.calls[i]) >= 2: # Don't want to count 1 ankan closed. Still am counting 2 ankan closed but rare enough.
                            did_kan = True
                        if c[0] > 30: continue
                        suits[c[0]//10] += 3

                    if self.didKakan[i]:
                        did_kan = True

                    suits.remove(max(suits))
                    if max(suits) <= 1: # Allow for 1 non-honitsu tile (safe tile, floating dora etc.)
                        cat = "honitsu"
                    else:
                        cat = "other"
                        for c in self.calls[i]:
                            if self.isYakuhai(c[0], i):
                                cat = "yakuhai"
                        for yakuhai in range(31,38):
                            if self.hands[i][yakuhai] >= 2: #Atozuke or ankou
                                cat = "yakuhai"

                # Tenpai by turn and yaku and kan
                shanten = sh.calculateMinimumShanten(self.hands[i])
                if shanten <= 0:
                    self.isTenpai[i] = True
                else:
                    self.isTenpai[i] = False

                if cat == "honitsu":
                    self.honitsu_turn_calls_c_df.loc[self.turn, len(self.calls[i])] += 1
                    if did_kan:
                        self.honitsu_kan_c_df.loc[self.turn, len(self.calls[i])] += 1
                    if self.isTenpai[i]:
                        self.honitsu_turn_calls_df.loc[self.turn, len(self.calls[i])] += 1
                        if did_kan:
                            self.honitsu_kan_df.loc[self.turn, len(self.calls[i])] += 1
                elif cat == "yakuhai":
                    self.yakuhai_turn_calls_c_df.loc[self.turn, len(self.calls[i])] += 1
                    if did_kan:
                        self.yakuhai_kan_c_df.loc[self.turn, len(self.calls[i])] += 1
                    if self.isTenpai[i]:
                        self.yakuhai_turn_calls_df.loc[self.turn, len(self.calls[i])] += 1
                        if did_kan:
                            self.yakuhai_kan_df.loc[self.turn, len(self.calls[i])] += 1
                else:
                    self.other_turn_calls_c_df.loc[self.turn, len(self.calls[i])] += 1
                    if did_kan:
                        self.other_kan_c_df.loc[self.turn, len(self.calls[i])] += 1
                    if self.isTenpai[i]:
                        self.other_turn_calls_df.loc[self.turn, len(self.calls[i])] += 1
                        if did_kan:
                            self.other_kan_df.loc[self.turn, len(self.calls[i])] += 1

                # If tanyao with 1 call, see what type of call (No kan)
                if cat == "other" and len(self.calls[i]) == 1:
                    call = self.calls[i][0]
                    if len(call) == 4: break
                    if call[0] == call[1]:
                        cat = "pon"
                        if call[0] in self.dora:
                            cat = "dora pon"
                    elif call[1] + 1 == call[2] and call[1] % 10 != 1 and call[2] % 10 != 9:
                        cat = "ryanmen"
                    else:
                        cat = "kanchan"
                    self.calltype_c_df.loc[self.turn, cat] += 1
                    if self.isTenpai[i]:
                        self.calltype_df.loc[self.turn, cat] += 1
                    if shanten == 1:
                        self.calltype_1sh_df.loc[self.turn, cat] += 1

        if len(self.calls[who]) == 4: return

        # Just called
        if self.just_called:
            shanten = sh.calculateMinimumShanten(self.hands[who])
            if shanten <= 0:
                self.isTenpai[who] = True
            else:
                self.isTenpai[who] = False

            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                self.justcalled_c_df.loc[self.turn, len(self.calls[who])] += 1
                if self.isTenpai[who]:
                    self.justcalled_df.loc[self.turn, len(self.calls[who])] += 1
                if shanten == 1:
                    self.justcalled_1sh_df.loc[self.turn, len(self.calls[who])] += 1

        # Safe tile tedashi - any honor tile AFTER a call
        if tile > 30 and not tsumogiri and not self.just_called:
            shanten = sh.calculateMinimumShanten(self.hands[who])
            if shanten <= 0:
                self.isTenpai[who] = True
            else:
                self.isTenpai[who] = False

            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                self.safetile_c_df.loc[self.turn, len(self.calls[who])] += 1
                if self.isTenpai[who]:
                    self.safetile_df.loc[self.turn, len(self.calls[who])] += 1
                if shanten == 1:
                    self.safetile_1sh_df.loc[self.turn, len(self.calls[who])] += 1

        # Normal tile tedashi - any number tile AFTER a call
        if tile < 30 and not tsumogiri and not self.just_called:
            shanten = sh.calculateMinimumShanten(self.hands[who])
            if shanten <= 0:
                self.isTenpai[who] = True
            else:
                self.isTenpai[who] = False

            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                self.normaltile_c_df.loc[self.turn, len(self.calls[who])] += 1
                if self.isTenpai[who]:
                    self.normaltile_df.loc[self.turn, len(self.calls[who])] += 1
                if shanten == 1:
                    self.normaltile_1sh_df.loc[self.turn, len(self.calls[who])] += 1

        # Dora discard
        if tile in self.dora:
            if not self.isTenpai[who]:
                shanten = sh.calculateMinimumShanten(self.hands[who])
                if shanten <= 0:
                    self.isTenpai[who] = True

            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                self.doradiscard_c_df.loc[self.turn, len(self.calls[who])] += 1
                if self.isTenpai[who]:
                    self.doradiscard_df.loc[self.turn, len(self.calls[who])] += 1

        # Aka discard
        aka_tile, aka = ut.convertTileCheckAka(element.tag[1:])
        if aka != None:
            if not self.isTenpai[who]:
                shanten = sh.calculateMinimumShanten(self.hands[who])
                if shanten <= 0:
                    self.isTenpai[who] = True

            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                self.akadiscard_c_df.loc[self.turn, len(self.calls[who])] += 1
                if self.isTenpai[who]:
                    self.akadiscard_df.loc[self.turn, len(self.calls[who])] += 1

        # Joint drop. If tedashi and connects to last tedashi.
        if not tsumogiri:
            last_tedashi = -1
            for i in range(len(self.tedashi[who])-2, -1, -1):
                if self.tedashi[who][i]:
                    last_tedashi = i
                    break
            if last_tedashi == -1: return

            last_ted_tile = self.discards[who][last_tedashi]
            
            cat = None
            if last_ted_tile == tile:
                cat = "pair"
            if tile < 30:
                if last_ted_tile // 10 == tile // 10:
                    if last_ted_tile + 1 == tile or last_ted_tile - 1 == tile:
                        cat = "ryanmen"
                        if last_ted_tile % 10 == 1 or last_ted_tile % 10 == 9 or tile % 10 == 1 or tile % 10 == 9:
                            cat = "kanchan"
                    if last_ted_tile + 2 == tile or last_ted_tile - 2 == tile:
                        cat = "kanchan"
            if cat == None: return

            shanten = sh.calculateMinimumShanten(self.hands[who])
            if shanten <= 0:
                self.isTenpai[who] = True
            else:
                self.isTenpai[who] = False

            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                # Check if tanki wait
                tanki = False
                if self.isTenpai[who]:
                    uke, wait = sh.calculateWait(self.hands[who])
                    if len(wait) == 1:
                        if wait[0] > 30:
                            tanki = True
                        elif self.hands[who][wait[0]]>0 and self.hands[who][wait[0]-1]+self.hands[who][wait[0]+1] < 3: #Cases where you have the tile and waiting on it, but it's kanchan eg 22344, 12234
                            tanki = True

                if cat == "pair":
                    self.pairdrop_c_df.loc[self.turn, len(self.calls[who])] += 1
                    if self.isTenpai[who]:
                        self.pairdrop_df.loc[self.turn, len(self.calls[who])] += 1
                        if tanki:
                            self.pairdrop_tanki_df.loc[self.turn, len(self.calls[who])] += 1
                    elif shanten == 1:
                        self.pairdrop_1sh_df.loc[self.turn, len(self.calls[who])] += 1
                if cat == "kanchan":
                    self.kanchandrop_c_df.loc[self.turn, len(self.calls[who])] += 1
                    if self.isTenpai[who]:
                        self.kanchandrop_df.loc[self.turn, len(self.calls[who])] += 1
                        if tanki:
                            self.kanchandrop_tanki_df.loc[self.turn, len(self.calls[who])] += 1
                    elif shanten == 1:
                        self.kanchandrop_1sh_df.loc[self.turn, len(self.calls[who])] += 1
                if cat == "ryanmen":
                    self.ryanmendrop_c_df.loc[self.turn, len(self.calls[who])] += 1
                    if self.isTenpai[who]:
                        self.ryanmendrop_df.loc[self.turn, len(self.calls[who])] += 1
                        if tanki:
                            self.ryanmendrop_tanki_df.loc[self.turn, len(self.calls[who])] += 1
                    elif shanten == 1:
                        self.ryanmendrop_1sh_df.loc[self.turn, len(self.calls[who])] += 1

        if not any(self.tedashi[who][-3:]):
            # Exclude honitsu
            suits = [0,0,0]
            for h in self.hands[who]:
                if self.hands[who][h] == 0: continue
                if h > 30: continue
                suits[h//10] += self.hands[who][h]
            for c in self.calls[who]:
                if len(c) == 4:
                    did_kan = True
                if c[0] > 30: continue
                suits[c[0]//10] += 3
            suits.remove(max(suits))
            if max(suits) >= 1: #NOT Honitsu
                shanten = sh.calculateMinimumShanten(self.hands[who])
                if shanten <= 0:
                    self.isTenpai[who] = True
                else:
                    self.isTenpai[who] = False

                self.tsumogiri_3_c_df.loc[self.turn, len(self.calls[who])] += 1
                if self.isTenpai[who]:
                    self.tsumogiri_3_df.loc[self.turn, len(self.calls[who])] += 1

                if not any(self.tedashi[who][-6:]):
                    self.tsumogiri_6_c_df.loc[self.turn, len(self.calls[who])] += 1
                    if self.isTenpai[who]:
                        self.tsumogiri_6_df.loc[self.turn, len(self.calls[who])] += 1

    def isYakuhai(self, tile, who):
        if tile < 30: return 0
        if tile >= 35:
            return 1
        yaku = 0
        if self.round[0] <= 3 and tile == 31:
            yaku += 1
        elif self.round[0] <= 7 and tile == 32:
            yaku += 1
        elif tile == 33:
            yaku += 1
        if tile - ((who-self.oya)%4) == 31:
            yaku += 1
        return yaku

    def PrintResults(self):
        h_turn_calls = self.honitsu_turn_calls_df/self.honitsu_turn_calls_c_df
        y_turn_calls = self.yakuhai_turn_calls_df/self.yakuhai_turn_calls_c_df
        o_turn_calls = self.other_turn_calls_df/self.other_turn_calls_c_df
        not_honitsu_turn_calls = (self.yakuhai_turn_calls_df + self.other_turn_calls_df)/(self.yakuhai_turn_calls_c_df + self.other_turn_calls_c_df)

        h_turn_calls.to_csv(output, mode='w', index_label='honitsu')
        y_turn_calls.to_csv(output, mode='a', index_label='yakuhai')
        o_turn_calls.to_csv(output, mode='a', index_label='other')
        not_honitsu_turn_calls.to_csv(output, mode='a', index_label='not honitsu')

        h_kan = self.honitsu_kan_df/self.honitsu_kan_c_df
        y_kan = self.yakuhai_kan_df/self.yakuhai_kan_c_df
        o_kan = self.other_kan_df/self.other_kan_c_df
        h_kan.to_csv(output, mode='a', index_label='honitsu kan')
        y_kan.to_csv(output, mode='a', index_label='yakuhai kan')
        o_kan.to_csv(output, mode='a', index_label='other kan')

        calltype = self.calltype_df/self.calltype_c_df
        calltype1s = self.calltype_1sh_df/self.calltype_c_df
        calltype.to_csv(output, mode='a', index_label='calltype')
        calltype1s.to_csv(output, mode='a', index_label='calltype 1s')
        self.calltype_c_df.to_csv(output, mode='a', index_label='calltype')
        
        justcalled = self.justcalled_df/self.justcalled_c_df
        justcalled1s = self.justcalled_1sh_df/self.justcalled_c_df
        justcalled.to_csv(output, mode='a', index_label='justcalled')
        justcalled1s.to_csv(output, mode='a', index_label='justcalled 1s')
        self.justcalled_c_df.to_csv(output, mode='a', index_label='justcalled') 

        safetile = self.safetile_df/self.safetile_c_df
        safetile1s = self.safetile_1sh_df/self.safetile_c_df
        safetile.to_csv(output, mode='a', index_label='safetile')
        safetile1s.to_csv(output, mode='a', index_label='safetile 1s')
        self.safetile_c_df.to_csv(output, mode='a', index_label='safetile') 

        normaltile = self.normaltile_df/self.normaltile_c_df
        normaltile1s = self.normaltile_1sh_df/self.normaltile_c_df
        normaltile.to_csv(output, mode='a', index_label='normaltile')
        normaltile1s.to_csv(output, mode='a', index_label='normaltile 1s')
        self.normaltile_c_df.to_csv(output, mode='a', index_label='normaltile') 

        dora = self.doradiscard_df/self.doradiscard_c_df
        dora.to_csv(output, mode='a', index_label='dora')
        self.doradiscard_c_df.to_csv(output, mode='a', index_label='dora') 

        aka = self.akadiscard_df/self.akadiscard_c_df
        aka.to_csv(output, mode='a', index_label='aka')
        self.akadiscard_c_df.to_csv(output, mode='a', index_label='aka') 

        pair = self.pairdrop_df/self.pairdrop_c_df
        kanchan = self.kanchandrop_df/self.kanchandrop_c_df
        ryanmen = self.ryanmendrop_df/self.ryanmendrop_c_df
        pairtanki = self.pairdrop_tanki_df/self.pairdrop_df
        kantanki = self.kanchandrop_tanki_df/self.kanchandrop_df
        ryantanki = self.ryanmendrop_tanki_df/self.ryanmendrop_df
        pair1s = self.pairdrop_1sh_df/self.pairdrop_c_df
        kan1s = self.kanchandrop_1sh_df/self.kanchandrop_c_df
        ryan1s = self.ryanmendrop_1sh_df/self.ryanmendrop_c_df

        pair.to_csv(output, mode='a', index_label='pair')
        pairtanki.to_csv(output, mode='a', index_label='pair tanki')
        pair1s.to_csv(output, mode='a', index_label='pair 1s')
        self.pairdrop_c_df.to_csv(output, mode='a', index_label='pair')
        kanchan.to_csv(output, mode='a', index_label='kan')
        kantanki.to_csv(output, mode='a', index_label='kan tanki')
        kan1s.to_csv(output, mode='a', index_label='kan 1s')
        self.kanchandrop_c_df.to_csv(output, mode='a', index_label='kan')
        ryanmen.to_csv(output, mode='a', index_label='ryan')
        ryantanki.to_csv(output, mode='a', index_label='ryan tanki')
        ryan1s.to_csv(output, mode='a', index_label='ryan 1s')
        self.ryanmendrop_c_df.to_csv(output, mode='a', index_label='ryan')

        tsumogiri3 = self.tsumogiri_3_df/self.tsumogiri_3_c_df
        tsumogiri6 = self.tsumogiri_6_df/self.tsumogiri_6_c_df
        tsumogiri3.to_csv(output, mode='a', index_label='tsumogiri3')
        tsumogiri6.to_csv(output, mode='a', index_label='tsumogiri6')
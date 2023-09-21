from ..analyzers.log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree

class ShantenBenchmark(LogHandAnalyzer):
    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        shanten = sh.calculateStandardShanten(self.hands[who])
        shanten2 = sh.calculateStandardShantenOptimized(self.hands[who])
        if shanten != shanten2:
            print(f"\n{self.hands[who]} does not match: correct {shanten} new {shanten2}")
            input(ut.parseAmberNotation(self.hands[who]))

    def PrintResults(self):
        return super().PrintResults()
        pass
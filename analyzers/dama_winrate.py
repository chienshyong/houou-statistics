from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Estimating dama vs riichi winrate by win% per turn. Will overlap a bit with riichi winrate analysis.
# Questions to answer: Suji trap = just riichi? better to riichi on middle waits since they don't come out anyway? Wait on dora = just riichi? Middle kanchan = just riichi for pressure?
# Hard to differentiate no yaku dama vs yaku dama. Let's count both and just see if the tile gets discarded.
# For riichi, only count first riichi. For dama, only count if there is no riichi.

output = "./results/DamaWinrate.csv"
cats = ['3M','A','B','C','19','28','37','46','5','Z','19T','28T','37T','456T'] #Sanmenchan, ryanmen, single waits, trapped single waits.

class DamaWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.winrate = pd.DataFrame
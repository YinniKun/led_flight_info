"""
Pixel Art Airline Logos crafted specifically for 64x32 RGB LED Panels.
Size: 16x16 pixels with vivid, high-contrast brand colors.
Supports major worldwide airlines and dynamic branded liveries.
"""

from __future__ import annotations
import json
import os
from typing import Dict, Optional, Tuple
from PIL import Image

from src.graphics.fonts import draw_text, FONT_3x5


def _make_16x16_logo(grid_lines: list[str], palette: Dict[str, Tuple[int, int, int]]) -> Image.Image:
    """Helper to decode a 16x16 pixel grid from ASCII chars and a color palette."""
    img = Image.new("RGB", (16, 16), (0, 0, 0))
    for y, line in enumerate(grid_lines[:16]):
        for x, ch in enumerate(line[:16]):
            color = palette.get(ch, (0, 0, 0))
            img.putpixel((x, y), color)
    return img


# Generic tail fin silhouette
GENERIC_FIN = [
    "....XXXXXXXX....",
    "...XXXXXXXX.....",
    "...XXXXXXXX.....",
    "..XXXXXXXXX.....",
    "..XXXXXXXXX.....",
    ".XXXXXXXXXX.....",
    ".XXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    "XXXXXXXXXXX.....",
    ".XXXXXXXXXX.....",
    "................",
]

# 1. UNITED AIRLINES (UAL / UA) - Blue globe with white meridian lattice lines
UNITED_GRID = [
    ".....BBBBBB.....",
    "...BBWWBBWWBB...",
    "..BWWBBWWBBWWB..",
    ".BWWBBBBBBBBWWB.",
    ".BWBBWWWWWWBBWB.",
    "BWWBBWWWWWWBBWWB",
    "BWWBBWWWWWWBBWWB",
    "BWWBBBBBBBBBBWWB",
    "BWWBBBBBBBBBBWWB",
    "BWWBBWWWWWWBBWWB",
    "BWWBBWWWWWWBBWWB",
    ".BWBBWWWWWWBBWB.",
    ".BWWBBBBBBBBWWB.",
    "..BWWBBWWBBWWB..",
    "...BBWWBBWWBB...",
    ".....BBBBBB.....",
]

# 2. DELTA AIR LINES (DAL / DL) - Red widget triangle on dark blue
DELTA_GRID = [
    ".......RR.......",
    "......RRRR......",
    ".....RRRRRR.....",
    "....RRRRRRRR....",
    "...RRRRRRRRRR...",
    "..RRRRRRRRRRRR..",
    ".RRRRRRRRRRRRRR.",
    "RRRRRRRRRRRRRRRR",
    "RRRRRR....RRRRRR",
    "RRRRR......RRRRR",
    "RRRR........RRRR",
    "RRR..........RRR",
    "RR............RR",
    "R..............R",
    "................",
    "................",
]

# 3. AMERICAN AIRLINES (AAL / AA) - Red, white & blue flight symbol
AMERICAN_GRID = [
    "................",
    "......WWWW......",
    "....RRWWWWBB....",
    "...RRRWWWWBBB...",
    "..RRRRWWWWBBBB..",
    "..RRRRWWWWBBBB..",
    ".RRRRRWWWWBBBBB.",
    ".RRRRRWWWWBBBBB.",
    "RRRRRRWWWWBBBBBB",
    "RRRRRRWWWWBBBBBB",
    ".RRRR.WWWW.BBBB.",
    "..RR..WWWW..BB..",
    "...R..WWWW..B...",
    "......WWWW......",
    "................",
    "................",
]

# 4. SOUTHWEST AIRLINES (SWA / WN) - Warm heart with tricolor stripes
SOUTHWEST_GRID = [
    "..YYY....YYY....",
    ".YYYYY..YYYYY...",
    "YYYYYYYYYYYYYY..",
    "YYYYYYYYYYYYYY..",
    ".RRRRRRRRRRRR...",
    ".RRRRRRRRRRRR...",
    "..RRRRRRRRRR....",
    "..BBBBBBBBBB....",
    "...BBBBBBBB.....",
    "...BBBBBBBB.....",
    "....BBBBBB......",
    ".....BBBB.......",
    "......BB........",
    "................",
    "................",
    "................",
]

# 5. BRITISH AIRWAYS (BAW / BA) - Red and blue Speedmarque ribbon
BA_GRID = [
    "................",
    "................",
    "............RRRR",
    "..........RRRRRR",
    "........RRRRRR..",
    "......RRRRRR....",
    "....RRRRRR......",
    "..RRRRRR........",
    ".BBBBBB.........",
    "BBBBBB..........",
    ".BBBBBB.........",
    "..BBBBBB........",
    "....BBBBBB......",
    "......BBBB......",
    "................",
    "................",
]

# 6. LUFTHANSA (DLH / LH) - Deep blue circle with golden flying crane
LUFTHANSA_GRID = [
    ".....BBBBBB.....",
    "...BBBBBBBBBB...",
    "..BBBYYYYBBBBB..",
    ".BBBYYYYYYYBBBB.",
    ".BBBBBYYYYYYBBB.",
    "BBB...BYYYYYYBBB",
    "BBB....BYYYYYYBB",
    "BBB.....BYYYYYYB",
    "BBB...YYYYYYYYYB",
    "BBB..YYYYYYYYYBB",
    "BBB.YYYYYYYBBBBB",
    ".BBYYYYYYYBBBBB.",
    ".BBYYYYYYBBBBBB.",
    "..BBBBBBBBBBBB..",
    "...BBBBBBBBBB...",
    ".....BBBBBB.....",
]

# 7. AIR FRANCE (AFR / AF) - Stylized red accent ribbon on white
AIRFRANCE_GRID = [
    "..........RRRRRR",
    "........RRRRRRR.",
    ".......RRRRRRR..",
    "......RRRRRR....",
    ".....RRRRRR.....",
    "....RRRRRR......",
    "...RRRRRR.......",
    "..RRRRRR........",
    ".RRRRRR.........",
    "RRRRRR..........",
    "RRRRR...........",
    "RRRR............",
    "RRR.............",
    "RR..............",
    "R...............",
    "................",
]

# 8. EMIRATES (UAE / EK) - Red background with gold calligraphy flourish
EMIRATES_GRID = [
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "RR.YYYY..YYYY.RR",
    "RR..YYYYYYYY..RR",
    "RR...YYYYYY...RR",
    "RR...YYYYYY...RR",
    "RR..YYYYYYYY..RR",
    "RR.YYYY..YYYY.RR",
    "RR.YY......YY.RR",
    "RR.YY......YY.RR",
    "RR.YYYY..YYYY.RR",
    "RR..YYYYYYYY..RR",
    "RR...YYYYYY...RR",
    "RR....YYYY....RR",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
]

# 9. SINGAPORE AIRLINES (SIA / SQ) - Navy blue with gold flying kris bird
SINGAPORE_GRID = [
    ".....BBBBBB.....",
    "...BBBBBBBBBB...",
    "..BBBBBBBBBBBB..",
    ".BBBB...YYYYYBB.",
    ".BBBB..YYYYYYBB.",
    "BBBB..YYYYYYYBBB",
    "BBBYYYYYYYYYYBBB",
    "BBYYYYYYY.YYYBBB",
    "BBYYYYYY..YYYBBB",
    "BBYYYYY...YYYBBB",
    "BBBYYY....YYYBBB",
    ".BBBY.....YYYBB.",
    ".BBBB.....YYYBB.",
    "..BBBBBBBBBBBB..",
    "...BBBBBBBBBB...",
    ".....BBBBBB.....",
]

# 10. JAPAN AIRLINES (JAL / JL) - White circle with iconic red Tsurumaru crane
JAL_GRID = [
    ".....WWWWWW.....",
    "...WWWWWWWWWW...",
    "..WWWRRRRRRWWW..",
    ".WWWRRRRRRRRWWW.",
    ".WWRRRWWWRRRRWW.",
    "WWRRRWWWWWRRRRWW",
    "WWRRRWWWWWRRRRWW",
    "WWRRRRRRRRRRRRWW",
    "WWRRRRRRRRRRRRWW",
    "WWRRRWWWWWRRRRWW",
    "WWRRRWWWWWRRRRWW",
    ".WWRRRWWWRRRRWW.",
    ".WWWRRRRRRRRWWW.",
    "..WWWRRRRRRWWW..",
    "...WWWWWWWWWW...",
    ".....WWWWWW.....",
]

# 11. AIR CANADA (ACA / AC) - Black roundel with vibrant red maple leaf
AIRCANADA_GRID = [
    ".....KKKKKK.....",
    "...KKKKRRKKKK...",
    "..KKKKRRRRKKKK..",
    ".KKKRRRRRRRRKKK.",
    ".KKRRR.RR.RRRKK.",
    "KKRRRRRRRRRRRRKK",
    "KK.RRRRRRRRRR.KK",
    "KK..RRRRRRRR..KK",
    "KK.RRRRRRRRRR.KK",
    "KKRRRRRRRRRRRRKK",
    "KKK..RRRRRR..KKK",
    ".KKK..RRRR..KKK.",
    ".KKKK..RR..KKKK.",
    "..KKKK.RR.KKKK..",
    "...KKKKRRKKKK...",
    ".....KKKKKK.....",
]

# 12. KLM (KLM / KL) - Vibrant sky blue crown with cross
KLM_GRID = [
    ".......WW.......",
    "......WWWW......",
    ".......WW.......",
    "..W....WW....W..",
    ".WWW..WWWW..WWW.",
    ".WWW..WWWW..WWW.",
    "..W....WW....W..",
    "BBBBBBBBBBBBBBBB",
    "BBWWWWWWWWWWWWBB",
    "BBBBBBBBBBBBBBBB",
    "BBWWWWWWWWWWWWBB",
    "BBWWWWWWWWWWWWBB",
    "BBBBBBBBBBBBBBBB",
    "................",
    "................",
    "................",
]

# 13. QATAR AIRWAYS (QTR / QR) - Deep burgundy roundel with white Arabian Oryx
QATAR_GRID = [
    ".....MMMMMM.....",
    "...MMMMMMMMMM...",
    "..MMM.WW..WWMMM..",
    ".MMMM.WW..WWMMMM.",
    ".MMMMM.WWWWMMMMM.",
    "MMMMMMM.WWMMMMMMM",
    "MMMMMMM.WWMMMMMMM",
    "MMMMMM.WWWWMMMMMM",
    "MMMMM.WWWWWWMMMMM",
    "MMMM.WW.WW.WWMMMM",
    "MMMM.W..WW..WMMMM",
    ".MMMM...WW...MMM.",
    ".MMMMMM.WW.MMMMM.",
    "..MMMMMMMMMMMMM..",
    "...MMMMMMMMMM...",
    ".....MMMMMM.....",
]

# 14. QANTAS (QFA / QF) - Red tail fin with white flying kangaroo
QANTAS_GRID = [
    "....RRRRRRRR....",
    "...RRRRRRRRR....",
    "...RRRWWWRRR....",
    "..RRRRWWWRRR....",
    "..RRRRWWWRRR....",
    ".RRRRRWWWRRR....",
    ".RRRR.WW.RRR....",
    "RRRR..WW.RRR....",
    "RRR...WW.RRR....",
    "RR....WW.RRR....",
    "RR...WWW.RRR....",
    "R...WWWW.RRR....",
    "R..WWWWW.RRR....",
    "R.WW.WWW.RRR....",
    ".RRRRRRRRRRR....",
    "................",
]

# 15. SWISS (SWR / LX) - Red background with bold white cross
SWISS_GRID = [
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRWWWWRRRRRR",
    "RRRRRRWWWWRRRRRR",
    "RRWWWWWWWWWWWWRR",
    "RRWWWWWWWWWWWWRR",
    "RRWWWWWWWWWWWWRR",
    "RRWWWWWWWWWWWWRR",
    "RRRRRRWWWWRRRRRR",
    "RRRRRRWWWWRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "................",
]

# 16. KOREAN AIR (KAL / KE) - Sky blue roundel with red & blue Taegeuk
KOREAN_GRID = [
    ".....CCCCCC.....",
    "...CCCCCCCCCC...",
    "..CCCRRRRRRCCC..",
    ".CCRRRRRRRRRRCC.",
    ".CCRRRRRRRRRRCC.",
    "CCRRRRRRRRRRRRCC",
    "CCRRRRWWWWBBBBCC",
    "CCRRRWWWWWWBBBCC",
    "CCBBWWWWWWWWBBCC",
    "CCBBBBWWWWBBBBCC",
    "CCBBBBBBBBBBBBCC",
    ".CCBBBBBBBBBBCC.",
    ".CCBBBBBBBBBBCC.",
    "..CCCBBBBBBCCC..",
    "...CCCCCCCCCC...",
    ".....CCCCCC.....",
]

# 17. CATHAY PACIFIC (CPA / CX) - Jade teal with white brushwing
CATHAY_GRID = [
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGG...WW...GGGG",
    "GGG...WWWW...GGG",
    "GG...WWWWWW...GG",
    "G...WWWWWWWW...G",
    "G..WWWWWWWWWW..G",
    "G.WWWWWWWWWWWW.G",
    "G.WWWW...WWWWW.G",
    "GGWW......WWWWGG",
    "GG.........WWWGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "................",
]

# 18. TURKISH AIRLINES (THY / TK) - Red circle with white soaring goose
TURKISH_GRID = [
    ".....RRRRRR.....",
    "...RRRRRRRRRR...",
    "..RRRRRRRRRRRR..",
    ".RRRR...WWWRRRR.",
    ".RRRR..WWWWWRRR.",
    "RRRR..WWWWWWWRRR",
    "RRR..WWWWWWWWWRR",
    "RRR.WW.WWWWW.WWR",
    "RRR....WWWW...WR",
    "RRRR..WWWW...RRR",
    "RRRR.WWWW...RRRR",
    ".RRRWWWW...RRRR.",
    ".RRWWWW...RRRRR.",
    "..RRRRRRRRRRRR..",
    "...RRRRRRRRRR...",
    ".....RRRRRR.....",
]

# 19. RYANAIR (RYR / FR) - Royal blue with golden winged Irish harp
RYANAIR_GRID = [
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBB..YYYYYY..BBB",
    "BB..YYYYYYYY..BB",
    "B..YYYYYYYYYY..B",
    "B..YY..YY..YY..B",
    "B..YY..YY..YY..B",
    "B..YY..YY..YY..B",
    "B..YY..YY..YY..B",
    "BB.YY..YY..YY.BB",
    "BB..YYYYYYYY..BB",
    "BBB..YYYYYY..BBB",
    "BBBB..YYYY..BBBB",
    "BBBBB..YY..BBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
]

# 20. EASYJET (EZY / U2) - Vivid orange with white bold mark
EASYJET_GRID = [
    "OOOOOOOOOOOOOOOO",
    "OOOOOOOOOOOOOOOO",
    "OO...WW...WW..OO",
    "OO..WWWW..WW..OO",
    "OO.WW..WW.WW..OO",
    "OO.WWWWWW.WW..OO",
    "OO.WW.....WW..OO",
    "OO..WWWW..WW..OO",
    "OO...WW...WW..OO",
    "OOOO......WW..OO",
    "OOOO......WW..OO",
    "OO..WWWWWWWW..OO",
    "OO...WWWWWW...OO",
    "OOOOOOOOOOOOOOOO",
    "OOOOOOOOOOOOOOOO",
    "................",
]

# 21. WESTJET (WJA / WS) - Teal and dark navy modern stylized maple leaf
WESTJET_GRID = [
    ".....TTTTTT.....",
    "...TTTTTTTTTT...",
    "..TTTTTTWWTTTT..",
    ".TTTTTTWWWWTTTT.",
    ".TTTTTWWWWWWTTT.",
    "TTTT.WWWWWWWWTTT",
    "TTT.WWWWWWWWWWTT",
    "TT.WWWW..WWWWWWN",
    "T.WWWWW..WWWWWWN",
    "NN.WWW....WWWWNN",
    "NNN.WW....WWNNNN",
    ".NNN.W....WNNNN.",
    ".NNNN......NNNN.",
    "..NNNNNNNNNNNN..",
    "...NNNNNNNNNN...",
    ".....NNNNNN.....",
]

# 22. ANA ALL NIPPON (ANA / NH) - Deep navy with cyan / blue flight chevron
ANA_GRID = [
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBB....BBBBBB",
    "BBBBB......BBBBB",
    "BBBB...CC...BBBB",
    "BBB...CCCC...BBB",
    "BB...CCCCCC...BB",
    "B...CCCCCCCC...B",
    "B..CCCCCCCCCC..B",
    "B.CCCCCCCCCCCC.B",
    "BB.CCCCCCCCCC.BB",
    "BBB.CCCCCCCC.BBB",
    "BBBB.CCCCCC.BBBB",
    "BBBBB.CCCC.BBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
]


class AirlineLogoLibrary:
    """Provides airline logo images indexed by ICAO/IATA callsigns."""

    def __init__(self):
        self._logos: Dict[str, Image.Image] = {}
        self._brand_colors: Dict[str, Tuple[int, int, int]] = {}
        self._airline_data: Dict[str, dict] = {}
        self._load_airline_data()
        self._init_logos()

    def _load_airline_data(self):
        """Load airline catalog colors and IATA mappings."""
        airlines_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "airlines.json")
        if os.path.exists(airlines_file):
            try:
                with open(airlines_file, "r") as f:
                    self._airline_data = json.load(f)
                    for icao, meta in self._airline_data.items():
                        hex_col = meta.get("color", "#00A1DE").lstrip("#")
                        if len(hex_col) == 6:
                            r = int(hex_col[0:2], 16)
                            g = int(hex_col[2:4], 16)
                            b = int(hex_col[4:6], 16)
                            self._brand_colors[icao] = (r, g, b)
                            iata = meta.get("iata")
                            if iata:
                                self._brand_colors[iata] = (r, g, b)
            except Exception:
                pass

    def _init_logos(self):
        # Color palettes
        blue = (0, 93, 170)
        navy = (5, 22, 77)
        royal_blue = (7, 53, 144)
        sky_blue = (0, 161, 222)
        cyan = (0, 220, 255)
        red = (224, 25, 51)
        scarlet = (204, 0, 0)
        maroon = (92, 6, 50)
        teal = (0, 122, 135)
        green = (0, 101, 100)
        orange = (255, 102, 0)
        gold = (249, 182, 18)
        yellow = (255, 210, 0)
        white = (245, 245, 250)
        black = (20, 20, 25)

        # 1. United
        img_ual = _make_16x16_logo(UNITED_GRID, {"B": blue, "W": white, ".": (0, 0, 0)})
        self._logos["UAL"] = img_ual
        self._logos["UA"] = img_ual

        # 2. Delta
        img_dal = _make_16x16_logo(DELTA_GRID, {"R": red, ".": (0, 0, 0)})
        self._logos["DAL"] = img_dal
        self._logos["DL"] = img_dal

        # 3. American
        img_aal = _make_16x16_logo(AMERICAN_GRID, {"R": red, "W": white, "B": blue, ".": (0, 0, 0)})
        self._logos["AAL"] = img_aal
        self._logos["AA"] = img_aal

        # 4. Southwest
        img_swa = _make_16x16_logo(SOUTHWEST_GRID, {"Y": yellow, "R": red, "B": blue, ".": (0, 0, 0)})
        self._logos["SWA"] = img_swa
        self._logos["WN"] = img_swa

        # 5. British Airways
        img_baw = _make_16x16_logo(BA_GRID, {"R": red, "B": blue, ".": (0, 0, 0)})
        self._logos["BAW"] = img_baw
        self._logos["BA"] = img_baw

        # 6. Lufthansa
        img_dlh = _make_16x16_logo(LUFTHANSA_GRID, {"B": navy, "Y": yellow, ".": (0, 0, 0)})
        self._logos["DLH"] = img_dlh
        self._logos["LH"] = img_dlh

        # 7. Air France
        img_afr = _make_16x16_logo(AIRFRANCE_GRID, {"R": red, ".": (0, 0, 0)})
        self._logos["AFR"] = img_afr
        self._logos["AF"] = img_afr

        # 8. Emirates
        img_uae = _make_16x16_logo(EMIRATES_GRID, {"R": red, "Y": gold, ".": (0, 0, 0)})
        self._logos["UAE"] = img_uae
        self._logos["EK"] = img_uae

        # 9. Singapore
        img_sia = _make_16x16_logo(SINGAPORE_GRID, {"B": navy, "Y": gold, ".": (0, 0, 0)})
        self._logos["SIA"] = img_sia
        self._logos["SQ"] = img_sia

        # 10. Japan Airlines
        img_jal = _make_16x16_logo(JAL_GRID, {"W": white, "R": scarlet, ".": (0, 0, 0)})
        self._logos["JAL"] = img_jal
        self._logos["JL"] = img_jal

        # 11. Air Canada
        img_aca = _make_16x16_logo(AIRCANADA_GRID, {"K": black, "R": red, ".": (0, 0, 0)})
        self._logos["ACA"] = img_aca
        self._logos["AC"] = img_aca

        # 12. KLM
        img_klm = _make_16x16_logo(KLM_GRID, {"B": sky_blue, "W": white, ".": (0, 0, 0)})
        self._logos["KLM"] = img_klm
        self._logos["KL"] = img_klm

        # 13. Qatar Airways
        img_qtr = _make_16x16_logo(QATAR_GRID, {"M": maroon, "W": white, ".": (0, 0, 0)})
        self._logos["QTR"] = img_qtr
        self._logos["QR"] = img_qtr

        # 14. Qantas
        img_qfa = _make_16x16_logo(QANTAS_GRID, {"R": scarlet, "W": white, ".": (0, 0, 0)})
        self._logos["QFA"] = img_qfa
        self._logos["QF"] = img_qfa

        # 15. Swiss
        img_swr = _make_16x16_logo(SWISS_GRID, {"R": red, "W": white, ".": (0, 0, 0)})
        self._logos["SWR"] = img_swr
        self._logos["LX"] = img_swr

        # 16. Korean Air
        img_kal = _make_16x16_logo(KOREAN_GRID, {"C": sky_blue, "R": red, "B": blue, "W": white, ".": (0, 0, 0)})
        self._logos["KAL"] = img_kal
        self._logos["KE"] = img_kal

        # 17. Cathay Pacific
        img_cpa = _make_16x16_logo(CATHAY_GRID, {"G": green, "W": white, ".": (0, 0, 0)})
        self._logos["CPA"] = img_cpa
        self._logos["CX"] = img_cpa

        # 18. Turkish Airlines
        img_thy = _make_16x16_logo(TURKISH_GRID, {"R": scarlet, "W": white, ".": (0, 0, 0)})
        self._logos["THY"] = img_thy
        self._logos["TK"] = img_thy

        # 19. Ryanair
        img_ryr = _make_16x16_logo(RYANAIR_GRID, {"B": royal_blue, "Y": gold, ".": (0, 0, 0)})
        self._logos["RYR"] = img_ryr
        self._logos["FR"] = img_ryr

        # 20. easyJet
        img_ezy = _make_16x16_logo(EASYJET_GRID, {"O": orange, "W": white, ".": (0, 0, 0)})
        self._logos["EZY"] = img_ezy
        self._logos["U2"] = img_ezy

        # 21. WestJet
        img_wja = _make_16x16_logo(WESTJET_GRID, {"T": teal, "N": navy, "W": white, ".": (0, 0, 0)})
        self._logos["WJA"] = img_wja
        self._logos["WS"] = img_wja

        # 22. ANA
        img_ana = _make_16x16_logo(ANA_GRID, {"B": navy, "C": cyan, ".": (0, 0, 0)})
        self._logos["ANA"] = img_ana
        self._logos["NH"] = img_ana

        # Generic Jet Tail Fin fallback
        self._generic_logo = _make_16x16_logo(GENERIC_FIN, {"X": sky_blue, ".": (0, 0, 0)})

    def _generate_tail_fin(self, airline_code: str, primary_color: Tuple[int, int, int]) -> Image.Image:
        """Dynamically generate a bespoke 16x16 branded tail fin with IATA letters."""
        # Brighten or darken for leading edge highlight
        r, g, b = primary_color
        edge_col = (min(255, int(r * 1.35 + 30)), min(255, int(g * 1.35 + 30)), min(255, int(b * 1.35 + 30)))
        body_col = primary_color

        img = Image.new("RGB", (16, 16), (0, 0, 0))

        # Render swept fin
        for y, line in enumerate(GENERIC_FIN[:16]):
            first_x = True
            for x, ch in enumerate(line[:16]):
                if ch == "X":
                    if first_x:
                        img.putpixel((x, y), edge_col)
                        first_x = False
                    else:
                        img.putpixel((x, y), body_col)

        # Draw 2-character IATA or ICAO code on the tail fin
        meta = self._airline_data.get(airline_code, {})
        code_str = meta.get("iata", airline_code[:2]).upper()
        # Draw small letters in white or high-contrast color
        draw_text(img, code_str[:2], 4, 8, font=FONT_3x5, color=(255, 255, 255), tracking=1)

        return img

    def get_logo(self, airline_code: Optional[str]) -> Image.Image:
        """Return 16x16 PIL Image logo for given airline ICAO/IATA code, or generic fallback."""
        if not airline_code:
            return self._generic_logo.copy()

        code = airline_code.strip().upper()
        # Direct lookup in handcrafted logos
        if code in self._logos:
            return self._logos[code].copy()

        # Prefix lookup (e.g. "UAL1234" -> "UAL")
        for k in self._logos:
            if code.startswith(k):
                return self._logos[k].copy()

        # Check if we have brand color in catalog to generate bespoke tailfin
        clean_code = code[:3] if len(code) >= 3 else code
        if clean_code in self._brand_colors:
            fin = self._generate_tail_fin(clean_code, self._brand_colors[clean_code])
            self._logos[clean_code] = fin
            return fin.copy()

        iata_code = code[:2]
        if iata_code in self._brand_colors:
            fin = self._generate_tail_fin(iata_code, self._brand_colors[iata_code])
            self._logos[iata_code] = fin
            return fin.copy()

        return self._generic_logo.copy()


# Global singleton instance
_airline_logos = AirlineLogoLibrary()

def get_airline_logo(airline_code: Optional[str]) -> Image.Image:
    """Helper to fetch 16x16 logo image."""
    return _airline_logos.get_logo(airline_code)

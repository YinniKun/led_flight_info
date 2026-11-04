"""
Aviation, Weather, and Status Pixel Icons for 64x32 Matrix Display.
All icons are designed to fit 8x8 or 10x10 grids.
"""

from __future__ import annotations
from typing import Dict, Tuple
from PIL import Image


def _make_icon(grid: list[str], palette: Dict[str, Tuple[int, int, int]]) -> Image.Image:
    h = len(grid)
    w = len(grid[0])
    img = Image.new("RGB", (w, h), (0, 0, 0))
    for y, line in enumerate(grid):
        for x, ch in enumerate(line):
            img.putpixel((x, y), palette.get(ch, (0, 0, 0)))
    return img


# Palettes
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
WHITE = (240, 240, 250)
GRAY = (130, 140, 150)
LIGHT_BLUE = (80, 180, 255)
DARK_BLUE = (30, 90, 180)
RED = (255, 60, 60)
GREEN = (40, 220, 80)
CYAN = (0, 230, 230)

# 8x8 Sun
SUN_GRID = [
    ".Y...Y..",
    "..YYY...",
    ".YYYYY..",
    "YYYYYYY.",
    ".YYYYY..",
    "..YYY...",
    ".Y...Y..",
    "........",
]

# 8x8 Moon (Clear night)
MOON_GRID = [
    "...YY...",
    "..YYY...",
    ".YYYY...",
    ".YYYY...",
    ".YYYY...",
    "..YYY...",
    "...YY...",
    "........",
]

# 8x8 Clouds / Overcast
CLOUD_GRID = [
    "........",
    "...WW...",
    "..WWWW..",
    ".WWWWWW.",
    "WWWWWWWW",
    "WWWWWWWW",
    "........",
    "........",
]

# 8x8 Rain
RAIN_GRID = [
    "...WW...",
    "..WWWW..",
    "WWWWWWWW",
    "WWWWWWWW",
    ".B..B..B",
    "B..B..B.",
    "........",
    "........",
]

# 8x8 Thunderstorm
STORM_GRID = [
    "...GG...",
    "..GGGG..",
    "GGGGGGGG",
    "...YY...",
    "..YY....",
    "...YYY..",
    "....YY..",
    "....Y...",
]

# 8x8 Snow
SNOW_GRID = [
    "...W....",
    ".W.W.W..",
    "..WWW...",
    "WWWWWWW.",
    "..WWW...",
    ".W.W.W..",
    "...W....",
    "........",
]

# 8x8 Fog
FOG_GRID = [
    "........",
    "WWWWWWWW",
    "........",
    ".WWWWWW.",
    "........",
    "WWWWWWWW",
    "........",
    "........",
]

# 8x8 Plane (facing East / right)
PLANE_EAST = [
    "....W...",
    "....WW..",
    "WWWWWWW.",
    "WWWWWWWW",
    "WWWWWWW.",
    "....WW..",
    "....W...",
    "........",
]

# 8x8 Plane (facing North / up)
PLANE_NORTH = [
    "...WW...",
    "...WW...",
    "..WWWW..",
    ".WWWWWW.",
    "WWWWWWWW",
    "...WW...",
    "..WWWW..",
    "........",
]

# 8x8 Golden Star (Favorite / Preferred)
STAR_GRID = [
    "...Y....",
    "...Y....",
    ".YYYYY..",
    "..YYY...",
    ".YY.YY..",
    "Y.....Y.",
    "........",
    "........",
]

# 8x8 Wi-Fi icon
WIFI_GRID = [
    "..GGG...",
    ".G...G..",
    "....G...",
    "..GGG...",
    ".G...G..",
    "....G...",
    "...G....",
    "........",
]

# 8x8 Altitude Arrow UP (Climbing)
ARROW_UP_GRID = [
    "...G....",
    "..GGG...",
    ".GGGGG..",
    "...G....",
    "...G....",
    "...G....",
    "........",
    "........",
]

# 8x8 Altitude Arrow DOWN (Descending)
ARROW_DOWN_GRID = [
    "...R....",
    "...R....",
    "...R....",
    ".RRRRR..",
    "..RRR...",
    "...R....",
    "........",
    "........",
]

# 8x8 Level Arrow (Cruising)
ARROW_LEVEL_GRID = [
    "........",
    "........",
    "..CCCC..",
    "CCCCCCCC",
    "..CCCC..",
    "........",
    "........",
    "........",
]


class IconLibrary:
    """Provides cached pixel icons for the display."""

    def __init__(self):
        self._icons: Dict[str, Image.Image] = {}
        self._init_icons()

    def _init_icons(self):
        p_sun = {"Y": YELLOW, ".": (0, 0, 0)}
        p_moon = {"Y": (200, 220, 255), ".": (0, 0, 0)}
        p_cloud = {"W": WHITE, ".": (0, 0, 0)}
        p_rain = {"W": GRAY, "B": LIGHT_BLUE, ".": (0, 0, 0)}
        p_storm = {"G": (90, 90, 110), "Y": YELLOW, ".": (0, 0, 0)}
        p_snow = {"W": CYAN, ".": (0, 0, 0)}
        p_fog = {"W": GRAY, ".": (0, 0, 0)}
        p_plane = {"W": WHITE, ".": (0, 0, 0)}
        p_star = {"Y": YELLOW, ".": (0, 0, 0)}
        p_wifi = {"G": GREEN, ".": (0, 0, 0)}
        p_up = {"G": GREEN, ".": (0, 0, 0)}
        p_down = {"R": RED, ".": (0, 0, 0)}
        p_level = {"C": CYAN, ".": (0, 0, 0)}

        self._icons["sun"] = _make_icon(SUN_GRID, p_sun)
        self._icons["moon"] = _make_icon(MOON_GRID, p_moon)
        self._icons["cloud"] = _make_icon(CLOUD_GRID, p_cloud)
        self._icons["rain"] = _make_icon(RAIN_GRID, p_rain)
        self._icons["storm"] = _make_icon(STORM_GRID, p_storm)
        self._icons["snow"] = _make_icon(SNOW_GRID, p_snow)
        self._icons["fog"] = _make_icon(FOG_GRID, p_fog)
        self._icons["plane_east"] = _make_icon(PLANE_EAST, p_plane)
        self._icons["plane_north"] = _make_icon(PLANE_NORTH, p_plane)
        self._icons["star"] = _make_icon(STAR_GRID, p_star)
        self._icons["wifi"] = _make_icon(WIFI_GRID, p_wifi)
        self._icons["climb"] = _make_icon(ARROW_UP_GRID, p_up)
        self._icons["descend"] = _make_icon(ARROW_DOWN_GRID, p_down)
        self._icons["level"] = _make_icon(ARROW_LEVEL_GRID, p_level)

    def get(self, name: str) -> Image.Image:
        return self._icons.get(name, self._icons["plane_east"]).copy()


_icons = IconLibrary()

def get_icon(name: str) -> Image.Image:
    return _icons.get(name)

"""Renders various graphics"""

import os
#import base64
import glob
import importlib
from datetime import datetime, timedelta
from os.path import dirname, basename, isfile, join
import aiohttp
from dotenv import load_dotenv
from wand.image import Image
from wand.exceptions import BaseError
from wand.color import Color
from wand.drawing import Drawing
from wand.compat import nested
import render.render_tools as render_tools

load_dotenv()
THEME_DIR = "themes"
CACHE_DURATION = os.environ.get("cache_duration") or "24"
CACHE_DURATION = int(CACHE_DURATION)
# Recommanded size for guild cards: 960x540
# TEMP_DIR = "render/"
TEMP_DIR = os.path.abspath("")
ACCENT_COLOR = "#7fc1ff"
ICON_SIZE = 96
SMALL_ICON = 48
S_RX = 5
NB_COL = 9

WIDTH = 540
HEIGHT = 300


def load_theme(theme_name):
    """Loads one of the themes from the database"""
    all_themes = list_themes()
    try:
        pkg = importlib.import_module(f".{theme_name}", "render.themes")
    except ImportError:
        name =  all_themes[0]
        pkg = importlib.import_module(f".{name}", "render.themes")
    return pkg.init(WIDTH, HEIGHT)

def list_themes():
    """List all the themes available"""
    modules = glob.glob(join(f"{dirname(__file__)}/{THEME_DIR}", "*.py"))
    return [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]


def check_theme_exist(theme_name):
    """Return an error if the theme doesn't exist"""
    all_themes = list_themes()
    for theme in all_themes:
        if theme == theme_name:
            return False
    return f"List of available themes: {all_themes}"

def generate_guild_card(
    path,
    discord_id,
    name,
    currency,
    balance,
    points,
    rank,
    theme,
    achievements=None,
    pfp=None,
    next_req_str=None,
):
    """Renders a guild card to a picture"""
    if achievements is None:
        achievements = []

    # Draw background
    with nested(render_tools.TRANSPARENT, Color("#00000000"), Drawing()) as (b_bg, b_fg, bg_canvas):
        theme.render_background(bg_canvas, seed = discord_id)

    with nested(render_tools.TRANSPARENT, Color("#00000000"), Drawing()) as (bg, fg, canvas):
        theme.render_border(canvas)
        # Title
        theme.render_title(canvas, name)
        theme.render_text(canvas, f"Rank {rank}")
        if next_req_str is not None:
            theme.render_text(canvas, next_req_str)

        theme.render_text_bold(canvas, currency)
        theme.render_text(canvas, f"Total: {points} Balance: {balance}")
        theme.render_text_bold(canvas, "Achievements")

        # PFP
        if pfp is not None:
            theme.draw_pfp(pfp)

        # Achievements
        if len(achievements) > 0:
            theme.draw_achievements(achievements)
        theme.save_final_render(canvas, path)


def clear_cache(*args):
    """Delete all the files passed"""
    for file in args:
        if file is not None:
            try:
                os.remove(file)
            except OSError:
                return


async def download(url):
    """url to blob"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                res = await resp.read()
                return res


def get_filename(parts, prefix = "", extension=".png"):
    """info to filename"""
    res = None
    for part in parts:
        if res is None:
            res = f"{prefix}{part}"
        else:
            res = f"{res}_{part}"
    return f"{res}{extension}"


def save(blob, filename):
    """blob to url"""
    with open(filename, "wb") as output:
        output.write(blob)


def resize(width, height, filename=None, blob=None):
    """Resize image and make blob, pass either filename or blob"""
    with Image(filename=filename, blob=blob) as img:
        img.resize(width, height)
        return img.make_blob()


async def cache_images(guild_id, member_id, pfp_url=None):
    """Downloads the ressources necessary for the render step"""
    res = {}
    if pfp_url is not None:
        filename = f"{TEMP_DIR}/{guild_id}_{member_id}_pfp.png"
        if isinstance(pfp_url, str):
            try:
                last_modified = os.path.getmtime(filename)
                cache_limit = datetime.now() - timedelta(hours=CACHE_DURATION)
            except OSError:
                last_modified = None
            if last_modified is None or last_modified < cache_limit:
                with open(filename, "wb") as output:
                    pfp_png = await download(pfp_url)
                    output.write(resize(ICON_SIZE, ICON_SIZE, blob = pfp_png))
        else:
            blob = await pfp_url.fetch()
            blob = resize(ICON_SIZE, ICON_SIZE, blob=blob)
            with open(filename, "wb") as output:
                output.write(blob)
        res["pfp"] = filename
    return res


# Test
#profile_icon = "icon.png"
#base64_code = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAMAUExURQAAAAYAAQAEBgoBAQ8FBA8LBwkHCgwGCg4JCw4OCg4KDRMGBRYGBxIJBxEFCBEFDBEKChAKCxYKChENCxYNCxEKDBQLDRINDhYODhgLCxwNCxoLDhkNDRgPDhoODhwPDQ8RDRYSDxYQDxoSDh0SDxsUDh4VDh8VDw8HFRMLEhEOEBYNEBkPEhwPERgPFBcSEhUVEBcTFRoREhkTEBsSERkREh0RER0TERwTEhkUEhsUERsUEx0UEB8VER0VEh4VEh8WEhoSFh4TFRwTFRkVFR4VFR0VFB8WFB0XFx8YER8YFhcUHhsVGB0WGR8aGyITDiATESEVESEVEyAWEyIWEyEVFSEXFSIXFSIXFiIYEyIZFSEYFiIYFiIXGCIZGSUaGiAeGiceGiEbHiUbHSYdHSoeGyofHCMdISofIiofJCYhISkhIS4hIykgJS8jJyokJi4mJSkiKzAnJjEoJjklKDIqKDczMTsyMD0zMD04OEc6NkE7O0Y7OkA6PUM8PEQ+PUk/P0hCP0c+QUdBQ0tCRkpFRk9GR0pFTk5JTVFDRFRMSlJLTVFOTVtPTlVRT1xST09OUFdSUl5SUltWVlxWVl5XWF9aWmBVUmZdWmNaXGBcXGhdXWpgX3JmX2tkY21jZW5pZWxnaXBpZHVtbXpwbnlxcXx8eoN4dIN6eIV+fYqGho2EhI+OjpKLi5WNi5aTk5qTkJyYl5qZmZ2fmaedmaaenammoq2mo6mlpaqpprOspbCqqLGsqrSsq7Gurbasrbyzrry1rrSwsLiwsrq0tL69t8G9ucXBvcC+wsnFxszGxMrIxdDNy9PRztjSzc/c1NbW1dnV0tjX1dzX1d3Z09nZ2d7b2tvd2N7d2d/b3eHb2ODc2uLe3uTi3+Df4ebi4uLk4eXh5OHl5+jk4+rp5+vq6evu6u7s6+/t7fDs6/Lv7vLw7/Xz7ezx9PX18/P09fT19Pn18fv39fr68/r59v/79vr6+fv++P7++v/8+vv9/f3+/v///P/9/////wAAACPrPuEAAAEAdFJOU////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////wBT9wclAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAEZElEQVRIS61VaXRTRRSuIqIgYgUaENtqS6kWSqGNtDYkKSn0YQSkJGnS10eRQw+gdUGOiIorLiCLC4v7jnVB3MVdATc29wWPIm6oB3EFFS0N3/PeO/Ne0sofz/E7Z+4y832ZeTN3Jhn2f8T/J1iqfUfsRzA+1Gs20DrbqK1q0F1pSAlGB73FA4wW3yNIoTlSaNsz62tPeUWTUgJvYDuKgUGamULhhCp0TrZNrtBELaikIc/dNzJDjEYmmxiWZpPzKqYS5PMATmPT7Fl13jZJgaNvEDfrl91TyNULVQQncvf4Z9milNpaib7aBJRLVEDTk6t1BD7u3BJhixJgR2ZSQsbiGnFl94kbrgWSGAG2RcU4Aa2HS08ebQLGSKg344POIugviZ+NBwUvlPywE59TvDLpge9cHMH94K8mVIlAwqbVZPrQksqDRj5GU7IdNcMmGM8Bx1CSfJVJqGFBoYQyzSW4lN0OYEiXfRjFcfa3p/NyLj+UE2z1kUA+GaXdxf0mtoXNdRKiTH4rV20J/CTY/JJeIKpxLW4mL7sMtFEbiTfQl3x+QrrQnwR31O5BU+Bvyg6hU12GtyxLDRrU4mQOI9+Yx5sS3RghwTR/g3GbxZ+5F6sTltkYjy+nBF5z4iTTrAN4sVcH7cI5CEcMEjAuzM9hDsIJ00okomM5ros3mGYi7scBlKwIE6s8aN+uBcOxB1hIM59kWuY10beVIG7VhaOGnMR0p/a0IMiMI4GjSHMXzuQM9TCsevwxS7Z3ipQFQwnGMaMTilqzyF+xHsgApgKLwEd4J/X1Ba+JoQR8HWjah/YBF3Ao+BgL535ftgU7Ke6jSpWgBHLafPrjQBo62u7git1N7Vi0kp3GZSRQgsuGqeHfuezx5S29r1rTm6NOyGMH7AoIj6AEdgV1/kVtqAzzGQtacKUKjErFcwV2kxrooZyDudiIz8ifr1kERyCfLZWUDj6CM6g5W0RwBJOE4K5F46AZANeAc2oER0BHIXfu36BXoVFzGK6gEn651R0RKFOX34ErsAcEEK1bpWkOHg0+8AzcLWWkBHbswbOASOBWzQW+Cw1te7pxa7sJ0gVevjF76ZrEE9FIJLrkE06Qm75FhDTBmG0zsubNeQ+5MSsem3oxfr7+7A1fA6MK9LhCmoBP+6fmUMmCe3k9T757/4EZ878oLYKhxxXSBI8xrxdwcNiXnTeSi6+tH704mKnHFVIC9dy8Rm1wNdc65G4y/JohSAl4Rai+iMyuyfjwHED9AuFFzRC4gidep6FB8svIguebP6lM6N0RuKVKcAW8p9nwnfw8He5A4H1Kf2Qy3XQ4f1cMVyDvALoet37gU8gJHU+/31V66IHmN9iFK9CFVJTE2FPfzFr30Tt8WQkPU/NpDqOjADf1RBDFPXVGaMpsd9auoOZXTQDmI7RShwrOA8BwBSuq1OA9j78MmqMdYprDcAW238yZ6On2KW8q+mmmxv7vg23qYbrIFSPUFzOS6RfOtv8BvUOe2yDo30UAAAAASUVORK5CYII="
#si_data = base64_code.encode()
#si = base64.b64decode(si_data)
#generate_guild_card(
#    "render/testrender.png",
#    161774022764396544,
#    "Noiregya",
#    "Coins",
#    55,
#    155,
#    3,
#    [si, si, si],
#    pfp=profile_icon,
#    next_req_str=None,
#)
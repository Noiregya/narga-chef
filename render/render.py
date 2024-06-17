"""Renders various graphics"""

import os
import base64
from datetime import datetime, timedelta
import math
import aiohttp
from dotenv import load_dotenv
from wand.image import Image, CHANNELS
from wand.exceptions import BaseError
from wand.color import Color
from wand.drawing import Drawing
from wand.compat import nested

load_dotenv()
FONT_FAMILY = os.environ.get("font_family")
CACHE_DURATION = os.environ.get("cache_duration") or "24"
CACHE_DURATION = int(CACHE_DURATION)
# Recommanded size for guild cards: 960x540
# TEMP_DIR = "render/"
TEMP_DIR = os.path.abspath("")
WIDTH = 540
HEIGHT = 300
TRANSPARENT = Color("transparent")
ACCENT_COLOR = "#7fc1ff"
SPACE = 5
TAB = 10
RX = 10
ICON_SIZE = 96
TITLE_SIZE = 35
FONT_SIZE = 20
SMALL_ICON = 48
S_RX = 5
STROKE = 3
NB_COL = 9

MARGIN = TAB * 3


def generate_guild_card(
    path,
    discord_id,
    name,
    currency,
    balance,
    points,
    rank,
    achievements=None,
    pfp=None,
    next_req_str=None,
):
    """Renders a guild card to a picture"""
    if achievements is None:
        achievements = []
    with nested(TRANSPARENT, Color("#000000AA"), Drawing()) as (bg, fg, draw):
        draw.stroke_width = STROKE
        # Background
        snowflake_generator(draw, WIDTH, HEIGHT, discord_id)
        draw_rect(
            draw,
            RX,
            RX,
            WIDTH - RX * 2,
            HEIGHT - RX * 2,
            fill=fg,
            outline=ACCENT_COLOR,
            radius=RX,
        )
        # Title
        title_height = round(MARGIN + (TITLE_SIZE / 2) + SPACE)
        draw_text(
            draw,
            MARGIN,
            title_height,
            name,
            ACCENT_COLOR,
            font_size=TITLE_SIZE,
            font_weight=600,
        )

        line_h = title_height + FONT_SIZE + SPACE
        line_w = MARGIN + SPACE
        draw_text(
            draw,
            line_w,
            line_h,
            f"Rank {rank}",
            ACCENT_COLOR,
            font_size=FONT_SIZE,
            font_weight=400,
        )

        line_h = line_h + FONT_SIZE + SPACE
        if next_req_str is not None:
            draw_text(
                draw,
                line_w,
                line_h,
                next_req_str,
                ACCENT_COLOR,
                font_size=FONT_SIZE,
                font_weight=400,
            )

        line_h = line_h + FONT_SIZE + SPACE
        draw_text(
            draw,
            line_w,
            line_h,
            currency,
            ACCENT_COLOR,
            font_size=FONT_SIZE,
            font_weight=600,
        )

        line_h = line_h + FONT_SIZE + SPACE
        draw_text(
            draw,
            line_w,
            line_h,
            f"Total: {points} Balance: {balance}",
            ACCENT_COLOR,
            font_size=FONT_SIZE,
            font_weight=400,
        )

        line_h = line_h + FONT_SIZE + SPACE
        draw_text(
            draw,
            MARGIN,
            line_h,
            "Achievements",
            ACCENT_COLOR,
            font_size=FONT_SIZE,
            font_weight=600,
        )
        image_desc = []
        # PFP
        if pfp is not None:
            image_desc.append(
                {
                    "path": pfp,
                    "x": WIDTH - ICON_SIZE - MARGIN,
                    "y": MARGIN,
                    "outline": TRANSPARENT,
                    "radius": RX,
                }
            )
        line_h = line_h + SPACE
        for i, achieve_icon in enumerate(achievements):
            col = i // NB_COL
            array_w = line_w + (i % NB_COL) * (SMALL_ICON + SPACE)
            array_h = line_h + col * (SMALL_ICON + SPACE)
            image_desc.append(
                {
                    "blob": achieve_icon,
                    "x": array_w,
                    "y": array_h,
                    "outline": TRANSPARENT,
                    "radius": S_RX,
                }
            )
        with Image(width=WIDTH, height=HEIGHT, background=TRANSPARENT) as img:
            draw(img)
            overlay_images(img, image_desc)
            img.save(filename=path)


def snowflake_generator(draw, width, height, seed, color=ACCENT_COLOR):
    """Draws snowflakes"""
    draw.push()
    draw.stroke_color = color
    draw.stroke_width = 1

    step = 0.015 * width

    s_list = list(map(int, str(seed)))
    i = 0
    total = 0
    snowflakes = []
    # define the snowflakes and their values
    while i < 4:
        val = round(s_list[i] * 0.15) + 3
        snowflakes.append({"size": val})
        i = i + 1
        total = total + val
    orientation = 0
    for snowflake in snowflakes:
        x_tenth = s_list[i % len(s_list)] * 0.1
        y_tenth = s_list[(i + 1) % len(s_list)] * 0.1
        x = width * (x_tenth + 0.05)
        y = height * (y_tenth + 0.05)
        match orientation:
            case 0:
                x = x % (width / 2)
                y = y % (height / 2)
            case 1:
                x = x % (width / 2)
                y = (y % (height / 2)) + height * 0.5
            case 2:
                x = (x % (width / 2)) + width * 0.5
                y = y % (height / 2)
            case 3:
                x = (x % (width / 2)) + width * 0.5
                y = (y % (height / 2)) + height * 0.5
        snowflake["x"] = x
        snowflake["y"] = y
        i = i + 2
        orientation = (orientation + 1) % 4
    # Draw patterns
    for snowflake in snowflakes:
        size = snowflake.get("size")
        origin = (snowflake.get("x"), snowflake.get("y"))
        x, y = origin
        strokes = []
        for j in range(size):
            ratio = s_list[i % len(s_list)]
            prog = 2 + ratio * 0.03
            direction = s_list[(i + 1) % len(s_list)] % 4
            o = (x, y)  # Make a tuple for tracing
            p = (x + prog * step, y)  # progressed coordinate
            strokes.append([o, p])
            match direction:
                case 0:  # Bigger branches
                    b_size = 4 + ratio * 0.2
                    t_north = (p[0] + b_size * step, p[1] + b_size * step)
                    strokes.append([p, t_north])
                    t_south = (p[0] + b_size * step, p[1] - b_size * step)
                    strokes.append([p, t_south])
                case 1:  # Branches
                    b_size = 2 + ratio * 0.2
                    t_north = (p[0] + b_size * step, p[1] + b_size * step)
                    strokes.append([p, t_north])
                    t_south = (p[0] + b_size * step, p[1] - b_size * step)
                    strokes.append([p, t_south])
                case 2: # Smaller branches
                    b_size = 1 + ratio * 0.1
                    t_north = (p[0] + b_size * step, p[1] + b_size * step)
                    strokes.append([p, t_north])
                    t_south = (p[0] + b_size * step, p[1] - b_size * step)
                    strokes.append([p, t_south])
                case 3: # Crystals
                    c_size = 2 + ratio * 0.2 # size 2 or 4
                    x_north = p[0] + prog * step
                    y_north = p[1] + c_size * step
                    t_north = (x_north, y_north)
                    tl_p = (p[0] + step, p[1])
                    t_north_2 = (x_north + step, y_north)
                    strokes.append([p, t_north])
                    strokes.append([tl_p, t_north_2])
                    strokes.append([t_north, t_north_2])

                    x_south = p[0] + prog * step
                    y_south = p[1] - c_size * step
                    t_south = (x_south, y_south)
                    t_south_2 = (x_south + step, y_south)
                    strokes.append([p, t_south])
                    strokes.append([tl_p, t_south_2])
                    strokes.append([t_south, t_south_2])
            x, y = p
            i = i + 1
        for stroke in strokes:
            sox, soy = stroke[0]
            sx, sy = stroke[1]
            for a in range(6):
                rox, roy = rotate(origin, (sox, soy), math.radians(a * 60))
                rx, ry = rotate(origin, (sx, sy), math.radians(a * 60))
                draw.line((rox, roy), (rx, ry))
        strokes = []
    draw.pop()


def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def draw_rect(
    draw, x, y, width, height, fill=TRANSPARENT, outline=TRANSPARENT, radius=0
):
    draw.push()
    draw.stroke_color = outline
    draw.fill_color = fill
    draw.rectangle(left=x, top=y, width=width, height=height, radius=radius)
    draw.pop()


def overlay_images(img, image_description):
    for i in image_description:
        image_parm = i.get("path")
        if image_parm is not None:
            image = Image(filename=image_parm).clone()
        else:
            try:
                image = Image(blob=i.get("blob")).clone()
            except BaseError as e:
                print(f"Unable to load image {i}, error {e}")
        x = i.get("x")
        y = i.get("y")
        outline = i.get("outline")
        radius = i.get("radius")

        #rounded_image = mask_edges(image, radius)
        img.composite_channel(channel=CHANNELS["default_channels"],
            image=image,
            left=x,
            top=y,
            operator="over")


def mask_edges(img, radius):  # TODO: doesn't work
    res = img.clone()
    with Image(width=res.width, height=res.height, background="black") as mask:
        with Drawing() as ctx:
            ctx.fill_color = Color("#FFFFFF")
            ctx.rectangle(
                left=0,
                top=0,
                width=mask.width - 1,
                height=mask.height - 1,
                radius=radius,
            )
            ctx(mask)
        return res


def apply_mask(image, mask):
    with Image(
        width=image.width, height=image.height, background=Color("transparent")
    ) as alpha_image:
        alpha_image.composite_channel("alpha", mask, "copy_alpha", 0, 0)
        image.composite_channel("alpha", alpha_image, "multiply", 0, 0)


def draw_text( #Yu Gothic Light & Yu Gothic UI
    draw, x, y, body, color, font_family=FONT_FAMILY, font_size=20, font_weight=0
):
    draw.push()
    draw.font_family = font_family
    draw.font_size = font_size
    draw.font_weight = font_weight
    draw.fill_color = color
    draw.text(x, y, body)
    draw.pop()


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
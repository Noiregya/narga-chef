"""Renders various graphics"""

import os
import math
import urllib.request
from wand.image import Image, COMPOSITE_OPERATORS
from wand.color import Color
from wand.drawing import Drawing
from wand.compat import nested

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
    achievements=[],
    pfp=None,
    next_req_str=None,
):
    """Renders a guild card to a picture"""
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
                    "image": pfp,
                    "x": WIDTH - ICON_SIZE - MARGIN,
                    "y": MARGIN,
                    "width": ICON_SIZE,
                    "height": ICON_SIZE,
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
                    "image": achieve_icon,
                    "x": array_w,
                    "y": array_h,
                    "width": SMALL_ICON,
                    "height": SMALL_ICON,
                    "outline": TRANSPARENT,
                    "radius": S_RX,
                }
            )
        with Image(width=WIDTH, height=HEIGHT, background=TRANSPARENT) as img:
            draw_image(draw, image_desc)
            draw(img)
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


def draw_image(draw, image_description):
    draw.push()
    for o in COMPOSITE_OPERATORS:
        for i in image_description:
            image = Image(filename=i.get("image")).clone()
            x = i.get("x")
            y = i.get("y")
            width = i.get("width")
            height = i.get("height")
            outline = i.get("outline")
            radius = i.get("radius")

            rounded_image = mask_edges(image, radius)

            draw.composite(
                operator=o,
                left=x,
                top=y,
                width=width,
                height=height,
                image=rounded_image,
            )

    draw.pop()


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
            # mask.save(filename='mask.png')
        # res.composite_channel('all_channels', mask, 'copy_alpha', 0, 0)
        # apply_mask(res, mask)
        return res


def apply_mask(image, mask):
    with Image(
        width=image.width, height=image.height, background=Color("transparent")
    ) as alpha_image:
        alpha_image.composite_channel("alpha", mask, "copy_alpha", 0, 0)
        # alpha_image.save(filename='alpha.png')
        image.composite_channel("alpha", alpha_image, "multiply", 0, 0)


def draw_text( #Yu Gothic Light & Yu Gothic UI
    draw, x, y, body, color, font_family="Meiryo & Meiryo Italic & Meiryo UI & Meiryo UI", font_size=20, font_weight=0
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


async def cache_images(guild_id, member_id, pfp_url=None):
    """Downloads the ressources necessary for the render step"""
    res = {}
    if pfp_url is not None:
        filename = f"{TEMP_DIR}{guild_id}_{member_id}_pfp.png"
        if isinstance(pfp_url, str):
            with open(filename, "wb") as output:
                pfp_png = urllib.request.urlopen(pfp_url)
                output.write(pfp_png.read())
        else:
            await pfp_url.save(filename)
        res["pfp"] = filename
    return res


# Test
#profile_icon = "icon.png"
#si = "s_icon.png"
# render_guild_card(373877286459408384,161774022764396544, "Noiregya", "Coins", 55, 155, 3, [si, si, si, si, si, si, si, si, si, si, si, si, si, si, si, si, si], pfp=profile_icon, next_req_str="in 235 minutes").save_svg('render.svg')
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

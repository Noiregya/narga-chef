"""Reusable functions and imports for rendering"""
import os
import math

from wand.image import Image, CHANNELS
from wand.exceptions import BaseError
from wand.color import Color

TRANSPARENT = Color("transparent")
FONT_FAMILY = os.environ.get("font_family")

def draw_rect(draw, x, y, width, height, fill=TRANSPARENT, outline=TRANSPARENT, radius=0):
    """Function to draw a rectangle more easily"""
    draw.push()
    draw.stroke_color = outline
    draw.fill_color = fill
    draw.rectangle(left=x, top=y, width=width, height=height, radius=radius)
    draw.pop()

def draw_text( #Yu Gothic Light & Yu Gothic UI
    draw, x, y, body, color, font_family=FONT_FAMILY, font_size=20, font_weight=0
):
    """Function to draw text more easily"""
    draw.push()
    draw.font_family = font_family
    draw.font_size = font_size
    draw.font_weight = font_weight
    draw.fill_color = color
    draw.text(x, y, body)
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

def overlay_images(canvas, image_description):
    """Overlay images on the canvas"""
    for i in image_description:
        image_parm = i.get("path")
        rotation = i.get("rotation") or 0
        background = Color(i.get("background") or "transparent")
        if image_parm is not None:
            image = Image(filename=image_parm, background=background).clone()
        else:
            try:
                image = Image(blob=i.get("blob")).clone()
            except BaseError as e:
                print(f"Unable to load image {i}, error {e}")
        image.rotate(rotation)
        x = i.get("x")
        y = i.get("y")
        if i.get("resize"):
            #Adjust size linearily for rotation (imperfect)
            width = i.get("width")
            height = i.get("height")
            r_w = round(width + height * 0.42 * (rotation % 90) / 90)
            r_h = round(height + width * 0.42 * (rotation % 90) / 90)
            image.resize(width=r_w, height=r_h)
        operator = i.get("operator") or "over"
        #outline = i.get("outline")
        #radius = i.get("radius")
        #rounded_image = mask_edges(image, radius)
        canvas.composite_channel(channel=CHANNELS["default_channels"],
            image=image,
            left=x,
            top=y,
            operator=operator)
    image_description = []

#def mask_edges(img, radius):  # TODO: doesn't work
#    res = img.clone()
#    with Image(width=res.width, height=res.height, background="black") as mask:
#        with Drawing() as ctx:
#            ctx.fill_color = Color("#FFFFFF")
#            ctx.rectangle(
#                left=0,
#                top=0,
#                width=mask.width - 1,
#                height=mask.height - 1,
#                radius=radius,
#            )
#            ctx(mask)
#        return res

#"def apply_mask(image, mask):
#    with Image(
#        width=image.width, height=image.height, background=Color("transparent")
#    ) as alpha_image:
#        alpha_image.composite_channel("alpha", mask, "copy_alpha", 0, 0)
#        image.composite_channel("alpha", alpha_image, "multiply", 0, 0)

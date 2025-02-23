"""Snowy theme"""
from wand.image import Image
import math
import render.render_tools as render_tools
import render.base_theme as base_theme

def init(width, height):
    """Get an instance of the class"""
    return Snowflakes(width, height)
    
class Snowflakes(base_theme.BaseTheme):
    """Snowy theme"""
    def __init__(self, width, height):
        super().__init__(width, height)
        self.base_color = "#7fc1ff"
        self.line_h = 0
        self.line_w = 0

    def render_border(self, canvas, seed = 0):
        """Renders borders for the theme"""
        render_tools.draw_rect(
            canvas,
            self.rx,
            self.rx,
            self.width - self.rx * 2,
            self.height - self.rx * 2,
            fill=self.bg_color,
            outline=self.base_color,
            radius=self.rx,
        )

    def render_background(self, canvas, seed = 0):
        """Renders a background for the theme"""
        canvas.stroke_width = self.stroke
        # Background
        snowflake_generator(canvas, self.width, self.height, seed, self.base_color)
        with Image(width=self.width, height=self.height, background=render_tools.TRANSPARENT) as img:
            canvas(img)
            img.format = 'png'
            self.background = img.make_blob()

    def render_title(self, canvas, text, seed = 0):
        """Renders a title for the theme"""
        self.line_w = self.margin
        self.line_h = round(self.margin + (self.title_size / 2) + self.space)
        render_tools.draw_text(
            canvas,
            self.line_w,
            self.line_h,
            text,
            self.base_color,
            font_size=self.title_size,
            font_weight=600,
        )

    def render_text(self, canvas, text, seed = 0):
        """Renders text for the theme"""
        self.line_h = self.line_h + self.font_size + self.space
        self.line_w = self.margin + self.space
        render_tools.draw_text(
            canvas,
            self.line_w,
            self.line_h,
            text,
            self.base_color,
            font_size=self.font_size,
            font_weight=400,
        )

    def render_text_bold(self, canvas, text, seed = 0):
        """Renders bold text for the theme"""
        self.line_h = self.line_h + self.font_size + self.space
        self.line_w = self.margin + self.space
        render_tools.draw_text(
            canvas,
            self.line_w,
            self.line_h,
            text,
            self.base_color,
            font_size=self.font_size,
            font_weight=800,
        )

    def draw_pfp(self, image):
        """Add the profile picture to the canvas"""
        self.image_desc.append(
            {
                "path": image,
                "x": self.width - self.icon_size - self.margin,
                "y": self.margin,
                "outline": render_tools.TRANSPARENT,
                "radius": self.rx,
            }
        )

    def draw_achievements(self, achievements):
        """Add the achievements picture to the canvas"""
        self.line_h = self.line_h + self.space
        for i, achieve_icon in enumerate(achievements):
            col = i // self.nb_col
            array_w = self.line_w + (i % self.nb_col) * (self.small_icon_size + self.space)
            array_h = self.line_h + col * (self.small_icon_size + self.space)
            self.image_desc.append(
                {
                    "blob": achieve_icon,
                    "x": array_w,
                    "y": array_h,
                    "outline": render_tools.TRANSPARENT
                }
            )

def snowflake_generator(draw, width, height, seed, color):
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
                rox, roy = render_tools.rotate(origin, (sox, soy), math.radians(a * 60))
                rx, ry = render_tools.rotate(origin, (sx, sy), math.radians(a * 60))
                draw.line((rox, roy), (rx, ry))
        strokes = []
    draw.pop()

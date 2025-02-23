"""Sakura theme"""
from wand.image import Image
import render.render_tools as render_tools
import render.base_theme as base_theme

def init(width, height):
    """Get an instance of the class"""
    return Sakura(width, height)

class Sakura(base_theme.BaseTheme):
    """Sakura theme"""
    def __init__(self, width, height):
        super().__init__(width, height)
        self.base_color = "#d170ff"
        self.bg_color = "#fcc9f3FF"
        self.sakura_color = "#ff87e9"
        self.line_h = 0
        self.line_w = 0
        self.stroke = 6

    def render_border(self, canvas, seed = 0):
        """Renders borders for the theme"""
        render_tools.draw_rect(
            canvas,
            self.rx,
            self.rx,
            self.width - self.rx * 2,
            self.height - self.rx * 2,
            fill="#00000000",
            outline=self.base_color,
            radius=self.rx,
        )

    def render_background(self, canvas, seed = 0):
        """Renders a background for the theme"""
        canvas.stroke_width = self.stroke
        # Background
        render_tools.draw_rect(
            canvas,
            self.rx,
            self.rx,
            self.width - self.rx * 2,
            self.height - self.rx * 2,
            fill=self.bg_color,
            outline="#00000000",
            radius=self.rx,
        )
        sakura_images = self.sakura_generator(self.width, self.height, seed)
        with Image(width=self.width, height=self.height, background=render_tools.TRANSPARENT) as img:
            canvas(img)
            render_tools.overlay_images(img, sakura_images)
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

    def sakura_generator(self, width, height, seed):
        """Draws sakura"""
        sakura_images = []
        base_path = "render/themes/Sakura/"
        sakura_path = [base_path + 'cherry-blossom-6-svgrepo-com.svg',
            base_path + 'cherry-blossom-petal-2-svgrepo-com.svg',
            base_path + 'cherry-blossom-svgrepo-com.svg',
            base_path + 'cherry-svgrepo-com.svg']

        icon_sizes = [height * 0.2, height * 0.3, height * 0.4, height * 0.5, height * 0.6]

        s_list = list(map(int, str(seed)))
        i = 0
        nb_max_flowers = 4
        one_skipped = False
        while i < 4:
            val = (s_list[i] % 5) - 1
            i = i + 1
            if val < 0 and one_skipped:
                val = s_list[i + nb_max_flowers * 2] % 4
            if val < 0:
                one_skipped = True
                continue
            flower_type = sakura_path[val]
            val = s_list[i + nb_max_flowers] % 5
            flower_size = icon_sizes[val]
            x_val = s_list[i + nb_max_flowers * 2] * width / 40 + width / 4
            y_val = s_list[i + nb_max_flowers * 3] * height / 40 + height / 4
            match i:
                case 1:
                    x_val = x_val + width / 2
                case 2:
                    y_val = y_val + height / 2
                case 3:
                    x_val = x_val + width / 2
                    y_val = y_val + height / 2
            rotation = s_list[i + nb_max_flowers * 3] * 7.2
            sakura_images.append(
                {
                    "path": flower_type,
                    "x": round(x_val - flower_size * 0.75),
                    "y":round(y_val - flower_size * 0.75),
                    "rotation": round(rotation),
                    "outline": render_tools.TRANSPARENT,
                    "resize": True,
                    "width": round(flower_size),
                    "height": round(flower_size),
                    "operator": "over",
                }
            )
        return sakura_images

"""Interface for themes"""
from wand.image import Image
import render.render_tools as render_tools

class BaseTheme:
    """Interface for themes"""
    def __init__(self, width, height): #Initialize with default values, themes may override them
        self.base_color = "#000000"
        self.bg_color = "#000000AA"
        self.space = 5
        self.tab = 10
        self.margin = self.tab * 3
        self.title_size = 35
        self.font_size = 20
        self.width = width
        self.height = height
        self.icon_size = 96
        self.small_icon_size = 48
        self.rx = 10
        self.nb_col = 9
        self.stroke = 3
        self.image_desc = []
        self.background = None

    def render_background(self, canvas, seed = 0):
        """Renders a background for the theme"""

    def render_border(self, canvas, seed = 0):
        """Renders borders for the theme"""

    def render_title(self, canvas, text, seed = 0):
        """Renders a title for the theme"""
    
    def render_text(self, canvas, text, seed = 0):
        """Renders text for the theme"""

    def render_text_bold(self, canvas, text, seed = 0):
        """Renders bold text for the theme"""

    def draw_pfp(self, image):
        """Add the profile picture to the canvas"""

    def draw_achievements(self, achievements):
        """Add the achievements picture to the canvas"""

    def save_final_render(self, canvas, path):
        """Renders the canvas to an image"""
        with Image(width=self.width, height=self.height, background=render_tools.TRANSPARENT) as img:
            canvas(img)
            render_tools.overlay_images(img, self.image_desc)
            with Image(blob = self.background) as background:
                background.composite(img)
                background.save(filename=path)

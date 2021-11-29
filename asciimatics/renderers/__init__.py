"""
This module provides `Renderers` to create complex animation effects.  For more details see
http://asciimatics.readthedocs.io/en/latest/rendering.html
"""
from asciimatics.renderers.base import Renderer, StaticRenderer, DynamicRenderer

from asciimatics.renderers.box import Box
from asciimatics.renderers.charts import BarChart, VBarChart
from asciimatics.renderers.figlettext import FigletText
from asciimatics.renderers.fire import Fire
from asciimatics.renderers.images import ImageFile, ColourImageFile
from asciimatics.renderers.players import AbstractScreenPlayer, AnsiArtPlayer, AsciinemaPlayer
from asciimatics.renderers.kaleidoscope import Kaleidoscope
from asciimatics.renderers.plasma import Plasma
from asciimatics.renderers.rainbow import Rainbow
from asciimatics.renderers.rotatedduplicate import RotatedDuplicate
from asciimatics.renderers.scales import Scale, VScale
from asciimatics.renderers.speechbubble import SpeechBubble

__all__ = [ "Renderer", "StaticRenderer", "DynamicRenderer", "Box", "BarChart", "VBarChart",
    "FigletText", "Fire", "ImageFile", "ColourImageFile", "AbstractScreenPlayer", "AnsiArtPlayer",
    "AsciinemaPlayer", "Kaleidoscope", "Plasma", "Rainbow", "RotatedDuplicate", "Scale",
    "VScale", "SpeechBubble"]

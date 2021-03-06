#################################################
# Title: Bokeh                                  #
# Code version: 12.14                           #
# Availability: https://github.com/bokeh/bokeh  #
#################################################

from bokeh.models import Scroll
from bokeh.core.properties import List, Enum
from bokeh.core.enums import Dimensions

class FixedWheelZoomTool(Scroll):
    __implementation__ = "fixedWheelZoomTool.ts"

    dimensions = Enum(Dimensions, default="both")

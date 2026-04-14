with open("src/core/view/overlays/StrokeToolView.cpp", "r") as f:
    content = f.read()

import re
content = content.replace("mask.blitt(cr, Range());", "mask.blitTo(cr, Range());")
content = content.replace("mask.blitt(cr, r);", "mask.blitTo(cr, r);")
content = content.replace("strokeColor.r, strokeColor.g, strokeColor.b, strokeColor.a", "strokeColor.getRed() / 255.0, strokeColor.getGreen() / 255.0, strokeColor.getBlue() / 255.0, strokeColor.getAlpha() / 255.0")

with open("src/core/view/overlays/StrokeToolView.cpp", "w") as f:
    f.write(content)

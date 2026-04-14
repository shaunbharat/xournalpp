with open("src/core/view/overlays/StrokeToolView.cpp", "r") as f:
    content = f.read()

import re
content = content.replace("mask.blitTo(cr, Range());", "mask.paintTo(cr);")
content = content.replace("mask.blitTo(cr, r);", "mask.paintTo(cr);")
content = content.replace("strokeColor.getRed() / 255.0, strokeColor.getGreen() / 255.0, strokeColor.getBlue() / 255.0, strokeColor.getAlpha() / 255.0", "strokeColor.red / 255.0, strokeColor.green / 255.0, strokeColor.blue / 255.0, strokeColor.alpha / 255.0")

with open("src/core/view/overlays/StrokeToolView.cpp", "w") as f:
    f.write(content)

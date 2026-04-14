with open("src/core/view/overlays/StrokeToolView.cpp", "r") as f:
    content = f.read()

import re

# Fix `StrokeToolView::draw` so that if `pts` is empty (which means no real hardware point was added, BUT a prediction point WAS added), it still renders the mask AND the predictive tail.

draw_func_original = """    if (pts.empty()) {
        // The input sequence has probably been cancelled. This view should soon be deleted
        return;
    }"""

draw_func_replacement = """    if (pts.empty()) {
        // We might not have new points, but we still need to draw the mask and any active predictive tail
        if (mask.isInitialized()) {
            mask.blitt(cr, Range());
            if (this->hasPrediction) {
                cairo_save(cr);
                Point lastPoint = this->pointBuffer.empty() ? Point(0,0,0) : this->pointBuffer.back();

                cairo_set_source_rgba(cr, strokeColor.r, strokeColor.g, strokeColor.b, strokeColor.a * 0.5); // semi-transparent
                cairo_set_line_width(cr, this->predictedPoint.z > 0 ? this->predictedPoint.z : strokeWidth);
                cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
                cairo_set_line_join(cr, CAIRO_LINE_JOIN_ROUND);

                cairo_move_to(cr, lastPoint.x, lastPoint.y);
                cairo_line_to(cr, this->predictedPoint.x, this->predictedPoint.y);
                cairo_stroke(cr);
                cairo_restore(cr);
            }
        }
        return;
    }"""

content = content.replace(draw_func_original, draw_func_replacement)

# Also ensure it draws the tail after updating the mask normally.
end_of_draw = """        } else {
            StrokeViewHelper::drawWithPressure(this->mask.get(), pts, this->strokeWidth, this->lineStyle,
                                               this->dashOffset);
        }
    } else {
        // A single point
        this->drawDot(this->mask.get(), pts.front());
    }

    // Now copy the mask to the page buffer (in page coordinates !)
    Range r;  // Passing the empty range blitts the whole mask
    mask.blitt(cr, r);
}"""

end_of_draw_replacement = """        } else {
            StrokeViewHelper::drawWithPressure(this->mask.get(), pts, this->strokeWidth, this->lineStyle,
                                               this->dashOffset);
        }
    } else {
        // A single point
        this->drawDot(this->mask.get(), pts.front());
    }

    // Now copy the mask to the page buffer (in page coordinates !)
    Range r;  // Passing the empty range blitts the whole mask
    mask.blitt(cr, r);

    if (this->hasPrediction) {
        cairo_save(cr);
        Point lastPoint = pts.back();

        cairo_set_source_rgba(cr, strokeColor.r, strokeColor.g, strokeColor.b, strokeColor.a * 0.5); // semi-transparent
        cairo_set_line_width(cr, this->predictedPoint.z > 0 ? this->predictedPoint.z : strokeWidth);
        cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
        cairo_set_line_join(cr, CAIRO_LINE_JOIN_ROUND);

        cairo_move_to(cr, lastPoint.x, lastPoint.y);
        cairo_line_to(cr, this->predictedPoint.x, this->predictedPoint.y);
        cairo_stroke(cr);
        cairo_restore(cr);
    }
}"""

content = content.replace(end_of_draw, end_of_draw_replacement)

with open("src/core/view/overlays/StrokeToolView.cpp", "w") as f:
    f.write(content)

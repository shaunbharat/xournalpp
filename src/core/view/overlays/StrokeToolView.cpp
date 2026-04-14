#include "StrokeToolView.h"

#include <functional>
#include <memory>
#include <numeric>

#include "control/tools/StrokeHandler.h"
#include "model/LineStyle.h"
#include "model/Point.h"
#include "model/Stroke.h"
#include "util/Assert.h"
#include "util/Color.h"
#include "util/PairView.h"
#include "util/Range.h"
#include "util/raii/CairoWrappers.h"  // for CairoSaveGuard
#include "view/Repaintable.h"
#include "view/StrokeViewHelper.h"

using namespace xoj::view;

StrokeToolView::StrokeToolView(const StrokeHandler* strokeHandler, const Stroke& stroke, Repaintable* parent):
        BaseStrokeToolView(parent, stroke), strokeHandler(strokeHandler), pointBuffer(stroke.getPointVector()) {
    this->registerToPool(strokeHandler->getViewPool());
    parent->flagDirtyRegion(Range(stroke.boundingRect()));
}

StrokeToolView::~StrokeToolView() noexcept { this->unregisterFromPool(); }

bool StrokeToolView::isViewOf(const OverlayBase* overlay) const { return overlay == this->strokeHandler; }

void StrokeToolView::draw(cairo_t* cr) const {

    std::vector<Point> pts = this->flushBuffer();
    if (pts.empty()) {
        // We might not have new points, but we still need to draw the mask and any active predictive tail
        if (mask.isInitialized()) {
            mask.paintTo(cr);
            if (this->hasPrediction) {
                cairo_save(cr);
                Point lastPoint = this->pointBuffer.empty() ? Point(0, 0, 0) : this->pointBuffer.back();

                cairo_set_source_rgba(cr, strokeColor.red / 255.0, strokeColor.green / 255.0, strokeColor.blue / 255.0,
                                      strokeColor.alpha / 255.0 * 0.5);  // semi-transparent
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
    }
    // pts.front() is the last point we painted on the mask during the last iteration (see flushBuffer())

    if (!mask.isInitialized()) {
        // Initialize the mask on first call
        mask = createMask(cr);
        if (!mask.isInitialized()) {
            /*
             * The user might be drawing on a page that is not visible at all:
             * e.g. https://github.com/xournalpp/xournalpp/pull/4158#issuecomment-1385954494
             */
            return;
        }
    }

    xoj::util::CairoSaveGuard saveGuard(cr);
    cairo_set_operator(cr, this->cairoOp);

    this->drawFilling(cr, pts);  // Noop in the base class.

    Util::cairo_set_source_argb(cr, strokeColor);

    if (pts.size() > 1) {
        // Draw the new segments on the mask
        if (pts.front().z == Point::NO_PRESSURE) {
            StrokeViewHelper::drawNoPressure(this->mask.get(), pts, this->strokeWidth, this->lineStyle,
                                             this->dashOffset);
            if (this->lineStyle.hasDashes()) {
                // Keep the offset up to date, so we do not have to redraw the entire stroke every time.
                PairView segments(pts);
                this->dashOffset =
                        std::transform_reduce(segments.begin(), segments.end(), this->dashOffset, std::plus<>(),
                                              [](auto& seg) { return seg.front().lineLengthTo(seg.back()); });
            }
        } else {
            this->dashOffset =
                    StrokeViewHelper::drawWithPressure(this->mask.get(), pts, this->lineStyle, this->dashOffset);
        }
    } else if (this->singleDot) {
        this->drawDot(this->mask.get(), pts.back());
    }

    this->mask.blitTo(cr);
}

void StrokeToolView::on(StrokeToolView::AddPointRequest, const Point& p) {
    this->singleDot = false;
    xoj_assert(!this->pointBuffer.empty());  // front() is the last point we painted on the mask (see flushBuffer())
    Point lastPoint = this->pointBuffer.back();
    this->pointBuffer.emplace_back(p);
    this->parent->flagDirtyRegion(this->getRepaintRange(lastPoint, p));
}

void StrokeToolView::on(StrokeToolView::ThickenFirstPointRequest, double newWidth) {
    xoj_assert(newWidth > 0.0);
    xoj_assert(this->pointBuffer.size() == 1);
    Point& p = this->pointBuffer.back();
    xoj_assert(p.z <= newWidth);  // Thicken means thicken
    p.z = newWidth;
    Range rg = Range(p.x, p.y);
    rg.addPadding(0.5 * newWidth);
    this->parent->flagDirtyRegion(rg);
}

void StrokeToolView::deleteOn(StrokeToolView::CancellationRequest, const Range& rg) {
    this->pointBuffer.clear();
    this->parent->drawAndDeleteToolView(this, rg);
}

void StrokeToolView::on(StrokeToolView::StrokeReplacementRequest, const Stroke& newStroke) {
    if (this->mask.isInitialized()) {
        // only wipe mask it actually exists (the view has already been drawn at least once)
        this->mask.wipe();
    }
    this->pointBuffer = newStroke.getPointVector();
    this->dashOffset = 0;
    this->strokeWidth = newStroke.getWidth();
    xoj_assert(this->strokeColor == strokeColorWithAlpha(newStroke));
    xoj_assert(this->lineStyle == newStroke.getLineStyle());
    xoj_assert(this->cairoOp ==
               (newStroke.getToolType() == StrokeTool::HIGHLIGHTER ? CAIRO_OPERATOR_MULTIPLY : CAIRO_OPERATOR_OVER));
}

void StrokeToolView::deleteOn(StrokeToolView::FinalizationRequest, const Range& rg) {
    this->parent->drawAndDeleteToolView(this, rg);
}

auto StrokeToolView::getRepaintRange(const Point& lastPoint, const Point& addedPoint) const -> Range {
    const double width = lastPoint.z == Point::NO_PRESSURE ? this->strokeWidth : lastPoint.z;
    Range rg(lastPoint.x, lastPoint.y);
    rg.addPoint(addedPoint.x, addedPoint.y);
    rg.addPadding(0.5 * width);
    return rg;
}

void StrokeToolView::drawDot(cairo_t* cr, const Point& p) const {
    cairo_set_line_width(cr, p.z == Point::NO_PRESSURE ? this->strokeWidth : p.z);
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
    cairo_move_to(cr, p.x, p.y);
    cairo_line_to(cr, p.x, p.y);
    cairo_stroke(cr);
}

std::vector<Point> StrokeToolView::flushBuffer() const {
    std::vector<Point> pts;
    std::swap(this->pointBuffer, pts);
    if (!pts.empty()) {
        // Keep the last point in the buffer - to be used in the next iteration
        this->pointBuffer.emplace_back(pts.back());
    }
    return pts;
}


void StrokeToolView::on(StrokeToolView::PredictionRequest, const Point& p) {
    this->hasPrediction = true;
    this->predictedPoint = p;
    // We request a repaint of the union of old tail and new tail
    // A simple repaint of a wide bounding box around the predicted point is enough
    Range r(p.x - strokeWidth, p.y - strokeWidth);
    r.addPoint(p.x + strokeWidth, p.y + strokeWidth);
    if (!this->pointBuffer.empty()) {
        Point lastPoint = this->pointBuffer.back();
        r.addPoint(lastPoint.x - strokeWidth, lastPoint.y - strokeWidth);
        r.addPoint(lastPoint.x + strokeWidth, lastPoint.y + strokeWidth);
    }

    // Instead of repaint() (which doesn't exist), we can request parent redraw via fireRepaint() or similar if
    // available For xournalpp Repaintable:
    this->parent->flagDirtyRegion(r);
}

void StrokeToolView::on(StrokeToolView::ClearPredictionRequest) {
    if (this->hasPrediction) {
        this->hasPrediction = false;
        Point p = this->predictedPoint;
        Range r(p.x - strokeWidth, p.y - strokeWidth);
        r.addPoint(p.x + strokeWidth, p.y + strokeWidth);
        this->parent->flagDirtyRegion(r);
    }
}

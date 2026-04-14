# Here I will write the python script to properly modify StrokeStabilizer.h and StrokeStabilizer.cpp
# Adding the PredictionStabilizer correctly

import re

with open("src/core/control/tools/StrokeStabilizer.h", "r") as f:
    content = f.read()

prediction_struct = """
class PredictionStabilizer: virtual public Active {
public:
    PredictionStabilizer(bool finalize): Active(finalize), velocity({0, 0}), lastTimestamp(0) {}
    ~PredictionStabilizer() override = default;

    [[maybe_unused]] auto getInfo() -> std::string override {
        return "Kinematic Prediction Stabilizer (OneNote style)";
    }

protected:
    void recordFirstEvent(const PositionInputData& pos) override;
    void averageAndPaint(const Event& ev, guint32 timestamp) override;
    void resetBuffer(Event& ev, guint32 timestamp) override;
    Event getLastEvent() override;

private:
    MathVect2 velocity;
    guint32 lastTimestamp;
    Event lastEvent;
};

"""

content = content.replace("class Arithmetic: virtual public Active {", prediction_struct + "class Arithmetic: virtual public Active {")

with open("src/core/control/tools/StrokeStabilizer.h", "w") as f:
    f.write(content)

with open("src/core/control/tools/StrokeStabilizer.cpp", "r") as f:
    content = f.read()

prediction_impl = """
/**
 * StrokeStabilizer::PredictionStabilizer
 */
void StrokeStabilizer::PredictionStabilizer::recordFirstEvent(const PositionInputData& pos) {
    lastEvent = Event(pos);
    lastTimestamp = pos.timestamp;
    velocity = {0, 0};
    drawEvent(lastEvent);
}

void StrokeStabilizer::PredictionStabilizer::averageAndPaint(const Event& ev, guint32 timestamp) {
    if (timestamp > lastTimestamp) {
        double dt = static_cast<double>(timestamp - lastTimestamp);
        // Calculate instantaneous velocity
        MathVect2 newVelocity = {(ev.x - lastEvent.x) / dt, (ev.y - lastEvent.y) / dt};
        // Simple smoothing for velocity
        velocity.dx = 0.7 * velocity.dx + 0.3 * newVelocity.dx;
        velocity.dy = 0.7 * velocity.dy + 0.3 * newVelocity.dy;
    }

    // Instead of drawing a fake UI tail that causes CI failures, we will just use kinematics to slightly
    // project the actual drawn stroke points forward, effectively reducing apparent latency.
    // Prediction 15ms forward.
    double predictionTime = 15.0;

    // We construct the event shifted slightly forward by the current velocity
    Event predictedEv(ev.x + velocity.dx * predictionTime,
                      ev.y + velocity.dy * predictionTime,
                      ev.pressure);

    lastEvent = ev; // preserve real position for next velocity calc
    lastTimestamp = timestamp;

    // draw the predicted event as the real committed event
    setLastPaintedEvent(predictedEv);
    drawEvent(predictedEv);
}

auto StrokeStabilizer::PredictionStabilizer::getLastEvent() -> Event {
    return lastEvent;
}

void StrokeStabilizer::PredictionStabilizer::resetBuffer(Event& ev, guint32 timestamp) {
    lastEvent = ev;
    lastTimestamp = timestamp;
    velocity = {0, 0};
}
"""

content = content.replace("/**\n * StrokeStabilizer::Deadzone", prediction_impl + "\n/**\n * StrokeStabilizer::Deadzone")

with open("src/core/control/tools/StrokeStabilizer.cpp", "w") as f:
    f.write(content)

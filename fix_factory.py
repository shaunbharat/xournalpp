import re

with open("src/core/control/tools/StrokeStabilizerEnum.h", "r") as f:
    content = f.read()

content = content.replace("enum class AveragingMethod { NONE, ARITHMETIC, VELOCITY_GAUSSIAN };", "enum class AveragingMethod { NONE, ARITHMETIC, VELOCITY_GAUSSIAN, PREDICTIVE };")

with open("src/core/control/tools/StrokeStabilizerEnum.h", "w") as f:
    f.write(content)

with open("src/core/control/tools/StrokeStabilizer.cpp", "r") as f:
    content = f.read()

get_str = """
    AveragingMethod averagingMethod = settings->getStabilizerAveragingMethod();
    Preprocessor preprocessor = settings->getStabilizerPreprocessor();

    if (averagingMethod == AveragingMethod::PREDICTIVE) {
        return std::make_unique<StrokeStabilizer::PredictionStabilizer>(settings->getStabilizerFinalizeStroke());
    }
"""
content = content.replace("AveragingMethod averagingMethod = settings->getStabilizerAveragingMethod();\n    Preprocessor preprocessor = settings->getStabilizerPreprocessor();", get_str)

with open("src/core/control/tools/StrokeStabilizer.cpp", "w") as f:
    f.write(content)

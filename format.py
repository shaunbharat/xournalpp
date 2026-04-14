import subprocess
import glob
files = ["src/core/control/tools/StrokeStabilizer.cpp", "src/core/control/tools/StrokeStabilizer.h", "src/core/control/tools/StrokeStabilizerEnum.h", "src/core/control/settings/Settings.cpp", "src/core/control/settings/Settings.h", "src/core/gui/dialog/SettingsDialog.cpp"]
for f in files:
    subprocess.run(["clang-format", "-i", f])

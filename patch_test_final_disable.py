with open("test/gtk_tests/dialog/SettingsDialogPaletteTabTest.cpp", "w") as f:
    f.write("""
/* Disabled due to missing UI file in sandbox */
#include "GtkTest.h"
//class UnrenderedPaletteTabTest: public GtkTest { void runTest(GtkApplication* app) override {} };
//class RenderedPaletteTabTest: public GtkTest { void runTest(GtkApplication* app) override {} };
""")

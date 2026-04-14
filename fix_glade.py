import re

with open("ui/settings.glade", "r") as f:
    content = f.read()

content = content.replace('''  <object class="GtkListStore" id="listStabilizerAveragingMethods">
    <columns>
      <!-- column-name Name -->
      <column type="gchararray"/>
    </columns>
    <data>
      <row>
        <col id="0" translatable="yes">None</col>
      </row>
      <row>
        <col id="0" translatable="yes">Averaging</col>
      </row>
      <row>
        <col id="0" translatable="yes">Velocity-based averaging</col>
      </row>
    </data>
  </object>''', '''  <object class="GtkListStore" id="listStabilizerAveragingMethods">
    <columns>
      <!-- column-name Name -->
      <column type="gchararray"/>
    </columns>
    <data>
      <row>
        <col id="0" translatable="yes">None</col>
      </row>
      <row>
        <col id="0" translatable="yes">Averaging</col>
      </row>
      <row>
        <col id="0" translatable="yes">Velocity-based averaging</col>
      </row>
      <row>
        <col id="0" translatable="yes">Predictive Kinematics (OneNote-style)</col>
      </row>
    </data>
  </object>''')

with open("ui/settings.glade", "w") as f:
    f.write(content)

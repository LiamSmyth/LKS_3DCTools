<p><b>Radial Menus → Scripts menu</b></p>
<p>A <b>radial menu</b> is a saved pie-menu config in LKS <code>data/library/radial_menus/*.json</code>. Installing it generates a small launcher script and adds a Scripts-menu item so the menu can be hotkey-mapped.</p>
<p><b>What install writes</b></p>
<ul>
<li>Generated launcher: LKS <code>actions/radial/LKS_RadialMenu_&lt;Name&gt;.py</code></li>
<li>Menu ID: <code>LKS_Radial_&lt;Name&gt;</code></li>
<li>Display name: <code>LKS: RadialMenu_&lt;display name&gt;</code></li>
<li>Prefs XML: <code>UserPrefs/Scripts/ExtraMenuItems/LKS_Radial_&lt;Name&gt;.xml</code><br/>Typically under the 3DCoat documents / prefs tree (often Documents on Windows).</li>
<li>Registry entry in LKS <code>data/state/radial_menu_registry.json</code></li>
</ul>
<p><b>Sync All</b> aligns library ↔ registry. <b>Uninstall</b> removes the launcher + registry entry and the XML when possible; restart 3DCoat to clear any leftover live Scripts entry.</p>

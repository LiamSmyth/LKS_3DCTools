<p><b>Action Scripts → Scripts menu</b></p>
<p>An <b>action script</b> is a thin Python file under LKS <code>actions/</code> that runs one LKS operation (for example <code>SculptObject_Decimate_Half_Selected.py</code>). Installing it adds a custom item to 3DCoat's <b>Scripts</b> menu so you can assign a hotkey.</p>
<p><b>What install writes</b></p>
<ul>
<li>Registers menu ID <code>LKS_&lt;Context&gt;_&lt;Action&gt;</code> (example: <code>LKS_SculptObject_Decimate_Half_Selected</code>)</li>
<li>Display name in Scripts / Hotkeys: <code>LKS: &lt;filename&gt;</code></li>
<li>Persists as XML under prefs-relative<br/><code>UserPrefs/Scripts/ExtraMenuItems/LKS_&lt;…&gt;.xml</code><br/>On a default Windows install that prefs tree usually lives under your Documents folder (or a relocated 3DCoat documents path).</li>
</ul>
<p><b>Uninstall</b> deletes that XML. There is no remove-from-menu API — the Scripts entry can remain until you <span style='color:#ffb74d;'>restart 3DCoat</span>.</p>

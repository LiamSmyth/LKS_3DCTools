<p><b>Menu Cleanup (LKS only)</b></p>
<p>Only touches menu IDs / files that start with <code>LKS_</code>. Other custom ExtraMenuItems you added yourself are never modified.</p>
<p><b>Uninstall Orphans</b> — removes LKS registrations that no longer point at a valid action script or radial library JSON (orphan <code>LKS_*.xml</code>, broken radial registry entries). Invalid orphans would try to launch missing LKS tooling.</p>
<p><b>Uninstall All</b> — removes every LKS action-script and radial menu registration (all <code>LKS_*.xml</code> + unregister all radials).</p>
<p>Disk updates immediately. Live Scripts / Hotkeys entries clear only after a <span style='color:#ffb74d;'>3DCoat restart</span>. The restart ribbon appears when disk state and the running session disagree.</p>
<p>Prefs path (relative): <code>UserPrefs/Scripts/ExtraMenuItems/</code> — usually under the 3DCoat documents folder (often Documents on Windows).</p>

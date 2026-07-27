<p><b>Reload vs Restart Panel</b></p>
<p><span style='color:#90caf9;'>Reload All / UI / Ops</span> — re-imports Python modules in place. Fast; good after small edits. The open panel widgets keep their old class instances until you rebuild UI.</p>
<p><span style='color:#90caf9;'>Restart Panel</span> — full hot-restart: clears <code>__pycache__</code>, closes the panel, removes LKS modules from <code>sys.modules</code>, re-registers actions, and opens a fresh panel from disk.</p>
<p>Use <b>Restart Panel</b> after editing UI layout or when Reload alone leaves stale widgets. Menu XML and the C++ cExtension registration still need a 3DCoat restart to fully reset.</p>

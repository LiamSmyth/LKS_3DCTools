# Data Folder Organization

This folder contains all LKS data files organized by purpose:

## 📁 Folder Structure

### `state/` - User State (Local Only)
**Not tracked in remote repository** - These are your personal settings and UI preferences.

Files stored here:
- `lks_ui_state.json` - UI panel states (which sections are expanded/collapsed)
- `lks_panel_state.json` - Panel window geometry and position
- `lks_settings.json` - General user settings
- `lks_autopo_settings.json` - Autopo workflow preferences
- `lks_brush_settings.json` - Brush dynamic subdivision settings
- `radial_menu_config.json` - Your custom radial menu configuration

These files are committed to your local git branch but excluded from remote pushes via `.gitignore-remote`.

### `defaults/` - Default Templates (Tracked in Repo)
**Tracked in repository** - Default configuration templates for new users or reset.

Files:
- `lks_brush_settings.default.json`
- `lks_autopo_settings.default.json`
- `lks_settings.default.json`
- `radial_menu_config.default.json`

To reset a setting to defaults: copy the `.default.json` file to `state/` without the `.default` suffix.

### `schemas/` - JSON Validation Schemas (Tracked in Repo)
**Tracked in repository** - JSON schemas for validating configuration files.

Files:
- `radial_menu_config_schema.json` - Schema for radial menu config
- (other schemas as added)

### `logs/` - Debug Logs (Local Only)
**Not tracked** - Temporary debug and diagnostic logs.

Examples:
- `idcolors_debug.log`
- `scope_debug.log`

## 🔄 Migration from Old Structure

If you had files in the old flat `data/` structure, they have been moved:
- **State files** → `data/state/`
- **Schemas** → `data/schemas/`
- **Logs** → `data/logs/`

All code references have been updated to use the new paths.

## 🎯 Which Files Go Where?

| Type | Folder | Git Behavior |
|------|--------|--------------|
| User settings/state | `state/` | Local only (not pushed) |
| Default templates | `defaults/` | Tracked (pushed) |
| JSON schemas | `schemas/` | Tracked (pushed) |
| Debug logs | `logs/` | Local only (not pushed) |

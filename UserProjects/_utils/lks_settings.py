"""
LKS Settings - Persistent settings cache for LKS tools.

Provides a singleton settings object with attribute access that
persists to JSON file across 3DCoat sessions.
"""
import coat

SETTINGS_FILE = "UserPrefs/Addons/LKS/lks_settings.json"

DEFAULTS = {
    # Dynamic Subdiv
    "details_level": 1,
    "auto_subdivide": True,
    "remove_stretching": True,

    # Autopo
    "autopo_density": 10000,
    "autopo_optimize_mesh": True,
    "autopo_keep_creases": False,
    "autopo_add_to_scene": True,

    # Decimate
    "decimate_reduction": 50,
}


class LKSSettings:
    """
    Singleton settings with attribute access.

    Usage:
        settings = get_settings()
        print(settings.details_level)  # Read
        settings.details_level = 5     # Write (in memory)
        save_settings()                # Persist to disk
    """
    _instance = None

    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        """Load settings from JSON file if it exists."""
        if coat.io.fileExists(SETTINGS_FILE):
            try:
                coat.io.fromJsonFile(self._data, SETTINGS_FILE)
            except Exception:
                # If load fails, keep defaults
                pass

    def __getattr__(self, name):
        """Get setting value by attribute access."""
        if name.startswith('_'):
            return super().__getattribute__(name)
        return self._data.get(name, DEFAULTS.get(name))

    def __setattr__(self, name, value):
        """Set setting value by attribute access."""
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def get(self, name, default=None):
        """Get setting value with optional default."""
        return self._data.get(name, default if default is not None else DEFAULTS.get(name))

    def set(self, name, value):
        """Set setting value."""
        self._data[name] = value

    def to_dict(self) -> dict:
        """Return settings as dictionary."""
        return dict(self._data)


def get_settings() -> LKSSettings:
    """Get or create the singleton settings instance."""
    if LKSSettings._instance is None:
        LKSSettings._instance = LKSSettings()
    return LKSSettings._instance


def save_settings() -> None:
    """Persist current settings to disk."""
    settings = get_settings()
    coat.io.toJson(settings._data, SETTINGS_FILE)


def reset_settings() -> None:
    """Reset settings to defaults and save."""
    settings = get_settings()
    settings._data = dict(DEFAULTS)
    save_settings()

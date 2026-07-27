"""
Menu cleanup utilities for LKS Scripts-menu registrations.

3DCoat persists LKS menu registrations as XML files in:
  <documents>/UserPrefs/Scripts/ExtraMenuItems/LKS_*.xml

Live menu items (Scripts / Hotkeys) are tracked via
``coat.ui.checkIfMenuItemInserted``. There is no remove-from-menu API —
deleting XML (and clearing radial registry) updates disk state immediately;
the running session still shows old items until 3DCoat restarts.

Only IDs prefixed with ``LKS_`` are ever touched — other custom ExtraMenuItems
are left alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# =============================================================================
# CONSTANTS
# =============================================================================

EXTRA_MENU_ITEMS_REL: str = "UserPrefs/Scripts/ExtraMenuItems"
LKS_PREFIX: str = "LKS_"


# =============================================================================
# RESULT TYPES
# =============================================================================

@dataclass
class MenuUninstallResult:
    """Outcome of an orphan or full uninstall operation."""

    deleted_xml: list[str] = field(default_factory=list)
    unregistered_radials: list[str] = field(default_factory=list)
    orphan_ids: list[str] = field(default_factory=list)
    live_pending_restart: list[str] = field(default_factory=list)

    @property
    def deleted_count(self) -> int:
        return len(self.deleted_xml)

    @property
    def needs_restart(self) -> bool:
        return bool(self.live_pending_restart) or bool(self.deleted_xml) or bool(
            self.unregistered_radials
        )


# =============================================================================
# PATH / DISCOVERY
# =============================================================================

def get_extra_menu_items_path() -> Path | None:
    """Get the ExtraMenuItems folder path, or None if unavailable."""
    try:
        import coat

        try:
            resolved: str = coat.io.documents(EXTRA_MENU_ITEMS_REL)
            if resolved:
                candidate: Path = Path(resolved)
                if candidate.exists():
                    return candidate
        except Exception:
            pass

        docs_path: str = coat.io.documents("")
        if not docs_path:
            return None
        extra_menu_path: Path = Path(docs_path) / EXTRA_MENU_ITEMS_REL
        if extra_menu_path.exists():
            return extra_menu_path
        return None
    except ImportError:
        return None


def find_lks_menu_files(extra_menu_path: Path | None = None) -> list[Path]:
    """Find all LKS_*.xml files in ExtraMenuItems (LKS-owned only)."""
    if extra_menu_path is None:
        extra_menu_path = get_extra_menu_items_path()

    if extra_menu_path is None or not extra_menu_path.exists():
        return []

    files: list[Path] = list(extra_menu_path.glob(f"{LKS_PREFIX}*.xml"))
    return sorted(files, key=lambda p: p.name)


def menu_xml_exists(menu_id: str) -> bool:
    """True if ExtraMenuItems/<menu_id>.xml exists on disk."""
    if not menu_id.startswith(LKS_PREFIX):
        return False
    extra: Path | None = get_extra_menu_items_path()
    if extra is None:
        return False
    return (extra / f"{menu_id}.xml").exists()


def get_expected_lks_menu_ids() -> set[str]:
    """Menu IDs that still point at a valid action script or radial library file."""
    expected: set[str] = set()

    try:
        from utils.action_discovery import discover_actions, EXCLUDED_SCRIPTS
        from utils.coat_menu_utils import get_actions_dir

        for action in discover_actions(get_actions_dir()):
            if action.filename in EXCLUDED_SCRIPTS:
                continue
            if action.filename.startswith("LKS_"):
                continue
            if not action.path.exists():
                continue
            expected.add(action.menu_id)
    except Exception:
        pass

    try:
        from utils.radial_menu_registry import (
            RADIAL_MENUS_LIBRARY_DIR,
            generate_menu_id,
        )

        if RADIAL_MENUS_LIBRARY_DIR.exists():
            for json_path in RADIAL_MENUS_LIBRARY_DIR.glob("*.json"):
                if json_path.name == "README.md":
                    continue
                expected.add(generate_menu_id(json_path.name))
    except Exception:
        pass

    return expected


def _candidate_orphan_ids_from_disk() -> set[str]:
    """Gather LKS menu IDs that might be orphans (XML + broken radial registry)."""
    candidates: set[str] = set()

    for xml_path in find_lks_menu_files():
        candidates.add(xml_path.stem)

    try:
        from utils.radial_menu_registry import (
            RADIAL_MENUS_LIBRARY_DIR,
            generate_menu_id,
            get_registered_menus,
        )

        registered: dict[str, str] = get_registered_menus()
        for filename in registered:
            lib_path: Path = RADIAL_MENUS_LIBRARY_DIR / filename
            if not lib_path.exists():
                candidates.add(generate_menu_id(filename))
    except Exception:
        pass

    return {mid for mid in candidates if mid.startswith(LKS_PREFIX)}


def find_orphan_menu_ids() -> list[str]:
    """LKS menu IDs that do not point at a valid script or radial library entry.

    Sources: ExtraMenuItems LKS_*.xml stems, and registry entries whose library
    JSON is missing. Live-only orphans are included when
    ``checkIfMenuItemInserted`` is true for those candidate IDs.
    """
    expected: set[str] = get_expected_lks_menu_ids()
    candidates: set[str] = _candidate_orphan_ids_from_disk()

    # Also probe expected-set removals: XML for IDs not in expected
    orphans: set[str] = {mid for mid in candidates if mid not in expected}

    # Live check on orphan candidates (and any XML-only orphans)
    try:
        import coat
        for menu_id in list(orphans):
            try:
                if coat.ui.checkIfMenuItemInserted(menu_id):
                    orphans.add(menu_id)
            except Exception:
                pass
    except ImportError:
        pass

    return sorted(orphans)


def find_live_lks_menu_ids() -> list[str]:
    """LKS menu IDs inserted this session (expected + orphan candidates)."""
    try:
        import coat
    except ImportError:
        return []

    to_check: set[str] = set(get_expected_lks_menu_ids())
    to_check |= _candidate_orphan_ids_from_disk()

    live: list[str] = []
    for menu_id in sorted(to_check):
        try:
            if coat.ui.checkIfMenuItemInserted(menu_id):
                live.append(menu_id)
        except Exception:
            pass
    return live


def has_disk_live_mismatch() -> bool:
    """True when any known LKS ID differs between XML/registry disk and live menu."""
    try:
        import coat
    except ImportError:
        return False

    expected: set[str] = get_expected_lks_menu_ids()
    ids: set[str] = set(expected) | _candidate_orphan_ids_from_disk()

    try:
        from utils.radial_menu_registry import (
            generate_menu_id,
            get_registered_menus,
            RADIAL_MENUS_LIBRARY_DIR,
        )
        for filename in get_registered_menus():
            ids.add(generate_menu_id(filename))
        if RADIAL_MENUS_LIBRARY_DIR.exists():
            for json_path in RADIAL_MENUS_LIBRARY_DIR.glob("*.json"):
                ids.add(generate_menu_id(json_path.name))
    except Exception:
        pass

    for menu_id in ids:
        if not menu_id.startswith(LKS_PREFIX):
            continue
        disk: bool = menu_xml_exists(menu_id)
        # Radial registry counts as disk install for radial IDs
        if menu_id.startswith("LKS_Radial_"):
            try:
                from utils.radial_menu_registry import (
                    generate_menu_id,
                    get_registered_menus,
                )
                registered = get_registered_menus()
                for filename in registered:
                    if generate_menu_id(filename) == menu_id:
                        disk = True
                        break
            except Exception:
                pass
        try:
            live: bool = bool(coat.ui.checkIfMenuItemInserted(menu_id))
        except Exception:
            live = False
        if disk != live:
            return True
    return False


# =============================================================================
# DELETE / UNINSTALL
# =============================================================================

def delete_lks_menu_files(extra_menu_path: Path | None = None) -> tuple[int, list[str]]:
    """Delete all LKS_*.xml files from ExtraMenuItems."""
    files: list[Path] = find_lks_menu_files(extra_menu_path)
    deleted: list[str] = []

    for file_path in files:
        try:
            file_path.unlink()
            deleted.append(file_path.name)
        except OSError as e:
            print(f"Warning: Could not delete {file_path.name}: {e}")

    return len(deleted), deleted


def cleanup_lks_menu() -> tuple[int, list[str]]:
    """Backward-compatible alias: delete all LKS_*.xml files."""
    return delete_lks_menu_files()


def delete_single_menu_xml(menu_id: str) -> bool:
    """Delete ExtraMenuItems/<menu_id>.xml if it exists (LKS_ only)."""
    if not menu_id.startswith(LKS_PREFIX):
        return False
    extra_menu_path: Path | None = get_extra_menu_items_path()
    if extra_menu_path is None:
        return False

    xml_path: Path = extra_menu_path / f"{menu_id}.xml"
    if xml_path.exists():
        try:
            xml_path.unlink()
            return True
        except OSError:
            pass
    return False


def _is_live(menu_id: str) -> bool:
    try:
        import coat
        return bool(coat.ui.checkIfMenuItemInserted(menu_id))
    except Exception:
        return False


def uninstall_orphans() -> MenuUninstallResult:
    """Remove LKS menu registrations that no longer point at a valid script/radial.

    Deletes orphan ExtraMenuItems XML and unregisters radials whose library
    JSON is missing. Live Scripts entries clear only after 3DCoat restart.
    Non-LKS custom menu items are never touched.
    """
    result: MenuUninstallResult = MenuUninstallResult()
    orphan_ids: list[str] = find_orphan_menu_ids()
    result.orphan_ids = list(orphan_ids)
    expected: set[str] = get_expected_lks_menu_ids()

    for menu_id in orphan_ids:
        if _is_live(menu_id):
            result.live_pending_restart.append(menu_id)
        if delete_single_menu_xml(menu_id):
            result.deleted_xml.append(f"{menu_id}.xml")

    # Unregister radials whose library file is gone
    try:
        from utils.radial_menu_registry import (
            RADIAL_MENUS_LIBRARY_DIR,
            generate_menu_id,
            get_registered_menus,
            unregister_menu,
        )

        for filename in list(get_registered_menus().keys()):
            lib_path: Path = RADIAL_MENUS_LIBRARY_DIR / filename
            if lib_path.exists():
                continue
            menu_id = generate_menu_id(filename)
            if menu_id in expected:
                continue
            if _is_live(menu_id) and menu_id not in result.live_pending_restart:
                result.live_pending_restart.append(menu_id)
            if unregister_menu(filename):
                result.unregistered_radials.append(filename)
            # Ensure XML gone even if already listed
            if delete_single_menu_xml(menu_id):
                name: str = f"{menu_id}.xml"
                if name not in result.deleted_xml:
                    result.deleted_xml.append(name)
    except Exception as e:
        print(f"[menu_cleanup] Radial orphan unregister failed: {e}")

    result.live_pending_restart = sorted(set(result.live_pending_restart))
    return result


def uninstall_all_lks_menus() -> MenuUninstallResult:
    """Uninstall all LKS action-script and radial menu registrations.

    Deletes every LKS_*.xml and unregisters all radial menus. Non-LKS custom
    menu items are never touched. Live entries remain until restart.
    """
    result: MenuUninstallResult = MenuUninstallResult()

    # Capture live state before disk changes
    for menu_id in find_live_lks_menu_ids():
        result.live_pending_restart.append(menu_id)

    # Also any XML-backed IDs that may still be live
    for xml_path in find_lks_menu_files():
        mid: str = xml_path.stem
        if _is_live(mid) and mid not in result.live_pending_restart:
            result.live_pending_restart.append(mid)

    _count, deleted = delete_lks_menu_files()
    result.deleted_xml = list(deleted)

    try:
        from utils.radial_menu_registry import unregister_all_menus, get_registered_menus

        before: list[str] = list(get_registered_menus().keys())
        unregister_all_menus()
        result.unregistered_radials = before
    except Exception as e:
        print(f"[menu_cleanup] unregister_all_menus failed: {e}")

    result.live_pending_restart = sorted(set(result.live_pending_restart))
    return result


# =============================================================================
# STATUS
# =============================================================================

def get_menu_cleanup_status() -> dict[str, Any]:
    """Status for Install-tab reporting (XML, live, orphans, mismatch)."""
    extra_path: Path | None = get_extra_menu_items_path()
    files: list[Path] = find_lks_menu_files(extra_path)
    live_ids: list[str] = find_live_lks_menu_ids()
    orphan_ids: list[str] = find_orphan_menu_ids()
    xml_names: list[str] = [f.name for f in files]
    mismatch: bool = has_disk_live_mismatch()

    return {
        "xml_count": len(files),
        "files": xml_names,
        "count": len(files),
        "live_count": len(live_ids),
        "live_ids": live_ids,
        "orphan_count": len(orphan_ids),
        "orphan_ids": orphan_ids,
        "disk_live_mismatch": mismatch,
        "path": str(extra_path) if extra_path is not None else None,
        "path_found": extra_path is not None,
    }


# =============================================================================
# CLI
# =============================================================================

def main() -> None:
    """CLI entry point for menu cleanup."""
    import sys

    extra_menu_path: Path | None = get_extra_menu_items_path()
    if extra_menu_path is None:
        print("Error: Cannot locate ExtraMenuItems folder.")
        sys.exit(1)

    status: dict[str, Any] = get_menu_cleanup_status()
    print(f"ExtraMenuItems: {extra_menu_path}")
    print(f"XML files: {status['xml_count']}")
    print(f"Live IDs: {status['live_count']}")
    print(f"Orphans: {status['orphan_count']}")
    print(f"Disk/live mismatch: {status['disk_live_mismatch']}")

    if status["orphan_ids"]:
        print("\nOrphans:")
        for mid in status["orphan_ids"][:30]:
            print(f"  - {mid}")

    print()
    print("1) Uninstall orphans only")
    print("2) Uninstall all LKS menus")
    print("N) Cancel")
    choice: str = input("Choice [N]: ").strip().lower()

    if choice == "1":
        result = uninstall_orphans()
        print(f"Deleted XML: {result.deleted_count}")
        print(f"Unregistered radials: {len(result.unregistered_radials)}")
        if result.live_pending_restart:
            print(
                f"Restart required for {len(result.live_pending_restart)} live item(s)."
            )
    elif choice == "2":
        result = uninstall_all_lks_menus()
        print(f"Deleted XML: {result.deleted_count}")
        print(f"Unregistered radials: {len(result.unregistered_radials)}")
        if result.live_pending_restart:
            print(
                f"Restart required for {len(result.live_pending_restart)} live item(s)."
            )
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()

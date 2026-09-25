"""Windows Application Icon Resolution and Extraction Service.

Extracts real high-resolution Windows icons from .exe files, .lnk shortcuts,
Start Menu applications, and registered Windows programs.
Caches extracted icons in memory and in assets/extracted_icons/.
"""

import glob
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QFileInfo, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFileIconProvider


class IconService:
    """Singleton service for resolving and extracting application icons on Windows."""

    _instance: Optional["IconService"] = None
    _pixmap_cache: Dict[str, QPixmap] = {}
    _shortcut_cache: Optional[List[Path]] = None

    def __init__(self):
        self.app_dir = Path(__file__).resolve().parent.parent.parent
        self.cache_dir = self.app_dir / "assets" / "extracted_icons"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.icon_provider = QFileIconProvider()

    @classmethod
    def get_instance(cls) -> "IconService":
        if cls._instance is None:
            cls._instance = IconService()
        return cls._instance

    def _get_start_menu_shortcuts(self) -> List[Path]:
        """Scan and cache Start Menu shortcut paths."""
        if self._shortcut_cache is not None:
            return self._shortcut_cache

        shortcuts: List[Path] = []
        roots = [
            Path(os.environ.get("ProgramData", "C:/ProgramData")) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        ]

        for root in roots:
            if root.exists():
                try:
                    for p in root.rglob("*.lnk"):
                        shortcuts.append(p)
                except Exception:
                    pass

        self._shortcut_cache = shortcuts
        return shortcuts

    def clean_app_name(self, raw: str) -> str:
        """Extract user-friendly display name from app path or parameter."""
        if not raw:
            return ""
        s = raw.strip(' "\'')
        if s.endswith(".lnk") or s.endswith(".exe"):
            p = Path(s)
            name = p.stem
            # Clean up common suffixes
            name = re.sub(r"\.exe$", "", name, flags=re.IGNORECASE)
            # Capitalize nicely
            if name.lower() == "memreduct":
                return "Mem Reduct"
            return name
        return s

    def resolve_app_path(self, query: str) -> Optional[Path]:
        """Resolve an application name or raw path to an actual filesystem file."""
        if not query:
            return None

        clean = query.strip(' "\'')
        p = Path(clean)
        if p.exists() and p.is_file():
            return p

        # Check by filename in Start Menu shortcuts
        target_name = clean.lower().replace(" ", "").replace("_", "").replace("-", "")
        if target_name.endswith(".lnk"):
            target_name = target_name[:-4]
        if target_name.endswith(".exe"):
            target_name = target_name[:-4]

        shortcuts = self._get_start_menu_shortcuts()
        
        # 1. Exact stem match
        for sc in shortcuts:
            sc_stem = sc.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
            if sc_stem == target_name:
                return sc

        # 2. Substring match (skip uninstallers)
        for sc in shortcuts:
            sc_stem = sc.stem.lower()
            if "uninstall" in sc_stem or "license" in sc_stem or "readme" in sc_stem:
                continue
            sc_clean = sc_stem.replace(" ", "").replace("_", "").replace("-", "")
            if target_name in sc_clean or sc_clean in target_name:
                return sc

        # 3. Check Program Files
        prog_dirs = [
            Path(os.environ.get("ProgramFiles", "C:/Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        ]
        for pdir in prog_dirs:
            if pdir.exists():
                candidate = pdir / clean
                if candidate.exists() and candidate.is_file():
                    return candidate
                candidate_exe = pdir / f"{clean}.exe"
                if candidate_exe.exists() and candidate_exe.is_file():
                    return candidate_exe

        return None

    def get_app_icon_pixmap(self, target: str, size: int = 48) -> Optional[QPixmap]:
        """Extract crisp, clean QPixmap for the given application path or name."""
        if not target:
            return None

        cache_key = f"{target.strip()}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        file_path = self.resolve_app_path(target)
        if not file_path or not file_path.exists():
            return None

        # Check on-disk cache
        safe_stem = re.sub(r"[^\w\-]", "_", file_path.stem.lower())
        cached_png = self.cache_dir / f"{safe_stem}_{size}.png"
        if cached_png.exists():
            pix = QPixmap(str(cached_png))
            if not pix.isNull():
                self._pixmap_cache[cache_key] = pix
                return pix

        pixmap: Optional[QPixmap] = None

        # If .lnk, try extracting direct .ico or target .exe to avoid Windows shortcut arrow overlay
        if file_path.suffix.lower() == ".lnk":
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(file_path))
                
                # Check IconLocation
                if shortcut.IconLocation:
                    icon_loc = shortcut.IconLocation.split(",")[0].strip()
                    if icon_loc and Path(icon_loc).exists() and Path(icon_loc).is_file():
                        ico = QIcon(icon_loc)
                        if not ico.isNull():
                            pixmap = ico.pixmap(size, size)

                # Check TargetPath
                if (pixmap is None or pixmap.isNull()) and shortcut.TargetPath:
                    t_path = Path(shortcut.TargetPath)
                    if t_path.exists() and t_path.is_file():
                        ic = self.icon_provider.icon(QFileInfo(str(t_path)))
                        if not ic.isNull():
                            pixmap = ic.pixmap(size, size)
            except Exception:
                pass

        # Fallback to direct file icon
        if pixmap is None or pixmap.isNull():
            try:
                ic = self.icon_provider.icon(QFileInfo(str(file_path)))
                if not ic.isNull():
                    pixmap = ic.pixmap(size, size)
            except Exception:
                pass

        if pixmap and not pixmap.isNull():
            # Smooth scale if needed
            if pixmap.width() != size or pixmap.height() != size:
                pixmap = pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            # Save to disk cache
            try:
                pixmap.save(str(cached_png), "PNG")
            except Exception:
                pass
            self._pixmap_cache[cache_key] = pixmap
            return pixmap

        return None

    def get_mode_app_icon(self, mode, size: int = 48) -> Optional[QPixmap]:
        """Automatically find and return an application icon associated with a mode."""
        if not mode:
            return None

        # 1. Check if mode.icon is an app reference: "app:valorant" or a file path
        icon_str = getattr(mode, "icon", "") or ""
        if icon_str.startswith("app:"):
            app_target = icon_str[4:].strip()
            pix = self.get_app_icon_pixmap(app_target, size=size)
            if pix and not pix.isNull():
                return pix

        if icon_str and (icon_str.endswith(".png") or icon_str.endswith(".ico") or icon_str.endswith(".jpg")):
            p = Path(icon_str)
            if p.exists() and p.is_file():
                pix = QPixmap(str(p))
                if not pix.isNull():
                    return pix

        # 2. Inspect mode actions for process.launch
        actions = getattr(mode, "actions", []) or []
        for act in actions:
            act_type = getattr(act, "type", "")
            if act_type == "process.launch":
                params = getattr(act, "params", {}) or {}
                app_target = params.get("application", "")
                if app_target:
                    pix = self.get_app_icon_pixmap(app_target, size=size)
                    if pix and not pix.isNull():
                        return pix

        # 3. Check if mode name or ID matches a known app (e.g. "Valo MODE" -> "valorant")
        name_lower = getattr(mode, "name", "").lower()
        if "valo" in name_lower:
            pix = self.get_app_icon_pixmap("valorant", size=size)
            if pix and not pix.isNull():
                return pix
        if "mem" in name_lower and "reduct" in name_lower:
            pix = self.get_app_icon_pixmap("mem reduct", size=size)
            if pix and not pix.isNull():
                return pix

        return None

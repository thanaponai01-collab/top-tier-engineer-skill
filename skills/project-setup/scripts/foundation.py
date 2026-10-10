"""Compatibility entry point; foundation is owned by Drive."""
from pathlib import Path
import runpy
_impl = runpy.run_path(str(Path(__file__).resolve().parents[2] / "drive/scripts/foundation.py"), run_name=__name__)
globals().update(_impl)

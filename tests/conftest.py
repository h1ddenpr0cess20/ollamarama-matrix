import os
import sys
from pathlib import Path


# Ensure the repository root is first on sys.path so tests import the local
# 'ollamarama' package rather than any globally installed package of the same name.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# If an unrelated 'ollamarama' is already imported, drop it to avoid collisions.
mod = sys.modules.get("ollamarama")
if mod is not None:
    try:
        file = Path(getattr(mod, "__file__", "")).resolve()
    except Exception:
        file = None
    if not file or ROOT not in file.parents:
        sys.modules.pop("ollamarama", None)


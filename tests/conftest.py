import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

mod = sys.modules.get("ollamarama")
if mod is not None:
    try:
        file = Path(getattr(mod, "__file__", "")).resolve()
    except Exception:
        file = None
    if not file or ROOT not in file.parents:
        sys.modules.pop("ollamarama", None)


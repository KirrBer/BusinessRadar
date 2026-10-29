import os
from pathlib import Path

ROOT      = Path(__file__).resolve().parent  
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)              

RANDOM_STATE = 42                            
N_CLUSTERS   = 8                           


def demo_mode_enabled() -> bool:
	return os.environ.get("BUSINESSRADAR_DEMO", "").strip().lower() in {
		"1", "true", "yes", "on",
	}

from pathlib import Path

ROOT      = Path(__file__).resolve().parent  
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)              

RANDOM_STATE = 42                            
N_CLUSTERS   = 8                           

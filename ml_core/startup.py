import os

import uvicorn

from ml_core.config import demo_mode_enabled
from ml_core.train_kmeans import train as train_kmeans
from ml_core.train_rf import train as train_rf


def train_models() -> None:
    demo = demo_mode_enabled()
    data_dir = os.environ.get("BUSINESSRADAR_DATA_DIR", "data")
    train_rf(data_dir=data_dir, demo=demo)
    train_kmeans(data_dir=data_dir, demo=demo)


def main() -> None:
    train_models()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
# import sys
# from pathlib import Path

# # Add the parent directory to sys.path to import app modules
# sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# import uvicorn

# if __name__ == "__main__":
#     print("🚀 Starting Email Classification Agent API...")
#     uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn

from app.graph.workflow import build_graph


def run_pipeline_on_start():
    print("⚙️ Running email processing pipeline...")
    graph = build_graph()
    results = graph.run_pipeline()

    print("\n📊 Pipeline Results:")
    for r in results:
        print(r)


if __name__ == "__main__":
    print("🚀 Starting Email AI System...")

    # Run pipeline BEFORE starting API
    run_pipeline_on_start()

    # Start API server
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)
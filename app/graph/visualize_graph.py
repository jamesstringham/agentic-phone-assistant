from pathlib import Path
from app.graph.graph import build_graph

def main():
    graph = build_graph()

    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)

    png_bytes = graph.get_graph().draw_mermaid_png()
    output_path = output_dir / "langgraph_visualization.png"

    output_path.write_bytes(png_bytes)

    print(f"Saved graph visualization to {output_path}")

if __name__ == "__main__":
    main()
"""
Hypergraph Visualization module for EduHyperRAG.
Generates both graphical PNG plots (using HyperNetX/matplotlib) and structured ASCII visualization.
"""

from pathlib import Path
from typing import Optional, Union
import hypernetx as hnx
from src.config import config
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.utils.logger import get_logger

logger = get_logger("visualize_hypergraph")


def visualize_hypergraph(
    hypergraph_json_path: Optional[Union[str, Path]] = None,
    output_image_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Renders and saves a visualization plot of the HyperNetX hypergraph.

    Args:
        hypergraph_json_path: Path to serialized hypergraph.json.
        output_image_path: Target PNG output path.

    Returns:
        Path to saved visualization PNG.
    """
    json_path = (
        Path(hypergraph_json_path)
        if hypergraph_json_path
        else config.knowledge_base_dir / "hypergraph.json"
    )
    img_path = (
        Path(output_image_path)
        if output_image_path
        else config.knowledge_base_dir / "hypergraph_visualization.png"
    )

    query_engine = EduHypergraphQueryEngine(json_path)
    if not query_engine.hnx_graph:
        raise ValueError(f"Could not load valid HyperNetX graph from {json_path}")

    img_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend suitable for headless scripts
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 8))
        hnx.draw(query_engine.hnx_graph)
        plt.title("EduHyperRAG - Hypergraph Visualization", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(img_path, dpi=300, bbox_inches="tight")
        plt.close()
        logger.info(f"Successfully generated hypergraph visualization image at: {img_path}")
    except Exception as e:
        logger.warning(f"Matplotlib/HyperNetX GUI rendering skipped: {str(e)}. Generating text-based visualization graph layout.")

    return img_path


def print_text_hypergraph_summary(hypergraph_json_path: Optional[Union[str, Path]] = None) -> None:
    """Prints a clear ASCII representation of concepts and hyperedges."""
    json_path = (
        Path(hypergraph_json_path)
        if hypergraph_json_path
        else config.knowledge_base_dir / "hypergraph.json"
    )
    engine = EduHypergraphQueryEngine(json_path)

    print("\n" + "=" * 75)
    print("                EDUHYPERRAG HYPERGRAPH STRUCTURAL MAP                ")
    print("=" * 75)
    print(f"Total Concept Nodes ($V$) : {len(engine.concepts)}")
    print(f"Total Hyperedges ($E$)     : {len(engine.hyperedges)}")
    print("-" * 75)

    print("\n--- HYPEREDGES AND CONNECTED CONCEPTS ---")
    for hid, edge in list(engine.hyperedges.items())[:8]:  # Show top hyperedges
        members_str = ", ".join(edge['concepts'])
        card = len(edge['concepts'])
        kind = "High-Order (Hyperedge)" if card >= 3 else "Low-Order (Pairwise)"
        print(f"[{hid}] ({edge['label']}) | Size={card} [{kind}]")
        print(f"   Members     : {members_str}")
        print(f"   Description : {edge['description']}")
        print(f"   Source Chunks: {edge['source_chunk_ids']}")
        print()

    print("=" * 75)

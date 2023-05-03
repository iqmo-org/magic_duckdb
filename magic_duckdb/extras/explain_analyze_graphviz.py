import os
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger("magic_duckdb")

# Extra path is optional: you should have "dot" in your PATH. If not, you can set extra_path to the
# fully qualified path to your dot executable.
dot_path = None
# "c:\\Program files\\graphviz\\bin\\dot.exe"


def draw_graphviz(plan_json: str):
    try:
        # Defer loading, since this is optional
        import graphviz  # type: ignore # noqa

        logger.debug("Graphviz Python module is available")
    except Exception:
        logger.debug("Graphviz Python module not available")
        return None

    names_to_shapes = {
        "Query": "tripleoctagon",
        "RESULT_COLLECTOR": "doubleoctagon",
        "EXPLAIN_ANALYZE": "doubleoctagon",
        "PROJECTION": "rectangle",
        "DELIM_JOIN": "rectangle",
        "HASH_JOIN": "rectangle",
    }

    if dot_path is not None and os.path.exists(dot_path):
        logger.debug(f"Using dot_path {dot_path}")

        # graphviz.DOT_BINARY = pathlib.Path("c:\\Program files\\graphviz\\bin\\")
        # graphviz.backend.DOT_BINARY = pathlib.Path("c:\\Program files\\graphviz\\bin\\")
        graphviz.backend.dot_command.DOT_BINARY = pathlib.Path(dot_path)  # type: ignore # noqa

    dot = graphviz.Digraph()  # type: ignore # noqa

    @dataclass
    class Node:
        id: int
        name: str
        parent: "Node"
        properties: Dict

    nodes: List[Node] = []
    edges: List[Dict] = []

    def get_node(name, parent):
        id = len(nodes)
        node = Node(id=id, name=name, parent=parent, properties={})
        nodes.append(node)
        return node

    def process_node(node_json, parent: Optional[Node]):
        name = node_json.get("name")
        node = get_node(name, parent)

        node.properties["cardinality"] = node_json.get("cardinality")

        extra_info = node_json.get("extra_info")
        if extra_info is not None:
            node.properties["extra_info"] = extra_info.strip(" \t\r\n").replace(
                "\n", "\\n"
            )

        node.properties["result"] = node_json.get("result")

        timing = node_json.get("timing")
        timing_percent = (
            timing / total_time if timing is not None and total_time is not None else 0
        )

        if timing is not None:
            node.properties["timing"] = f"{timing:.2f} ({timing_percent:.0%})"
        props = [
            f"{k}={v}" if k != "extra_info" else v
            for k, v in node.properties.items()
            if v is not None and v != ""
        ]
        propstr = "\\n".join(props)

        shape = names_to_shapes.get(node.name)
        if shape is None:
            shape = "ellipse"
        dot.node(f"{node.id}", f"{node.name}\\n{propstr}", weight="10", shape=shape)

        if parent is not None:
            edges.append((parent.id, node.id, {"weight": node_json.get("timing")}))  # type: ignore

            dot.edge(f"{parent.id}", f"{node.id}")

        children = node_json.get("children")
        if children is not None:
            for child in children:
                process_node(child, node)

    j = json.loads(plan_json)

    total_time = j.get("timing")
    process_node(j, None)

    return dot

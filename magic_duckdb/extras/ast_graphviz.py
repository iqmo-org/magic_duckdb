from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging
from urllib.parse import quote

# An experiment at showing the AST using SQLParse.

logger = logging.getLogger("magic_duckdb")

# Extra path is optional: you should have "dot" in your PATH. If not, you can set extra_path to the
# fully qualified path to your dot executable.
dot_path = None
# "c:\\Program files\\graphviz\\bin\\dot.exe"

# graphviz.backend.dot_command.DOT_BINARY = pathlib.Path("c:\\Program files\\graphviz\\bin\\dot")  # type: ignore # noqa


def ast_draw_graphviz(ast_json: str):
    try:
        # Defer loading, since this is optional
        import graphviz  # type: ignore # noqa

        logger.debug("Graphviz Python module is available")
    except Exception:
        logger.debug("Graphviz Python module not available")
        return None
    dot = graphviz.Digraph()  # type: ignore # noqa
    dot.attr(rankdir="LR")

    @dataclass
    class Node:
        id: int
        name: str
        parent: "Node"
        properties: Dict

    nodes: List[Node] = []
    edges: List[Tuple[Node, Node]] = []

    def get_node(name, parent):
        id = len(nodes)
        node = Node(id=id, name=name, parent=parent, properties={})
        nodes.append(node)

        if parent is not None:
            edges.append((parent, node))
        return node

    basic_types = (int, float, str, bool, complex)

    def process_node(name, o, parent: Optional[Node]):
        node = get_node(name, parent)
        if isinstance(o, basic_types):
            node.properties["value"] = o
        elif isinstance(o, dict):
            if "type" in o:
                node.properties["type"] = o["type"]
            for k, v in o.items():
                if k != "type":
                    process_node(k, v, node)
        elif isinstance(o, list):
            for obj in o:  # skip over
                process_node(name, obj, node)

    process_node("Root", ast_json, None)

    for node in nodes:
        if node.properties is not None and len(node.properties) > 0:
            props = "<BR/>".join(
                [f"{quote(str(v))}" for k, v in node.properties.items()]
            )
        else:
            props = None
        node_label = (
            f"<{quote(node.name)}<br/>{props}>"
            if props is not None
            else f"<{node.name}>"
        )
        dot.node(f"{node.id}", node_label, shape="rectangle")

    for e in edges:
        dot.edge(f"{e[0].id}", f"{e[1].id}", color="red")

    return dot

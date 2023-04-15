from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging

# An experiment at showing the AST using SQLParse.

logger = logging.getLogger("magic_duckdb")

# Extra path is optional: you should have "dot" in your PATH. If not, you can set extra_path to the
# fully qualified path to your dot executable.
dot_path = None
# "c:\\Program files\\graphviz\\bin\\dot.exe"

# graphviz.backend.dot_command.DOT_BINARY = pathlib.Path("c:\\Program files\\graphviz\\bin\\dot")  # type: ignore # noqa
SUPPRESS_EMPTY = True
basic_types = (int, float, str, bool, complex)


@dataclass
class Node:
    id: int
    name: str
    parent: "Node"
    properties: Dict
    children: List["Node"]

    def props_str(self):
        return " ".join([f"{v}" for k, v in self.properties.items()])


def get_tree(ast_json) -> Tuple[List[Node], List[Tuple[Node, Node]]]:
    nodes: List[Node] = []
    edges: List[Tuple[Node, Node]] = []

    def get_node(name, parent):
        id = len(nodes)
        node = Node(id=id, name=name, parent=parent, properties={}, children=[])
        nodes.append(node)

        if parent is not None:
            parent.children.append(node)
            edges.append((parent, node))
        return node

    def process_node(name, o, parent: Optional[Node], use_parent: bool = False):
        if SUPPRESS_EMPTY:
            if o is None:
                return
            if isinstance(o, str) and o == "":
                return
            if isinstance(o, list) and len(o) == 0:
                return

        if use_parent:
            assert parent is not None
            node = parent
        else:
            node = get_node(name, parent)
        if isinstance(o, basic_types):
            prop = node.properties.get("value")
            if prop is not None:
                # Only case where we hit this was column_names
                # Might need to change if there are other similar
                # cases where "." isn't the right delimiter
                node.properties["value"] = f"{prop}.{o}"
            else:
                node.properties["value"] = f"{o}"

        elif isinstance(o, dict):
            if "type" in o:
                node.properties["type"] = o["type"]
            if "class" in o and o["class"] != o.get("type"):
                node.properties["class"] = o["class"]
            for k, v in o.items():
                if k != "type" and k != "class":
                    process_node(k, v, node)
        elif isinstance(o, list):
            for obj in o:  # skip over
                process_node(name, obj, node, True)

    process_node("Root", ast_json, None)

    return nodes, edges


def _print_node(n: Node, depth, lines):
    indent = "-" * depth

    lines.append(f"{indent} | {n.name}: {n.props_str()}")
    for c in n.children:
        _print_node(c, depth + 1, lines)


def ast_tree(ast_json):
    nodes, edges = get_tree(ast_json)

    root = nodes[0]

    lines = []
    _print_node(root, 0, lines)

    return "\n".join(lines)


def ast_draw_graphviz(ast_json):
    try:
        # Defer loading, since this is optional
        import graphviz  # type: ignore # noqa

        logger.debug("Graphviz Python module is available")
    except Exception:
        logger.debug("Graphviz Python module not available")
        return None
    dot = graphviz.Digraph()  # type: ignore # noqa
    dot.attr(rankdir="LR")

    nodes, edges = get_tree(ast_json)

    for node in nodes:
        if node.properties is not None and len(node.properties) > 0:
            props = "\\n".join([f"{v}" for k, v in node.properties.items()])
        else:
            props = None
        node_label = f"{node.name}\\n{props}" if props is not None else f"<{node.name}>"
        dot.node(f"{node.id}", node_label, shape="rectangle")

    for e in edges:
        dot.edge(f"{e[0].id}", f"{e[1].id}", color="red")

    return dot

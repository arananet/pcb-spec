"""KiCad S-expression netlist parser.

Reads a KiCad .net file (sexp format exported by Eeschema) and returns
typed dataclasses. Uses only the Python standard library.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["Component", "Net", "NetNode", "Netlist", "parse_kicad_netlist"]


@dataclass
class NetNode:
    ref: str
    pin: str


@dataclass
class Net:
    code: str
    name: str
    nodes: list[NetNode] = field(default_factory=list)


@dataclass
class Component:
    ref: str
    value: str
    footprint: str


@dataclass
class Netlist:
    components: list[Component] = field(default_factory=list)
    nets: list[Net] = field(default_factory=list)

    def component_refs(self) -> set[str]:
        return {c.ref for c in self.components}

    def net_names(self) -> set[str]:
        return {n.name for n in self.nets}


# ── S-expression tokenizer + parser ───────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == "(":
            tokens.append("(")
            i += 1
        elif ch == ")":
            tokens.append(")")
            i += 1
        elif ch == ";":
            # Line comment — skip to end of line
            while i < n and text[i] != "\n":
                i += 1
        elif ch == '"':
            i += 1
            buf: list[str] = []
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    buf.append(text[i + 1])
                    i += 2
                else:
                    buf.append(text[i])
                    i += 1
            tokens.append("".join(buf))
            i += 1  # closing "
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "();":
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def _parse(tokens: list[str], pos: int) -> tuple[object, int]:
    if pos >= len(tokens):
        raise ValueError("Unexpected end of input")
    tok = tokens[pos]
    if tok == "(":
        pos += 1
        items: list[object] = []
        while pos < len(tokens) and tokens[pos] != ")":
            val, pos = _parse(tokens, pos)
            items.append(val)
        if pos >= len(tokens):
            raise ValueError("Unmatched '(' in netlist")
        return items, pos + 1
    if tok == ")":
        raise ValueError("Unexpected ')'")
    return tok, pos + 1


def _find_all(tree: object, key: str) -> list[list]:
    """Return every sub-list whose first element is key (recursive)."""
    if not isinstance(tree, list):
        return []
    results = []
    if tree and tree[0] == key:
        results.append(tree)
    for item in tree:
        results.extend(_find_all(item, key))
    return results


def _attr(node: list, key: str) -> str | None:
    """Return value of a named child list: (key value) → value."""
    for item in node[1:]:
        if isinstance(item, list) and item and item[0] == key:
            return item[1] if len(item) > 1 else None
    return None


# ── Public API ─────────────────────────────────────────────────────────────

def parse_kicad_netlist(path: str | Path) -> Netlist:
    """Parse a KiCad S-expression netlist file and return a Netlist."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Netlist file not found: {p}")

    text = p.read_text(encoding="utf-8", errors="replace")
    try:
        tokens = _tokenize(text)
        if not tokens:
            raise ValueError("Empty file")
        tree, _ = _parse(tokens, 0)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Failed to parse {p}: {exc}") from exc

    if not isinstance(tree, list) or not tree or tree[0] != "export":
        raise ValueError(f"{p} does not appear to be a KiCad netlist (expected top-level 'export')")

    components: list[Component] = []
    for comp in _find_all(tree, "comp"):
        ref = _attr(comp, "ref")
        if ref:
            components.append(Component(
                ref=ref,
                value=_attr(comp, "value") or "",
                footprint=_attr(comp, "footprint") or "",
            ))

    nets: list[Net] = []
    for net in _find_all(tree, "net"):
        name = _attr(net, "name")
        if name is None:
            continue
        nodes = [
            NetNode(ref=_attr(node, "ref") or "", pin=_attr(node, "pin") or "")
            for node in _find_all(net, "node")
            if _attr(node, "ref")
        ]
        nets.append(Net(code=_attr(net, "code") or "", name=name, nodes=nodes))

    return Netlist(components=components, nets=nets)

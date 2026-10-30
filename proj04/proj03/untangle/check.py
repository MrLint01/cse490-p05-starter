"""The judge. Replays a move list and scores it in turns.

  python3 check.py graph.json moves.json

moves.json is {"moves": [[node, x, y], ...]}: one node to one new spot per
turn, integer coordinates inside the canvas. Every move costs one turn, a
move back to the start included. At the end no two nodes may share a point,
and an edge through a node counts as a crossing. The score is the number
of turns when the crossings reach zero. Prints one JSON report; exit 0 on
a legal, crossing-free result, 1 otherwise.
"""
import json
import sys


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (v > 0) - (v < 0)


def _on_segment(a, b, c):
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def segments_cross(p1, p2, q1, q2):
    """True when the two closed segments meet (touching counts)."""
    o1, o2 = _orient(p1, p2, q1), _orient(p1, p2, q2)
    o3, o4 = _orient(q1, q2, p1), _orient(q1, q2, p2)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(p1, p2, q1): return True
    if o2 == 0 and _on_segment(p1, p2, q2): return True
    if o3 == 0 and _on_segment(q1, q2, p1): return True
    if o4 == 0 and _on_segment(q1, q2, p2): return True
    return False


def crossing_pairs(nodes, edges):
    """Every pair of edges that cross, as (edge index, edge index)."""
    out = []
    m = len(edges)
    for i in range(m):
        a, b = edges[i]
        for j in range(i + 1, m):
            c, d = edges[j]
            if a in (c, d) or b in (c, d):
                continue
            if segments_cross(nodes[a], nodes[b], nodes[c], nodes[d]):
                out.append((i, j))
    return out


def node_hits(nodes, edges):
    """(node, edge index) for every node lying on an edge that is not its own."""
    out = []
    for v, p in enumerate(nodes):
        for k, (a, b) in enumerate(edges):
            if v in (a, b):
                continue
            if _orient(nodes[a], nodes[b], p) == 0 and _on_segment(nodes[a], nodes[b], p):
                out.append((v, k))
    return out


def crossings(nodes, edges):
    return len(crossing_pairs(nodes, edges)) + len(node_hits(nodes, edges))


def replay(graph, moves):
    """Apply the moves to the start layout. Returns (positions, violations)."""
    n = graph["n"]
    lo, hi = graph.get("canvas", [0, 1000])
    pos = [tuple(p) for p in graph["nodes"]]
    bad = []
    for t, mv in enumerate(moves):
        if not (isinstance(mv, (list, tuple)) and len(mv) == 3 and all(isinstance(x, int) and not isinstance(x, bool) for x in mv)):
            bad.append("move %d is not [node, x, y] with integers" % t)
            continue
        v, x, y = mv
        if not 0 <= v < n:
            bad.append("move %d names node %d; there are %d" % (t, v, n))
            continue
        if not (lo <= x <= hi and lo <= y <= hi):
            bad.append("move %d puts node %d outside the canvas" % (t, v))
            continue
        pos[v] = (x, y)
    seen = {}
    for v, p in enumerate(pos):
        if p in seen:
            bad.append("nodes %d and %d share the point %s" % (seen[p], v, list(p)))
        seen[p] = v
    return pos, bad


def verify(graph, submission):
    edges = [tuple(e) for e in graph["edges"]]
    moves = submission.get("moves")
    if not isinstance(moves, list):
        return {"ok": False, "violations": ["moves.json has no moves list"]}
    pos, bad = replay(graph, moves)
    if bad:
        return {"ok": False, "violations": bad[:10]}
    c = len(crossing_pairs(pos, edges)) + len(node_hits(pos, edges))
    return {"ok": c == 0, "crossings": c, "turns": len(moves),
            "nodes_moved": len({m[0] for m in moves}), "n": graph["n"], "edges": len(edges), "violations": []}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    r = verify(json.load(open(sys.argv[1])), json.load(open(sys.argv[2])))
    print(json.dumps(r))
    sys.exit(0 if r["ok"] else 1)

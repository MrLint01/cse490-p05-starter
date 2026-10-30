import json
import random
import sys
import time


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_seg(a, b, p):
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def segs_cross(a, b, c, d):
    o1 = orient(a, b, c)
    o2 = orient(a, b, d)
    o3 = orient(c, d, a)
    o4 = orient(c, d, b)
    if ((o1 > 0 and o2 < 0) or (o1 < 0 and o2 > 0)) and \
       ((o3 > 0 and o4 < 0) or (o3 < 0 and o4 > 0)):
        return True
    if o1 == 0 and on_seg(a, b, c):
        return True
    if o2 == 0 and on_seg(a, b, d):
        return True
    if o3 == 0 and on_seg(c, d, a):
        return True
    if o4 == 0 and on_seg(c, d, b):
        return True
    return False


def point_on_seg(p, a, b):
    return orient(a, b, p) == 0 and on_seg(a, b, p) and p != a and p != b


def total_violations(pos, edges):
    n = len(pos)
    m = len(edges)
    c = 0
    for i in range(m):
        a, b = edges[i]
        for j in range(i + 1, m):
            x, y = edges[j]
            if len({a, b, x, y}) < 4:
                continue
            if segs_cross(pos[a], pos[b], pos[x], pos[y]):
                c += 1
    for v in range(n):
        for a, b in edges:
            if v == a or v == b:
                continue
            if point_on_seg(pos[v], pos[a], pos[b]):
                c += 1
    c += n - len(set(map(tuple, pos)))
    return c


def cost(v, p, pos, edges, adj):
    """Violations involving node v if it sat at p (others fixed)."""
    n = len(pos)
    m = len(edges)
    old = pos[v]
    pos[v] = p
    c = 0
    for u in range(n):
        if u != v and pos[u] == p:
            c += 1000
    inc = set(adj[v])
    for ei in adj[v]:
        a, b = edges[ei]
        for ej in range(m):
            if ej == ei:
                continue
            x, y = edges[ej]
            if len({a, b, x, y}) < 4:
                continue
            if segs_cross(pos[a], pos[b], pos[x], pos[y]):
                c += 1
        for u in range(n):
            if u != a and u != b and point_on_seg(pos[u], pos[a], pos[b]):
                c += 1
    for ej in range(m):
        if ej in inc:
            continue
        a, b = edges[ej]
        if v != a and v != b and point_on_seg(p, pos[a], pos[b]):
            c += 1
    pos[v] = old
    return c


def main():
    graph_path, moves_path = sys.argv[1], sys.argv[2]
    with open(graph_path) as f:
        g = json.load(f)

    orig = [tuple(p) for p in g["nodes"]]
    edges = [tuple(e) for e in g["edges"]]
    n = len(orig)
    lo, hi = g.get("canvas", [0, 1000])
    adj = [[] for _ in range(n)]
    for i, (a, b) in enumerate(edges):
        adj[a].append(i)
        adj[b].append(i)
    nbrs = [set() for _ in range(n)]
    for a, b in edges:
        nbrs[a].add(b)
        nbrs[b].add(a)

    rng = random.Random(1)
    pos = [tuple(p) for p in orig]
    start = time.time()
    time_budget = 20.0

    def clamp(v):
        return max(lo, min(hi, int(round(v))))

    for _ in range(60):
        if total_violations(pos, edges) == 0 or time.time() - start > time_budget:
            break
        order = list(range(n))
        rng.shuffle(order)
        for v in order:
            best_p = pos[v]
            best_c = cost(v, best_p, pos, edges, adj)
            if best_c == 0:
                continue
            cands = []
            for _ in range(60):
                cands.append((rng.randint(lo, hi), rng.randint(lo, hi)))
            if nbrs[v]:
                cx = sum(pos[u][0] for u in nbrs[v]) / len(nbrs[v])
                cy = sum(pos[u][1] for u in nbrs[v]) / len(nbrs[v])
                for _ in range(20):
                    cands.append((clamp(cx + rng.gauss(0, 60)),
                                  clamp(cy + rng.gauss(0, 60))))
            for _ in range(10):
                cands.append((clamp(pos[v][0] + rng.gauss(0, 30)),
                              clamp(pos[v][1] + rng.gauss(0, 30))))
            for p in cands:
                c = cost(v, p, pos, edges, adj)
                if c < best_c:
                    best_c = c
                    best_p = p
                    if c == 0:
                        break
            pos[v] = best_p
        if time.time() - start > time_budget:
            break

    moves = []
    for v in range(n):
        if pos[v] != orig[v]:
            moves.append([v, int(pos[v][0]), int(pos[v][1])])

    with open(moves_path, "w") as f:
        json.dump({"moves": moves}, f)


if __name__ == "__main__":
    main()

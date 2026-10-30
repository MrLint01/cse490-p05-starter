# Untangle

graph.json is a planar graph drawn with every node in the wrong place: 30
nodes on a 1000 by 1000 grid, 76 edges, hundreds of crossings. A drawing
with no crossing exists. Find one by moving nodes, and use as few moves as
you can.

Rules:
- A move is one node to one integer point inside the canvas, any distance.
- Every move costs one turn, a move back to the start included.
- At the end no two nodes may share a point, and an edge passing through a
  node counts as a crossing.
- The score is the number of turns when the crossings reach zero. Lower wins.
  One move per node is the reference.
- solve.py uses only Python's standard library. The grader runs it on a
  plain Python with nothing installed.

Your harness writes solve.py. It takes two arguments, the graph file to
read and the moves file to write, and writes:

    {"moves": [[node, x, y], [node, x, y], ...]}

## Run it

Every command runs in the VS Code terminal with the project's .venv selected
(the Python the setup wizard made), from the project folder:

    python untangle/solve.py untangle/graph.json untangle/moves.json   your solver writes the move list
    python untangle/check.py untangle/graph.json untangle/moves.json   the judge: crossings and turns
    python untangle/view.py  untangle/graph.json untangle/moves.json   watch it: Play, Step, Restart

The viewer opens a window. If no window opens, or it opens blank, the same
player opens in your browser instead, by itself (view.py writes view.html
beside moves.json). To go straight to the browser, add --browser.

The judge is the only scorer. Your solver is graded on graphs you have not
seen, of the same size, with a time limit; a run that does not reach zero
crossings ranks below every run that does.

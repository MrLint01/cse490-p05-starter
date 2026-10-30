"""A window that replays a move list, the way the judge scores it.

  python view.py graph.json moves.json
  python view.py graph.json moves.json --browser   the same player as a web
                                                    page in your browser
  python view.py graph.json --planar      staff: the hidden drawing, one move per node

Buttons: Play / Pause, Step (one turn), Restart. Keys: space, n, r, q.
Edges are tinted by how many crossings they carry; each crossing is an x;
a moved node keeps a ghost at its start; the strip plots crossings against
turns, which is the score.

Needs only Python. The window is Tk; when Tk is missing or too old to draw
(Apple's own /usr/bin/python3 ships Tk 8.5, which opens a blank window),
the player is written as view.html next to the move list and opened in the
browser instead, automatically.
"""
import json
import os
import sys
import webbrowser

from check import crossing_pairs, node_hits, replay

SIZE, PAD, R, STRIP = 720, 36, 6, 120
BG, EDGE, GHOST, NODE, MOVED, FLY, MARK, TEXT = "#0f1117", "#3a3f4b", "#2a2f3a", "#e6e6e6", "#4aa3ff", "#5df0a0", "#ff4d4d", "#c8ccd4"


def tint(k):
    if k == 0:
        return EDGE
    t = min(1.0, k / 6.0)
    return "#%02x%02x%02x" % (255, int(170 * (1 - t) + 60 * t), int(40 * (1 - t) + 60 * t))


def meet(p1, p2, q1, q2):
    d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
    if d == 0:
        return None
    t = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d
    return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))


def ease(t):
    return 1 - (1 - t) ** 3


class Viewer:
    def __init__(self, graph, moves):
        import tkinter as tk
        self.tk = tk
        self.g = graph
        self.edges = [tuple(e) for e in graph["edges"]]
        self.lo, self.hi = graph["canvas"]
        self.start = [tuple(p) for p in graph["nodes"]]
        self.moves = moves
        tk = self.tk
        self.root = tk.Tk()
        self.root.title("Untangle: seed %d, %d nodes, %d edges, %d turns in the move list"
                        % (graph["seed"], graph["n"], len(self.edges), len(moves)))
        self.root.configure(bg=BG)
        self.cv = tk.Canvas(self.root, width=SIZE, height=SIZE + STRIP, bg=BG, highlightthickness=0)
        self.cv.pack()
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=PAD, pady=(0, 12))
        self.play_btn = tk.Button(bar, text="Play", width=8, command=self.toggle)
        self.play_btn.pack(side="left", padx=(0, 8))
        tk.Button(bar, text="Step", width=8, command=self.step_once).pack(side="left", padx=(0, 8))
        tk.Button(bar, text="Restart", width=8, command=self.restart).pack(side="left")
        tk.Label(bar, text="space play/pause   n step   r restart   q quit", bg=BG, fg=EDGE, font=("Menlo", 11)).pack(side="right")
        self.root.bind("<space>", lambda e: self.toggle())
        self.root.bind("n", lambda e: self.step_once())
        self.root.bind("r", lambda e: self.restart())
        self.root.bind("q", lambda e: self.root.destroy())
        self.restart()
        self.tick()

    # ---- state
    def restart(self):
        self.pos = list(self.start)
        self.i = 0
        self.playing = False
        self.busy = False
        self.flying = None
        self.rings = []
        self.history = []
        self.moved = set()
        self.play_btn.config(text="Play")
        self.draw()

    def toggle(self):
        if self.i >= len(self.moves):
            return
        self.playing = not self.playing
        self.play_btn.config(text="Pause" if self.playing else "Play")

    def step_once(self):
        if not self.busy and self.i < len(self.moves):
            self.playing = False
            self.play_btn.config(text="Play")
            self.animate_move()

    def tick(self):
        if self.playing and not self.busy and self.i < len(self.moves):
            self.animate_move()
        elif self.rings:
            self.draw()
        self.root.after(90, self.tick)

    def animate_move(self):
        self.busy = True
        v, x1, y1 = self.moves[self.i]
        x0, y0 = self.pos[v]
        self.flying = v
        frames = 12
        for k in range(1, frames + 1):
            t = ease(k / frames)
            self.pos[v] = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            self.draw()
            self.root.update()
            self.root.after(14)
        self.pos[v] = (x1, y1)
        self.moved.add(v)
        self.flying = None
        self.rings.append([v, 0])
        self.i += 1
        self.busy = False
        if self.i >= len(self.moves):
            self.playing = False
            self.play_btn.config(text="Play")
        self.draw()

    # ---- drawing
    def px(self, p):
        s = (SIZE - 2 * PAD) / (self.hi - self.lo)
        return PAD + (p[0] - self.lo) * s, PAD + (self.hi - p[1]) * s

    def draw(self):
        cv, pos, edges = self.cv, self.pos, self.edges
        cv.delete("all")
        pairs = crossing_pairs(pos, edges)
        hits = node_hits(pos, edges) if self.flying is None else []
        load = [0] * len(edges)
        for i, j in pairs:
            load[i] += 1; load[j] += 1
        for v in self.moved:
            x0, y0 = self.px(self.start[v]); x1, y1 = self.px(pos[v])
            cv.create_line(x0, y0, x1, y1, fill=GHOST, dash=(2, 4))
            cv.create_oval(x0 - 3, y0 - 3, x0 + 3, y0 + 3, outline=GHOST, fill="")
        for k in sorted(range(len(edges)), key=lambda k: load[k]):
            a, b = edges[k]
            cv.create_line(*self.px(pos[a]), *self.px(pos[b]), fill=tint(load[k]), width=1 if load[k] == 0 else 2)
        for i, j in pairs:
            a, b = edges[i]; c, d = edges[j]
            m = meet(pos[a], pos[b], pos[c], pos[d])
            if m:
                x, y = self.px(m)
                cv.create_line(x - 3, y - 3, x + 3, y + 3, fill=MARK, width=2)
                cv.create_line(x - 3, y + 3, x + 3, y - 3, fill=MARK, width=2)
        keep = []
        for ring in self.rings:
            v, age = ring
            x, y = self.px(pos[v])
            rr = R + 4 + age * 3
            cv.create_oval(x - rr, y - rr, x + rr, y + rr, outline=FLY, width=max(1, 3 - age // 3))
            if age < 8:
                ring[1] += 1
                keep.append(ring)
        self.rings = keep
        for v, p in enumerate(pos):
            x, y = self.px(p)
            fill = FLY if v == self.flying else (MOVED if v in self.moved else NODE)
            cv.create_oval(x - R - 2, y - R - 2, x + R + 2, y + R + 2, fill=BG, outline="")
            cv.create_oval(x - R, y - R, x + R, y + R, fill=fill, outline="")
        # the strip: crossings against turns
        c = len(pairs) + len(hits)
        if self.flying is None and (not self.history or self.history[-1][0] != self.i):
            self.history.append((self.i, c))
        top = SIZE + 8
        base = top + STRIP - 48
        cv.create_line(PAD, base, SIZE - PAD, base, fill=EDGE)
        c0 = max(1, self.history[0][1]) if self.history else 1
        total = max(1, len(self.moves))
        pts = []
        for turn, k in self.history:
            pts += [PAD + (SIZE - 2 * PAD) * turn / total, base - (STRIP - 60) * k / c0]
        if len(pts) >= 4:
            cv.create_line(*pts, fill=MOVED, width=2)
        if pts:
            cv.create_oval(pts[-2] - 3, pts[-1] - 3, pts[-2] + 3, pts[-1] + 3, fill=FLY, outline="")
        done = self.i >= len(self.moves)
        status = ("score %d turns" % self.i if c == 0 else "did not finish") if done else ("playing" if self.playing else "")
        cv.create_text(PAD, base + 22, anchor="w", fill=TEXT, font=("Menlo", 13),
                       text="crossings %d    turn %d of %d    %s" % (c, self.i, len(self.moves), status))
        cv.create_text(SIZE - PAD, base + 22, anchor="e", fill=EDGE, font=("Menlo", 11), text="crossings vs turns")


HTML = """<!doctype html><meta charset="utf-8"><title>Untangle</title>
<style>body{margin:0;background:%(bg)s;color:%(text)s;font:14px Menlo,monospace}
#wrap{width:720px;margin:0 auto}canvas{display:block}button{font:13px Menlo,monospace;margin:0 8px 12px 0;padding:4px 14px}
#bar{padding:0 36px}#keys{float:right;color:%(edge)s}</style>
<div id=wrap><canvas id=c width=720 height=840></canvas>
<div id=bar><button id=play>Play</button><button id=step>Step</button><button id=restart>Restart</button>
<span id=keys>space play/pause &nbsp; n step &nbsp; r restart</span></div></div>
<script>
const G=%(graph)s, MOVES=%(moves)s, SIZE=720, PAD=36, R=6, STRIP=120;
const BG="%(bg)s", EDGE="%(edge)s", GHOST="%(ghost)s", NODE="%(node)s", MOVED="%(moved)s", FLY="%(fly)s", MARK="%(mark)s", TEXT="%(text)s";
const lo=G.canvas[0], hi=G.canvas[1], start=G.nodes.map(p=>[p[0],p[1]]), E=G.edges;
let pos, i, playing, busy, flying, rings, hist, moved;
const cv=document.getElementById("c").getContext("2d");
function px(p){const s=(SIZE-2*PAD)/(hi-lo);return [PAD+(p[0]-lo)*s, PAD+(hi-p[1])*s];}
function orient(a,b,c){const v=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);return v>0?1:(v<0?-1:0);}
function onseg(a,b,c){return Math.min(a[0],b[0])<=c[0]&&c[0]<=Math.max(a[0],b[0])&&Math.min(a[1],b[1])<=c[1]&&c[1]<=Math.max(a[1],b[1]);}
function cross(p1,p2,q1,q2){const o1=orient(p1,p2,q1),o2=orient(p1,p2,q2),o3=orient(q1,q2,p1),o4=orient(q1,q2,p2);
 if(o1!=o2&&o3!=o4)return true; if(o1==0&&onseg(p1,p2,q1))return true; if(o2==0&&onseg(p1,p2,q2))return true;
 if(o3==0&&onseg(q1,q2,p1))return true; if(o4==0&&onseg(q1,q2,p2))return true; return false;}
function pairs(){const out=[];for(let a=0;a<E.length;a++){const[u,v]=E[a];for(let b=a+1;b<E.length;b++){const[x,y]=E[b];
 if(u==x||u==y||v==x||v==y)continue; if(cross(pos[u],pos[v],pos[x],pos[y]))out.push([a,b]);}}return out;}
function hits(){let n=0;for(let v=0;v<pos.length;v++)for(const[a,b]of E){if(v==a||v==b)continue;
 if(orient(pos[a],pos[b],pos[v])==0&&onseg(pos[a],pos[b],pos[v]))n++;}return n;}
function meet(p1,p2,q1,q2){const d=(p2[0]-p1[0])*(q2[1]-q1[1])-(p2[1]-p1[1])*(q2[0]-q1[0]);if(d==0)return null;
 const t=((q1[0]-p1[0])*(q2[1]-q1[1])-(q1[1]-p1[1])*(q2[0]-q1[0]))/d;return [p1[0]+t*(p2[0]-p1[0]),p1[1]+t*(p2[1]-p1[1])];}
function tint(k){if(k==0)return EDGE;const t=Math.min(1,k/6);return `rgb(255,${Math.round(170*(1-t)+60*t)},${Math.round(40*(1-t)+60*t)})`;}
function restart(){pos=start.map(p=>[p[0],p[1]]);i=0;playing=false;busy=false;flying=null;rings=[];hist=[];moved=new Set();
 document.getElementById("play").textContent="Play";draw();}
function draw(){cv.fillStyle=BG;cv.fillRect(0,0,SIZE,SIZE+STRIP);const P=pairs();const load=new Array(E.length).fill(0);
 for(const[a,b]of P){load[a]++;load[b]++;}
 for(const v of moved){const[x0,y0]=px(start[v]),[x1,y1]=px(pos[v]);cv.strokeStyle=GHOST;cv.setLineDash([2,4]);cv.beginPath();cv.moveTo(x0,y0);cv.lineTo(x1,y1);cv.stroke();cv.setLineDash([]);cv.beginPath();cv.arc(x0,y0,3,0,7);cv.stroke();}
 const order=[...E.keys()].sort((a,b)=>load[a]-load[b]);
 for(const k of order){const[a,b]=E[k];const[x0,y0]=px(pos[a]),[x1,y1]=px(pos[b]);cv.strokeStyle=tint(load[k]);cv.lineWidth=load[k]?2:1;cv.beginPath();cv.moveTo(x0,y0);cv.lineTo(x1,y1);cv.stroke();}
 cv.lineWidth=2;cv.strokeStyle=MARK;for(const[a,b]of P){const[u,v]=E[a],[x,y]=E[b];const m=meet(pos[u],pos[v],pos[x],pos[y]);if(!m)continue;const[mx,my]=px(m);
 cv.beginPath();cv.moveTo(mx-3,my-3);cv.lineTo(mx+3,my+3);cv.moveTo(mx-3,my+3);cv.lineTo(mx+3,my-3);cv.stroke();}
 const keep=[];for(const r of rings){const[x,y]=px(pos[r[0]]);const rr=R+4+r[1]*3;cv.strokeStyle=FLY;cv.lineWidth=Math.max(1,3-Math.floor(r[1]/3));cv.beginPath();cv.arc(x,y,rr,0,7);cv.stroke();if(r[1]<8){r[1]++;keep.push(r);}}rings=keep;
 cv.lineWidth=1;pos.forEach((p,v)=>{const[x,y]=px(p);cv.fillStyle=BG;cv.beginPath();cv.arc(x,y,R+2,0,7);cv.fill();
 cv.fillStyle=v===flying?FLY:(moved.has(v)?MOVED:NODE);cv.beginPath();cv.arc(x,y,R,0,7);cv.fill();});
 const c=P.length+(flying===null?hits():0);if(flying===null&&(!hist.length||hist[hist.length-1][0]!=i))hist.push([i,c]);
 const top=SIZE+8,base=top+STRIP-48;cv.strokeStyle=EDGE;cv.beginPath();cv.moveTo(PAD,base);cv.lineTo(SIZE-PAD,base);cv.stroke();
 const c0=Math.max(1,hist.length?hist[0][1]:1),total=Math.max(1,MOVES.length);
 cv.strokeStyle=MOVED;cv.lineWidth=2;cv.beginPath();hist.forEach(([t,k],j)=>{const x=PAD+(SIZE-2*PAD)*t/total,y=base-(STRIP-60)*k/c0;j?cv.lineTo(x,y):cv.moveTo(x,y);});if(hist.length>1)cv.stroke();cv.lineWidth=1;
 if(hist.length){const[t,k]=hist[hist.length-1];cv.fillStyle=FLY;cv.beginPath();cv.arc(PAD+(SIZE-2*PAD)*t/total,base-(STRIP-60)*k/c0,3,0,7);cv.fill();}
 const done=i>=MOVES.length;const status=done?(c==0?`score ${i} turns`:"did not finish"):(playing?"playing":"");
 cv.fillStyle=TEXT;cv.font="13px Menlo,monospace";cv.textAlign="left";cv.fillText(`crossings ${c}    turn ${i} of ${MOVES.length}    ${status}`,PAD,base+26);
 cv.fillStyle=EDGE;cv.font="11px Menlo,monospace";cv.textAlign="right";cv.fillText("crossings vs turns",SIZE-PAD,base+26);}
function ease(t){return 1-Math.pow(1-t,3);}
function animate(cb){busy=true;const[v,x1,y1]=MOVES[i];const[x0,y0]=pos[v];flying=v;let k=0;const frames=12;
 const tick=()=>{k++;const t=ease(k/frames);pos[v]=[x0+(x1-x0)*t,y0+(y1-y0)*t];draw();if(k<frames)setTimeout(tick,14);else{pos[v]=[x1,y1];moved.add(v);flying=null;rings.push([v,0]);i++;busy=false;
 if(i>=MOVES.length){playing=false;document.getElementById("play").textContent="Play";}draw();if(cb)cb();}};tick();}
function loop(){if(playing&&!busy&&i<MOVES.length)animate();else if(rings.length)draw();setTimeout(loop,90);}
function toggle(){if(i>=MOVES.length)return;playing=!playing;document.getElementById("play").textContent=playing?"Pause":"Play";}
function stepOnce(){if(!busy&&i<MOVES.length){playing=false;document.getElementById("play").textContent="Play";animate();}}
document.getElementById("play").onclick=toggle;document.getElementById("step").onclick=stepOnce;document.getElementById("restart").onclick=restart;
document.addEventListener("keydown",e=>{if(e.key==" "){e.preventDefault();toggle();}else if(e.key=="n")stepOnce();else if(e.key=="r")restart();});
restart();loop();
</script>"""


def browser(graph, moves, out):
    """Write the player as one web page beside the move list and open it."""
    page = HTML % {"graph": json.dumps(graph), "moves": json.dumps(moves), "bg": BG, "edge": EDGE, "ghost": GHOST,
                   "node": NODE, "moved": MOVED, "fly": FLY, "mark": MARK, "text": TEXT}
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("player written to %s; opening it in your browser" % out)
    webbrowser.open("file://" + os.path.abspath(out))


def tk_draws():
    """True when this Python has a Tk that draws (8.6 or newer)."""
    try:
        import tkinter
    except ImportError:
        return False
    return float(str(tkinter.TkVersion)) >= 8.6


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    g = json.load(open(sys.argv[1]))
    if sys.argv[2] == "--planar":
        import graph
        moves = [[v, x, y] for v, (x, y) in enumerate(graph.planar_layout(g["seed"], g["n"]))]
        out = "view.html"
    else:
        moves = json.load(open(sys.argv[2]))["moves"]
        out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), "view.html")
    if "--browser" in sys.argv or not tk_draws():
        browser(g, moves, out)
        return
    Viewer(g, moves).root.mainloop()


if __name__ == "__main__":
    main()

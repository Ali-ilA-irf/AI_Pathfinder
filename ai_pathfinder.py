"""
AI Pathfinder -  
Uninformed Search Visualization

Algorithms: BFS, DFS, UCS, DLS, IDDFS, Bidirectional Search
Movement: 6 Directions (Up, Right, Bottom, Bottom-Right, Left, Top-Left)
"""

import pygame
import sys
import time
import math
from collections import deque
import heapq

pygame.init()

# ─── Constants ────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1000
WINDOW_HEIGHT = 800
GRID_COLS     = 20
GRID_ROWS     = 20
CELL_SIZE     = 22
GRID_OFFSET_X = 30
GRID_OFFSET_Y = 130
PANEL_X       = GRID_OFFSET_X + GRID_COLS * CELL_SIZE + 30

# ─── Colors ───────────────────────────────────────────────────────────────────
C_BG          = (15,  23,  42)
C_GRID        = (40,  55,  75)
C_EMPTY       = (51,  65,  85)
C_WALL        = (20,  20,  25)
C_START       = (34,  197, 94)
C_TARGET      = (239, 68,  68)
C_FRONTIER    = (59,  130, 246)
C_EXPLORED    = (139, 60,  210)
C_PATH        = (250, 204, 21)
C_TEXT        = (240, 245, 255)
C_BTN         = (55,  70,  95)
C_BTN_HOVER   = (80,  100, 130)
C_BTN_ACTIVE  = (34,  197, 94)
C_ACCENT      = (99,  179, 237)
C_SUBTEXT     = (148, 163, 184)

# ─── Strict Movement Order (6 directions only) ────────────────────────────────
DIRECTIONS = [
    (-1,  0),  # 1. Up
    ( 0,  1),  # 2. Right
    ( 1,  0),  # 3. Bottom
    ( 1,  1),  # 4. Bottom-Right (Main Diagonal)
    ( 0, -1),  # 5. Left
    (-1, -1),  # 6. Top-Left (Main Diagonal)
]

ALGORITHMS = ["BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional"]
DLS_DEPTH_LIMIT = 20


# ─── Node ─────────────────────────────────────────────────────────────────────
class Node:
    def __init__(self, row, col, cost=0, parent=None):
        self.row    = row
        self.col    = col
        self.cost   = cost
        self.parent = parent

    def __lt__(self, other): return self.cost < other.cost
    def __eq__(self, other): return self.row == other.row and self.col == other.col
    def __hash__(self):      return hash((self.row, self.col))


# ─── Button ───────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font_size=19):
        self.rect    = pygame.Rect(x, y, w, h)
        self.text    = text
        self.font    = pygame.font.Font(None, font_size)
        self.active  = False
        self.hovered = False

    def draw(self, surf):
        col = C_BTN_ACTIVE if self.active else (C_BTN_HOVER if self.hovered else C_BTN)
        pygame.draw.rect(surf, col, self.rect, border_radius=7)
        pygame.draw.rect(surf, C_TEXT, self.rect, 1, border_radius=7)
        ts = self.font.render(self.text, True, C_TEXT)
        surf.blit(ts, ts.get_rect(center=self.rect.center))

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


# ─── Main App ─────────────────────────────────────────────────────────────────
class PathfinderApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI Pathfinder  –   ")
        self.clock  = pygame.time.Clock()

        self.font_title  = pygame.font.Font(None, 38)
        self.font_info   = pygame.font.Font(None, 23)
        self.font_small  = pygame.font.Font(None, 19)

        self._init_grid()
        self._build_buttons()
        self._reset_state()

    # ── Grid setup ──────────────────────────────────────────────────────────
    def _init_grid(self):
        self.grid   = [[0]*GRID_COLS for _ in range(GRID_ROWS)]
        self.start  = (1, 1)
        self.target = (GRID_ROWS - 2, GRID_COLS - 2)
        self.grid[self.start[0]][self.start[1]]   = 2
        self.grid[self.target[0]][self.target[1]] = 3

    def _reset_state(self):
        self.frontier  = set()
        self.explored  = set()
        self.path      = []
        self.algo_idx  = 0
        self.running   = False
        self.paused    = False
        self.step_delay = 40   # ms between steps
        self.stats = dict(nodes_explored=0, frontier_size=0,
                          path_length=0, elapsed=0.0, status="Ready")

    # ── Button layout ───────────────────────────────────────────────────────
    def _build_buttons(self):
        # Algorithm row (top)
        aw, ah, agap = 118, 40, 8
        self.algo_btns = []
        for i, name in enumerate(ALGORITHMS):
            col = i % 3
            row = i // 3
            x = GRID_OFFSET_X + col * (aw + agap)
            y = 30 + row * (ah + 6)
            b = Button(x, y, aw, ah, name, 20)
            if i == 0:
                b.active = True
            self.algo_btns.append(b)

        # Control buttons (bottom-left row)
        cw, ch, cgap = 95, 38, 8
        cy = WINDOW_HEIGHT - 58
        cx = GRID_OFFSET_X
        self.btn_run   = Button(cx,                    cy, cw, ch, "Run")
        self.btn_pause = Button(cx + cw + cgap,        cy, cw, ch, "Pause")
        self.btn_clear = Button(cx + 2*(cw+cgap),      cy, cw, ch, "Clear")
        self.btn_reset = Button(cx + 3*(cw+cgap),      cy, cw, ch, "Reset Grid")
        self.ctrl_btns = [self.btn_run, self.btn_pause,
                          self.btn_clear, self.btn_reset]

        # Edit mode buttons (bottom, second row)
        ew, eh = 105, 33
        ey = cy - eh - 8
        ex = GRID_OFFSET_X
        self.mode_btns = {
            'place_start':  Button(ex,              ey, ew, eh, "Place Start",  17),
            'place_target': Button(ex + ew + cgap,  ey, ew, eh, "Place Target", 17),
            'place_wall':   Button(ex+2*(ew+cgap),  ey, ew, eh, "Place Wall",   17),
            'erase':        Button(ex+3*(ew+cgap),  ey, ew, eh, "Erase",        17),
        }
        self.edit_mode = 'place_wall'
        self.mode_btns['place_wall'].active = True

    # ── Grid helpers ────────────────────────────────────────────────────────
    def _is_valid(self, r, c):
        return (0 <= r < GRID_ROWS and 0 <= c < GRID_COLS
                and self.grid[r][c] != 1)

    def _neighbors(self, node):
        result = []
        for dr, dc in DIRECTIONS:
            nr, nc = node.row + dr, node.col + dc
            if self._is_valid(nr, nc):
                cost = math.sqrt(2) if abs(dr) + abs(dc) == 2 else 1.0
                result.append(Node(nr, nc, node.cost + cost, node))
        return result

    def _trace_path(self, node):
        path = []
        while node:
            path.append((node.row, node.col))
            node = node.parent
        return path[::-1]

    def _clear_search(self):
        self.frontier = set()
        self.explored = set()
        self.path     = []
        self.stats    = dict(nodes_explored=0, frontier_size=0,
                             path_length=0, elapsed=0.0, status="Ready")

    def _step(self):
        """Draw one frame and wait step_delay ms. Returns False if app quit."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            # Allow pause toggle while running
            if self.btn_pause.handle(ev):
                self.paused = not self.paused
                self.btn_pause.text = "Resume" if self.paused else "Pause"
        self._draw()
        pygame.time.wait(self.step_delay)
        while self.paused and self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.btn_pause.handle(ev):
                    self.paused = not self.paused
                    self.btn_pause.text = "Resume" if self.paused else "Pause"
            self._draw()
            self.clock.tick(30)

    # ─────────────────────────────────────────────────────────────────────────
    # Algorithms
    # ─────────────────────────────────────────────────────────────────────────
    def _bfs(self):
        t0 = time.time()
        self.stats['status'] = "Running BFS…"
        queue   = deque([Node(*self.start)])
        visited = {self.start}

        while queue and self.running:
            cur = queue.popleft()
            pos = (cur.row, cur.col)
            self.explored.add(pos)
            self.frontier.discard(pos)
            self.stats['nodes_explored'] += 1

            if pos == self.target:
                self.path = self._trace_path(cur)
                self.stats.update(path_length=len(self.path),
                                  elapsed=time.time()-t0, status="✓ Path Found!")
                return

            for nb in self._neighbors(cur):
                nbp = (nb.row, nb.col)
                if nbp not in visited:
                    visited.add(nbp)
                    queue.append(nb)
                    self.frontier.add(nbp)

            self.stats['frontier_size'] = len(queue)
            self._step()

        if self.running:
            self.stats.update(elapsed=time.time()-t0, status="✗ No path found")

    def _dfs(self):
        t0 = time.time()
        self.stats['status'] = "Running DFS…"
        stack   = [Node(*self.start)]
        visited = {self.start}

        while stack and self.running:
            cur = stack.pop()
            pos = (cur.row, cur.col)
            self.explored.add(pos)
            self.frontier.discard(pos)
            self.stats['nodes_explored'] += 1

            if pos == self.target:
                self.path = self._trace_path(cur)
                self.stats.update(path_length=len(self.path),
                                  elapsed=time.time()-t0, status="✓ Path Found!")
                return

            for nb in reversed(self._neighbors(cur)):
                nbp = (nb.row, nb.col)
                if nbp not in visited:
                    visited.add(nbp)
                    stack.append(nb)
                    self.frontier.add(nbp)

            self.stats['frontier_size'] = len(stack)
            self._step()

        if self.running:
            self.stats.update(elapsed=time.time()-t0, status="✗ No path found")

    def _ucs(self):
        t0 = time.time()
        self.stats['status'] = "Running UCS…"
        heap    = [Node(*self.start, cost=0)]
        visited = {}

        while heap and self.running:
            cur = heapq.heappop(heap)
            pos = (cur.row, cur.col)

            if pos in self.explored:
                continue
            self.explored.add(pos)
            self.frontier.discard(pos)
            self.stats['nodes_explored'] += 1

            if pos == self.target:
                self.path = self._trace_path(cur)
                self.stats.update(path_length=len(self.path),
                                  elapsed=time.time()-t0, status="✓ Path Found!")
                return

            for nb in self._neighbors(cur):
                nbp = (nb.row, nb.col)
                if nbp not in self.explored:
                    if nbp not in visited or nb.cost < visited[nbp]:
                        visited[nbp] = nb.cost
                        heapq.heappush(heap, nb)
                        self.frontier.add(nbp)

            self.stats['frontier_size'] = len(heap)
            self._step()

        if self.running:
            self.stats.update(elapsed=time.time()-t0, status="✗ No path found")

    def _dls(self, limit=DLS_DEPTH_LIMIT):
        """Iterative (stack-based) Depth-Limited Search. Returns found node or None."""
        self.stats['status'] = f"Running DLS (limit={limit})…"
        # Stack holds (node, depth)
        stack   = [(Node(*self.start), 0)]
        visited = {self.start}

        while stack and self.running:
            cur, depth = stack.pop()
            pos = (cur.row, cur.col)
            self.explored.add(pos)
            self.frontier.discard(pos)
            self.stats['nodes_explored'] += 1

            if pos == self.target:
                return cur

            if depth < limit:
                for nb in reversed(self._neighbors(cur)):
                    nbp = (nb.row, nb.col)
                    if nbp not in visited:
                        visited.add(nbp)
                        stack.append((nb, depth + 1))
                        self.frontier.add(nbp)

            self.stats['frontier_size'] = len(stack)
            self._step()

        return None

    def _run_dls(self):
        t0 = time.time()
        result = self._dls()
        if result:
            self.path = self._trace_path(result)
            self.stats.update(path_length=len(self.path),
                              elapsed=time.time()-t0, status="✓ Path Found!")
        elif self.running:
            self.stats.update(elapsed=time.time()-t0,
                              status=f"✗ No path within depth {DLS_DEPTH_LIMIT}")

    def _iddfs(self):
        t0 = time.time()
        for limit in range(1, GRID_ROWS * GRID_COLS):
            if not self.running:
                return
            self._clear_search()
            self.stats['status'] = f"IDDFS – trying depth {limit}…"
            result = self._dls(limit)
            if result:
                self.path = self._trace_path(result)
                self.stats.update(path_length=len(self.path),
                                  elapsed=time.time()-t0,
                                  status=f"✓ Found at depth {limit}!")
                return
        if self.running:
            self.stats.update(elapsed=time.time()-t0, status="✗ No path found")

    def _bidirectional(self):
        t0 = time.time()
        self.stats['status'] = "Running Bidirectional…"

        fwd_queue   = deque([Node(*self.start)])
        bwd_queue   = deque([Node(*self.target)])
        fwd_visited = {self.start:  Node(*self.start)}
        bwd_visited = {self.target: Node(*self.target)}

        while (fwd_queue or bwd_queue) and self.running:
            # ── Forward step ──
            if fwd_queue:
                cur = fwd_queue.popleft()
                pos = (cur.row, cur.col)
                self.explored.add(pos)
                self.frontier.discard(pos)
                self.stats['nodes_explored'] += 1

                if pos in bwd_visited:
                    # Stitch path
                    fwd_path = self._trace_path(cur)
                    bwd_path = self._trace_path(bwd_visited[pos])
                    self.path = fwd_path + bwd_path[-2::-1]
                    self.stats.update(path_length=len(self.path),
                                      elapsed=time.time()-t0, status="✓ Paths Met!")
                    return

                for nb in self._neighbors(cur):
                    nbp = (nb.row, nb.col)
                    if nbp not in fwd_visited:
                        fwd_visited[nbp] = nb
                        fwd_queue.append(nb)
                        self.frontier.add(nbp)

            # ── Backward step ──
            if bwd_queue:
                cur = bwd_queue.popleft()
                pos = (cur.row, cur.col)
                self.explored.add(pos)
                self.frontier.discard(pos)
                self.stats['nodes_explored'] += 1

                if pos in fwd_visited:
                    fwd_path = self._trace_path(fwd_visited[pos])
                    bwd_path = self._trace_path(cur)
                    self.path = fwd_path + bwd_path[-2::-1]
                    self.stats.update(path_length=len(self.path),
                                      elapsed=time.time()-t0, status="✓ Paths Met!")
                    return

                for nb in self._neighbors(cur):
                    nbp = (nb.row, nb.col)
                    if nbp not in bwd_visited:
                        bwd_visited[nbp] = nb
                        bwd_queue.append(nb)
                        self.frontier.add(nbp)

            self.stats['frontier_size'] = len(fwd_queue) + len(bwd_queue)
            self._step()

        if self.running:
            self.stats.update(elapsed=time.time()-t0, status="✗ No path found")

    def _run_algorithm(self):
        self._clear_search()
        self.running = True
        name = ALGORITHMS[self.algo_idx]
        fn = {"BFS": self._bfs, "DFS": self._dfs, "UCS": self._ucs,
              "DLS": self._run_dls, "IDDFS": self._iddfs,
              "Bidirectional": self._bidirectional}[name]
        fn()
        self.running = False

    # ─────────────────────────────────────────────────────────────────────────
    # Drawing
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_grid(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = GRID_OFFSET_X + c * CELL_SIZE
                y = GRID_OFFSET_Y + r * CELL_SIZE
                pos = (r, c)

                if pos == self.start:
                    col = C_START
                elif pos == self.target:
                    col = C_TARGET
                elif pos in self.path:
                    col = C_PATH
                elif pos in self.explored:
                    col = C_EXPLORED
                elif pos in self.frontier:
                    col = C_FRONTIER
                elif self.grid[r][c] == 1:
                    col = C_WALL
                else:
                    col = C_EMPTY

                pygame.draw.rect(self.screen, col,
                                 (x+1, y+1, CELL_SIZE-2, CELL_SIZE-2))
                pygame.draw.rect(self.screen, C_GRID,
                                 (x, y, CELL_SIZE, CELL_SIZE), 1)

                # Label S / T
                if pos == self.start or pos == self.target:
                    lbl = self.font_small.render(
                        "S" if pos == self.start else "T", True, C_TEXT)
                    self.screen.blit(lbl, lbl.get_rect(
                        center=(x + CELL_SIZE//2, y + CELL_SIZE//2)))

    def _draw_panel(self):
        px, py = PANEL_X, GRID_OFFSET_Y

        # Title
        self.screen.blit(
            self.font_info.render("Statistics", True, C_ACCENT), (px, py))
        py += 32

        algo_name = ALGORITHMS[self.algo_idx]
        self.screen.blit(
            self.font_info.render(f"Algorithm:  {algo_name}", True, C_TEXT), (px, py))
        py += 26

        status_col = (250, 180, 50) if "✗" in self.stats['status'] else \
                     (100, 220, 120) if "✓" in self.stats['status'] else C_TEXT
        self.screen.blit(
            self.font_small.render(self.stats['status'], True, status_col), (px, py))
        py += 30

        # Stats rows
        rows = [
            ("Nodes Explored", self.stats['nodes_explored']),
            ("Frontier Size",  self.stats['frontier_size']),
            ("Path Length",    self.stats['path_length']),
            ("Time",           f"{self.stats['elapsed']:.3f}s"),
        ]
        for label, val in rows:
            self.screen.blit(
                self.font_small.render(f"{label}:  {val}", True, C_SUBTEXT), (px, py))
            py += 22

        # Legend
        py += 18
        self.screen.blit(self.font_info.render("Legend", True, C_ACCENT), (px, py))
        py += 26
        legend = [("Start (S)",  C_START), ("Target (T)", C_TARGET),
                  ("Wall",       C_WALL),  ("Frontier",   C_FRONTIER),
                  ("Explored",   C_EXPLORED), ("Path",    C_PATH)]
        for label, col in legend:
            pygame.draw.rect(self.screen, col, (px, py, 18, 18), border_radius=3)
            self.screen.blit(
                self.font_small.render(label, True, C_TEXT), (px + 26, py + 2))
            py += 26

        # Edit mode indicator
        py += 10
        mode_label = self.edit_mode.replace("_", " ").title()
        self.screen.blit(
            self.font_small.render(f"Edit Mode:  {mode_label}", True, C_ACCENT),
            (px, py))

    def _draw(self):
        self.screen.fill(C_BG)

        # Title bar
        title = self.font_title.render(
            "AI Pathfinder  –   ", True, C_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 6))

        # Buttons
        for b in self.algo_btns:
            b.draw(self.screen)
        for b in self.ctrl_btns:
            b.draw(self.screen)
        for b in self.mode_btns.values():
            b.draw(self.screen)

        self._draw_grid()
        self._draw_panel()
        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────────────────
    # Grid interaction
    # ─────────────────────────────────────────────────────────────────────────
    def _grid_click(self, mouse_pos):
        x, y = mouse_pos
        c = (x - GRID_OFFSET_X) // CELL_SIZE
        r = (y - GRID_OFFSET_Y) // CELL_SIZE
        if not (0 <= r < GRID_ROWS and 0 <= c < GRID_COLS):
            return

        if self.edit_mode == 'place_start':
            self.grid[self.start[0]][self.start[1]] = 0
            self.start = (r, c)
            self.grid[r][c] = 2

        elif self.edit_mode == 'place_target':
            self.grid[self.target[0]][self.target[1]] = 0
            self.target = (r, c)
            self.grid[r][c] = 3

        elif self.edit_mode == 'place_wall':
            if (r, c) not in (self.start, self.target):
                self.grid[r][c] = 0 if self.grid[r][c] == 1 else 1

        elif self.edit_mode == 'erase':
            if (r, c) not in (self.start, self.target):
                self.grid[r][c] = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        import threading
        dragging = False

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                # ── Algorithm selection ──
                for i, b in enumerate(self.algo_btns):
                    if b.handle(event):
                        for ob in self.algo_btns: ob.active = False
                        b.active = True
                        self.algo_idx = i
                        self._clear_search()

                # ── Mode selection ──
                for mode, b in self.mode_btns.items():
                    if b.handle(event):
                        for ob in self.mode_btns.values(): ob.active = False
                        b.active = True
                        self.edit_mode = mode

                # ── Control buttons ──
                if self.btn_run.handle(event) and not self.running:
                    t = threading.Thread(target=self._run_algorithm, daemon=True)
                    t.start()

                if self.btn_pause.handle(event):
                    self.paused = not self.paused
                    self.btn_pause.text = "Resume" if self.paused else "Pause"

                if self.btn_clear.handle(event) and not self.running:
                    self._clear_search()

                if self.btn_reset.handle(event) and not self.running:
                    self._init_grid()
                    self._clear_search()

                # ── Grid drawing (click + drag for walls) ──
                if event.type == pygame.MOUSEBUTTONDOWN and not self.running:
                    dragging = True
                    self._grid_click(event.pos)
                if event.type == pygame.MOUSEBUTTONUP:
                    dragging = False
                if event.type == pygame.MOUSEMOTION and dragging and not self.running:
                    if self.edit_mode in ('place_wall', 'erase'):
                        self._grid_click(event.pos)

            self._draw()
            self.clock.tick(60)


if __name__ == "__main__":
    PathfinderApp().run()

# agents/astar_agent.py
#
# A* Search Minesweeper Agent.
# Operates strictly on observation data without peeking at hidden mine positions.
# Uses an evaluation function f(n) = g(n) + h(n) in a priority queue to select the optimal move.

from collections import deque
import heapq
import random
from agents.base_agent import BaseAgent


class AStarAgent(BaseAgent):
    name = "AStarAgent"

    def __init__(self):
        self.safe_queue = deque()
        self.flag_queue = deque()
        self.known_mines = set()
        self.flagged = set()
        self.g_scores = {}  # Cost g(n) for explored frontier nodes

    def reset_state(self):
        self.safe_queue.clear()
        self.flag_queue.clear()
        self.known_mines.clear()
        self.flagged.clear()
        self.g_scores.clear()

    def _mark_mine(self, cell):
        if cell not in self.known_mines:
            self.known_mines.add(cell)
            if cell not in self.flagged:
                self.flagged.add(cell)
                self.flag_queue.append(cell)

    def _get_neighbors(self, r, c, rows, cols):
        neighbors = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    neighbors.append((nr, nc))
        return neighbors

    def choose_action(self, observation, env):
        rows = env.rows
        cols = env.cols

        # 1. Reset state on brand-new game
        total_revealed = sum(
            1 for r in range(rows) for c in range(cols) if observation[r][c] >= 0
        )
        if total_revealed == 0:
            self.reset_state()
            self.g_scores[(rows // 2, cols // 2)] = 0
            return ("reveal", rows // 2, cols // 2)

        # 2. Flag any queued mines
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        # 3. Pop from safe queue if available
        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # Sync known mines
        for r in range(rows):
            for c in range(cols):
                if observation[r][c] == -2:
                    self.known_mines.add((r, c))
                    self.flagged.add((r, c))

        # 4. Rule propagation to discover safe cells (h = 0)
        changed = True
        constraints = []
        while changed:
            changed = False
            constraints.clear()
            for r in range(rows):
                for c in range(cols):
                    val = observation[r][c]
                    if val >= 0:
                        unrevealed = []
                        flagged = 0
                        for nr, nc in self._get_neighbors(r, c, rows, cols):
                            if (nr, nc) in self.known_mines or observation[nr][nc] == -2:
                                flagged += 1
                            elif observation[nr][nc] == -1:
                                unrevealed.append((nr, nc))

                        eff = val - flagged
                        if unrevealed:
                            constraints.append(((r, c), eff, set(unrevealed)))

            for (r, c), eff, unrevealed in constraints:
                if eff == 0:
                    for cell in unrevealed:
                        if cell not in self.safe_queue and cell not in self.known_mines:
                            self.safe_queue.append(cell)
                            changed = True
                elif eff == len(unrevealed):
                    for cell in unrevealed:
                        if cell not in self.known_mines:
                            self._mark_mine(cell)
                            changed = True

        # Flag queued mines or pop from discovered safe cells
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # 4. A* Priority Queue Selection using f(n) = g(n) + h(n)
        # Candidate set: all unrevealed cells
        all_unrevealed = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] == -1 and (r, c) not in self.known_mines
        ]
        if not all_unrevealed:
            valid = env.valid_actions()
            if valid:
                return ("reveal", valid[0][0], valid[0][1])
            return ("reveal", 0, 0)

        # Compute heuristic risk h(n) for frontier cells
        frontier_risk = {}
        for (r, c), eff, unrevealed in constraints:
            if unrevealed:
                p = max(0.0, min(1.0, eff / len(unrevealed)))
                for u in unrevealed:
                    if u not in frontier_risk or p < frontier_risk[u]:
                        frontier_risk[u] = p

        remaining_mines = max(0, env.mines - len(self.known_mines))
        p_background = remaining_mines / max(1, len(all_unrevealed))

        pq = []
        for cell in all_unrevealed:
            # g(n): distance/step cost (scaled to keep risk dominant)
            g = self.g_scores.get(cell, 1.0)
            # h(n): estimated probability of mine
            h = frontier_risk.get(cell, p_background)
            f = h * 10.0 + g * 0.1
            heapq.heappush(pq, (f, cell))

        if pq:
            best_f, best_cell = heapq.heappop(pq)
            self.g_scores[best_cell] = self.g_scores.get(best_cell, 1.0) + 1.0
            return ("reveal", best_cell[0], best_cell[1])

        choice = random.choice(all_unrevealed)
        return ("reveal", choice[0], choice[1])

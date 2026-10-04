# agents/bfs_agent.py
#
# Breadth-First Search (BFS) Minesweeper Agent.
# Operates strictly on observation data without peeking at hidden mine positions.
# Uses BFS queue discipline to discover and expand safe cells layer by layer.

from collections import deque
import random
from agents.base_agent import BaseAgent


class BFSAgent(BaseAgent):
    name = "BFSAgent"

    def __init__(self):
        self.safe_queue = deque()  # FIFO Queue for BFS exploration
        self.flag_queue = deque()
        self.known_mines = set()
        self.flagged = set()

    def reset_state(self):
        self.safe_queue.clear()
        self.flag_queue.clear()
        self.known_mines.clear()
        self.flagged.clear()

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
            return ("reveal", rows // 2, cols // 2)

        # 2. Flag any queued mines
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        # 3. Pop next safe cell from BFS FIFO queue
        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # Sync known mines with flagged cells
        for r in range(rows):
            for c in range(cols):
                if observation[r][c] == -2:
                    self.known_mines.add((r, c))
                    self.flagged.add((r, c))

        # 4. BFS Frontier Exploration to discover new safe cells
        visited = set()
        seeds = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] >= 0
        ]

        bfs_queue = deque(seeds)
        while bfs_queue:
            curr_r, curr_c = bfs_queue.popleft()
            if (curr_r, curr_c) in visited:
                continue
            visited.add((curr_r, curr_c))

            val = observation[curr_r][curr_c]
            neighbors = self._get_neighbors(curr_r, curr_c, rows, cols)
            unrevealed = []
            flagged = 0

            for nr, nc in neighbors:
                if (nr, nc) in self.known_mines or observation[nr][nc] == -2:
                    flagged += 1
                elif observation[nr][nc] == -1:
                    unrevealed.append((nr, nc))
                elif observation[nr][nc] >= 0 and (nr, nc) not in visited:
                    bfs_queue.append((nr, nc))

            eff = val - flagged
            if eff == 0:
                for cell in unrevealed:
                    if cell not in self.safe_queue and cell not in self.known_mines:
                        self.safe_queue.append(cell)
            elif eff == len(unrevealed):
                for cell in unrevealed:
                    self._mark_mine(cell)

        # Flag queued mines or pop from discovered safe cells
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # 4. Fallback: choose valid unrevealed action with lowest estimated risk
        all_unrevealed = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] == -1 and (r, c) not in self.known_mines
        ]
        if all_unrevealed:
            return ("reveal", all_unrevealed[0][0], all_unrevealed[0][1])

        valid = env.valid_actions()
        if valid:
            return ("reveal", valid[0][0], valid[0][1])
        return ("reveal", 0, 0)

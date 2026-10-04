# agents/dfs_agent.py
#
# Depth-First Search (DFS) Minesweeper Agent.
# Operates strictly on observation data without peeking at hidden mine positions.
# Uses DFS LIFO stack discipline to deeply explore safe branches along the frontier.

import random
from agents.base_agent import BaseAgent


class DFSAgent(BaseAgent):
    name = "DFSAgent"

    def __init__(self):
        self.safe_stack = []  # LIFO Stack for DFS exploration
        self.flag_stack = []
        self.known_mines = set()
        self.flagged = set()

    def reset_state(self):
        self.safe_stack.clear()
        self.flag_stack.clear()
        self.known_mines.clear()
        self.flagged.clear()

    def _mark_mine(self, cell):
        if cell not in self.known_mines:
            self.known_mines.add(cell)
            if cell not in self.flagged:
                self.flagged.add(cell)
                self.flag_stack.append(cell)

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
        while self.flag_stack:
            fr, fc = self.flag_stack.pop()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        # 3. Pop next safe cell from DFS LIFO stack
        while self.safe_stack:
            r, c = self.safe_stack.pop()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # Sync known mines with flagged cells
        for r in range(rows):
            for c in range(cols):
                if observation[r][c] == -2:
                    self.known_mines.add((r, c))
                    self.flagged.add((r, c))

        # 4. DFS Frontier Exploration to discover new safe cells
        visited = set()
        seeds = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] >= 0
        ]

        dfs_stack = list(seeds)
        while dfs_stack:
            curr_r, curr_c = dfs_stack.pop()
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
                    dfs_stack.append((nr, nc))

            eff = val - flagged
            if eff == 0:
                for cell in unrevealed:
                    if cell not in self.safe_stack and cell not in self.known_mines:
                        self.safe_stack.append(cell)
            elif eff == len(unrevealed):
                for cell in unrevealed:
                    self._mark_mine(cell)

        # Flag queued mines or pop from discovered safe cells
        while self.flag_stack:
            fr, fc = self.flag_stack.pop()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        while self.safe_stack:
            r, c = self.safe_stack.pop()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # 4. Fallback: choose valid unrevealed action
        all_unrevealed = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] == -1 and (r, c) not in self.known_mines
        ]
        if all_unrevealed:
            return ("reveal", all_unrevealed[-1][0], all_unrevealed[-1][1])

        valid = env.valid_actions()
        if valid:
            return ("reveal", valid[0][0], valid[0][1])
        return ("reveal", 0, 0)

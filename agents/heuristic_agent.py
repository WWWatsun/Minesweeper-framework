# agents/heuristic_agent.py
#
# Heuristic / Rule-based Minesweeper solver agent.
# Strictly complies with fair-play rules: operates ONLY on observation data (-1, -2, 0..8)
# and never inspects hidden bomb locations.

from collections import deque
import random
from agents.base_agent import BaseAgent


class HeuristicAgent(BaseAgent):
    name = "HeuristicAgent"

    def __init__(self):
        self.safe_queue = deque()
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

        # 1. Detect new game: if no cells are revealed yet, reset internal state
        total_revealed = sum(
            1 for r in range(rows) for c in range(cols) if observation[r][c] >= 0
        )
        if total_revealed == 0:
            self.reset_state()
            return ("reveal", rows // 2, cols // 2)

        # 2. Check if there are mines queued to be flagged
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        # 3. Check if safe queue has valid unrevealed actions
        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # Sync known_mines with any flags present in observation (-2)
        for r in range(rows):
            for c in range(cols):
                if observation[r][c] == -2:
                    self.known_mines.add((r, c))
                    self.flagged.add((r, c))

        # 3. Iterative deduction using Single-Cell and Subset Rules
        changed = True
        while changed:
            changed = False

            # Build frontier constraints
            constraints = []  # list of (r, c, effective_mines, list_of_unknown_neighbors)
            for r in range(rows):
                for c in range(cols):
                    val = observation[r][c]
                    if val >= 0:
                        neighbors = self._get_neighbors(r, c, rows, cols)
                        unrevealed = []
                        mine_count = 0
                        for nr, nc in neighbors:
                            if (nr, nc) in self.known_mines or observation[nr][nc] == -2:
                                mine_count += 1
                            elif observation[nr][nc] == -1:
                                unrevealed.append((nr, nc))

                        eff = val - mine_count
                        if unrevealed:
                            constraints.append(((r, c), eff, set(unrevealed)))

            # 3A. Single-Cell Rules
            for (r, c), eff, unrevealed in constraints:
                # All remaining are safe
                if eff == 0:
                    for cell in unrevealed:
                        if cell not in self.safe_queue and cell not in self.known_mines:
                            self.safe_queue.append(cell)
                            changed = True
                # All remaining are mines
                elif eff == len(unrevealed):
                    for cell in unrevealed:
                        if cell not in self.known_mines:
                            self._mark_mine(cell)
                            changed = True

            if changed:
                continue

            # 3B. Subset / Set-Difference Rules
            # If U1 is a subset of U2, the difference U2 \ U1 contains E2 - E1 mines
            n_const = len(constraints)
            for i in range(n_const):
                c1, e1, u1 = constraints[i]
                for j in range(n_const):
                    if i == j:
                        continue
                    c2, e2, u2 = constraints[j]

                    if u1.issubset(u2):
                        diff = u2 - u1
                        diff_mines = e2 - e1
                        if len(diff) > 0:
                            if diff_mines == 0:
                                for cell in diff:
                                    if cell not in self.safe_queue and cell not in self.known_mines:
                                        self.safe_queue.append(cell)
                                        changed = True
                            elif diff_mines == len(diff):
                                for cell in diff:
                                    if cell not in self.known_mines:
                                        self._mark_mine(cell)
                                        changed = True
                if changed:
                    break

        # 4. If deductions found mines to flag or safe cells to reveal
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # 5. Probabilistic / Heuristic Guessing Fallback
        # When pure logic reaches an impasse, estimate mine risk for all candidate unrevealed cells
        all_unrevealed = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] == -1 and (r, c) not in self.known_mines
        ]

        if not all_unrevealed:
            # Fallback to any valid action
            actions = env.valid_actions()
            if actions:
                return ("reveal", actions[0][0], actions[0][1])
            return ("reveal", 0, 0)

        # Estimate risk for each unrevealed frontier cell
        frontier_risk = {}
        for (r, c), eff, unrevealed in constraints:
            if len(unrevealed) > 0:
                p = max(0.0, min(1.0, eff / len(unrevealed)))
                for u in unrevealed:
                    if u not in frontier_risk or p < frontier_risk[u]:
                        frontier_risk[u] = p

        # Background mine density for isolated cells
        remaining_mines = max(0, env.mines - len(self.known_mines))
        background_density = remaining_mines / max(1, len(all_unrevealed))

        best_cell = None
        min_risk = float("inf")

        for cell in all_unrevealed:
            if cell in frontier_risk:
                risk = frontier_risk[cell]
            else:
                # Isolated cell gets background density
                risk = background_density

            if risk < min_risk:
                min_risk = risk
                best_cell = cell

        if best_cell is not None:
            return ("reveal", best_cell[0], best_cell[1])

        # Ultimate fallback
        choice = random.choice(all_unrevealed)
        return ("reveal", choice[0], choice[1])

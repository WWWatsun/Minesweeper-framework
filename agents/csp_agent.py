# agents/csp_agent.py
#
# Advanced Constraint Satisfaction Problem (CSP) & Probabilistic Minesweeper Solver.
# Fair-play guarantee: Strictly reads from observation (-1, -2, 0..8) and env dimensions.
# Never accesses tile.is_mine or internal board mine layout.

from collections import deque
import math
import random
from agents.base_agent import BaseAgent


class CSPAgent(BaseAgent):
    name = "CSPAgent"

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
        total_mines = env.mines

        # 1. Detect new game: if no cells are revealed yet, reset internal state
        total_revealed = sum(
            1 for r in range(rows) for c in range(cols) if observation[r][c] >= 0
        )
        if total_revealed == 0:
            self.reset_state()
            return ("reveal", rows // 2, cols // 2)

        # 2. Flag any queued mines so they visibly appear with red flags on the board
        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        # 3. Pop from safe queue if any safe cell is still unrevealed
        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # Sync known mines from observation flags
        for r in range(rows):
            for c in range(cols):
                if observation[r][c] == -2:
                    self.known_mines.add((r, c))
                    self.flagged.add((r, c))

        # 3. Main Deductive Loop (Single-Cell + Subset Rules)
        self._run_rule_deductions(observation, rows, cols)

        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # 4. Global CSP / Component Backtracking Search
        csp_safe_found = self._run_csp_solver(observation, rows, cols, total_mines)

        while self.flag_queue:
            fr, fc = self.flag_queue.popleft()
            if observation[fr][fc] == -1:
                return ("flag", fr, fc)

        while self.safe_queue:
            r, c = self.safe_queue.popleft()
            if observation[r][c] == -1 and (r, c) not in self.known_mines:
                return ("reveal", r, c)

        # 5. Probabilistic Fallback (Minimum Mine Risk)
        best_cell = self._compute_best_probabilistic_move(observation, rows, cols, total_mines)
        if best_cell:
            return ("reveal", best_cell[0], best_cell[1])

        # 6. Fallback to any valid action
        valid = env.valid_actions()
        if valid:
            return ("reveal", valid[0][0], valid[0][1])
        return ("reveal", 0, 0)

    def _run_rule_deductions(self, observation, rows, cols):
        """Iterative propagation of single-cell and subset rules."""
        changed = True
        while changed:
            changed = False
            constraints = []

            for r in range(rows):
                for c in range(cols):
                    val = observation[r][c]
                    if val >= 0:
                        unrevealed = []
                        mine_count = 0
                        for nr, nc in self._get_neighbors(r, c, rows, cols):
                            if (nr, nc) in self.known_mines or observation[nr][nc] == -2:
                                mine_count += 1
                            elif observation[nr][nc] == -1:
                                unrevealed.append((nr, nc))

                        eff = val - mine_count
                        if unrevealed:
                            constraints.append(((r, c), eff, set(unrevealed)))

            # Single-cell rules
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

            if changed:
                continue

            # Subset rules
            n = len(constraints)
            for i in range(n):
                c1, e1, u1 = constraints[i]
                for j in range(n):
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

    def _run_csp_solver(self, observation, rows, cols, total_mines):
        """Builds linear constraints, clusters into independent components, and searches models."""
        # 1. Collect active constraints
        constraints = []
        frontier_vars = set()
        for r in range(rows):
            for c in range(cols):
                val = observation[r][c]
                if val >= 0:
                    unrevealed = []
                    mine_count = 0
                    for nr, nc in self._get_neighbors(r, c, rows, cols):
                        if (nr, nc) in self.known_mines or observation[nr][nc] == -2:
                            mine_count += 1
                        elif observation[nr][nc] == -1:
                            unrevealed.append((nr, nc))

                    eff = val - mine_count
                    if unrevealed:
                        constraints.append((eff, unrevealed))
                        frontier_vars.update(unrevealed)

        if not frontier_vars:
            return False

        # 2. Decompose into connected components
        components = self._decompose_components(constraints)

        new_info = False
        for comp_constraints, comp_vars in components:
            if len(comp_vars) > 22:
                # Avoid exponential blowup on overly large dense components
                continue

            models = self._solve_component(comp_constraints, comp_vars)
            if not models:
                continue

            num_models = len(models)
            var_mine_counts = {v: 0 for v in comp_vars}
            for model in models:
                for v in comp_vars:
                    if model[v] == 1:
                        var_mine_counts[v] += 1

            for v in comp_vars:
                if var_mine_counts[v] == 0:
                    # Guaranteed safe in ALL models
                    if v not in self.safe_queue and v not in self.known_mines:
                        self.safe_queue.append(v)
                        new_info = True
                elif var_mine_counts[v] == num_models:
                    # Guaranteed mine in ALL models
                    if v not in self.known_mines:
                        self._mark_mine(v)
                        new_info = True

        if new_info:
            # Re-run rule deduction with newly identified mines/safes
            self._run_rule_deductions(observation, rows, cols)
            return True

        return False

    def _decompose_components(self, constraints):
        """Partitions constraints and variables into independent connected subgraphs."""
        var_to_constraints = {}
        for idx, (eff, unrev) in enumerate(constraints):
            for v in unrev:
                var_to_constraints.setdefault(v, []).append(idx)

        visited_constraints = set()
        components = []

        for idx in range(len(constraints)):
            if idx in visited_constraints:
                continue

            comp_c_indices = []
            comp_vars = set()
            queue = deque([idx])
            visited_constraints.add(idx)

            while queue:
                c_idx = queue.popleft()
                comp_c_indices.append(c_idx)
                eff, unrev = constraints[c_idx]
                for v in unrev:
                    comp_vars.add(v)
                    for neighbor_c_idx in var_to_constraints.get(v, []):
                        if neighbor_c_idx not in visited_constraints:
                            visited_constraints.add(neighbor_c_idx)
                            queue.append(neighbor_c_idx)

            comp_constraints = [constraints[i] for i in comp_c_indices]
            components.append((comp_constraints, list(comp_vars)))

        return components

    def _solve_component(self, comp_constraints, comp_vars):
        """Backtracking search with forward pruning to find all valid binary models."""
        var_list = comp_vars
        var_index = {v: i for i, v in enumerate(var_list)}
        n_vars = len(var_list)

        # Pre-index constraints: for each constraint, list of variable indices and required sum
        indexed_constraints = []
        var_to_c = [[] for _ in range(n_vars)]
        for c_idx, (eff, unrev) in enumerate(comp_constraints):
            v_indices = [var_index[v] for v in unrev]
            indexed_constraints.append((eff, v_indices))
            for vi in v_indices:
                var_to_c[vi].append(c_idx)

        models = []
        assignment = [-1] * n_vars

        # Track constraint sums: current_assigned_mines, remaining_unassigned_vars
        c_current = [0] * len(indexed_constraints)
        c_unassigned = [len(v_indices) for eff, v_indices in indexed_constraints]

        def backtrack(v_idx):
            if v_idx == n_vars:
                models.append({var_list[i]: assignment[i] for i in range(n_vars)})
                return

            # Try assigning 0 (Safe) and then 1 (Mine)
            for val in (0, 1):
                # Check feasibility with affected constraints
                feasible = True
                for c_i in var_to_c[v_idx]:
                    target, _ = indexed_constraints[c_i]
                    new_curr = c_current[c_i] + val
                    new_unassigned = c_unassigned[c_i] - 1

                    if new_curr > target or new_curr + new_unassigned < target:
                        feasible = False
                        break

                if feasible:
                    assignment[v_idx] = val
                    for c_i in var_to_c[v_idx]:
                        c_current[c_i] += val
                        c_unassigned[c_i] -= 1

                    backtrack(v_idx + 1)

                    for c_i in var_to_c[v_idx]:
                        c_current[c_i] -= val
                        c_unassigned[c_i] += 1
                    assignment[v_idx] = -1

        backtrack(0)
        return models

    def _compute_best_probabilistic_move(self, observation, rows, cols, total_mines):
        """Estimates mine probability across frontier and isolated cells to select the safest guess."""
        all_unrevealed = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if observation[r][c] == -1 and (r, c) not in self.known_mines
        ]

        if not all_unrevealed:
            return None

        # Collect constraints and frontier
        constraints = []
        frontier_vars = set()
        for r in range(rows):
            for c in range(cols):
                val = observation[r][c]
                if val >= 0:
                    unrevealed = []
                    mine_count = 0
                    for nr, nc in self._get_neighbors(r, c, rows, cols):
                        if (nr, nc) in self.known_mines or observation[nr][nc] == -2:
                            mine_count += 1
                        elif observation[nr][nc] == -1:
                            unrevealed.append((nr, nc))

                    eff = val - mine_count
                    if unrevealed:
                        constraints.append((eff, unrevealed))
                        frontier_vars.update(unrevealed)

        isolated_vars = [u for u in all_unrevealed if u not in frontier_vars]
        cell_probabilities = {}

        if frontier_vars:
            components = self._decompose_components(constraints)
            known_mines_count = len(self.known_mines)
            n_isolated = len(isolated_vars)

            for comp_constraints, comp_vars in components:
                if len(comp_vars) <= 22:
                    models = self._solve_component(comp_constraints, comp_vars)
                else:
                    models = []

                if models:
                    # Model counting with combinatorial weights
                    comp_var_weights = {v: 0 for v in comp_vars}
                    total_comp_weight = 0

                    for model in models:
                        model_mines = sum(model.values())
                        remaining_mines = total_mines - known_mines_count - model_mines

                        if 0 <= remaining_mines <= n_isolated:
                            weight = math.comb(n_isolated, remaining_mines)
                        else:
                            weight = 1  # Fallback uniform weight if mine counts exceed bounds

                        total_comp_weight += weight
                        for v in comp_vars:
                            if model[v] == 1:
                                comp_var_weights[v] += weight

                    if total_comp_weight > 0:
                        for v in comp_vars:
                            cell_probabilities[v] = comp_var_weights[v] / total_comp_weight
                    else:
                        for v in comp_vars:
                            cell_probabilities[v] = sum(m[v] for m in models) / len(models)
                else:
                    # Local approximation for uncomputable components
                    for eff, unrev in comp_constraints:
                        p = max(0.0, min(1.0, eff / max(1, len(unrev))))
                        for v in unrev:
                            if v not in cell_probabilities or p < cell_probabilities[v]:
                                cell_probabilities[v] = p

        # Background probability for isolated cells
        remaining_mines = max(0, total_mines - len(self.known_mines))
        p_isolated = remaining_mines / max(1, len(all_unrevealed))

        for v in isolated_vars:
            cell_probabilities[v] = p_isolated

        # Pick cell with lowest mine probability
        min_p = float("inf")
        best_cells = []

        for cell in all_unrevealed:
            p = cell_probabilities.get(cell, p_isolated)
            if p < min_p - 1e-7:
                min_p = p
                best_cells = [cell]
            elif abs(p - min_p) < 1e-7:
                best_cells.append(cell)

        if not best_cells:
            return all_unrevealed[0]

        # Tie-breaker: prioritize cells with more unrevealed neighbors for greater opening potential
        best_cells.sort(
            key=lambda c: sum(
                1 for nr, nc in self._get_neighbors(c[0], c[1], rows, cols) if observation[nr][nc] == -1
            ),
            reverse=True,
        )

        return best_cells[0]

from core.board import Board, GameState

REVEAL = "reveal"
FLAG = "flag"

class MinesweeperEnv:
    def __init__(self, rows=15, cols=15, mines=20, first_click_safe=True):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.first_click_safe = first_click_safe

        self.board = None
        self.done = False
        self.steps_taken = 0

    def reset(self):
        self.board = Board(self.rows, self.cols, self.mines, first_click_safe=self.first_click_safe)
        self.done = False
        self.steps_taken = 0
        return self._get_obs()

    def step(self, action):
        if self.done:
            raise RuntimeError("Ván đã kết thúc - reset() trước khi step() tiếp.")

        action_type, x, y = action
        self.steps_taken += 1
        reward = 0.0
        info = {}

        if action_type == REVEAL:
            if self.board._is_inside(x, y):
                tile = self.board.board_grid[x][y]
                wasted = tile.revealed or tile.flagged
            else:
                wasted = True
            
            alive = self.board.reveal(x, y)
            if not alive:
                reward = -1.0
                self.done = True
                info["result"] = "loss"
            elif self.board.state == GameState.WON:
                reward = 1.0
                self.done = True
                info["result"] = "win"
            elif wasted:
                reward = 0.0
            else:
                reward = 0.01
        elif action_type == FLAG:
            self.board.toggle_flag(x, y)
        else:
            raise ValueError(f"Action không hợp lệ: {action_type!r} (chỉ chấp nhận 'reveal' hoặc 'flag')")

        return self._get_obs(), reward, self.done, info

    def _get_obs(self):
        return self.board.to_observation()

    def render(self):
        """In bàn chơi ra console - dùng để debug agent mà không cần mở pygame."""
        self.board.display()

    def valid_actions(self):
        """Danh sách toạ độ các ô CHƯA đào - hữu ích cho baseline/random agent,
        hoặc để agent thông minh hơn lọc bớt không gian tìm kiếm."""
        return [
            (x, y)
            for x in range(self.rows)
            for y in range(self.cols)
            if not self.board.board_grid[x][y].revealed and not self.board.board_grid[x][y].flagged
        ]
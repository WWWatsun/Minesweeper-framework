# Source game logic duy nhất trong toàn bộ framework
# Bao gồm implementation của game rules, game board, action behaviors
# Làm việc chủ yếu với board_grid là một matrix 2 chiều chứa thông tin của từng tile
#
# Thay đổi so với phiên bản cũ:
# - Tách biệt khỏi render và GUI (chuyển qua sprites.py và main.py). Do đó implementation của các
# search algorithms (agents) và environment liên quan đến game logic không còn cần import pygame nữa.
# - Tách biệt khỏi event handler (đã chuyển qua main.py) 


import random
from collections import deque
from core.tile import Tile

class GameState:
    ONGOING = "ongoing"
    WON = "won"
    LOST = "lost"


# Bàn chơi là một matrix 2 chiều: board_grid[rows][cols] với first_click_safe là
# một biến đảm bảo lần đào đầu tiên an toàn, giúp các agents tránh khỏi trường hợp
# chết oan ở nước đầu tiên gây sai lệch thông số
class Board:
    def __init__(self, rows, cols, mines, first_click_safe=True):
        self.rows = rows
        self.cols = cols
        max_mines = rows * cols - (1 if first_click_safe else 0)
        if not (0 < mines <= max_mines):
            raise ValueError(f"Số mìn không hợp lệ: mines={mines}, nhưng bàn {rows}x{cols} "f"chỉ cho phép tối đa {max_mines} mìn"
        + (" (trừ 1 ô an toàn cho first click)" if first_click_safe else "")
        )
        self.mines = mines
        self.first_click_safe = first_click_safe

        self.board_grid = [[Tile(x, y) for y in range(cols)] for x in range(rows)]
        self.state = GameState.ONGOING
        self._mines_placed = False
        self.exploded_tile = None

#---------- Initialize game board ----------

# Hàm đặt mìn lên toàn bộ board
# Biến exclude = (x, y) là một tuple đảm bảo first click ở tọa độ [x][y] sẽ safe
    def _place_mines(self, exclude=None):
        count = 0
        while count < self.mines:
            x = random.randint(0, self.rows - 1)
            y = random.randint(0, self.cols - 1)
            if exclude is not None and (x, y) == exclude:
                continue
            
            tile = self.board_grid[x][y]
            if not tile.is_mine:
                tile.is_mine = True
                count += 1
# Đếm số mìn xung quanh một tile.
    def _compute_adjacency(self):
        for x in range(self.rows):
            for y in range(self.cols):
                tile = self.board_grid[x][y]
                if not tile.is_mine:
                    tile.adjacent_mines = sum(
                        1 for nx, ny in self._neighbours(x, y) if self.board_grid[nx][ny].is_mine
                    )

#---------- Helper functions ----------   

# Kiểm tra tọa độ out of bound.
    def _is_inside(self, x, y):
        return 0 <= x < self.rows and 0 <= y < self.cols

# Trả về một list chứa tọa độ của các ô xung quanh, phục vụ cho việc đếm mìn
    def _neighbours(self, x, y):
        adj_coord = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self._is_inside(nx, ny):
                    adj_coord.append((nx, ny))
        return adj_coord

    def _check_win(self):
        for row in self.board_grid:
            for tile in row:
                if not tile.is_mine and not tile.revealed:
                    return
        self.state = GameState.WON

#---------- Action functions ---------- 
# Can be used by both player and agents

# Hành động lật một tile. 
# - Đối với player, hành động này sẽ được thực hiện gắn liền với MOUSEBUTTONDOWN
# - Agent có thể sử dụng hành động đào này thông qua board.reveal(x, y)
# - Return True khi nước đi an toàn và player/agent còn sống. Lật trúng mìn thì chết và return False.
    def reveal(self, x, y):
        if self.state != GameState.ONGOING:
            return self.state != GameState.LOST
        if not self._is_inside(x, y):
            return True

        tile = self.board_grid[x][y]
        if tile.flagged or tile.revealed:
            return True
        # Nếu mìn chưa được đặt lên board khi reveal -> nước đi đầu tiên luôn safe vì trong board ko có mìn
        # Thực hiện đặt mìn sau khi đã lật tile đầu tiên
        if not self._mines_placed:
            self._place_mines(exclude=(x, y) if self.first_click_safe else None)
            self._compute_adjacency()
            self._mines_placed = True
            tile = self.board_grid[x][y]

        if tile.is_mine:
            tile.revealed = True
            self.state = GameState.LOST
            self.exploded_tile = (x, y)
            return False

        # Áp dụng BFS để thực hiện hiệu ứng loang khi lật trúng một ô empty.
        queue = deque([(x, y)])
        while queue:
            cx, cy = queue.popleft()
            ctile = self.board_grid[cx][cy]
            if ctile.revealed or ctile.flagged:
                continue
            ctile.revealed = True
            if ctile.adjacent_mines == 0:
                for nx, ny in self._neighbours(cx, cy):
                    if not self.board_grid[nx][ny].revealed and not self.board_grid[nx][ny].flagged:
                        queue.append((nx, ny))

        self._check_win()
        return True
    
    # flagged = not.flagged: toggle flag 
    def toggle_flag(self, x, y):
        if self.state != GameState.ONGOING or not self._is_inside(x, y):
            return
        tile = self.board_grid[x][y]
        if not tile.revealed:
            tile.flagged = not tile.flagged

#---------- Debug functions ---------- 
# Can be used by both player and agents

    def to_observation(self):
        # Ma trận quan sát dành cho agent - không lộ vị trí mìn chưa đào (đúng luật chơi):
        #    -1  = ô chưa đào (unknown)
        #    -2  = ô đã cắm cờ
        #    0..8 = số mìn lân cận (ô đã đào)

        obs = [[0] * self.cols for _ in range(self.rows)]
        for x in range(self.rows):
            for y in range(self.cols):
                tile = self.board_grid[x][y]
                if tile.flagged and not tile.revealed:
                    obs[x][y] = -2
                elif not tile.revealed:
                    obs[x][y] = -1
                else:
                    obs[x][y] = tile.adjacent_mines
        return obs

    def display(self):
        # In bàn chơi ra console - hữu ích để debug agent mà không cần mở pygame.
        for row in self.board_grid:
            print(row)







    

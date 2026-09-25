# Structure của một Tile.

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_mine = False
        self.adjacent_mines = 0
        self.revealed = False
        self.flagged = False

    def __repr__(self):
        if self.flagged and not self.revealed:
            return "-2"
        if not self.revealed:
            return "-1"
        if self.is_mine:
            return "X"
        if self.adjacent_mines == 0:
            return "0"
        return str(self.adjacent_mines)


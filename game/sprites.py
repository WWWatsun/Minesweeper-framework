import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_settings import *

class BoardView:
    def __init__(self, board):
        self.board = board

        self._wrong_flags = set()

    def _tile_image(self, tile):
        if (tile.x, tile.y) in self._wrong_flags:
            return tile_not_mine
        if tile.flagged and not tile.revealed:
            return tile_flag
        if not tile.revealed:
            return tile_unknown
        if tile.is_mine:
            if (tile.x, tile.y) == self.board.exploded_tile:
                return tile_exploded
            return tile_mine
        if tile.adjacent_mines == 0:
            return tile_empty
        return tile_numbers[tile.adjacent_mines - 1]

    def draw(self, surface):
        for row in self.board.board_grid:
            for tile in row:
                image = self._tile_image(tile)
                surface.blit(image, (tile.x * TILESIZE, tile.y * TILESIZE))

    def reveal_all_on_loss(self):
        """Khi thua: hiện toàn bộ mìn, và với các ô bị cắm cờ SAI (không phải mìn),
        gỡ cờ và đánh dấu để hiện ảnh 'not mine' cho người chơi biết mình đoán nhầm."""
        for row in self.board.board_grid:
            for tile in row:
                if tile.is_mine:
                    tile.revealed = True
                elif tile.flagged and not tile.is_mine:
                    tile.flagged = False
                    tile.revealed = True
                    self._wrong_flags.add((tile.x, tile.y))

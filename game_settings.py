# Game setting để init toàn bộ các var, consts cần dùng.
# Thực hiện load các assets có sẵn
import pygame
import os

# Load toàn bộ assets cần dùng
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 200, 0)
HOVER_GREEN = (0, 255, 0)
RED = (200, 0, 0)
BGCOLOUR = DARKGREY

# Variable
TILESIZE = 32
FPS = 60
TITLE = "Minesweeper Clone"
DEFAULT_ROW_NUM = 15
DEFAULT_COL_NUM = 15
DEFAULT_MINE_NUM = 20


# Font
pygame.font.init()
FONT_SMALL = pygame.font.SysFont("arial", 20)
FONT_MEDIUM = pygame.font.SysFont("arial", 28, bold=True)
FONT_LARGE = pygame.font.SysFont("arial", 36, bold=True)

# Ảnh từ folder "Assets"
tile_numbers = []
for i in range(1, 9):
    tile_numbers.append(pygame.transform.scale(pygame.image.load(os.path.join("assets", f"Tile{i}.png")), (TILESIZE, TILESIZE)))

tile_empty = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileEmpty.png")), (TILESIZE, TILESIZE))
tile_exploded = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileExploded.png")), (TILESIZE, TILESIZE))
tile_flag = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileFlag.png")), (TILESIZE, TILESIZE))
tile_mine = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileMine.png")), (TILESIZE, TILESIZE))
tile_unknown = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileUnknown.png")), (TILESIZE, TILESIZE))
tile_not_mine = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileNotMine.png")), (TILESIZE, TILESIZE))




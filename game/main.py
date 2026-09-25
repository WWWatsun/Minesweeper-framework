# Handle game state của phần chơi dành cho player

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from game_settings import *
from core.board import Board, GameState
from game.sprites import BoardView


class Button:
    def __init__(self, x, y, width, height, text, bg_color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=5)
        text_surf = FONT_MEDIUM.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.rows = DEFAULT_ROW_NUM
        self.cols = DEFAULT_COL_NUM
        self.mines = DEFAULT_MINE_NUM

        self.screen = pygame.display.set_mode((450, 400))

    def settings_menu(self):
        self.screen = pygame.display.set_mode((450, 400))

        btn_row_sub = Button(250, 80, 40, 40, "-", LIGHTGREY, WHITE)
        btn_row_add = Button(370, 80, 40, 40, "+", LIGHTGREY, WHITE)

        btn_col_sub = Button(250, 140, 40, 40, "-", LIGHTGREY, WHITE)
        btn_col_add = Button(370, 140, 40, 40, "+", LIGHTGREY, WHITE)

        btn_mine_sub = Button(250, 200, 40, 40, "-", LIGHTGREY, WHITE)
        btn_mine_add = Button(370, 200, 40, 40, "+", LIGHTGREY, WHITE)

        btn_start = Button(125, 300, 200, 50, "PLAY GAME", GREEN, WHITE)

        in_menu = True
        while in_menu:
            self.clock.tick(FPS)
            self.screen.fill(BGCOLOUR)

            title_surf = FONT_LARGE.render("GAME SETTINGS", True, WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(center=(225, 35)))

            row_txt = FONT_MEDIUM.render(f"Rows: {self.rows}", True, WHITE)
            col_txt = FONT_MEDIUM.render(f"Cols: {self.cols}", True, WHITE)
            mine_txt = FONT_MEDIUM.render(f"Mines: {self.mines}", True, WHITE)

            self.screen.blit(row_txt, (40, 85))
            self.screen.blit(col_txt, (40, 145))
            self.screen.blit(mine_txt, (40, 205))

            btn_row_sub.draw(self.screen)
            btn_row_add.draw(self.screen)
            btn_col_sub.draw(self.screen)
            btn_col_add.draw(self.screen)
            btn_mine_sub.draw(self.screen)
            btn_mine_add.draw(self.screen)
            btn_start.draw(self.screen)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos

                    if btn_row_sub.is_clicked(pos):
                        self.rows = max(1, self.rows - 1)
                    elif btn_row_add.is_clicked(pos):
                        self.rows = min(30, self.rows + 1)

                    if btn_col_sub.is_clicked(pos):
                        self.cols = max(1, self.cols - 1)
                    elif btn_col_add.is_clicked(pos):
                        self.cols = min(30, self.cols + 1)

                    max_allowed_mines = (self.rows * self.cols) - 1
                    self.mines = min(self.mines, max_allowed_mines)

                    if btn_mine_sub.is_clicked(pos):
                        self.mines = max(1, self.mines - 1)
                    elif btn_mine_add.is_clicked(pos):
                        self.mines = min(max_allowed_mines, self.mines + 1)

                    if btn_start.is_clicked(pos):
                        in_menu = False

    def new(self):
        """Khi bắt đầu ván mới: tạo core.Board (nguồn logic) + BoardView (vẽ),
        và chỉnh màn hình theo đúng kích thước bàn chơi đã chọn."""
        width = self.rows * TILESIZE
        height = self.cols * TILESIZE
        self.screen = pygame.display.set_mode((width, height))
        self.board = Board(self.rows, self.cols, self.mines)
        self.view = BoardView(self.board)

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.draw()
        self.end_screen()

    def draw(self):
        self.screen.fill(BGCOLOUR)
        self.view.draw(self.screen)
        pygame.display.flip()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                mx //= TILESIZE
                my //= TILESIZE

                if 0 <= mx < self.rows and 0 <= my < self.cols:
                    tile = self.board.board_grid[mx][my]

                    if event.button == 1:  # Nút chuột trái: đào tile
                        if not tile.flagged:
                            alive = self.board.reveal(mx, my)
                            if not alive:
                                self.view.reveal_all_on_loss()
                                self.playing = False

                    elif event.button == 3:  # Nút chuột phải: cắm/gỡ cờ
                        self.board.toggle_flag(mx, my)

                    if self.board.state == GameState.WON:
                        self.playing = False

    def end_screen(self):
        """Màn hình kết thúc ván chơi - click chuột để về menu cài đặt"""
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False


if __name__ == "__main__":
    game = Game()
    while True:
        game.settings_menu()
        game.new()
        game.run()




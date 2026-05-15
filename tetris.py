#!/usr/bin/env python3
"""俄罗斯方块 - 使用 pygame 实现"""

import random
import sys

import pygame

# 网格与窗口
COLS = 10
ROWS = 20
CELL = 30
SIDEBAR = 180
WIDTH = COLS * CELL + SIDEBAR
HEIGHT = ROWS * CELL
FPS = 60

# 颜色 (R, G, B)
BLACK = (15, 15, 25)
GRID_COLOR = (35, 35, 50)
WHITE = (240, 240, 245)
GRAY = (120, 120, 140)
RED = (220, 60, 60)

# 七种方块形状 (相对坐标)
SHAPES = {
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "O": [(1, 0), (2, 0), (1, 1), (2, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}

COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}


def rotate_cells(cells):
    """顺时针旋转方块坐标"""
    if not cells:
        return cells
    cx = sum(x for x, _ in cells) / len(cells)
    cy = sum(y for _, y in cells) / len(cells)
    return [
        (int(round(cx + (y - cy))), int(round(cy - (x - cx))))
        for x, y in cells
    ]


class Piece:
    def __init__(self, kind=None):
        self.kind = kind or random.choice(list(SHAPES.keys()))
        self.cells = list(SHAPES[self.kind])
        self.color = COLORS[self.kind]
        self.x = COLS // 2 - 2
        self.y = 0

    def absolute_cells(self):
        return [(self.x + dx, self.y + dy) for dx, dy in self.cells]

    def rotated(self):
        p = Piece(self.kind)
        p.cells = rotate_cells(self.cells)
        p.color = self.color
        p.x, p.y = self.x, self.y
        return p


class Tetris:
    def __init__(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.current = Piece()
        self.next_piece = Piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.drop_timer = 0
        self.drop_interval = 500  # 毫秒

    def valid_position(self, piece):
        for x, y in piece.absolute_cells():
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def lock_piece(self):
        for x, y in self.current.absolute_cells():
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.current.color

        cleared = self.clear_lines()
        if cleared:
            points = [0, 100, 300, 500, 800]
            self.score += points[min(cleared, 4)] * self.level
            self.lines_cleared += cleared
            self.level = 1 + self.lines_cleared // 10
            self.drop_interval = max(80, 500 - (self.level - 1) * 40)

        self.current = self.next_piece
        self.next_piece = Piece()
        if not self.valid_position(self.current):
            self.game_over = True

    def clear_lines(self):
        full_rows = [r for r in range(ROWS) if all(self.board[r][c] for c in range(COLS))]
        for r in full_rows:
            del self.board[r]
            self.board.insert(0, [None for _ in range(COLS)])
        return len(full_rows)

    def try_move(self, dx, dy):
        p = Piece(self.current.kind)
        p.cells = self.current.cells
        p.color = self.current.color
        p.x = self.current.x + dx
        p.y = self.current.y + dy
        if self.valid_position(p):
            self.current = p
            return True
        return False

    def try_rotate(self):
        p = self.current.rotated()
        # 踢墙：旋转后若越界，尝试左右微调
        for kick in (0, -1, 1, -2, 2):
            p.x = self.current.x + kick
            if self.valid_position(p):
                self.current = p
                return True
        return False

    def hard_drop(self):
        while self.try_move(0, 1):
            self.score += 1
        self.lock_piece()

    def update(self, dt):
        if self.game_over:
            return
        self.drop_timer += dt
        if self.drop_timer >= self.drop_interval:
            self.drop_timer = 0
            if not self.try_move(0, 1):
                self.lock_piece()

    def ghost_piece(self):
        ghost = Piece(self.current.kind)
        ghost.cells = self.current.cells
        ghost.color = tuple(c // 3 for c in self.current.color)
        ghost.x, ghost.y = self.current.x, self.current.y
        while True:
            g = Piece(ghost.kind)
            g.cells = ghost.cells
            g.x, g.y = ghost.x, ghost.y + 1
            if self.valid_position(g):
                ghost.y += 1
            else:
                break
        return ghost


def draw_cell(surface, x, y, color, alpha=255):
    rect = pygame.Rect(x * CELL, y * CELL, CELL - 1, CELL - 1)
    if alpha < 255:
        s = pygame.Surface((CELL - 1, CELL - 1), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surface.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect)
        highlight = tuple(min(255, c + 40) for c in color)
        shadow = tuple(max(0, c - 40) for c in color)
        pygame.draw.line(surface, highlight, rect.topleft, (rect.right, rect.top))
        pygame.draw.line(surface, highlight, rect.topleft, (rect.left, rect.bottom))
        pygame.draw.line(surface, shadow, (rect.right, rect.top), rect.bottomright)
        pygame.draw.line(surface, shadow, (rect.left, rect.bottom), rect.bottomright)


def draw_board(surface, game):
    surface.fill(BLACK)
    play_w = COLS * CELL

    for x in range(COLS + 1):
        pygame.draw.line(surface, GRID_COLOR, (x * CELL, 0), (x * CELL, HEIGHT))
    for y in range(ROWS + 1):
        pygame.draw.line(surface, GRID_COLOR, (0, y * CELL), (play_w, y * CELL))

    for y in range(ROWS):
        for x in range(COLS):
            if game.board[y][x]:
                draw_cell(surface, x, y, game.board[y][x])

    if not game.game_over:
        for x, y in game.ghost_piece().absolute_cells():
            if y >= 0:
                draw_cell(surface, x, y, game.ghost_piece().color, alpha=90)
        for x, y in game.current.absolute_cells():
            if y >= 0:
                draw_cell(surface, x, y, game.current.color)


def draw_sidebar(surface, font, small_font, game):
    x0 = COLS * CELL + 20
    pygame.draw.line(surface, GRID_COLOR, (COLS * CELL, 0), (COLS * CELL, HEIGHT), 2)

    title = font.render("俄罗斯方块", True, WHITE)
    surface.blit(title, (x0, 24))

    labels = [
        ("分数", str(game.score)),
        ("等级", str(game.level)),
        ("消除行", str(game.lines_cleared)),
    ]
    y = 80
    for label, value in labels:
        surface.blit(small_font.render(label, True, GRAY), (x0, y))
        surface.blit(font.render(value, True, WHITE), (x0, y + 22))
        y += 70

    surface.blit(small_font.render("下一个", True, GRAY), (x0, y))
    preview_x, preview_y = x0, y + 28
    for dx, dy in game.next_piece.cells:
        rect = pygame.Rect(
            preview_x + dx * 22,
            preview_y + dy * 22,
            20,
            20,
        )
        pygame.draw.rect(surface, game.next_piece.color, rect)

    help_y = HEIGHT - 200
    hints = [
        "← → 移动",
        "↑ 旋转",
        "↓ 软降",
        "空格 硬降",
        "P 暂停",
        "R 重新开始",
        "ESC 退出",
    ]
    for i, line in enumerate(hints):
        surface.blit(small_font.render(line, True, GRAY), (x0, help_y + i * 22))


def draw_overlay(surface, font, text, subtext=""):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    main = font.render(text, True, WHITE)
    surface.blit(main, main.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
    if subtext:
        sub = pygame.font.SysFont("pingfangsc,stheiti,arial", 22).render(subtext, True, GRAY)
        surface.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


def main():
    pygame.init()
    pygame.display.set_caption("俄罗斯方块")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("pingfangsc,stheiti,arial", 28, bold=True)
    small_font = pygame.font.SysFont("pingfangsc,stheiti,arial", 18)

    game = Tetris()
    paused = False

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    game = Tetris()
                    paused = False
                    continue
                if event.key == pygame.K_p and not game.game_over:
                    paused = not paused
                if paused or game.game_over:
                    continue
                if event.key == pygame.K_LEFT:
                    game.try_move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.try_move(1, 0)
                elif event.key == pygame.K_DOWN:
                    if game.try_move(0, 1):
                        game.score += 1
                elif event.key == pygame.K_UP:
                    game.try_rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()

        if not paused and not game.game_over:
            game.update(dt)

        draw_board(screen, game)
        draw_sidebar(screen, font, small_font, game)

        if paused:
            draw_overlay(screen, font, "已暂停", "按 P 继续")
        elif game.game_over:
            draw_overlay(screen, font, "游戏结束", "按 R 重新开始")

        pygame.display.flip()


if __name__ == "__main__":
    main()

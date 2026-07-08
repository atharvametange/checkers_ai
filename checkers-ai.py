import copy
import pygame

# --- PYGAME CONSTANTS ---
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# RGB Colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BROWN = (110, 70, 45)
LIGHT_WOOD = (230, 200, 150)
CROWN_GOLD = (255, 215, 0)


# --- HELPER FUNCTIONS ---
def draw_squares(window):
    """Draws the light and dark squares of the checkerboard."""
    window.fill(DARK_BROWN)
    for row in range(ROWS):
        for col in range(row % 2, COLS, 2):
            pygame.draw.rect(window, LIGHT_WOOD, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(window, board):
    """Loops through our backend grid and draws circles for the pieces."""
    for row in range(ROWS):
        for col in range(COLS):
            piece = board.grid[row][col]
            if piece != 0:
                x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                color = RED if piece.color == "RED" else BLACK
                pygame.draw.circle(window, color, (x, y), SQUARE_SIZE // 2 - 10)
                if piece.is_king:
                    pygame.draw.circle(window, CROWN_GOLD, (x, y), SQUARE_SIZE // 4)


def get_row_col_from_mouse(pos):
    """Translates the (x, y) pixel coordinates of the mouse into grid rows and columns."""
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col


def draw_valid_moves(window, valid_moves):
    """Draws a small blue dot on the squares where the selected piece can legally move."""
    for move in valid_moves:
        row, col = move
        pygame.draw.circle(window, (0, 0, 255),
                           (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                            row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)


# --- CLASSES ---
class Piece:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.is_king = False

    def make_king(self):
        self.is_king = True


class Board:
    ROWS, COLS = 8, 8

    def __init__(self):
        self.grid = []
        self.red_left = self.black_left = 12
        self.red_kings = self.black_kings = 0
        self.create_board()

    def create_board(self):
        for row in range(self.ROWS):
            self.grid.append([])
            for col in range(self.COLS):
                if (row + col) % 2 != 0:
                    if row < 3:
                        self.grid[row].append(Piece(row, col, "BLACK"))
                    elif row > 4:
                        self.grid[row].append(Piece(row, col, "RED"))
                    else:
                        self.grid[row].append(0)
                else:
                    self.grid[row].append(0)

    def move(self, piece, row, col):
        self.grid[piece.row][piece.col], self.grid[row][col] = self.grid[row][col], self.grid[piece.row][piece.col]
        piece.row = row
        piece.col = col

        if row == self.ROWS - 1 or row == 0:
            piece.make_king()
            if piece.color == "RED":
                self.red_kings += 1
            else:
                self.black_kings += 1

    def remove(self, pieces_to_remove):
        for piece in pieces_to_remove:
            self.grid[piece.row][piece.col] = 0
            if piece.color == "RED":
                self.red_left -= 1
            else:
                self.black_left -= 1

    def get_valid_moves(self, piece):
        moves = {}
        row = piece.row

        step_directions = []
        if piece.color == "RED" or piece.is_king:
            step_directions.append(-1)
        if piece.color == "BLACK" or piece.is_king:
            step_directions.append(1)

        for step in step_directions:
            moves.update(self._explore_diagonal(row, piece.col, step, -1, piece.color, []))
            moves.update(self._explore_diagonal(row, piece.col, step, 1, piece.color, []))

        return moves

    def _explore_diagonal(self, current_row, current_col, row_step, col_step, color, skipped=[]):
        moves = {}
        target_row = current_row + row_step
        target_col = current_col + col_step

        if target_row < 0 or target_row >= self.ROWS or target_col < 0 or target_col >= self.COLS:
            return moves

        target_square = self.grid[target_row][target_col]

        if target_square == 0:
            moves[(target_row, target_col)] = skipped
            if skipped:
                moves.update(self._explore_diagonal(target_row, target_col, row_step, -1, color, skipped))
                moves.update(self._explore_diagonal(target_row, target_col, row_step, 1, color, skipped))

        elif target_square.color != color:
            jump_row = target_row + row_step
            jump_col = target_col + col_step

            if 0 <= jump_row < self.ROWS and 0 <= jump_col < self.COLS:
                landing_square = self.grid[jump_row][jump_col]
                if landing_square == 0:
                    new_skipped = skipped + [target_square]
                    moves.update(self._explore_diagonal(jump_row, jump_col, row_step, col_step, color, new_skipped))

        return moves


class Game:
    def __init__(self):
        self.board = Board()
        self.turn = "RED"


class AI:
    def __init__(self):
        pass

    def evaluate(self, board):
        return board.black_left - board.red_left

    def get_all_moves(self, board, color):
        moves = []
        for row in range(board.ROWS):
            for col in range(board.COLS):
                piece = board.grid[row][col]
                if piece != 0 and piece.color == color:
                    valid_moves = board.get_valid_moves(piece)
                    for (dest_row, dest_col), captured in valid_moves.items():
                        temp_board = copy.deepcopy(board)
                        temp_piece = temp_board.grid[piece.row][piece.col]
                        temp_board.move(temp_piece, dest_row, dest_col)
                        if captured:
                            temp_captured = [temp_board.grid[c.row][c.col] for c in captured]
                            temp_board.remove(temp_captured)
                        moves.append(temp_board)
        return moves

    def minimax(self, current_board, depth, alpha, beta, max_player):
        if depth == 0 or current_board.red_left == 0 or current_board.black_left == 0:
            return self.evaluate(current_board), current_board

        if max_player:
            max_eval = float('-inf')
            best_board = None
            for move in self.get_all_moves(current_board, "BLACK"):
                evaluation = self.minimax(move, depth - 1, alpha, beta, False)[0]
                if evaluation > max_eval:
                    max_eval = evaluation
                    best_board = move
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            return max_eval, best_board

        else:
            min_eval = float('inf')
            best_board = None
            for move in self.get_all_moves(current_board, "RED"):
                evaluation = self.minimax(move, depth - 1, alpha, beta, True)[0]
                if evaluation < min_eval:
                    min_eval = evaluation
                    best_board = move
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            return min_eval, best_board


# --- MAIN GAME LOOP ---
def main():
    pygame.init()
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers AI")

    game = Game()
    ai_engine = AI()

    run = True
    clock = pygame.time.Clock()

    selected_piece = None
    valid_moves = {}

    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.turn == "RED":
                    pos = pygame.mouse.get_pos()
                    row, col = get_row_col_from_mouse(pos)

                    if selected_piece and (row, col) in valid_moves:
                        game.board.move(selected_piece, row, col)
                        captured = valid_moves[(row, col)]
                        if captured:
                            game.board.remove(captured)

                        game.turn = "BLACK"
                        selected_piece = None
                        valid_moves = {}
                    else:
                        piece = game.board.grid[row][col]
                        if piece != 0 and piece.color == "RED":
                            selected_piece = piece
                            valid_moves = game.board.get_valid_moves(piece)
                        else:
                            selected_piece = None
                            valid_moves = {}

        draw_squares(WIN)
        draw_pieces(WIN, game.board)

        if valid_moves:
            draw_valid_moves(WIN, valid_moves)

        pygame.display.update()

        if game.turn == "BLACK":
            pygame.time.delay(500)
            score, new_board = ai_engine.minimax(game.board, 4, float('-inf'), float('inf'), True)

            if new_board is None:
                print("AI has no moves left. You win!")
                run = False
            else:
                game.board = new_board
                game.turn = "RED"

    pygame.quit()


if __name__ == "__main__":
    main()
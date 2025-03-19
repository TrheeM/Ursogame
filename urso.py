import pygame
import pygame_gui
import random

# Configurações da interface e do tabuleiro
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
BOARD_ROWS, BOARD_COLS, NUM_BOMBS = 5, 5, 5
CELL_SIZE = 80
BOARD_OFFSET_X, BOARD_OFFSET_Y = 50, 150

# Cores
COLOR_BG = (30, 30, 30)
COLOR_CELL_HIDDEN = (70, 70, 70)
COLOR_CELL_SAFE = (50, 205, 50)
COLOR_CELL_BOMB = (220, 20, 60)
COLOR_BORDER = (0, 0, 0)
COLOR_TEXT = (255, 255, 255)

class Board: 
    def __init__(self, rows, cols, num_bombs):
        self.rows, self.cols, self.num_bombs = rows, cols, num_bombs
        self.bombs = [[False] * cols for _ in range(rows)]
        self.revealed = [[False] * cols for _ in range(rows)]
        self._place_bombs()

    def _place_bombs(self):
        positions = random.sample([(r, c) for r in range(self.rows) for c in range(self.cols)], self.num_bombs)
        for r, c in positions:
            self.bombs[r][c] = True
    
    def reveal_cell(self, row, col):
        if self.revealed[row][col]:
            return None
        self.revealed[row][col] = True
        return self.bombs[row][col]

    def draw(self, surface, font, bomb_image=None):
        for row in range(self.rows):
            for col in range(self.cols):
                rect = pygame.Rect(BOARD_OFFSET_X + col * CELL_SIZE, BOARD_OFFSET_Y + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = COLOR_CELL_BOMB if self.bombs[row][col] and self.revealed[row][col] else COLOR_CELL_SAFE if self.revealed[row][col] else COLOR_CELL_HIDDEN
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, COLOR_BORDER, rect, 2)
                if self.revealed[row][col]:
                    if self.bombs[row][col]:
                        if bomb_image:
                            surface.blit(bomb_image, bomb_image.get_rect(center=rect.center))
                        else:
                            surface.blit(font.render("URSO", True, COLOR_TEXT), (rect.x + 5, rect.y + CELL_SIZE // 3))
                    else:
                        surface.blit(font.render("OK", True, COLOR_BORDER), (rect.x + 25, rect.y + CELL_SIZE // 3))
    
class GameEngine:
    def __init__(self, initial_balance):
        self.balance, self.current_bet = initial_balance, 0.0
        self.board, self.round_active = None, False

    def new_round(self):
        if self.balance <= 0:
            raise Exception("Saldo insuficiente! Game Over.")
        self.board, self.round_active = Board(BOARD_ROWS, BOARD_COLS, NUM_BOMBS), True

    def place_bet(self, bet_amount):
        if not (0 < bet_amount <= self.balance):
            raise ValueError("Aposta inválida!")
        self.current_bet, self.balance = bet_amount, self.balance - bet_amount

    def play_move(self, row, col):
        if not self.round_active:
            raise Exception("Rodada não ativa!")
        result = self.board.reveal_cell(row, col)
        if result is None:
            return "Célula já revelada."
        if result:
            self.round_active = False
            return "Perdeu! 😭"
        self.balance += self.current_bet * 1.5
        return f"Ganhou! +{self.current_bet * 1.5:.2f} moedas"

class GameUI:
    def __init__(self, engine):
        pygame.init()
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background.fill(COLOR_BG)
        self.manager, self.clock, self.engine = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT)), pygame.time.Clock(), engine
        self._setup_ui()
        self.bomb_image = self._load_bomb_image()
        self.engine.new_round()

    def _setup_ui(self):
        self.balance_label = pygame_gui.elements.UILabel(pygame.Rect(50, 20, 300, 40), f"Saldo: {self.engine.balance:.2f}", self.manager)
        self.bet_input = pygame_gui.elements.UITextEntryLine(pygame.Rect(50, 70, 140, 40), self.manager)
        self.bet_button = pygame_gui.elements.UIButton(pygame.Rect(200, 70, 100, 40), "Apostar", self.manager)
        self.new_round_button = pygame_gui.elements.UIButton(pygame.Rect(310, 70, 150, 40), "Nova Rodada", self.manager)
        self.new_round_button.disable()
        self.message_label = pygame_gui.elements.UILabel(pygame.Rect(50, 110, 400, 30), "Bem-vindo ao Jogo do Urso!", self.manager)

    def _load_bomb_image(self):
        try:
            img = pygame.image.load("bear.png").convert_alpha()
            return pygame.transform.scale(img, (CELL_SIZE - 10, CELL_SIZE - 10))
        except:
            print("Erro ao carregar 'bear.png'. Usando texto para o urso.")
            return None

    def run(self):
        while True:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and self.engine.round_active:
                    self._handle_board_click(*pygame.mouse.get_pos())
                if event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    self._handle_button_click(event.ui_element)
                self.manager.process_events(event)
            self.manager.update(time_delta)
            self.window.blit(self.background, (0, 0))
            if self.engine.board:
                self.engine.board.draw(self.window, pygame.font.SysFont("Arial", 24), self.bomb_image)
            self.manager.draw_ui(self.window)
            pygame.display.update()

    def _handle_board_click(self, mouse_x, mouse_y):
        if BOARD_OFFSET_X <= mouse_x < BOARD_OFFSET_X + BOARD_COLS * CELL_SIZE and BOARD_OFFSET_Y <= mouse_y < BOARD_OFFSET_Y + BOARD_ROWS * CELL_SIZE:
            col, row = (mouse_x - BOARD_OFFSET_X) // CELL_SIZE, (mouse_y - BOARD_OFFSET_Y) // CELL_SIZE
            self.message_label.set_text(self.engine.play_move(row, col))
            self.balance_label.set_text(f"Saldo: {self.engine.balance:.2f}")
            if not self.engine.round_active:
                self.new_round_button.enable()

    def _handle_button_click(self, button):
        if button == self.bet_button:
            try:
                self.engine.place_bet(float(self.bet_input.get_text()))
                self.message_label.set_text("Aposta aceita! Clique em uma célula.")
                self.balance_label.set_text(f"Saldo: {self.engine.balance:.2f}")
            except ValueError:
                self.message_label.set_text("Aposta inválida!")
        elif button == self.new_round_button:
            self.engine.new_round()
            self.new_round_button.disable()
            self.message_label.set_text("Nova rodada iniciada. Faça sua aposta!")

   
if __name__ == "__main__":
    GameUI(GameEngine(100.0)).run()

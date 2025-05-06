import asyncio
import platform
import pygame
import random
import heapq

# Initialize Pygame
pygame.init()

# Game constants
CELL_SIZE = 30
GRID_WIDTH = 20
GRID_HEIGHT = 15
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT
FPS = 10

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
PINK = (255, 192, 203)

# Game states
MAIN_MENU = "main_menu"
PLAYING = "playing"
PAUSED = "paused"
WIN = "win"
LOSE = "lose"

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pacman with A*")
clock = pygame.time.Clock()

# Game grid
grid = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# Place food
for y in range(len(grid)):
    for x in range(len(grid[0])):
        if grid[y][x] == 0 and random.random() < 0.3:
            grid[y][x] = 2

# Initial positions
pacman_pos = [1, 1]
ghosts = [(18, 13)]
ghost_paths = [[]]

# Movement directions
directions = {
    pygame.K_UP: (0, -1),
    pygame.K_RIGHT: (1, 0),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0)
}

# Game variables
score = 0
font = pygame.font.Font(None, 36)
game_state = MAIN_MENU
current_direction = None
show_ghost_paths = True
move_counter = 0
ghost_move_timer = 0


# Button class
class Button:
    def __init__(self, text, x, y, width, height, color, hover_color):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.Font(None, 36)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, color, self.rect)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


# A* algorithm
def astar_search(start, goal, avoid_positions=None):
    if avoid_positions is None:
        avoid_positions = []
    move_directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    frontier = []
    heapq.heappush(frontier, (0, start))
    cost_so_far = {start: 0}
    came_from = {start: None}

    while frontier:
        current_f, current = heapq.heappop(frontier)
        if current == goal:
            break
        for dx, dy in move_directions:
            next_node = (current[0] + dx, current[1] + dy)
            if (0 <= next_node[0] < GRID_WIDTH and
                    0 <= next_node[1] < GRID_HEIGHT and
                    grid[next_node[1]][next_node[0]] != 1 and
                    next_node not in avoid_positions):
                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    f_score = new_cost + heuristic(next_node, goal)
                    heapq.heappush(frontier, (f_score, next_node))
                    came_from[next_node] = current

    if goal not in came_from:
        return None
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path


# Valid move check
def is_valid_move(pos, dx, dy):
    new_x = pos[0] + dx
    new_y = pos[1] + dy
    if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and grid[new_y][new_x] != 1:
        return True
    return False


# Draw ghost paths
def draw_ghost_paths():
    for path in ghost_paths:
        if path:
            for i, pos in enumerate(path):
                if i > 0:
                    pygame.draw.rect(
                        screen,
                        PINK,
                        pygame.Rect(
                            pos[0] * CELL_SIZE + CELL_SIZE // 4,
                            pos[1] * CELL_SIZE + CELL_SIZE // 4,
                            CELL_SIZE // 2,
                            CELL_SIZE // 2
                        ),
                        1
                    )
                    step_font = pygame.font.Font(None, 20)
                    step_text = step_font.render(str(i), True, PINK)
                    screen.blit(
                        step_text,
                        (pos[0] * CELL_SIZE + CELL_SIZE // 2 - step_text.get_width() // 2,
                         pos[1] * CELL_SIZE + CELL_SIZE // 2 - step_text.get_height() // 2)
                    )


# Draw game
def draw_game():
    screen.fill(BLACK)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if grid[y][x] == 1:
                pygame.draw.rect(screen, BLUE, rect)
            elif grid[y][x] == 2:
                pygame.draw.rect(screen, BLACK, rect)
                pygame.draw.circle(screen, WHITE, (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2),
                                   CELL_SIZE // 6)

    if show_ghost_paths:
        draw_ghost_paths()

    pygame.draw.circle(screen, YELLOW,
                       (pacman_pos[0] * CELL_SIZE + CELL_SIZE // 2, pacman_pos[1] * CELL_SIZE + CELL_SIZE // 2),
                       CELL_SIZE // 2)

    for ghost in ghosts:
        pygame.draw.circle(screen, RED, (ghost[0] * CELL_SIZE + CELL_SIZE // 2, ghost[1] * CELL_SIZE + CELL_SIZE // 2),
                           CELL_SIZE // 2)

    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    controls_text = font.render("Arrows: Move | G: Toggle paths", True, WHITE)
    controls_rect = controls_text.get_rect(center=(WIDTH // 2, 20))
    screen.blit(controls_text, controls_rect)

    pause_hint = font.render("P: Pause", True, WHITE)
    screen.blit(pause_hint, (WIDTH - pause_hint.get_width() - 10, 10))


# Draw main menu
def draw_main_menu():
    screen.fill(BLACK)
    title_font = pygame.font.Font(None, 64)
    title_text = title_font.render("Pacman A*", True, YELLOW)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(title_text, title_rect)

    start_button.draw(screen)


# Draw pause menu
def draw_pause_menu():
    draw_game()
    pause_surface = pygame.Surface((WIDTH, HEIGHT))
    pause_surface.set_alpha(180)
    pause_surface.fill(GRAY)
    screen.blit(pause_surface, (0, 0))

    pause_font = pygame.font.Font(None, 64)
    pause_text = pause_font.render("GAME PAUSED", True, WHITE)
    text_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(pause_text, text_rect)

    continue_button.draw(screen)
    quit_button.draw(screen)


# Draw win screen
def draw_win_screen():
    screen.fill(BLACK)
    win_font = pygame.font.Font(None, 64)
    win_text = win_font.render("YOU WIN!", True, GREEN)
    win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(win_text, win_rect)

    score_text = font.render(f"Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(score_text, score_rect)

    main_menu_button.draw(screen)


# Draw lose screen
def draw_lose_screen():
    screen.fill(BLACK)
    lose_font = pygame.font.Font(None, 64)
    lose_text = lose_font.render("GAME OVER", True, RED)
    lose_rect = lose_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(lose_text, lose_rect)

    score_text = font.render(f"Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(score_text, score_rect)

    main_menu_button.draw(screen)


# Reset game
def reset_game():
    global pacman_pos, ghosts, ghost_paths, score, grid, current_direction, move_counter, ghost_move_timer
    pacman_pos = [1, 1]
    ghosts = [(18, 13)]
    ghost_paths = [[]]
    score = 0
    current_direction = None
    move_counter = 0
    ghost_move_timer = 0
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
        [1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if grid[y][x] == 0 and random.random() < 0.3:
                grid[y][x] = 2


# Initialize buttons
start_button = Button("Start Game", WIDTH // 4, HEIGHT // 2, WIDTH // 2, 50, BLUE, GREEN)
continue_button = Button("Continue", WIDTH // 4, HEIGHT // 2 - 30, WIDTH // 2, 50, BLUE, GREEN)
quit_button = Button("Quit", WIDTH // 4, HEIGHT // 2 + 30, WIDTH // 2, 50, BLUE, RED)
main_menu_button = Button("Main Menu", WIDTH // 4, HEIGHT // 2 + 30, WIDTH // 2, 50, BLUE, GREEN)


# Setup function
def setup():
    reset_game()


# Update loop
def update_loop():
    global game_state, current_direction, move_counter, ghost_move_timer, score, pacman_pos, ghosts, ghost_paths, show_ghost_paths

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN:
            if game_state == PLAYING:
                if event.key == pygame.K_p:
                    game_state = PAUSED
                elif event.key == pygame.K_g:
                    show_ghost_paths = not show_ghost_paths
                elif event.key in directions:
                    current_direction = directions[event.key]
        elif game_state == MAIN_MENU and start_button.is_clicked(event):
            game_state = PLAYING
            reset_game()
        elif game_state == PAUSED:
            if continue_button.is_clicked(event):
                game_state = PLAYING
            elif quit_button.is_clicked(event):
                game_state = LOSE
        elif game_state in (WIN, LOSE) and main_menu_button.is_clicked(event):
            game_state = MAIN_MENU

    if game_state == PLAYING:
        move_counter += 1
        if move_counter >= FPS // 5:
            move_counter = 0
            if current_direction:
                dx, dy = current_direction
                if is_valid_move(pacman_pos, dx, dy):
                    new_x = pacman_pos[0] + dx
                    new_y = pacman_pos[1] + dy
                    pacman_pos = [new_x, new_y]
                    if grid[pacman_pos[1]][pacman_pos[0]] == 2:
                        grid[pacman_pos[1]][pacman_pos[0]] = 0
                        score += 10
                    for i, ghost in enumerate(ghosts):
                        ghost_paths[i] = astar_search(ghost, tuple(pacman_pos))

        ghost_move_timer += 1
        if ghost_move_timer >= FPS // 2:
            ghost_move_timer = 0
            for i, ghost in enumerate(ghosts):
                ghost_paths[i] = astar_search(ghost, tuple(pacman_pos))
                if ghost_paths[i] and len(ghost_paths[i]) > 1:
                    ghosts[i] = ghost_paths[i][1]
                    if tuple(ghosts[i]) == tuple(pacman_pos):
                        game_state = LOSE

        food_left = False
        for row in grid:
            if 2 in row:
                food_left = True
                break
        if not food_left:
            game_state = WIN

    if game_state == MAIN_MENU:
        draw_main_menu()
    elif game_state == PLAYING:
        draw_game()
    elif game_state == PAUSED:
        draw_pause_menu()
    elif game_state == WIN:
        draw_win_screen()
    elif game_state == LOSE:
        draw_lose_screen()

    pygame.display.flip()
    return True


# Main game loop
async def main():
    setup()
    running = True
    while running:
        running = update_loop()
        await asyncio.sleep(1.0 / FPS)


# Run the game
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
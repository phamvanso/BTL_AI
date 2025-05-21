import asyncio
import platform
import pygame
import random
import heapq

# Khởi tạo Pygame
pygame.init()

# Hằng số trò chơi
CELL_SIZE = 50
GRID_WIDTH =20  # Cập nhật theo ma trận mới (12 cột)
GRID_HEIGHT = 15  # Cập nhật theo ma trận mới (11 hàng)
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT
FPS = 10

# Màu sắc
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
PINK = (255, 192, 203)

# Trạng thái trò chơi
MAIN_MENU = "main_menu"
PLAYING = "playing"
PAUSED = "paused"
WIN = "win"
LOSE = "lose"

# Thiết lập màn hình
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pacman with A*")
clock = pygame.time.Clock()

# Vị trí ban đầu của Pacman và ma quỷ
pacman_pos = [1, 1]  # Vẫn hợp lệ trong ma trận mới
ghosts = [(18, 3)]   # Cập nhật vị trí ma quỷ để nằm trong ô đi được
ghost_paths = [[]]

# Hướng di chuyển
directions = {
    pygame.K_UP: (0, -1),
    pygame.K_RIGHT: (1, 0),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0)
}

# Biến trò chơi
score = 0
font = pygame.font.Font(None, 36)
game_state = MAIN_MENU
current_direction = None
show_ghost_paths = True
move_counter = 0
ghost_move_timer = 0

# Lớp nút bấm
class Button:
    def __init__(self, text, x, y, width, height, color, hover_color):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.Font(None, 36)

    def draw(self, screen):
        # Vẽ nút bấm, thay đổi màu khi chuột di chuột qua
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, color, self.rect)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        # Kiểm tra xem nút có được nhấn không
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

# Lớp lưu trữ thông tin ô trong thuật toán A*
class Cell:
    def __init__(self):
        self.parent_i = 0  # Chỉ số hàng của ô cha
        self.parent_j = 0  # Chỉ số cột của ô cha
        self.f = float('inf')  # Tổng chi phí (g + h)
        self.g = float('inf')  # Chi phí từ điểm bắt đầu đến ô này
        self.h = 0  # Chi phí heuristic từ ô này đến đích

# Kiểm tra ô có nằm trong lưới không
def is_valid(row, col):
    return (row >= 0) and (row < GRID_HEIGHT) and (col >= 0) and (col < GRID_WIDTH)

# Kiểm tra ô có đi được không (phải là 1 hoặc 2)
def is_unblocked(grid, row, col):
    return grid[row][col] == 1 or grid[row][col] == 2

# Kiểm tra xem ô có phải đích không
def is_destination(row, col, dest):
    return row == dest[1] and col == dest[0]

# Tính giá trị heuristic (khoảng cách Manhattan)
def calculate_h_value(row, col, dest):
    return abs(row - dest[1]) + abs(col - dest[0])

# Thuật toán A* tìm đường đi ngắn nhất
def astar_search(start, goal, avoid_positions=None):
    if avoid_positions is None:
        avoid_positions = []

    # Kiểm tra tính hợp lệ của điểm bắt đầu và đích
    if not is_valid(start[1], start[0]) or not is_valid(goal[1], goal[0]):
        return None  # Trả về None nếu điểm bắt đầu hoặc đích không hợp lệ

    # Kiểm tra xem điểm bắt đầu hoặc đích có bị chặn không
    if not is_unblocked(grid, start[1], start[0]) or not is_unblocked(grid, goal[1], goal[0]):
        return None  # Trả về None nếu điểm bắt đầu hoặc đích bị chặn

    # Kiểm tra xem đã ở đích chưa
    if is_destination(start[1], start[0], goal):
        return [start]  # Trả về danh sách chỉ chứa điểm bắt đầu nếu đã ở đích

    # Khởi tạo danh sách các ô đã duyệt
    closed_list = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    # Khởi tạo thông tin chi tiết của các ô
    cell_details = [[Cell() for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    # Thiết lập thông tin ô bắt đầu
    i = start[1]
    j = start[0]
    cell_details[i][j].f = 0
    cell_details[i][j].g = 0
    cell_details[i][j].h = 0
    cell_details[i][j].parent_i = i
    cell_details[i][j].parent_j = j

    # Danh sách mở để lưu các ô cần khám phá
    open_list = []
    heapq.heappush(open_list, (0.0, i, j))

    # Các hướng di chuyển: phải, trái, xuống, lên
    move_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while len(open_list) > 0:
        p = heapq.heappop(open_list)
        i = p[1]
        j = p[2]
        closed_list[i][j] = True  # Đánh dấu ô đã duyệt

        for dir in move_directions:
            new_i = i + dir[0]
            new_j = j + dir[1]

            if (is_valid(new_i, new_j) and is_unblocked(grid, new_i, new_j) and
                    not closed_list[new_i][new_j] and (new_j, new_i) not in avoid_positions):
                if is_destination(new_i, new_j, goal):
                    cell_details[new_i][new_j].parent_i = i
                    cell_details[new_i][new_j].parent_j = j
                    # Truy vết đường đi
                    path = []
                    row = goal[1]
                    col = goal[0]
                    while not (cell_details[row][col].parent_i == row and
                               cell_details[row][col].parent_j == col):
                        path.append((col, row))
                        temp_row = cell_details[row][col].parent_i
                        temp_col = cell_details[row][col].parent_j
                        row = temp_row
                        col = temp_col
                    path.append((col, row))
                    path.reverse()
                    return path
                else:
                    g_new = cell_details[i][j].g + 1.0
                    h_new = calculate_h_value(new_i, new_j, goal)
                    f_new = g_new + h_new

                    if cell_details[new_i][new_j].f == float('inf') or cell_details[new_i][new_j].f > f_new:
                        heapq.heappush(open_list, (f_new, new_i, new_j))
                        cell_details[new_i][new_j].f = f_new
                        cell_details[new_i][new_j].g = g_new
                        cell_details[new_i][new_j].h = h_new
                        cell_details[new_i][new_j].parent_i = i
                        cell_details[new_i][new_j].parent_j = j

    return None  # Trả về None nếu không tìm thấy đường đi

# Kiểm tra di chuyển hợp lệ
def is_valid_move(pos, dx, dy):
    new_x = pos[0] + dx
    new_y = pos[1] + dy
    if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and is_unblocked(grid, new_y, new_x):
        return True
    return False

# Vẽ đường đi của ma quỷ
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

# Vẽ trò chơi
def draw_game():
    screen.fill(BLACK)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if grid[y][x] == 0:  # Tường
                pygame.draw.rect(screen, BLUE, rect)
            elif grid[y][x] == 2:  # Thức ăn
                pygame.draw.rect(screen, BLACK, rect)
                pygame.draw.circle(screen, WHITE, (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2),
                                   CELL_SIZE // 6)

    if show_ghost_paths:
        draw_ghost_paths()

    # Vẽ Pacman
    pygame.draw.circle(screen, YELLOW,
                       (pacman_pos[0] * CELL_SIZE + CELL_SIZE // 2, pacman_pos[1] * CELL_SIZE + CELL_SIZE // 2),
                       CELL_SIZE // 2)

    # Vẽ ma quỷ
    for ghost in ghosts:
        pygame.draw.circle(screen, RED, (ghost[0] * CELL_SIZE + CELL_SIZE // 2, ghost[1] * CELL_SIZE + CELL_SIZE // 2),
                           CELL_SIZE // 2)

    # Hiển thị điểm số
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Hiển thị hướng dẫn điều khiển
    controls_text = font.render("Arrows: Move | G: Toggle paths", True, WHITE)
    controls_rect = controls_text.get_rect(center=(WIDTH // 2, 20))
    screen.blit(controls_text, controls_rect)

    # Hiển thị nút tạm dừng
    pause_hint = font.render("P: Pause", True, WHITE)
    screen.blit(pause_hint, (WIDTH - pause_hint.get_width() - 10, 10))

# Vẽ menu chính
def draw_main_menu():
    screen.fill(BLACK)
    title_font = pygame.font.Font(None, 64)
    title_text = title_font.render("Pacman A*", True, YELLOW)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(title_text, title_rect)
    start_button.draw(screen)

# Vẽ menu tạm dừng
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

# Vẽ màn hình thắng
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

# Vẽ màn hình thua
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

# Đặt lại trò chơi
def reset_game():
    global pacman_pos, ghosts, ghost_paths, score, grid, current_direction, move_counter, ghost_move_timer
    pacman_pos = [1, 1]
    ghosts = [(18, 13)]
    ghost_paths = [[]]
    score = 0
    current_direction = None
    move_counter = 0
    ghost_move_timer = 0
    # Ma trận mới: 0 là tường, 1 là đường, 2 là thức ăn
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0],
        [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]
    # Đặt thức ăn ngẫu nhiên trên các ô đi được (1)
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if grid[y][x] == 1 and random.random() < 0.3:
                grid[y][x] = 2

# Khởi tạo các nút bấm
start_button = Button("Start Game", WIDTH // 4, HEIGHT // 2, WIDTH // 2, 50, BLUE, GREEN)
continue_button = Button("Continue", WIDTH // 4, HEIGHT // 2 - 30, WIDTH // 2, 50, BLUE, GREEN)
quit_button = Button("Quit", WIDTH // 4, HEIGHT // 2 + 30, WIDTH // 2, 50, BLUE, RED)
main_menu_button = Button("Main Menu", WIDTH // 4, HEIGHT // 2 + 30, WIDTH // 2, 50, BLUE, GREEN)

# Thiết lập ban đầu
def setup():
    reset_game()

# Vòng lặp cập nhật
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
                        grid[pacman_pos[1]][pacman_pos[0]] = 1  # Thay thức ăn bằng đường trống
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

# Vòng lặp chính
async def main():
    setup()
    running = True
    while running:
        running = update_loop()
        await asyncio.sleep(1.0 / FPS)

# Chạy trò chơi
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
import pygame

from mathematics import BOARD_WIDTH, BOARD_HEIGHT, UP, DOWN, RIGHT, LEFT, ROW_ABOVE_BOARD, OCEAN_AN_IMAGES, move_ocean_ans, \
    get_board_copy_minus_ocean_ans, get_dropping_ocean_ans, EMPTY_SPACE, get_drop_slots, board_rects

WINDOW_WIDTH = 600  # ширина окна в пикселях
WINDOW_HEIGHT = 600  # высота окна в пикселях
OCEAN_AN_IMAGE_SIZE = 64  # ширина / высота ячейки в пикселях

FPS_CLOCK = pygame.time.Clock()
DISPLAY_SURF = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
FPS = 30  # кадров в секунду

# NUM_OCEAN_AN_IMAGES это количество видов морских обитателей, для каждого - своя картинка
# имена файлов p0.png, p1.png, и так далее до p(N-1).png.
NUM_OCEAN_AN_IMAGES = 7
assert NUM_OCEAN_AN_IMAGES >= 5  # нужно минимум 5 видов морских обитателей, для корректной работы

# NUM_MATCH_SOUNDS это количество звуков, используемых в игре
# Мы имеем .wav файлы, с названиями match0.wav, match1.wav, и так далее
NUM_MATCH_SOUNDS = 6

MOVE_RATE = 25  # от 1 до 100, чем больше значение, тем быстрее анимация
DEDUCT_SPEED = 0.8  # счет уменьшает на 1 очко за каждое количество секунд этого параметра

# для простоты вызова создадим константы цветов
PURPLE = (255, 0, 255)
LIGHT_BLUE = (170, 190, 255)
BLUE = (0, 0, 255)
RED = (255, 100, 100)
BLACK = (0, 0, 0)
BROWN = (85, 65, 0)
HIGHLIGHT_COLOR = PURPLE  # цвет границы выбранной ячейки
BG_COLOR = LIGHT_BLUE  # цвет фона
GRID_COLOR = BLUE  # цвет поля
GAME_OVER_COLOR = RED  # цвет результата "Game over"
GAME_OVER_BG_COLOR = BLACK  # цвет фона результата "Game over"
SCORE_COLOR = BROWN  # цвет счета

# Количество пикселей по бокам от поля до края окна
# будем использовать несколько раз, поэтому вычислим заранее
X_MARGIN = int((WINDOW_WIDTH - OCEAN_AN_IMAGE_SIZE * BOARD_WIDTH) / 2)
Y_MARGIN = int((WINDOW_HEIGHT - OCEAN_AN_IMAGE_SIZE * BOARD_HEIGHT) / 2)

pygame.font.init()
BASIC_FONT = pygame.font.Font('freesansbold.ttf', 36)
# BASIC_FONT = pygame.font.Font('/home/npocbet/PycharmProjects/Yandex_pygame_project/ui/freesansbold.ttf', 36)

pygame.mixer.init()
GAME_SOUNDS = {'bad swap': pygame.mixer.Sound('./sounds/badswap.wav'),
               'match': []}


def draw_moving_ocean_an(ocean_an_t, progress):
    # Рисуем перемещение морского обитателя
    # Параметр progress принимает значение от 0 (в начале перемещения)
    # до 100 (когда морской обитатель перемещен).
    move_x = 0
    move_y = 0
    progress *= 0.01

    if ocean_an_t['direction'] == UP:
        move_y = -int(progress * OCEAN_AN_IMAGE_SIZE)
    elif ocean_an_t['direction'] == DOWN:
        move_y = int(progress * OCEAN_AN_IMAGE_SIZE)
    elif ocean_an_t['direction'] == RIGHT:
        move_x = int(progress * OCEAN_AN_IMAGE_SIZE)
    elif ocean_an_t['direction'] == LEFT:
        move_x = -int(progress * OCEAN_AN_IMAGE_SIZE)

    base_x = ocean_an_t['x']
    base_y = ocean_an_t['y']
    if base_y == ROW_ABOVE_BOARD:
        base_y = -1

    pixel_x = X_MARGIN + (base_x * OCEAN_AN_IMAGE_SIZE)
    pixel_y = Y_MARGIN + (base_y * OCEAN_AN_IMAGE_SIZE)
    r = pygame.Rect((pixel_x + move_x, pixel_y + move_y, OCEAN_AN_IMAGE_SIZE, OCEAN_AN_IMAGE_SIZE))
    DISPLAY_SURF.blit(OCEAN_AN_IMAGES[ocean_an_t['imageNum']], r)


def highlight_space(x, y):
    # рисует отдельную ячейку
    pygame.draw.rect(DISPLAY_SURF, HIGHLIGHT_COLOR, board_rects[x][y], 4)


def draw_score(score):
    score_img = BASIC_FONT.render(str(score), True, SCORE_COLOR)
    score_rect = score_img.get_rect()
    score_rect.bottomleft = (10, WINDOW_HEIGHT - 6)
    DISPLAY_SURF.blit(score_img, score_rect)


def draw_board(board):
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            pygame.draw.rect(DISPLAY_SURF, GRID_COLOR, board_rects[x][y], 1)
            ocean_an_to_draw = board[x][y]
            if ocean_an_to_draw != EMPTY_SPACE:
                DISPLAY_SURF.blit(OCEAN_AN_IMAGES[ocean_an_to_draw], board_rects[x][y])


def check_for_ocean_an_click(pos):
    # промеряем клик, попал он на ячейку или нет
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            if board_rects[x][y].collidepoint(pos[0], pos[1]):
                return {'x': x, 'y': y}
    return None  # клик был не на ячейку


def animate_moving_ocecan_ans(surface, board, ocean_ans, points_text, score):
    progress = 0  # progress 0 означает начало анимации, 100 - по завершении.
    while progress < 100:  # цикл анимации
        surface.fill(BG_COLOR)
        draw_board(board)
        for ocean_an_t in ocean_ans:  # рисуем каждый гем
            draw_moving_ocean_an(ocean_an_t, progress)
        draw_score(score)
        for pointText in points_text:
            points_surf = BASIC_FONT.render(str(pointText['points']), True, SCORE_COLOR)
            points_rect = points_surf.get_rect()
            points_rect.center = (pointText['x'], pointText['y'])
            surface.blit(points_surf, points_rect)

        pygame.display.update()
        FPS_CLOCK.tick(FPS)
        progress += MOVE_RATE  # немного увеличиваем прогресс анимации


def fill_board_and_animate(surface, board, points, score):
    drop_slots = get_drop_slots(board)
    while drop_slots != [[]] * BOARD_WIDTH:
        # делаем анимацию падающих морских обитателей, пока таковые имеются
        moving_ocean_ans = get_dropping_ocean_ans(board)
        for x in range(len(drop_slots)):
            if len(drop_slots[x]) != 0:
                # сдвигаем вниз самого нижнего морского обитателя в каждой колонке, если возможно
                moving_ocean_ans.append({'imageNum': drop_slots[x][0], 'x': x, 'y': ROW_ABOVE_BOARD, 'direction': DOWN})

        board_copy = get_board_copy_minus_ocean_ans(board, moving_ocean_ans)
        animate_moving_ocecan_ans(surface, board_copy, moving_ocean_ans, points, score)
        move_ocean_ans(board, moving_ocean_ans)

        # Обрабатываем следующую строку
        for x in range(len(drop_slots)):
            if len(drop_slots[x]) == 0:
                continue
            board[x][0] = drop_slots[x][0]
            del drop_slots[x][0]

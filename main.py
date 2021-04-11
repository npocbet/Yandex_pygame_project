import copy
from datetime import datetime

import pygame
import random
import time
import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QTableWidgetItem
from pygame.locals import *

FPS = 30  # кадров в секунду
WINDOW_WIDTH = 600  # ширина окна в пикселях
WINDOW_HEIGHT = 600  # высота окна в пикселях

BOARD_WIDTH = 8  # количество "столбцов" на поле
BOARD_HEIGHT = 8  # количество "рядов" на поле
OCEAN_AN_IMAGE_SIZE = 64  # ширина / высота ячейки в пикселях

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
# Будем использовать несколько раз, поэтому вычислим заранее
X_MARGIN = int((WINDOW_WIDTH - OCEAN_AN_IMAGE_SIZE * BOARD_WIDTH) / 2)
Y_MARGIN = int((WINDOW_HEIGHT - OCEAN_AN_IMAGE_SIZE * BOARD_HEIGHT) / 2)

# константы для значения направлений
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

EMPTY_SPACE = -1  # произвольное неположительное значение
ROW_ABOVE_BOARD = 'row above board'  # произвольное, нецелое значение

HEADERS = {'results': ['date', 'score']}


class ResultWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("results.ui", self)
        self.result = []
        self.update_table()

    def update_table(self):
        con = sqlite3.connect('results.sqlite')
        cur = con.cursor()
        self.result = cur.execute(f"""SELECT date, score FROM results ORDER BY score DESC;""").fetchall()

        self.tableWidget.setRowCount(len(self.result))
        self.tableWidget.setColumnCount(len(self.result[0]))

        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

        con.close()


def main():
    global FPS_CLOCK, DISPLAY_SURF, OCEAN_AN_IMAGES, GAME_SOUNDS, BASIC_FONT, board_rects

    # Инициализация
    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURF = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('На днем морском!')
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', 36)

    # Загружаем картинки
    OCEAN_AN_IMAGES = []
    for i in range(1, NUM_OCEAN_AN_IMAGES + 1):
        ocean_an_image = pygame.image.load('p%s.png' % i)
        if ocean_an_image.get_size() != (OCEAN_AN_IMAGE_SIZE, OCEAN_AN_IMAGE_SIZE):
            ocean_an_image = pygame.transform.smoothscale(ocean_an_image, (OCEAN_AN_IMAGE_SIZE, OCEAN_AN_IMAGE_SIZE))
        OCEAN_AN_IMAGES.append(ocean_an_image)

    # Загружаем звуки
    GAME_SOUNDS = {'bad swap': pygame.mixer.Sound('badswap.wav'),
                   'match': []}
    for i in range(NUM_MATCH_SOUNDS):
        GAME_SOUNDS['match'].append(pygame.mixer.Sound('match%s.wav' % i))

    # Для каждой ячейки создадим pygame.Rect
    # чтобы делать преобразования от координат в "ячейках" к координатам
    # в пикселях
    board_rects = []
    for x in range(BOARD_WIDTH):
        board_rects.append([])
        for y in range(BOARD_HEIGHT):
            r = pygame.Rect((X_MARGIN + (x * OCEAN_AN_IMAGE_SIZE),
                             Y_MARGIN + (y * OCEAN_AN_IMAGE_SIZE),
                             OCEAN_AN_IMAGE_SIZE,
                             OCEAN_AN_IMAGE_SIZE))
            board_rects[x].append(r)

    # вызываем цикл игр, после окончания
    # одной можно кликом ЛКМ запустить новую
    while True:
        run_game()


def run_game():
    # Функция запускает одиночную игру

    # инициализируем поле
    # global ocean_an
    game_board = get_blank_board()
    score = 0
    fill_board_and_animate(game_board, [], score)

    # инициализируем переменные
    first_selected_ocean_an = None
    last_mouse_down_x = None
    last_mouse_down_y = None
    game_is_over = False
    last_score_deduction = time.time()
    click_continue_text_surf = None
    click_continue_text_surf1 = None
    click_continue_text_rect = None
    click_continue_text_rect1 = None

    while True:  # основной игровой цикл
        clicked_space = None
        for event in pygame.event.get():  # цикл обработки событий
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_BACKSPACE:
                return  # запускаем новую игру
            elif event.type == KEYUP and event.key == K_r:
                app = QApplication(sys.argv)
                ex = ResultWidget()
                ex.show()
                sys.exit(app.exec())
            elif event.type == MOUSEBUTTONUP:
                if game_is_over:
                    return  # если игра закончена по клику ЛКС - начинаем новую

                if event.pos == (last_mouse_down_x, last_mouse_down_y):
                    # событие, позволяющее использовать метод через 2 одинарных клика
                    clicked_space = check_for_ocean_an_click(event.pos)
                else:
                    # в этом случае использован метод перетаскивания ячейки
                    first_selected_ocean_an = check_for_ocean_an_click((last_mouse_down_x, last_mouse_down_y))
                    clicked_space = check_for_ocean_an_click(event.pos)
                    if not first_selected_ocean_an or not clicked_space:
                        # если это не "соседняя" ячейка или не задета никакая ячейка кроме первой
                        # считаем обе ячейки незадействованными
                        first_selected_ocean_an = None
                        clicked_space = None
            elif event.type == MOUSEBUTTONDOWN:
                # это либо одиночный клик, либо начало перетаскивания - запоминаем координаты
                last_mouse_down_x, last_mouse_down_y = event.pos

        if clicked_space and not first_selected_ocean_an:
            # это кликнули по "первой" ячейке
            first_selected_ocean_an = clicked_space
        elif clicked_space and first_selected_ocean_an:
            # кликнули по "второй" ячейке, меняем их местами
            first_swapping_ocean_an, second_swapping_ocean_an = \
                get_swapping_ocean_ans(game_board, first_selected_ocean_an, clicked_space)
            if first_swapping_ocean_an is None and second_swapping_ocean_an is None:
                # в этом случае кристаллы не были смежными
                first_selected_ocean_an = None  # отменяем выбор первого гема
                continue

            # показать анимацию замены ячеек
            board_copy = get_board_copy_minus_ocean_ans(game_board, (first_swapping_ocean_an, second_swapping_ocean_an))
            animate_moving_ocecan_ans(board_copy, [first_swapping_ocean_an, second_swapping_ocean_an], [], score)

            # замена картинок в ячейках после замены
            game_board[first_swapping_ocean_an['x']][first_swapping_ocean_an['y']] = \
                second_swapping_ocean_an['imageNum']
            game_board[second_swapping_ocean_an['x']][second_swapping_ocean_an['y']] = \
                first_swapping_ocean_an['imageNum']

            # смотрим, подходит ли этот ход - встали ли в 1 ряд 3 и более одинаковых ячеек
            matched_ocean_ans = find_matching_ocean_ans(game_board)
            if not matched_ocean_ans:
                # Морские обитатели не стали в ряд - возвращаем на исходные позиции
                GAME_SOUNDS['bad swap'].play()
                animate_moving_ocecan_ans(board_copy, [first_swapping_ocean_an, second_swapping_ocean_an], [], score)
                game_board[first_swapping_ocean_an['x']][first_swapping_ocean_an['y']] = \
                    first_swapping_ocean_an['imageNum']
                game_board[second_swapping_ocean_an['x']][second_swapping_ocean_an['y']] = \
                    second_swapping_ocean_an['imageNum']
            else:
                # Корректный ход, стали в ряд.
                score_add = 0
                while matched_ocean_ans:
                    # удаляем подходящих морских обитателей, сдвигаем вниз и заполняем новыми освободившееся место
                    # points это список из словарей, потому что "собранных линий"
                    # может быть несколько и за каждую полагается начислить очки

                    points = []
                    for ocean_an_set in matched_ocean_ans:
                        score_add += (10 + (len(ocean_an_set) - 3) * 10)
                        for ocean_an in ocean_an_set:
                            game_board[ocean_an[0]][ocean_an[1]] = EMPTY_SPACE
                        points.append({'points': score_add,
                                       'x': ocean_an[0] * OCEAN_AN_IMAGE_SIZE + X_MARGIN,
                                       'y': ocean_an[1] * OCEAN_AN_IMAGE_SIZE + Y_MARGIN})
                    random.choice(GAME_SOUNDS['match']).play()
                    score += score_add

                    # заполняем новыми морскими обитателями освободившиеся ячейки
                    fill_board_and_animate(game_board, points, score)

                    # проверяем, нет ли новых линий одинаковых морских обитателей
                    matched_ocean_ans = find_matching_ocean_ans(game_board)
            first_selected_ocean_an = None

            # условие проверки возможности хода
            if not can_make_move(game_board):
                game_is_over = True

        # отрисовать поле
        DISPLAY_SURF.fill(BG_COLOR)
        draw_board(game_board)
        if first_selected_ocean_an is not None:
            highlight_space(first_selected_ocean_an['x'], first_selected_ocean_an['y'])
        if game_is_over:
            if click_continue_text_surf is None:
                # Выводим результат

                con = sqlite3.connect('results.sqlite')
                cur = con.cursor()
                request = f'INSERT INTO results (' + \
                          ', '.join(HEADERS['results']) + \
                          ') VALUES ( ' + \
                          ', '.join([datetime.now().strftime("'%A %d-%B-%y %H:%M'"), str(score)]) + \
                          ')'
                print(request)
                cur.execute(request).fetchall()

                con.commit()
                con.close()

                click_continue_text_surf = BASIC_FONT.render('Final Score: %s (Click to continue)'
                                                             % score, True, GAME_OVER_COLOR, GAME_OVER_BG_COLOR)
                click_continue_text_rect = click_continue_text_surf.get_rect()
                click_continue_text_rect.center = int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2)
                click_continue_text_surf1 = BASIC_FONT.render('Press R to results',
                                                              True, GAME_OVER_COLOR, GAME_OVER_BG_COLOR)
                click_continue_text_rect1 = click_continue_text_surf1.get_rect()
                click_continue_text_rect1.size = int(WINDOW_WIDTH), int(WINDOW_HEIGHT / 4)
                click_continue_text_rect1.bottomleft = 10, int(WINDOW_HEIGHT) - 20

            DISPLAY_SURF.blit(click_continue_text_surf, click_continue_text_rect)
            DISPLAY_SURF.blit(click_continue_text_surf1, click_continue_text_rect1)
        elif score > 0 and time.time() - last_score_deduction > DEDUCT_SPEED:
            # счет постоянно уменьшается
            score -= 1
            last_score_deduction = time.time()
        draw_score(score)
        pygame.display.update()
        FPS_CLOCK.tick(FPS)


def get_swapping_ocean_ans(board, first_x_y, second_x_y):
    # Если морские обитатели смежны, мы должны установить направление для каждого
    # в котором они будут меняться местами

    first_ocean_an = {'imageNum': board[first_x_y['x']][first_x_y['y']],
                      'x': first_x_y['x'],
                      'y': first_x_y['y']}
    second_ocean_an = {'imageNum': board[second_x_y['x']][second_x_y['y']],
                       'x': second_x_y['x'],
                       'y': second_x_y['y']}
    if first_ocean_an['x'] == second_ocean_an['x'] + 1 and first_ocean_an['y'] == second_ocean_an['y']:
        first_ocean_an['direction'] = LEFT
        second_ocean_an['direction'] = RIGHT
    elif first_ocean_an['x'] == second_ocean_an['x'] - 1 and first_ocean_an['y'] == second_ocean_an['y']:
        first_ocean_an['direction'] = RIGHT
        second_ocean_an['direction'] = LEFT
    elif first_ocean_an['y'] == second_ocean_an['y'] + 1 and first_ocean_an['x'] == second_ocean_an['x']:
        first_ocean_an['direction'] = UP
        second_ocean_an['direction'] = DOWN
    elif first_ocean_an['y'] == second_ocean_an['y'] - 1 and first_ocean_an['x'] == second_ocean_an['x']:
        first_ocean_an['direction'] = DOWN
        second_ocean_an['direction'] = UP
    else:
        # Морских обитатели не соседние и не могут поменяться местами
        return None, None
    return first_ocean_an, second_ocean_an


def get_blank_board():
    # создает и возвращает пустое поле
    board = []
    for x in range(BOARD_WIDTH):
        board.append([EMPTY_SPACE] * BOARD_HEIGHT)
    return board


def can_make_move(board):
    # Возвращает True если есть возможные ходы иначе False.

    # Шаблоны в one_off_patterns представляют собой комбинации положений морских обитателей,
    # которые расположены таким образом, что для создания "линии" требуется всего один ход.

    one_off_patterns = (((0, 1), (1, 0), (2, 0)),
                        ((0, 1), (1, 1), (2, 0)),
                        ((0, 0), (1, 1), (2, 0)),
                        ((0, 1), (1, 0), (2, 1)),
                        ((0, 0), (1, 0), (2, 1)),
                        ((0, 0), (1, 1), (2, 1)),
                        ((0, 0), (0, 2), (0, 3)),
                        ((0, 0), (0, 1), (0, 3)))

    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            for pat in one_off_patterns:
                # проверяем все шаблоны для данной клетки
                if (get_ocean_an_at(board, x + pat[0][0], y + pat[0][1]) ==
                    get_ocean_an_at(board, x + pat[1][0], y + pat[1][1]) ==
                    get_ocean_an_at(board, x + pat[2][0], y + pat[2][1]) is not None) or \
                        (get_ocean_an_at(board, x + pat[0][1], y + pat[0][0]) ==
                         get_ocean_an_at(board, x + pat[1][1], y + pat[1][0]) ==
                         get_ocean_an_at(board, x + pat[2][1], y + pat[2][0]) is not None):
                    return True  # возвращаем True, как только найдем хотя бы 1 возможный ход
    return False


def draw_moving_ocean_an(ocean_an_t, progress):
    # Рисуем перемещение морского обитателеля
    # Параметр progress принимает значение от 0 (в начале перемещения
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


def pull_down_all_ocean_ans(board):
    # добавляем морских обитателей пока не заполним поле
    for x in range(BOARD_WIDTH):
        ocean_ans_in_column = []
        for y in range(BOARD_HEIGHT):
            if board[x][y] != EMPTY_SPACE:
                ocean_ans_in_column.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARD_HEIGHT - len(ocean_ans_in_column))) + ocean_ans_in_column


def get_ocean_an_at(board, x, y):
    # возвращает тип морского обитателя в координатах х, у
    if x < 0 or y < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
        return None
    else:
        return board[x][y]


def get_drop_slots(board):
    # Создает набор морских обитателей для каждой колонки и заполняет его недостающим
    # количеством
    board_copy = copy.deepcopy(board)
    pull_down_all_ocean_ans(board_copy)

    drop_slots = []
    for i in range(BOARD_WIDTH):
        drop_slots.append([])

    # считаем количество пустых ячеек в каждой колонке
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT - 1, -1, -1):  # идем снизу вверх
            if board_copy[x][y] == EMPTY_SPACE:
                possible_ocean_ans = list(range(len(OCEAN_AN_IMAGES)))
                for offsetX, offsetY in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    # Определяем круг возможных морских обитателей, которые мы добавим
                    # на пустые ячейки, чтобы не поставить два одинаковых
                    # рядом друг с другом, когда они упадут.
                    neighbor_ocean_an = get_ocean_an_at(board_copy, x + offsetX, y + offsetY)
                    if neighbor_ocean_an is not None and neighbor_ocean_an in possible_ocean_ans:
                        possible_ocean_ans.remove(neighbor_ocean_an)

                new_ocean_an = random.choice(possible_ocean_ans)
                board_copy[x][y] = new_ocean_an
                drop_slots[x].append(new_ocean_an)
    return drop_slots


def find_matching_ocean_ans(board):
    ocean_ans_to_remove = []  # a список списков групп морских обитателей, которые должны быть удалены
    board_copy = copy.deepcopy(board)

    # проверяем наличие "линий"
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            # проверяем горизонтальные совпадения
            if get_ocean_an_at(board_copy, x, y) == get_ocean_an_at(board_copy, x + 1, y) == \
                    get_ocean_an_at(board_copy, x + 2, y) and get_ocean_an_at(board_copy, x, y) != EMPTY_SPACE:
                target_ocean_an = board_copy[x][y]
                offset = 0
                remove_set = []
                while get_ocean_an_at(board_copy, x + offset, y) == target_ocean_an:
                    # проверяем если в линии большее количество морских обитателей
                    remove_set.append((x + offset, y))
                    board_copy[x + offset][y] = EMPTY_SPACE
                    offset += 1
                ocean_ans_to_remove.append(remove_set)

            # проверяем вертикальные совпадения
            if get_ocean_an_at(board_copy, x, y) == get_ocean_an_at(board_copy, x, y + 1) == \
                    get_ocean_an_at(board_copy, x, y + 2) and get_ocean_an_at(board_copy, x, y) != EMPTY_SPACE:
                target_ocean_an = board_copy[x][y]
                offset = 0
                remove_set = []
                while get_ocean_an_at(board_copy, x, y + offset) == target_ocean_an:
                    # проверяем если в линии большее количество морских обитателей
                    remove_set.append((x, y + offset))
                    board_copy[x][y + offset] = EMPTY_SPACE
                    offset += 1
                ocean_ans_to_remove.append(remove_set)

    return ocean_ans_to_remove


def highlight_space(x, y):
    # рисует отдельную ячейку
    pygame.draw.rect(DISPLAY_SURF, HIGHLIGHT_COLOR, board_rects[x][y], 4)


def get_dropping_ocean_ans(board):
    # "Опускаем всех морских обитателей, под которыми есть пустые ячейки
    board_copy = copy.deepcopy(board)
    dropping_ocean_ans = []
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT - 2, -1, -1):
            if board_copy[x][y + 1] == EMPTY_SPACE and board_copy[x][y] != EMPTY_SPACE:
                # опускаем если в ячейке есть морской обитатель, но есть пустая ячейка ниже
                dropping_ocean_ans.append({'imageNum': board_copy[x][y], 'x': x, 'y': y, 'direction': DOWN})
                board_copy[x][y] = EMPTY_SPACE
    return dropping_ocean_ans


def animate_moving_ocecan_ans(board, ocean_ans, points_text, score):
    progress = 0  # progress 0 означает начало анимации, 100 - по завершении.
    while progress < 100:  # цикл анимации
        DISPLAY_SURF.fill(BG_COLOR)
        draw_board(board)
        for ocean_an_t in ocean_ans:  # рисуем каждый гем
            draw_moving_ocean_an(ocean_an_t, progress)
        draw_score(score)
        for pointText in points_text:
            points_surf = BASIC_FONT.render(str(pointText['points']), True, SCORE_COLOR)
            points_rect = points_surf.get_rect()
            points_rect.center = (pointText['x'], pointText['y'])
            DISPLAY_SURF.blit(points_surf, points_rect)

        pygame.display.update()
        FPS_CLOCK.tick(FPS)
        progress += MOVE_RATE  # немного увеличиваем прогресс анимации


def move_ocean_ans(board, moving_ocean_ans):
    # move_ocean_ans это список словарей с ключами x, y, direction, imageNum
    for ocean_an_t in moving_ocean_ans:
        if ocean_an_t['y'] != ROW_ABOVE_BOARD:
            board[ocean_an_t['x']][ocean_an_t['y']] = EMPTY_SPACE
            move_x = 0
            move_y = 0
            if ocean_an_t['direction'] == LEFT:
                move_x = -1
            elif ocean_an_t['direction'] == RIGHT:
                move_x = 1
            elif ocean_an_t['direction'] == DOWN:
                move_y = 1
            elif ocean_an_t['direction'] == UP:
                move_y = -1
            board[ocean_an_t['x'] + move_x][ocean_an_t['y'] + move_y] = ocean_an_t['imageNum']
        else:
            # морской обитатель находится над доской (откуда берутся новые кристаллы)
            board[ocean_an_t['x']][0] = ocean_an_t['imageNum']  # перейти в верхнюю строку


def fill_board_and_animate(board, points, score):
    drop_slots = get_drop_slots(board)
    while drop_slots != [[]] * BOARD_WIDTH:
        # делаем анимацию падающих морских обитателей, пока таковые имеются
        moving_ocean_ans = get_dropping_ocean_ans(board)
        for x in range(len(drop_slots)):
            if len(drop_slots[x]) != 0:
                # сдвигаем вниз самого нижнего морского обитателя в каждой колонке, если возможно
                moving_ocean_ans.append({'imageNum': drop_slots[x][0], 'x': x, 'y': ROW_ABOVE_BOARD, 'direction': DOWN})

        board_copy = get_board_copy_minus_ocean_ans(board, moving_ocean_ans)
        animate_moving_ocecan_ans(board_copy, moving_ocean_ans, points, score)
        move_ocean_ans(board, moving_ocean_ans)

        # Обрабатываем следующую строку
        for x in range(len(drop_slots)):
            if len(drop_slots[x]) == 0:
                continue
            board[x][0] = drop_slots[x][0]
            del drop_slots[x][0]


def check_for_ocean_an_click(pos):
    # промеряем клик, попал он на ячейку или нет
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            if board_rects[x][y].collidepoint(pos[0], pos[1]):
                return {'x': x, 'y': y}
    return None  # клик был не на ячейку


def draw_board(board):
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            pygame.draw.rect(DISPLAY_SURF, GRID_COLOR, board_rects[x][y], 1)
            ocean_an_to_draw = board[x][y]
            if ocean_an_to_draw != EMPTY_SPACE:
                DISPLAY_SURF.blit(OCEAN_AN_IMAGES[ocean_an_to_draw], board_rects[x][y])


def get_board_copy_minus_ocean_ans(board, ocean_ans):
    # Создает и возвращает копию переданной структуры данных поля,
    # с удаленными морскими обитателями из списка 'ocean_ans'

    board_copy = copy.deepcopy(board)

    for ocean_an_t in ocean_ans:
        if ocean_an_t['y'] != ROW_ABOVE_BOARD:
            board_copy[ocean_an_t['x']][ocean_an_t['y']] = EMPTY_SPACE
    return board_copy


def draw_score(score):
    score_img = BASIC_FONT.render(str(score), True, SCORE_COLOR)
    score_rect = score_img.get_rect()
    score_rect.bottomleft = (10, WINDOW_HEIGHT - 6)
    DISPLAY_SURF.blit(score_img, score_rect)


if __name__ == '__main__':
    main()

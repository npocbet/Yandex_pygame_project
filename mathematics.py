import copy
import random

BOARD_WIDTH = 8  # количество "столбцов" на поле
BOARD_HEIGHT = 8  # количество "рядов" на поле

EMPTY_SPACE = -1  # произвольное неположительное значение

ROW_ABOVE_BOARD = 'row above board'  # произвольное, нецелое значение

# константы для значения направлений
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

OCEAN_AN_IMAGES = []
board_rects = []

def get_blank_board():
    # создает и возвращает пустое поле
    board = []
    for x in range(BOARD_WIDTH):
        board.append([EMPTY_SPACE] * BOARD_HEIGHT)
    return board


def get_ocean_an_at(board, x, y):
    # возвращает тип морского обитателя в координатах х, у
    if x < 0 or y < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
        return None
    else:
        return board[x][y]


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
        # Морские обитатели не соседние и не могут поменяться местами
        return None, None
    return first_ocean_an, second_ocean_an


def pull_down_all_ocean_ans(board):
    # добавляем морских обитателей пока не заполним поле
    for x in range(BOARD_WIDTH):
        ocean_ans_in_column = []
        for y in range(BOARD_HEIGHT):
            if board[x][y] != EMPTY_SPACE:
                ocean_ans_in_column.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARD_HEIGHT - len(ocean_ans_in_column))) + ocean_ans_in_column


def find_matching_ocean_ans(board):
    ocean_ans_to_remove = []  # список списков групп морских обитателей, которые должны быть удалены
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


def get_board_copy_minus_ocean_ans(board, ocean_ans):
    # Создает и возвращает копию переданной структуры данных поля,
    # с удаленными морскими обитателями из списка 'ocean_ans'

    board_copy = copy.deepcopy(board)

    for ocean_an_t in ocean_ans:
        if ocean_an_t['y'] != ROW_ABOVE_BOARD:
            board_copy[ocean_an_t['x']][ocean_an_t['y']] = EMPTY_SPACE
    return board_copy


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

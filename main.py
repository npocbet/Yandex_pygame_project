import random

import pygame
import time
import sys

from PyQt5.QtWidgets import QApplication
from pygame.locals import *

from graph import WINDOW_WIDTH, WINDOW_HEIGHT, DISPLAY_SURF, fill_board_and_animate, BG_COLOR, draw_board, \
    highlight_space, NUM_OCEAN_AN_IMAGES, check_for_ocean_an_click, animate_moving_ocecan_ans, OCEAN_AN_IMAGE_SIZE, \
    X_MARGIN, Y_MARGIN, BASIC_FONT, GAME_OVER_COLOR, GAME_OVER_BG_COLOR, DEDUCT_SPEED, FPS_CLOCK, draw_score, FPS, \
    NUM_MATCH_SOUNDS, GAME_SOUNDS
from mathematics import get_blank_board, find_matching_ocean_ans, can_make_move, get_swapping_ocean_ans, \
    get_board_copy_minus_ocean_ans, EMPTY_SPACE, OCEAN_AN_IMAGES, BOARD_WIDTH, BOARD_HEIGHT, board_rects
from results import ResultWidget, paste_score_into_db


def run_game():
    # Функция запускает одиночную игру

    # инициализируем поле
    # global ocean_an
    game_board = get_blank_board()
    score = 0
    fill_board_and_animate(DISPLAY_SURF, game_board, [], score)

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
            animate_moving_ocecan_ans(DISPLAY_SURF, board_copy, [first_swapping_ocean_an, second_swapping_ocean_an], [], score)

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
                animate_moving_ocecan_ans(DISPLAY_SURF, board_copy, [first_swapping_ocean_an, second_swapping_ocean_an], [], score)
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
                    fill_board_and_animate(DISPLAY_SURF, game_board, points, score)

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

                paste_score_into_db(score)

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


def main():
    # global FPS_CLOCK, OCEAN_AN_IMAGES, GAME_SOUNDS, BASIC_FONT, board_rects

    # Инициализация
    pygame.init()
    pygame.display.set_caption('На днем морском!')

    # Загружаем картинки
    for i in range(1, NUM_OCEAN_AN_IMAGES + 1):
        ocean_an_image = pygame.image.load('./img/p%s.png' % i)
        if ocean_an_image.get_size() != (OCEAN_AN_IMAGE_SIZE, OCEAN_AN_IMAGE_SIZE):
            ocean_an_image = pygame.transform.smoothscale(ocean_an_image, (OCEAN_AN_IMAGE_SIZE, OCEAN_AN_IMAGE_SIZE))
        OCEAN_AN_IMAGES.append(ocean_an_image)

    # Загружаем звуки

    for i in range(NUM_MATCH_SOUNDS):
        GAME_SOUNDS['match'].append(pygame.mixer.Sound('./sounds/match%s.wav' % i))

    # Для каждой ячейки создадим pygame.Rect
    # чтобы делать преобразования от координат в "ячейках" к координатам
    # в пикселях

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


if __name__ == '__main__':
    main()

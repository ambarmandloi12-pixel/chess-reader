import sys
import os
import time
import pyautogui
import keyboard

from PIL import ImageChops, ImageStat
from stockfish import Stockfish


# =========================================================
# CONFIGURATION
# =========================================================

ENGINE_PATH = r"C:\Users\srw\Desktop\mentos zindagi\not mine\stockfish\stockfish.exe"
BOARD_REGION = (162, 159, 481, 483)

PLAYER_COLOR = "black"   # "white" or "black"

MOVE_DELAY_MIN = 2
MOVE_DELAY_MAX = 6


# =========================================================
# GLOBAL STATE
# =========================================================

last_screenshot = None
ORIENTATION = "normal"

stockfish = None
moves_history = []


# =========================================================
# ENGINE
# =========================================================

def start_engine():
    global stockfish

    try:
        if os.path.exists(ENGINE_PATH):

            stockfish = Stockfish(path=ENGINE_PATH)

            stockfish.set_skill_level(20)

            print(f"[SUCCESS] Stockfish Loaded")
            print(f"Path: {ENGINE_PATH}")

        else:
            print("[ERROR] Stockfish executable not found")

    except Exception as e:
        print(f"[ENGINE ERROR] {e}")


def get_best_move():
    global stockfish
    global moves_history

    if stockfish is None:
        return None

    try:
        stockfish.set_position(moves_history)

        return stockfish.get_best_move()

    except Exception as e:
        print(f"[MOVE ERROR] {e}")

        return None


def is_move_legal(uci_move):
    global stockfish
    global moves_history

    if stockfish is None:
        return False

    try:
        stockfish.set_position(moves_history)

        return stockfish.is_move_correct(uci_move)

    except:
        return False


# =========================================================
# BOARD / PIXEL HELPERS
# =========================================================

def get_square_pixel(square_str):
    global ORIENTATION

    file_char = square_str[0]
    rank_char = square_str[1]

    col = ord(file_char) - ord('a')
    row = 8 - int(rank_char)

    if ORIENTATION == "flipped":
        col = 7 - col
        row = 7 - row

    bx, by, bw, bh = BOARD_REGION

    sq_w = bw / 8
    sq_h = bh / 8

    target_x = bx + (col * sq_w) + (sq_w / 2)
    target_y = by + (row * sq_h) + (sq_h / 2)

    return int(target_x), int(target_y)


def click_move_on_screen(move_str):

    if not move_str or len(move_str) < 4:
        return

    start_square = move_str[0:2]
    end_square = move_str[2:4]

    start_x, start_y = get_square_pixel(start_square)
    end_x, end_y = get_square_pixel(end_square)

    original_x, original_y = pyautogui.position()

    pyautogui.click(start_x, start_y, _pause=False)

    time.sleep(0.10)

    pyautogui.click(end_x, end_y, _pause=False)

    pyautogui.moveTo(original_x, original_y)


# =========================================================
# ENGINE TURN
# =========================================================

def execute_engine_turn():

    global last_screenshot
    global moves_history

    stockfish.set_position(moves_history)

    engine_move = get_best_move()

    if engine_move:

        print(f"[ENGINE MOVE] {engine_move}")

        click_move_on_screen(engine_move)

        moves_history.append(engine_move)

        time.sleep(0.40)

        refreshed_raw = pyautogui.screenshot(region=BOARD_REGION)

        last_screenshot = refreshed_raw.copy()

        print("[DONE] Move Registered")


# =========================================================
# SCAN OPPONENT MOVE
# =========================================================

def scan():

    global last_screenshot
    global ORIENTATION
    global moves_history

    print("\n[SCANNING BOARD]")

    raw_img = pyautogui.screenshot(region=BOARD_REGION)

    current_img = raw_img.copy()

    w, h = current_img.size

    sq_w = w / 8
    sq_h = h / 8

    square_changes = {}

    for row in range(8):

        for col in range(8):

            margin = 14

            box = (
                int(col * sq_w + margin),
                int(row * sq_h + margin),
                int((col + 1) * sq_w - margin),
                int((row + 1) * sq_h - margin)
            )

            sq_old = last_screenshot.crop(box)
            sq_new = current_img.crop(box)

            diff_score = sum(
                ImageStat.Stat(
                    ImageChops.difference(sq_old, sq_new)
                ).mean
            )

            if diff_score > 15:

                if ORIENTATION == "flipped":

                    square_name = (
                        chr(ord('a') + (7 - col)),
                        str(row + 1)
                    )

                else:

                    square_name = (
                        chr(ord('a') + col),
                        str(8 - row)
                    )

                square_str = "".join(square_name)

                square_changes[square_str] = diff_score

    if not square_changes:

        print("[INFO] No board changes detected")

        return

    sorted_squares = [
        k for k, v in sorted(
            square_changes.items(),
            key=lambda item: item[1],
            reverse=True
        )
    ]

    print(f"[CHANGED SQUARES] {sorted_squares}")

    found_move = None

    stockfish.set_position(moves_history)

    for s in sorted_squares:

        piece_on_start = stockfish.get_what_is_on_square(s)

        if piece_on_start is None:
            continue

        is_piece_white = piece_on_start.name.startswith('W')

        # =================================================
        # DETECT ONLY OPPONENT PIECES
        # =================================================

        if PLAYER_COLOR == "white":

            if is_piece_white:
                continue

        else:

            if not is_piece_white:
                continue

        for e in sorted_squares:

            if s == e:
                continue

            uci_attempt = s + e

            move_variants = [
                uci_attempt,
                uci_attempt + "q"
            ]

            for mv in move_variants:

                if is_move_legal(mv):

                    found_move = mv

                    break

            if found_move:
                break

        if found_move:
            break

    if found_move:

        print(f"[OPPONENT MOVE] {found_move}")

        moves_history.append(found_move)

        execute_engine_turn()

    else:

        print("[FAILED] Could not parse legal move")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("===================================")
    print("DUAL COLOR CHESS AUTOPLAY BOT")
    print("===================================")

    start_engine()

    if PLAYER_COLOR == "white":
        ORIENTATION = "normal"
    else:
        ORIENTATION = "flipped"

    print(f"\n[PLAYER COLOR] {PLAYER_COLOR}")
    print(f"[ORIENTATION] {ORIENTATION}")

    print("\nINSTRUCTIONS")
    print("-----------------------------------")
    print("1. Open fresh chess board")
    print("2. Keep board visible")
    print("3. Press [`] to initialize")
    print("4. Press [`] after opponent move")
    print("5. Press [r] to reset")
    print("-----------------------------------")

    try:

        while True:

            # ============================================
            # START / SCAN
            # ============================================

            if keyboard.is_pressed('`'):

                if last_screenshot is None:

                    print("\n[BASELINE CAPTURE]")

                    raw_img = pyautogui.screenshot(region=BOARD_REGION)

                    last_screenshot = raw_img.copy()

                    print("[SUCCESS] Baseline Saved")

                    # White moves first
                    if PLAYER_COLOR == "white":

                        execute_engine_turn()

                else:

                    scan()

                time.sleep(0.8)

            # ============================================
            # RESET
            # ============================================

            if keyboard.is_pressed('r'):

                moves_history = []

                last_screenshot = None

                print("\n[RESET COMPLETE]")

                time.sleep(0.8)

            time.sleep(0.01)

    except KeyboardInterrupt:

        print("\n[EXITING]")

        sys.exit()

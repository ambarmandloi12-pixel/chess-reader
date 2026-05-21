import sys
import os
import time
import pyautogui
import keyboard
from PIL import ImageChops, ImageStat
from stockfish import Stockfish

# Path Configuration
ENGINE_PATH = r'C:\Users\srw\Desktop\cheat-\stockfish.exe'
BOARD_REGION = (162, 159, 481, 483) 

# State variables
last_screenshot = None 
ORIENTATION = 'normal'
stockfish = None
moves_history = []  # Tracks game state for Stockfish wrapper

def start_engine():
    """Initializes the Stockfish wrapper package."""
    global stockfish
    try:
        if os.path.exists(ENGINE_PATH):
            stockfish = Stockfish(path=ENGINE_PATH)
            print(f" SUCCESS: Stockfish loaded from {ENGINE_PATH}")
        else:
            print(f" ERROR: Cannot find stockfish.exe at {ENGINE_PATH}")
    except Exception as e:
        print(f" STARTUP CRASH: {e}")

def get_best_move():
    """Gets the next best move based on the tracked moves history."""
    global stockfish, moves_history
    if stockfish is None:
        return None
    try:
        stockfish.set_position(moves_history)
        return stockfish.get_best_move()
    except Exception as e:
        print(f"Engine Error: {e}")
        return None

def is_move_legal(uci_move):
    """Checks if a generated move string is valid according to the engine."""
    global stockfish, moves_history
    if stockfish is None:
        return False
    stockfish.set_position(moves_history)
    return stockfish.is_move_correct(uci_move)

def get_square_pixel(square_str):
    """Calculates the exact central screen coordinates (X, Y) for any UCI square."""
    global ORIENTATION
    file_char = square_str[0]
    rank_char = square_str[1]
    
    col = ord(file_char) - ord('a')
    row = 8 - int(rank_char)
    
    if ORIENTATION == 'flipped':
        col = 7 - col
        row = 7 - row
        
    bx, by, bw, bh = BOARD_REGION
    sq_w = bw / 8
    sq_h = bh / 8
    
    target_x = bx + (col * sq_w) + (sq_w / 2)
    target_y = by + (row * sq_h) + (sq_h / 2)
    return int(target_x), int(target_y)

def click_move_on_screen(move_str):
    """Executes mouse movements and clicks to play the move on screen."""
    if not move_str or len(move_str) < 4:
        return
        
    start_square = move_str[0:2]
    end_square = move_str[2:4]
    
    start_x, start_y = get_square_pixel(start_square)
    end_x, end_y = get_square_pixel(end_square)
    
    orig_x, orig_y = pyautogui.position()
    
    pyautogui.click(start_x, start_y, _pause=False)
    time.sleep(0.1)
    pyautogui.click(end_x, end_y, _pause=False)
    
    pyautogui.moveTo(orig_x, orig_y)

def scan():
    global last_screenshot, ORIENTATION, moves_history
    
    is_whites_turn = (len(moves_history) % 2 == 0)
    
    # Enforce strict turn order
    if is_whites_turn and len(moves_history) > 0:
        print("\n[Notice] Waiting for Opponent (Black) to move. Do not scan yet.")
        return

    print(f"\n[Scanning... Detecting Opponent's Move]")
    
    raw_img = pyautogui.screenshot(region=BOARD_REGION)
    current_img = raw_img.copy()

    w, h = current_img.size
    sq_w, sq_h = w / 8, h / 8
    square_changes = {}

    for row in range(8):
        for col in range(8):
            margin = 14  
            box = (int(col*sq_w+margin), int(row*sq_h+margin), int((col+1)*sq_w-margin), int((row+1)*sq_h-margin))
            sq_old = last_screenshot.crop(box)
            sq_new = current_img.crop(box)
            
            diff_score = sum(ImageStat.Stat(ImageChops.difference(sq_old, sq_new)).mean)
            
            if diff_score > 15:
                square_name = (chr(ord('a')+(7-col)), str(row+1)) if ORIENTATION == 'flipped' else (chr(ord('a')+col), str(8-row))
                square_str = "".join(square_name)
                square_changes[square_str] = diff_score

    if not square_changes:
        print(" No changes detected.")
        return

    sorted_squares = [k for k, v in sorted(square_changes.items(), key=lambda item: item[1], reverse=True)]
    print(f"Detected Changes: {sorted_squares}")
    
    found_move = None
    stockfish.set_position(moves_history)
    
    # Look for Black's move exclusively
    for s in sorted_squares:
        piece_on_start = stockfish.get_what_is_on_square(s)
        if piece_on_start is None:
            continue
            
        is_piece_white = piece_on_start.name.startswith('W')
        if is_piece_white:  
            continue  
            
        for e in sorted_squares:
            if s == e: 
                continue
            uci_attempt = s + e
            for move_variant in [uci_attempt, uci_attempt + "q"]:
                if is_move_legal(move_variant):
                    found_move = move_variant
                    break
            if found_move: break
        if found_move: break
            
    if found_move:
        print(f" Detected Black Move: {found_move}")
        moves_history.append(found_move)
        execute_white_turn()
    else:
        print(" Invalid move parsing profile. Could not extract a legal Black move.")

def execute_white_turn():
    """Handles Stockfish calculation, Autoplay clicking, and updates baseline image."""
    global last_screenshot, moves_history
    stockfish.set_position(moves_history)
    white_reply = get_best_move()
    
    if white_reply:
        print(f"🤖 Autoplay White Move: Executing {white_reply}...")
        click_move_on_screen(white_reply)
        moves_history.append(white_reply)
        
        # Wait for animation to finish, then save updated board state
        time.sleep(0.4)
        refreshed_raw = pyautogui.screenshot(region=BOARD_REGION)
        last_screenshot = refreshed_raw.copy()
        print(" White Move Registered. Waiting for Black's turn to complete...")

if __name__ == "__main__":
    print("--- 100% AUTOMATED WHITE AUTOPLAY BOT ---")
    start_engine()
    ORIENTATION = 'normal'
    
    print("\n🚀 Match Play Flow:")
    print("1. Open your chess game and make sure it is a brand-new board setup.")
    print("2. Move your cursor off the board and press [`] (backtick).")
    print("3. The bot will save the baseline and immediately execute the first White move for you!")
    print("4. From then on, ONLY press [`] (backtick) after Black completes their turn.")
    print("\nPress [r] to reset the engine history entirely.")
    
    try:
        while True:
            if keyboard.is_pressed('`'):
                if last_screenshot is None:
                    # Initial setup sequence
                    print("\n[System] Capturing initial baseline...")
                    raw_img = pyautogui.screenshot(region=BOARD_REGION)
                    last_screenshot = raw_img.copy()
                    print("✅ Baseline Set. Playing first White move now...")
                    execute_white_turn()
                else:
                    # Regular gameplay scan
                    scan()
                time.sleep(0.8)
                
            if keyboard.is_pressed('r'):
                moves_history = []
                last_screenshot = None
                print(" Reset complete. Set your baseline again on a clean board.")
                time.sleep(0.8)
            time.sleep(0.01)
    except KeyboardInterrupt:
        sys.exit()

import os
import sys
import ctypes
import time
import winsound
import random

from src.core import Kernel
from src.ui import WindowManager
from src.ai import ZobristHash, TranspositionTable, get_best_ai_move, calculate_material_advantage
from src.chess import is_square_attacked, get_king_pos, is_move_valid, has_legal_moves
from src.config import load_settings, save_settings

cursor = WindowManager()
menu = WindowManager()

def main():
    MIN_COLS, MIN_ROWS = 80, 24
    MAX_COLS, MAX_ROWS = 240, 60

    try:
        columns, rows = os.get_terminal_size()
    except OSError:
        columns, rows = 80, 24

    if not (MIN_COLS <= columns <= MAX_COLS and MIN_ROWS <= rows <= MAX_ROWS):
        print(f"Error: Terminal size ({columns}x{rows}) is outside the supported range.")
        print(f"Please resize your terminal to be between {MIN_COLS}x{MIN_ROWS} and {MAX_COLS}x{MAX_ROWS}.")
        sys.exit(1)

    kernel = Kernel(columns, rows)
    kernel.clear_screen()

    player_col, player_row = 4, 4
    player_x, player_y = 0.0, 0.0
    menu_selection = 0
    menu_options = ["Resume", "Restart", "Game Mode", "FPS Select", "Exit"]
    
    white_pieces = {
        '♖': [(0, 7), (7, 7)], '♘': [(1, 7), (6, 7)], '♗': [(2, 7), (5, 7)], '♕': [(3, 7)], '♔': [(4, 7)],
        '♙': [(i, 6) for i in range(8)]
    }
    black_pieces = {
        '♜': [(0, 0), (7, 0)], '♞': [(1, 0), (6, 0)], '♝': [(2, 0), (5, 0)], '♛': [(3, 0)], '♚': [(4, 0)],
        '♟': [(i, 1) for i in range(8)]
    }
    all_pieces = {'white': white_pieces, 'black': black_pieces}
    
    marked_cells = []
    possible_moves = []
    last_move = {'piece': None, 'start': None, 'end': None, 'turn': 0}
    move_history = []
    white_captured = []
    black_captured = []

    has_moved = {'white_king': False, 'black_king': False, 'white_rook_a': False, 'white_rook_h': False, 'black_rook_a': False, 'black_rook_h': False}
    is_in_check = {'white': False, 'black': False}
    current_turn = 'white'
    
    zobrist_hash = ZobristHash()
    transposition_table = TranspositionTable(size_mb=64)
    
    settings = load_settings()
    colorblind_mode = settings.get('colorblind_mode', False)
    game_mode = settings.get('game_mode', 'pvp')
    ai_color = settings.get('ai_color', 'black')

    fps_selection = 1
    fps_options = [30, 60, 120, 240]
    sleep_time = 1 / fps_options[fps_selection]
    
    initial_cols, initial_rows = columns, rows
    
    ai_needs_first_move = (game_mode == 'vs_computer' and ai_color == 'white')
    
    TICK_RATE = 60
    MS_PER_UPDATE = 1.0 / TICK_RATE
    lag = 0.0
    previous_time = time.perf_counter()
    
    last_esc_press = 0
    ESC_COOLDOWN = 0.3
    last_menu_press = 0
    MENU_COOLDOWN = 0.15
    last_takeback_press = 0
    TAKEBACK_COOLDOWN = 1.0
    last_cb_toggle = 0
    CB_COOLDOWN = 1.0
    
    game_started = False

    while True:
        if not game_started and ai_needs_first_move and kernel.game_state == 'IN_GAME':
            game_started = True
            time.sleep(0.5)
            
            all_pieces_map = {}
            for color, piece_set in all_pieces.items():
                for char_key, positions in piece_set.items():
                    for pos in positions:
                        all_pieces_map[pos] = (char_key, color)
            
            ai_move = get_best_ai_move(all_pieces, all_pieces_map, 'white', is_in_check, zobrist_hash, transposition_table, has_moved, last_move, ai_color)
            
            if ai_move:
                ai_source, ai_dest, ai_char = ai_move
                captured_piece = None
                if ai_dest in all_pieces_map:
                    captured_piece_char, captured_piece_color = all_pieces_map[ai_dest]
                    captured_piece = (captured_piece_char, captured_piece_color, ai_dest)
                    all_pieces[captured_piece_color][captured_piece_char].remove(ai_dest)
                    if captured_piece_color == 'white':
                        black_captured.append(captured_piece_char)
                    else:
                        white_captured.append(captured_piece_char)
                
                all_pieces[ai_color][ai_char].remove(ai_source)
                all_pieces[ai_color][ai_char].append(ai_dest)
                
                move_record = {
                    'piece': (ai_char, ai_color, ai_source),
                    'target_pos': ai_dest,
                    'captured_piece': captured_piece,
                    'is_en_passant': False,
                    'is_castle': False
                }
                move_history.append(move_record)
                last_move = {'piece': ai_char, 'start': ai_source, 'end': ai_dest, 'turn': 1}
                
                if captured_piece:
                    winsound.Beep(1000, 100)
                else:
                    winsound.Beep(500, 100)
                
                all_pieces_map = {}
                for color, piece_set in all_pieces.items():
                    for char_key, positions in piece_set.items():
                        for pos in positions:
                            all_pieces_map[pos] = (char_key, color)
                
                is_in_check[ai_color] = False
                player_color = 'black'
                king_pos = get_king_pos(player_color, all_pieces_map)
                if king_pos and is_square_attacked(king_pos, ai_color, all_pieces_map):
                    is_in_check[player_color] = True
                    if not has_legal_moves(player_color, all_pieces, all_pieces_map):
                        kernel.game_state = 'IN_CHECKMATE'
                        winsound.Beep(1500, 500)
                    else:
                        winsound.Beep(1200, 200)
                else:
                    is_in_check[player_color] = False
                
                current_turn = player_color
        
        current_time = time.perf_counter()
        elapsed = current_time - previous_time
        previous_time = current_time
        lag += elapsed

        current_cols, current_rows = os.get_terminal_size()
        if current_cols != initial_cols or current_rows != initial_rows:
            kernel.clear_screen()
            print("Terminal resized. Please restart the game with a stable window size.")
            sys.exit(0)

        while lag >= MS_PER_UPDATE:
            if kernel.game_state == 'IN_GAME':
                now = time.perf_counter()
                if now - last_menu_press > MENU_COOLDOWN:
                    key_pressed = False
                    if ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000 and (now - last_esc_press) > ESC_COOLDOWN:
                        last_esc_press = now
                        kernel.game_state = 'IN_MENU'
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(ord('W')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x26) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(ord('K')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x68) & 0x8000:
                        player_row = max(0, player_row - 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(ord('S')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x28) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(ord('J')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x62) & 0x8000:
                        player_row = min(7, player_row + 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(ord('A')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x25) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(ord('H')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x64) & 0x8000:
                        player_col = max(-1, player_col - 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(ord('D')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x27) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(ord('L')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x66) & 0x8000:
                        player_col = min(9, player_col + 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x67) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x24) & 0x8000:
                        player_row = max(0, player_row - 1)
                        player_col = max(-1, player_col - 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x69) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x21) & 0x8000:
                        player_row = max(0, player_row - 1)
                        player_col = min(9, player_col + 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x61) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x23) & 0x8000:
                        player_row = min(7, player_row + 1)
                        player_col = max(-1, player_col - 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x63) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x22) & 0x8000:
                        player_row = min(7, player_row + 1)
                        player_col = min(9, player_col + 1)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x0D) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000:
                        if player_col == -1:
                            if (now - last_cb_toggle) > CB_COOLDOWN:
                                colorblind_mode = not colorblind_mode
                                save_settings(colorblind_mode, game_mode, ai_color)
                                winsound.Beep(800, 100)
                                last_cb_toggle = now
                        elif player_col == 8:
                           if move_history and (now - last_takeback_press) > TAKEBACK_COOLDOWN:
                               last_takeback_press = now
                               
                               moves_to_undo = 2 if game_mode == 'vs_computer' and len(move_history) >= 2 else 1
                               
                               for _ in range(moves_to_undo):
                                   if not move_history:
                                       break
                                       
                                   last_move_record = move_history.pop()
                                   
                                   piece_char, piece_color, original_pos = last_move_record['piece']
                                   moved_to_pos = last_move_record['target_pos']
                                   
                                   all_pieces[piece_color][piece_char].remove(moved_to_pos)
                                   all_pieces[piece_color][piece_char].append(original_pos)
                                   
                                   if last_move_record['captured_piece']:
                                       cap_char, cap_color, cap_pos = last_move_record['captured_piece']
                                       all_pieces[cap_color][cap_char].append(cap_pos)
                                       if cap_color == 'white':
                                           black_captured.remove(cap_char)
                                       else:
                                           white_captured.remove(cap_char)

                                   if last_move_record.get('is_castle', False):
                                       if moved_to_pos[0] == 6:
                                           rook_start_pos = (7, moved_to_pos[1])
                                           rook_end_pos = (5, moved_to_pos[1])
                                       else:
                                           rook_start_pos = (0, moved_to_pos[1])
                                           rook_end_pos = (3, moved_to_pos[1])
                                       
                                       rook_char = '♖' if piece_color == 'white' else '♜'
                                       all_pieces[piece_color][rook_char].remove(rook_end_pos)
                                       all_pieces[piece_color][rook_char].append(rook_start_pos)
                               
                               if move_history:
                                   prev_move = move_history[-1]
                                   last_move = {'piece': prev_move['piece'][0], 'start': prev_move['piece'][2], 'end': prev_move['target_pos'], 'turn': last_move['turn'] - moves_to_undo}
                               else:
                                   last_move = {'piece': None, 'start': None, 'end': None, 'turn': 0}

                               marked_cells.clear()
                               possible_moves.clear()
                               
                               winsound.Beep(600, 150)
                               
                               if game_mode == 'vs_computer':
                                   player_color = 'black' if ai_color == 'white' else 'white'
                                   current_turn = player_color
                               else:
                                   if moves_to_undo % 2 == 1:
                                       current_turn = 'black' if current_turn == 'white' else 'white'
                               
                               all_pieces_map = {}
                               for color, piece_set in all_pieces.items():
                                   for char, positions in piece_set.items():
                                       for pos in positions:
                                           all_pieces_map[pos] = (char, color)
                               
                               for check_color in ['white', 'black']:
                                   king_pos = get_king_pos(check_color, all_pieces_map)
                                   opponent = 'black' if check_color == 'white' else 'white'
                                   if king_pos and is_square_attacked(king_pos, opponent, all_pieces_map):
                                       is_in_check[check_color] = True
                                   else:
                                       is_in_check[check_color] = False

                        elif (player_col, player_row) in possible_moves:
                            source_pos = marked_cells[0]
                            dest_pos = (player_col, player_row)
                            
                            all_pieces_map = {}
                            for color, piece_set in all_pieces.items():
                                for char, positions in piece_set.items():
                                    for pos in positions:
                                        all_pieces_map[pos] = (char, color)
                            
                            moved = False
                            for color_name, piece_set in all_pieces.items():
                                if moved: break
                                for char, positions in piece_set.items():
                                    if source_pos in positions:
                                        captured_piece = None
                                        if dest_pos in all_pieces_map:
                                            captured_piece_char, captured_piece_color = all_pieces_map[dest_pos]
                                            captured_piece = (captured_piece_char, captured_piece_color, dest_pos)
                                            all_pieces[captured_piece_color][captured_piece_char].remove(dest_pos)
                                            if captured_piece_color == 'white':
                                                black_captured.append(captured_piece_char)
                                            else:
                                                white_captured.append(captured_piece_char)
                                        
                                        is_castle = char in ('♔', '♚') and abs(source_pos[0] - dest_pos[0]) == 2
                                        move_record = {
                                            'piece': (char, color_name, source_pos),
                                            'target_pos': dest_pos,
                                            'captured_piece': captured_piece,
                                            'is_en_passant': False,
                                            'is_castle': is_castle
                                        }

                                        positions.remove(source_pos)
                                        positions.append(dest_pos)

                                        if char == '♔' and source_pos == (4, 7): has_moved['white_king'] = True
                                        elif char == '♚' and source_pos == (4, 0): has_moved['black_king'] = True
                                        elif char == '♖' and source_pos == (0, 7): has_moved['white_rook_a'] = True
                                        elif char == '♖' and source_pos == (7, 7): has_moved['white_rook_h'] = True
                                        elif char == '♜' and source_pos == (0, 0): has_moved['black_rook_a'] = True
                                        elif char == '♜' and source_pos == (7, 0): has_moved['black_rook_h'] = True
                                        
                                        all_pieces[color_name][char] = positions
                                        
                                        if char in ('♙', '♟') and source_pos[0] != dest_pos[0] and dest_pos not in all_pieces_map:
                                            captured_pawn_pos = (dest_pos[0], source_pos[1])
                                            captured_piece_char, captured_piece_color = all_pieces_map[captured_pawn_pos]
                                            captured_piece = (captured_piece_char, captured_piece_color, captured_pawn_pos)
                                            move_record['captured_piece'] = captured_piece
                                            move_record['is_en_passant'] = True
                                            all_pieces[captured_piece_color][captured_piece_char].remove(captured_pawn_pos)
                                            if captured_piece_color == 'white':
                                                black_captured.append(captured_piece_char)
                                            else:
                                                white_captured.append(captured_piece_char)

                                        if move_record['is_castle']:
                                            if dest_pos[0] > source_pos[0]:
                                                rook_start_pos = (7, source_pos[1])
                                                rook_end_pos = (dest_pos[0] - 1, source_pos[1])
                                            else:
                                                rook_start_pos = (0, source_pos[1])
                                                rook_end_pos = (dest_pos[0] + 1, source_pos[1])
                                            
                                            rook_char = '♖' if color_name == 'white' else '♜'
                                            all_pieces[color_name][rook_char].remove(rook_start_pos)
                                            all_pieces[color_name][rook_char].append(rook_end_pos)

                                        last_move = {'piece': char, 'start': source_pos, 'end': dest_pos, 'turn': last_move['turn'] + 1}
                                        move_history.append(move_record)
                                        
                                        if char == '♙' and dest_pos[1] == 0:
                                            kernel.game_state = 'IN_PROMOTION_MENU'
                                            promotion_pos = dest_pos
                                        elif char == '♟' and dest_pos[1] == 7:
                                            kernel.game_state = 'IN_PROMOTION_MENU'
                                            promotion_pos = dest_pos
                                            
                                        moved = True
                                        
                                        if captured_piece or move_record['is_en_passant']:
                                            winsound.Beep(1000, 100)
                                        else:
                                            winsound.Beep(500, 100)
                                        
                                        all_pieces_map = {}
                                        for color, piece_set in all_pieces.items():
                                            for char_key, positions in piece_set.items():
                                                for pos in positions:
                                                    all_pieces_map[pos] = (char_key, color)
                                        
                                        is_in_check[color_name] = False
                                        
                                        opponent_color = 'black' if color_name == 'white' else 'white'
                                        king_pos = get_king_pos(opponent_color, all_pieces_map)
                                        if king_pos and is_square_attacked(king_pos, color_name, all_pieces_map):
                                            is_in_check[opponent_color] = True
                                            if not has_legal_moves(opponent_color, all_pieces, all_pieces_map):
                                                kernel.game_state = 'IN_CHECKMATE'
                                                winsound.Beep(1500, 500)
                                            else:
                                                winsound.Beep(1200, 200)
                                        else:
                                            is_in_check[opponent_color] = False
                                        
                                        current_turn = 'black' if current_turn == 'white' else 'white'
                                        
                                        if game_mode == 'vs_computer' and current_turn == ai_color and kernel.game_state == 'IN_GAME':
                                            time.sleep(0.3)
                                            
                                            all_pieces_map = {}
                                            for color, piece_set in all_pieces.items():
                                                for char_key, positions in piece_set.items():
                                                    for pos in positions:
                                                        all_pieces_map[pos] = (char_key, color)
                                            
                                            ai_move = get_best_ai_move(all_pieces, all_pieces_map, current_turn, is_in_check, zobrist_hash, transposition_table, has_moved, last_move, ai_color)
                                            
                                            if ai_move:
                                                ai_source, ai_dest, ai_char = ai_move
                                                
                                                captured_piece = None
                                                if ai_dest in all_pieces_map:
                                                    captured_piece_char, captured_piece_color = all_pieces_map[ai_dest]
                                                    captured_piece = (captured_piece_char, captured_piece_color, ai_dest)
                                                    all_pieces[captured_piece_color][captured_piece_char].remove(ai_dest)
                                                    if captured_piece_color == 'white':
                                                        black_captured.append(captured_piece_char)
                                                    else:
                                                        white_captured.append(captured_piece_char)
                                                
                                                all_pieces[ai_color][ai_char].remove(ai_source)
                                                all_pieces[ai_color][ai_char].append(ai_dest)
                                                
                                                move_record = {
                                                    'piece': (ai_char, ai_color, ai_source),
                                                    'target_pos': ai_dest,
                                                    'captured_piece': captured_piece,
                                                    'is_en_passant': False,
                                                    'is_castle': False
                                                }
                                                move_history.append(move_record)
                                                last_move = {'piece': ai_char, 'start': ai_source, 'end': ai_dest, 'turn': last_move['turn'] + 1}
                                                
                                                if captured_piece:
                                                    winsound.Beep(1000, 100)
                                                else:
                                                    winsound.Beep(500, 100)
                                                
                                                all_pieces_map = {}
                                                for color, piece_set in all_pieces.items():
                                                    for char_key, positions in piece_set.items():
                                                        for pos in positions:
                                                            all_pieces_map[pos] = (char_key, color)
                                                
                                                is_in_check[ai_color] = False
                                                player_color = 'white' if ai_color == 'black' else 'black'
                                                king_pos = get_king_pos(player_color, all_pieces_map)
                                                if king_pos and is_square_attacked(king_pos, ai_color, all_pieces_map):
                                                    is_in_check[player_color] = True
                                                    if not has_legal_moves(player_color, all_pieces, all_pieces_map):
                                                        kernel.game_state = 'IN_CHECKMATE'
                                                        winsound.Beep(1500, 500)
                                                    else:
                                                        winsound.Beep(1200, 200)
                                                else:
                                                    is_in_check[player_color] = False
                                                
                                                current_turn = player_color
                                        
                                        break
                                if moved:
                                    break
                            
                            marked_cells.clear()
                            possible_moves.clear()

                        elif (player_row, player_col) in marked_cells:
                            marked_cells.remove((player_row, player_col))
                            possible_moves = []
                        else:
                            marked_cells.clear()
                            marked_cells.append((player_col, player_row))
                            
                            selected_piece_char = None
                            selected_piece_color = None
                            all_pieces_map = {}
                            for color, piece_set in all_pieces.items():
                                for char, positions in piece_set.items():
                                    for pos in positions:
                                        all_pieces_map[pos] = (char, color)
                                        if (player_col, player_row) == pos:
                                            if color == current_turn:
                                                selected_piece_char = char
                                                selected_piece_color = color
                                            else:
                                                marked_cells.clear()
                                                possible_moves.clear()
                           
                            possible_moves = []
                            if selected_piece_char:
                                col, row = player_col, player_row
                                if selected_piece_char == '♙' and selected_piece_color == 'white':
                                    if row > 0 and (col, row - 1) not in all_pieces_map:
                                        possible_moves.append((col, row - 1))
                                    if row == 6 and (col, row - 1) not in all_pieces_map and (col, row - 2) not in all_pieces_map:
                                        possible_moves.append((col, row - 2))
                                    for dx in [-1, 1]:
                                        if 0 <= col + dx < 8 and (col + dx, row - 1) in all_pieces_map and all_pieces_map[(col + dx, row - 1)][1] == 'black':
                                            possible_moves.append((col + dx, row - 1))
                                    if last_move['piece'] == '♟' and abs(last_move['start'][1] - last_move['end'][1]) == 2 and last_move['end'][1] == row:
                                        if abs(last_move['end'][0] - col) == 1:
                                            possible_moves.append((last_move['end'][0], row - 1))
                                
                                elif selected_piece_char == '♟' and selected_piece_color == 'black':
                                    if row < 7 and (col, row + 1) not in all_pieces_map:
                                        possible_moves.append((col, row + 1))
                                    if row == 1 and (col, row + 1) not in all_pieces_map and (col, row + 2) not in all_pieces_map:
                                        possible_moves.append((col, row + 2))
                                    for dx in [-1, 1]:
                                        if 0 <= col + dx < 8 and (col + dx, row + 1) in all_pieces_map and all_pieces_map[(col + dx, row + 1)][1] == 'white':
                                            possible_moves.append((col + dx, row + 1))
                                    if last_move['piece'] == '♙' and abs(last_move['start'][1] - last_move['end'][1]) == 2 and last_move['end'][1] == row:
                                        if abs(last_move['end'][0] - col) == 1:
                                            possible_moves.append((last_move['end'][0], row + 1))
                                
                                elif selected_piece_char in ('♘', '♞'):
                                    offsets = [
                                        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                        (1, -2), (1, 2), (2, -1), (2, 1)
                                    ]
                                    for dx, dy in offsets:
                                        nx, ny = col + dx, row + dy
                                        if 0 <= nx < 8 and 0 <= ny < 8:
                                            if (nx, ny) not in all_pieces_map or all_pieces_map[(nx, ny)][1] != selected_piece_color:
                                                possible_moves.append((nx, ny))
                                
                                elif selected_piece_char in ('♖', '♜'):
                                    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                                    for dx, dy in directions:
                                        for i in range(1, 8):
                                            nx, ny = col + dx * i, row + dy * i
                                            if not (0 <= nx < 8 and 0 <= ny < 8):
                                                break
                                            if (nx, ny) in all_pieces_map:
                                                if all_pieces_map[(nx, ny)][1] != selected_piece_color:
                                                    possible_moves.append((nx, ny))
                                                break
                                            possible_moves.append((nx, ny))
                                
                                elif selected_piece_char in ('♗', '♝'):
                                    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                                    for dx, dy in directions:
                                        for i in range(1, 8):
                                            nx, ny = col + dx * i, row + dy * i
                                            if not (0 <= nx < 8 and 0 <= ny < 8):
                                                break
                                            if (nx, ny) in all_pieces_map:
                                                if all_pieces_map[(nx, ny)][1] != selected_piece_color:
                                                    possible_moves.append((nx, ny))
                                                break
                                            possible_moves.append((nx, ny))
                                
                                elif selected_piece_char in ('♕', '♛'):
                                    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                                    for dx, dy in directions:
                                        for i in range(1, 8):
                                            nx, ny = col + dx * i, row + dy * i
                                            if not (0 <= nx < 8 and 0 <= ny < 8):
                                                break
                                            if (nx, ny) in all_pieces_map:
                                                if all_pieces_map[(nx, ny)][1] != selected_piece_color:
                                                    possible_moves.append((nx, ny))
                                                break
                                            possible_moves.append((nx, ny))
                                            
                                elif selected_piece_char in ('♔', '♚'):
                                    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                                    for dx, dy in directions:
                                        nx, ny = col + dx, row + dy
                                        if 0 <= nx < 8 and 0 <= ny < 8:
                                            opponent_color = 'black' if selected_piece_color == 'white' else 'white'
                                            if not is_square_attacked((nx, ny), opponent_color, all_pieces_map):
                                                if (nx, ny) not in all_pieces_map or all_pieces_map[(nx, ny)][1] != selected_piece_color:
                                                    possible_moves.append((nx, ny))
                                    
                                    opponent_color = 'black' if selected_piece_color == 'white' else 'white'
                                    if not is_square_attacked((col, row), opponent_color, all_pieces_map):
                                        if selected_piece_color == 'white' and not has_moved['white_king']:
                                            if not has_moved['white_rook_h'] and (5, 7) not in all_pieces_map and (6, 7) not in all_pieces_map:
                                                if not is_square_attacked((5, 7), 'black', all_pieces_map) and not is_square_attacked((6, 7), 'black', all_pieces_map):
                                                    possible_moves.append((6, 7))
                                            if not has_moved['white_rook_a'] and (1, 7) not in all_pieces_map and (2, 7) not in all_pieces_map and (3, 7) not in all_pieces_map:
                                                if not is_square_attacked((2, 7), 'black', all_pieces_map) and not is_square_attacked((3, 7), 'black', all_pieces_map):
                                                    possible_moves.append((2, 7))
                                        elif selected_piece_color == 'black' and not has_moved['black_king']:
                                            if not has_moved['black_rook_h'] and (5, 0) not in all_pieces_map and (6, 0) not in all_pieces_map:
                                                if not is_square_attacked((5, 0), 'white', all_pieces_map) and not is_square_attacked((6, 0), 'white', all_pieces_map):
                                                    possible_moves.append((6, 0))
                                            if not has_moved['black_rook_a'] and (1, 0) not in all_pieces_map and (2, 0) not in all_pieces_map and (3, 0) not in all_pieces_map:
                                                if not is_square_attacked((2, 0), 'white', all_pieces_map) and not is_square_attacked((3, 0), 'white', all_pieces_map):
                                                    possible_moves.append((2, 0))
                                
                                final_moves = []
                                for move in possible_moves:
                                    if is_move_valid((col, row), move, selected_piece_char, selected_piece_color, all_pieces_map):
                                        final_moves.append(move)
                                possible_moves = final_moves
                        key_pressed = True

                    if key_pressed:
                        last_menu_press = now
            
            elif kernel.game_state in ['IN_MENU', 'IN_FPS_MENU', 'IN_GAMEMODE_MENU', 'IN_AI_COLOR_MENU', 'IN_PROMOTION_MENU', 'IN_CONFIRMATION', 'IN_CHECKMATE']:
                now = time.perf_counter()
                if now - last_menu_press > MENU_COOLDOWN:
                    key_pressed = False
                    if ctypes.windll.user32.GetAsyncKeyState(ord('W')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x26) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(ord('K')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x68) & 0x8000:
                        if kernel.game_state == 'IN_MENU': menu_selection = (menu_selection - 1) % len(menu_options)
                        elif kernel.game_state == 'IN_FPS_MENU': fps_selection = (fps_selection - 1) % len(fps_options)
                        elif kernel.game_state == 'IN_GAMEMODE_MENU': gamemode_selection = (gamemode_selection - 1) % 2
                        elif kernel.game_state == 'IN_AI_COLOR_MENU': ai_color_selection = (ai_color_selection - 1) % 2
                        elif kernel.game_state == 'IN_PROMOTION_MENU': promotion_selection = (promotion_selection - 1) % len(promotion_options_dict)
                        elif kernel.game_state == 'IN_CONFIRMATION': confirmation_selection = (confirmation_selection - 1) % 2
                        elif kernel.game_state == 'IN_CHECKMATE': menu_selection = (menu_selection - 1) % 2
                        else: sensitivity_selection = (sensitivity_selection - 1) % len(sensitivity_options)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(ord('S')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x28) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(ord('J')) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x62) & 0x8000:
                        if kernel.game_state == 'IN_MENU': menu_selection = (menu_selection + 1) % len(menu_options)
                        elif kernel.game_state == 'IN_FPS_MENU': fps_selection = (fps_selection + 1) % len(fps_options)
                        elif kernel.game_state == 'IN_GAMEMODE_MENU': gamemode_selection = (gamemode_selection + 1) % 2
                        elif kernel.game_state == 'IN_AI_COLOR_MENU': ai_color_selection = (ai_color_selection + 1) % 2
                        elif kernel.game_state == 'IN_PROMOTION_MENU': promotion_selection = (promotion_selection + 1) % len(promotion_options_dict)
                        elif kernel.game_state == 'IN_CONFIRMATION': confirmation_selection = (confirmation_selection + 1) % 2
                        elif kernel.game_state == 'IN_CHECKMATE': menu_selection = (menu_selection + 1) % 2
                        else: sensitivity_selection = (sensitivity_selection + 1) % len(sensitivity_options)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x0D) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x27) & 0x8000:
                        if kernel.game_state == 'IN_MENU':
                            selected = menu_options[menu_selection]
                            if selected == "Resume": kernel.game_state = 'IN_GAME'
                            elif selected == "Restart":
                                kernel.game_state = 'IN_CONFIRMATION'
                                confirmation_action = 'RESTART'
                                confirmation_selection = 1
                            elif selected == "Game Mode": kernel.game_state = 'IN_GAMEMODE_MENU'
                            elif selected == "FPS Select": kernel.game_state = 'IN_FPS_MENU'
                            elif selected == "Exit":
                                kernel.game_state = 'IN_CONFIRMATION'
                                confirmation_action = 'EXIT'
                                confirmation_selection = 1
                        elif kernel.game_state == 'IN_FPS_MENU':
                            sleep_time = 1 / fps_options[fps_selection]
                            kernel.game_state = 'IN_MENU'
                        elif kernel.game_state == 'IN_GAMEMODE_MENU':
                            old_game_mode = game_mode
                            game_mode = 'pvp' if gamemode_selection == 0 else 'vs_computer'
                            
                            if game_mode == 'vs_computer' and gamemode_selection == 1:
                                kernel.game_state = 'IN_AI_COLOR_MENU'
                            else:
                                save_settings(colorblind_mode, game_mode, ai_color)
                                
                                if old_game_mode != game_mode:
                                    kernel.game_state = 'IN_CONFIRMATION'
                                    confirmation_action = 'RESTART_MODE_CHANGE'
                                    confirmation_selection = 1
                                else:
                                    kernel.game_state = 'IN_MENU'
                        elif kernel.game_state == 'IN_AI_COLOR_MENU':
                            old_ai_color = ai_color
                            ai_color = 'black' if ai_color_selection == 0 else 'white'
                            save_settings(colorblind_mode, game_mode, ai_color)
                            
                            kernel.game_state = 'IN_CONFIRMATION'
                            confirmation_action = 'RESTART_MODE_CHANGE'
                            confirmation_selection = 1
                        elif kernel.game_state == 'IN_PROMOTION_MENU':
                            new_piece_char = list(promotion_options_dict.keys())[promotion_selection]
                            color_name = 'white' if promotion_pos[1] == 0 else 'black'
                            pawn_char = '♙' if color_name == 'white' else '♟'
                            all_pieces[color_name][pawn_char].remove(promotion_pos)
                            all_pieces[color_name][new_piece_char].append(promotion_pos)
                            kernel.game_state = 'IN_GAME'
                        elif kernel.game_state == 'IN_CONFIRMATION':
                            if confirmation_selection == 0:
                                if confirmation_action == 'RESTART':
                                    player_col, player_row = 4, 4
                                    marked_cells.clear()
                                    possible_moves.clear()
                                    white_pieces = {
                                        '♖': [(0, 7), (7, 7)], '♘': [(1, 7), (6, 7)], '♗': [(2, 7), (5, 7)], '♕': [(3, 7)], '♔': [(4, 7)],
                                        '♙': [(i, 6) for i in range(8)]
                                    }
                                    black_pieces = {
                                        '♜': [(0, 0), (7, 0)], '♞': [(1, 0), (6, 0)], '♝': [(2, 0), (5, 0)], '♛': [(3, 0)], '♚': [(4, 0)],
                                        '♟': [(i, 1) for i in range(8)]
                                    }
                                    all_pieces = {'white': white_pieces, 'black': black_pieces}
                                    has_moved = {'white_king': False, 'black_king': False, 'white_rook_a': False, 'white_rook_h': False, 'black_rook_a': False, 'black_rook_h': False}
                                    is_in_check = {'white': False, 'black': False}
                                    current_turn = 'white'
                                    last_move = {'piece': None, 'start': None, 'end': None, 'turn': 0}
                                    move_history = []
                                    white_captured = []
                                    black_captured = []
                                    transposition_table.clear()
                                    ai_needs_first_move = (game_mode == 'vs_computer' and ai_color == 'white')
                                    game_started = False
                                    kernel.game_state = 'IN_GAME'
                                    
                                elif confirmation_action == 'RESTART_MODE_CHANGE':
                                   player_col, player_row = 4, 4
                                   marked_cells.clear()
                                   possible_moves.clear()
                                   white_pieces = {
                                       '♖': [(0, 7), (7, 7)], '♘': [(1, 7), (6, 7)], '♗': [(2, 7), (5, 7)], '♕': [(3, 7)], '♔': [(4, 7)],
                                       '♙': [(i, 6) for i in range(8)]
                                   }
                                   black_pieces = {
                                       '♜': [(0, 0), (7, 0)], '♞': [(1, 0), (6, 0)], '♝': [(2, 0), (5, 0)], '♛': [(3, 0)], '♚': [(4, 0)],
                                       '♟': [(i, 1) for i in range(8)]
                                   }
                                   all_pieces = {'white': white_pieces, 'black': black_pieces}
                                   has_moved = {'white_king': False, 'black_king': False, 'white_rook_a': False, 'white_rook_h': False, 'black_rook_a': False, 'black_rook_h': False}
                                   is_in_check = {'white': False, 'black': False}
                                   current_turn = 'white'
                                   last_move = {'piece': None, 'start': None, 'end': None, 'turn': 0}
                                   move_history = []
                                   white_captured = []
                                   black_captured = []
                                   transposition_table.clear()
                                   ai_needs_first_move = (game_mode == 'vs_computer' and ai_color == 'white')
                                   game_started = False
                                   kernel.game_state = 'IN_GAME'
                                elif confirmation_action == 'EXIT':
                                    sys.exit(0)
                            else:
                                kernel.game_state = 'IN_MENU'
                        elif kernel.game_state == 'IN_CHECKMATE':
                            if menu_selection == 0:
                                player_col, player_row = 4, 4
                                marked_cells.clear()
                                possible_moves.clear()
                                white_pieces = {
                                    '♖': [(0, 7), (7, 7)], '♘': [(1, 7), (6, 7)], '♗': [(2, 7), (5, 7)], '♕': [(3, 7)], '♔': [(4, 7)],
                                    '♙': [(i, 6) for i in range(8)]
                                }
                                black_pieces = {
                                    '♜': [(0, 0), (7, 0)], '♞': [(1, 0), (6, 0)], '♝': [(2, 0), (5, 0)], '♛': [(3, 0)], '♚': [(4, 0)],
                                    '♟': [(i, 1) for i in range(8)]
                                }
                                all_pieces = {'white': white_pieces, 'black': black_pieces}
                                has_moved = {'white_king': False, 'black_king': False, 'white_rook_a': False, 'white_rook_h': False, 'black_rook_a': False, 'black_rook_h': False}
                                is_in_check = {'white': False, 'black': False}
                                transposition_table.clear()
                                kernel.game_state = 'IN_GAME'
                            else:
                                sys.exit(0)
                        key_pressed = True
                    if ctypes.windll.user32.GetAsyncKeyState(0x25) & 0x8000:
                        if kernel.game_state == 'IN_MENU':
                            pass
                        elif kernel.game_state == 'IN_FPS_MENU':
                            kernel.game_state = 'IN_MENU'
                        elif kernel.game_state == 'IN_GAMEMODE_MENU':
                            kernel.game_state = 'IN_MENU'
                        elif kernel.game_state == 'IN_PROMOTION_MENU':
                            pass
                        elif kernel.game_state == 'IN_CONFIRMATION':
                            kernel.game_state = 'IN_MENU'
                        key_pressed = True
                    
                    if key_pressed:
                        last_menu_press = now

                if ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000 and (time.perf_counter() - last_esc_press) > ESC_COOLDOWN:
                    last_esc_press = time.perf_counter()
                    if kernel.game_state == 'IN_CHECKMATE':
                        pass
                    elif kernel.game_state == 'IN_MENU': kernel.game_state = 'IN_GAME'
                    elif kernel.game_state == 'IN_FPS_MENU': kernel.game_state = 'IN_MENU'
                    elif kernel.game_state == 'IN_GAMEMODE_MENU': kernel.game_state = 'IN_MENU'
                    elif kernel.game_state == 'IN_AI_COLOR_MENU': kernel.game_state = 'IN_GAMEMODE_MENU'
                    elif kernel.game_state == 'IN_PROMOTION_MENU': kernel.game_state = 'IN_GAME'
                    elif kernel.game_state == 'IN_CONFIRMATION': kernel.game_state = 'IN_MENU'

            lag -= MS_PER_UPDATE

        cursor.clear_buffers(kernel)
        
        all_pieces_map = {}
        for color, piece_set in all_pieces.items():
            for char, positions in piece_set.items():
                for pos in positions:
                    all_pieces_map[pos] = (char, color)

        grid_w, grid_h = 8, 8
        
        box_h = kernel.height // grid_h
        box_w = box_h * 2
        
        total_grid_w = grid_w * box_w
        total_grid_h = grid_h * box_h
        
        start_x = (kernel.width - total_grid_w) // 2
        start_y = (kernel.height - total_grid_h) // 2

        if colorblind_mode:
            white = 0x00F0
            grey = 0x0080
            dark_green = 0x0030
            light_yellow = 0x00E6
            red = 0x00C4
            cursor_highlight = 0x00B0
        else:
            white = 0x00F0
            grey = 0x0080
            dark_green = 0x0020
            light_yellow = 0x00E0
            red = 0x00C0
            cursor_highlight = 0x00A0
    
        if kernel.game_state in ['IN_MENU', 'IN_FPS_MENU', 'IN_PROMOTION_MENU', 'IN_CONFIRMATION']:
            white = 0x0070
            light_yellow = 0x0080
            
        player_x = start_x + player_col * box_w + box_w / 2
        player_y = start_y + player_row * box_h + box_h / 2
    
        for row in range(grid_h):
            for col in range(grid_w):
                color = white if (row + col) % 2 == 0 else grey
                
                king_in_check_square = False
                if is_in_check['white'] and (col, row) == get_king_pos('white', all_pieces_map):
                    color = red
                    king_in_check_square = True
                elif is_in_check['black'] and (col, row) == get_king_pos('black', all_pieces_map):
                    color = red
                    king_in_check_square = True
                
                if not king_in_check_square:
                    if row == player_row and col == player_col:
                        color = cursor_highlight
                    elif (col, row) in marked_cells:
                        color = dark_green
                    elif (col, row) in possible_moves:
                        color = light_yellow
    
    
                draw_x = start_x + col * box_w
                draw_y = start_y + row * box_h
    
                if (col, row) in possible_moves:
                    cursor.draw_bordered_box(kernel, draw_x, draw_y, box_w, box_h, light_yellow, color, color)
                elif (col, row) in marked_cells:
                    cursor.draw_bordered_box(kernel, draw_x, draw_y, box_w, box_h, dark_green, color, color)
                else:
                    cursor.draw_filled_box(kernel, draw_x, draw_y, box_w, box_h, color, color)
    
        for color, piece_set in all_pieces.items():
            for char, positions in piece_set.items():
                for col, row in positions:
                    draw_x = start_x + col * box_w + (box_w - 1) // 2
                    draw_y = start_y + row * box_h + (box_h - 1) // 2
    
                    square_color = white if (row + col) % 2 == 0 else grey
                    
                    if is_in_check['white'] and (col, row) == get_king_pos('white', all_pieces_map):
                        square_color = red
                    elif is_in_check['black'] and (col, row) == get_king_pos('black', all_pieces_map):
                        square_color = red
                    elif row == player_row and col == player_col:
                        square_color = cursor_highlight
                    elif (col, row) in marked_cells:
                        square_color = dark_green
                    elif (col, row) in possible_moves:
                        square_color = light_yellow
                    
                    if color == 'white':
                        piece_color = square_color
                    else:
                        piece_color = 0x0000
                        if square_color != (white if (row + col) % 2 == 0 else grey):
                           piece_color = square_color
    
                    cursor.draw_text(kernel, draw_x, draw_y, char, piece_color, 0, transparent_bg=True)
    
        if player_col == -1:
            cb_button_color = cursor_highlight
        else:
            cb_button_color = grey

        cb_button_w = box_w * 2
        cb_button_x = start_x - cb_button_w - box_w // 2 - 5
        cb_button_y = start_y + (grid_h * box_h) // 2
        cb_status = "ON" if colorblind_mode else "OFF"
        cb_text = f"CB Mode: {cb_status}"
        cursor.draw_bordered_box(kernel, cb_button_x, cb_button_y, cb_button_w, box_h, cb_button_color, cb_button_color, cb_button_color)
        cursor.draw_text(kernel, cb_button_x + (cb_button_w - len(cb_text)) // 2, cb_button_y + box_h // 2, cb_text, grey, 0, transparent_bg=True)
        
        material_advantage = calculate_material_advantage(all_pieces, is_in_check, all_pieces_map)
        bar_width = 3
        bar_x = start_x - bar_width - 2
        bar_y = start_y
        bar_height = total_grid_h
        
        white_portion = (material_advantage + 1) / 2
        white_bar_height = int(bar_height * white_portion)
        grey_bar_height = bar_height - white_bar_height
        
        if white_bar_height > 0:
            cursor.draw_filled_box(kernel, bar_x, bar_y + grey_bar_height, bar_width, white_bar_height, white, white)
        
        if grey_bar_height > 0:
            cursor.draw_filled_box(kernel, bar_x, bar_y, bar_width, grey_bar_height, grey, grey)

        if player_col == 8:
            button_color = cursor_highlight
        else:
            button_color = grey

        button_x = start_x + grid_w * box_w + box_w // 2
        button_y = start_y + (grid_h * box_h) // 2
        button_w = box_w * 2
        cursor.draw_bordered_box(kernel, button_x, button_y, button_w, box_h, button_color, button_color, button_color)
        cursor.draw_text(kernel, button_x + (button_w - len("Takeback")) // 2, button_y + box_h // 2, "Takeback", grey, 0, transparent_bg=True)

        turn_text = f"{current_turn.capitalize()}'s Turn"
        text_width = len(turn_text)
        text_x = (kernel.width - text_width) // 2
        cursor.draw_text(kernel, text_x, 1, turn_text, white, 0, transparent_bg=True)
        box_width = 20
        box_height = 3
        cursor.draw_filled_box(kernel, 1, 1, box_width, box_height, grey, grey)
        cursor.draw_text(kernel, 2, 1, "Captured by Black:", 0, 0, transparent_bg=True)
        
        row1_black = white_captured[:8]
        row2_black = white_captured[8:16]
        cursor.draw_text(kernel, 2, 2, " ".join(row1_black), 0, 0, transparent_bg=True)
        cursor.draw_text(kernel, 2, 3, " ".join(row2_black), 0, 0, transparent_bg=True)

        box_x = kernel.width - box_width
        box_y = kernel.height - box_height - 1
        text_y = box_y -1
        cursor.draw_filled_box(kernel, box_x, box_y, box_width, box_height, grey, grey)
        cursor.draw_text(kernel, box_x + 1, text_y + 1, "Captured by White:", 0, 0, transparent_bg=True)

        row1_white = black_captured[:8]
        row2_white = black_captured[8:16]
        cursor.draw_text(kernel, box_x + 1, text_y + 2, " ".join(row1_white), 0, 0, transparent_bg=True)
        cursor.draw_text(kernel, box_x + 1, text_y + 3, " ".join(row2_white), 0, 0, transparent_bg=True)

        if kernel.game_state == 'IN_MENU':
            menu.draw_menu(kernel, menu_options, menu_selection)
        elif kernel.game_state == 'IN_FPS_MENU':
            fps_display_options = [f"{fps} FPS" for fps in fps_options]
            menu.draw_menu(kernel, fps_display_options, fps_selection)
        elif kernel.game_state == 'IN_GAMEMODE_MENU':
            gamemode_options = ["Player vs Player", "Player vs Computer"]
            if 'gamemode_selection' not in locals():
                gamemode_selection = 0 if game_mode == 'pvp' else 1
            menu.draw_menu(kernel, gamemode_options, gamemode_selection, title="Game Mode")
        elif kernel.game_state == 'IN_AI_COLOR_MENU':
            ai_color_options = ["Computer plays Black", "Computer plays White"]
            if 'ai_color_selection' not in locals():
                ai_color_selection = 0 if ai_color == 'black' else 1
            menu.draw_menu(kernel, ai_color_options, ai_color_selection, title="AI Color")
        elif kernel.game_state == 'IN_PROMOTION_MENU':
            promotion_options_dict = {'♕': 'Queen', '♖': 'Rook', '♗': 'Bishop', '♘': 'Knight'} if last_move['piece'] == '♙' else {'♛': 'Queen', '♜': 'Rook', '♝': 'Bishop', '♞': 'Knight'}
            promotion_options = [f"{char} {name}" for char, name in promotion_options_dict.items()]
            if 'promotion_selection' not in locals():
                promotion_selection = 0
            menu.draw_menu(kernel, promotion_options, promotion_selection, title="Pawn Promotion")
        elif kernel.game_state == 'IN_CONFIRMATION':
            confirmation_options = ["Yes", "No"]
            menu.draw_menu(kernel, confirmation_options, confirmation_selection, title="Are you sure?")
        elif kernel.game_state == 'IN_CHECKMATE':
            checkmate_options = ["Restart", "Exit"]
            winner = "White" if is_in_check['black'] else "Black"
            menu.draw_menu(kernel, checkmate_options, menu_selection, title=f"Checkmate! {winner} wins.")
            
        kernel.draw_buffer()
        time.sleep(sleep_time)

if __name__ == '__main__':
    main()
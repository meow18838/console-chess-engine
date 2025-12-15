import random
from .minimax import minimax
from ..chess.attack import is_square_attacked
from ..chess.move_validation import is_move_valid

def get_best_ai_move(all_pieces, all_pieces_map, current_turn, is_in_check, zobrist_hash, transposition_table, has_moved, last_move, ai_color='black'):
    piece_values = {
        '♙': 1, '♟': 1, '♘': 3, '♞': 3, '♗': 3, '♝': 3,
        '♖': 5, '♜': 5, '♕': 9, '♛': 9
    }
    
    nodes_checked = [0]
    max_nodes = 50000
    depth = 4
    
    try:
        maximizing = (ai_color == 'black')
        _, best_move = minimax(all_pieces, all_pieces_map, depth, -999999, 999999, maximizing, is_in_check, nodes_checked, max_nodes, zobrist_hash, transposition_table, has_moved, last_move)
        if best_move:
            return best_move
    except Exception as e:
        print(f"Minimax error: {e}")
        pass
    
    all_moves = []
    
    for piece_char, positions in all_pieces[ai_color].items():
        for pos in positions:
            col, row = pos
            possible_moves = []
            
            opponent = 'white' if ai_color == 'black' else 'black'
            
            if piece_char == '♟':
                if row < 7 and (col, row + 1) not in all_pieces_map:
                    possible_moves.append((col, row + 1))
                if row == 1 and (col, row + 1) not in all_pieces_map and (col, row + 2) not in all_pieces_map:
                    possible_moves.append((col, row + 2))
                for dx in [-1, 1]:
                    if 0 <= col + dx < 8 and (col + dx, row + 1) in all_pieces_map and all_pieces_map[(col + dx, row + 1)][1] == opponent:
                        possible_moves.append((col + dx, row + 1))
            
            elif piece_char == '♙':
                if row > 0 and (col, row - 1) not in all_pieces_map:
                    possible_moves.append((col, row - 1))
                if row == 6 and (col, row - 1) not in all_pieces_map and (col, row - 2) not in all_pieces_map:
                    possible_moves.append((col, row - 2))
                for dx in [-1, 1]:
                    if 0 <= col + dx < 8 and (col + dx, row - 1) in all_pieces_map and all_pieces_map[(col + dx, row - 1)][1] == opponent:
                        possible_moves.append((col + dx, row - 1))
            
            elif piece_char in ('♞', '♘'):
                offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                for dx, dy in offsets:
                    nx, ny = col + dx, row + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        if (nx, ny) not in all_pieces_map or all_pieces_map[(nx, ny)][1] != ai_color:
                            possible_moves.append((nx, ny))
            
            elif piece_char in ('♜', '♖'):
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                for dx, dy in directions:
                    for i in range(1, 8):
                        nx, ny = col + dx * i, row + dy * i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx, ny) in all_pieces_map:
                            if all_pieces_map[(nx, ny)][1] != ai_color:
                                possible_moves.append((nx, ny))
                            break
                        possible_moves.append((nx, ny))
            
            elif piece_char in ('♝', '♗'):
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dy in directions:
                    for i in range(1, 8):
                        nx, ny = col + dx * i, row + dy * i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx, ny) in all_pieces_map:
                            if all_pieces_map[(nx, ny)][1] != ai_color:
                                possible_moves.append((nx, ny))
                            break
                        possible_moves.append((nx, ny))
            
            elif piece_char in ('♛', '♕'):
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dy in directions:
                    for i in range(1, 8):
                        nx, ny = col + dx * i, row + dy * i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx, ny) in all_pieces_map:
                            if all_pieces_map[(nx, ny)][1] != ai_color:
                                possible_moves.append((nx, ny))
                            break
                        possible_moves.append((nx, ny))
            
            elif piece_char in ('♚', '♔'):
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dy in directions:
                    nx, ny = col + dx, row + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        if (nx, ny) not in all_pieces_map or all_pieces_map[(nx, ny)][1] != ai_color:
                            possible_moves.append((nx, ny))
            
            for move in possible_moves:
                if is_move_valid(pos, move, piece_char, ai_color, all_pieces_map):
                    score = 0
                    
                    piece_under_attack = is_square_attacked(pos, opponent, all_pieces_map)
                    piece_value = piece_values.get(piece_char, 0)
                    
                    move_is_attacked = is_square_attacked(move, opponent, all_pieces_map)
                    
                    capture_value = 0
                    if move in all_pieces_map:
                        captured_piece = all_pieces_map[move][0]
                        capture_value = piece_values.get(captured_piece, 0)
                        score += capture_value * 15
                    
                    if move_is_attacked:
                        if capture_value < piece_value and not piece_under_attack:
                            score -= piece_value * 20
                        elif capture_value > piece_value:
                            score += (capture_value - piece_value) * 10
                        elif capture_value == piece_value and not piece_under_attack:
                            score += 2
                    
                    if piece_under_attack and not move_is_attacked:
                        score += piece_value * 8
                    
                    if piece_value >= 5:
                        if not move_is_attacked:
                            score += 5
                    
                    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
                    if move in center_squares and not move_is_attacked:
                        score += 4
                    
                    if piece_char == '♟' and not move_is_attacked:
                        score += move[1] * 0.8
                    
                    if piece_char in ('♞', '♝', '♛') and pos[1] == 0 and move[1] > 0:
                        score += 3
                    
                    if piece_char in ('♞', '♝', '♜', '♛') and move == pos:
                        score -= 5
                    
                    all_moves.append((pos, move, piece_char, score))
    
    if not all_moves:
        return None
    
    all_moves.sort(key=lambda x: x[3], reverse=True)
    
    good_moves = [m for m in all_moves if m[3] > -10]
    if not good_moves:
        good_moves = all_moves[:5]
    
    top_count = min(3, len(good_moves))
    best_moves = good_moves[:top_count]
    chosen = random.choice(best_moves)
    
    return (chosen[0], chosen[1], chosen[2])
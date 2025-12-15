from .attack import is_square_attacked

def get_king_pos(color, all_pieces_map):
    king_char = '♔' if color == 'white' else '♚'
    for pos, (char, piece_color) in all_pieces_map.items():
        if char == king_char and piece_color == color:
            return pos
    return None

def is_move_valid(source_pos, dest_pos, piece_char, piece_color, all_pieces_map):
    temp_map = dict(all_pieces_map)
    
    temp_map[dest_pos] = (piece_char, piece_color)
    del temp_map[source_pos]
    
    king_pos = get_king_pos(piece_color, temp_map)
    if king_pos and is_square_attacked(king_pos, 'black' if piece_color == 'white' else 'white', temp_map):
        return False
        
    return True

def has_legal_moves(color, all_pieces, all_pieces_map):
    opponent_color = 'black' if color == 'white' else 'white'
    
    for piece_char, positions in all_pieces[color].items():
        for pos in list(positions):
            col, row = pos
            possible_moves = []
            
            if piece_char in ('♙', '♟'):
                if piece_char == '♙':
                    if row > 0 and (col, row - 1) not in all_pieces_map:
                        possible_moves.append((col, row - 1))
                    if row == 6 and (col, row - 1) not in all_pieces_map and (col, row - 2) not in all_pieces_map:
                        possible_moves.append((col, row - 2))
                    for dx in [-1, 1]:
                        if 0 <= col + dx < 8 and (col + dx, row - 1) in all_pieces_map and all_pieces_map[(col + dx, row - 1)][1] == 'black':
                            possible_moves.append((col + dx, row - 1))
                else:
                    if row < 7 and (col, row + 1) not in all_pieces_map:
                        possible_moves.append((col, row + 1))
                    if row == 1 and (col, row + 1) not in all_pieces_map and (col, row + 2) not in all_pieces_map:
                        possible_moves.append((col, row + 2))
                    for dx in [-1, 1]:
                        if 0 <= col + dx < 8 and (col + dx, row + 1) in all_pieces_map and all_pieces_map[(col + dx, row + 1)][1] == 'white':
                            possible_moves.append((col + dx, row + 1))
            
            elif piece_char in ('♘', '♞'):
                offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                for dx, dy in offsets:
                    nx, ny = col + dx, row + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        if (nx, ny) not in all_pieces_map or all_pieces_map[(nx, ny)][1] != color:
                            possible_moves.append((nx, ny))
            
            elif piece_char in ('♖', '♜'):
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                for dx, dy in directions:
                    for i in range(1, 8):
                        nx, ny = col + dx * i, row + dy * i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx, ny) in all_pieces_map:
                            if all_pieces_map[(nx, ny)][1] != color:
                                possible_moves.append((nx, ny))
                            break
                        possible_moves.append((nx, ny))
            
            elif piece_char in ('♗', '♝'):
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dy in directions:
                    for i in range(1, 8):
                        nx, ny = col + dx * i, row + dy * i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx, ny) in all_pieces_map:
                            if all_pieces_map[(nx, ny)][1] != color:
                                possible_moves.append((nx, ny))
                            break
                        possible_moves.append((nx, ny))
            
            elif piece_char in ('♕', '♛'):
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dy in directions:
                    for i in range(1, 8):
                        nx, ny = col + dx * i, row + dy * i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx, ny) in all_pieces_map:
                            if all_pieces_map[(nx, ny)][1] != color:
                                possible_moves.append((nx, ny))
                            break
                        possible_moves.append((nx, ny))
            
            elif piece_char in ('♔', '♚'):
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dy in directions:
                    nx, ny = col + dx, row + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        if (nx, ny) not in all_pieces_map or all_pieces_map[(nx, ny)][1] != color:
                            possible_moves.append((nx, ny))
            
            for move in possible_moves:
                if is_move_valid(pos, move, piece_char, color, all_pieces_map):
                    return True
    
    return False
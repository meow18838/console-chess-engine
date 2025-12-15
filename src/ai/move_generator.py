import copy

def simulate_move(all_pieces, all_pieces_map, pos, dest, piece_char, color):
    new_pieces = copy.deepcopy(all_pieces)
    new_map = dict(all_pieces_map)
    
    captured = None
    if dest in new_map:
        cap_char, cap_color = new_map[dest]
        captured = cap_char
        new_pieces[cap_color][cap_char].remove(dest)
    
    new_pieces[color][piece_char].remove(pos)
    new_pieces[color][piece_char].append(dest)
    
    del new_map[pos]
    new_map[dest] = (piece_char, color)
    
    return new_pieces, new_map, captured

def generate_captures_only(all_pieces, all_pieces_map, color):
    from ..chess.move_validation import is_move_valid
    piece_values = {'♙': 1, '♟': 1, '♘': 3, '♞': 3, '♗': 3, '♝': 3, '♖': 5, '♜': 5, '♕': 9, '♛': 9}
    captures = []
    
    for piece_char, positions in all_pieces[color].items():
        for pos in positions:
            col, row = pos
            possible = []
            
            if piece_char == '♟':
                for dx in [-1, 1]:
                    if 0 <= col + dx < 8 and row < 7:
                        target = (col + dx, row + 1)
                        if target in all_pieces_map and all_pieces_map[target][1] != color:
                            possible.append(target)
            elif piece_char == '♙':
                for dx in [-1, 1]:
                    if 0 <= col + dx < 8 and row > 0:
                        target = (col + dx, row - 1)
                        if target in all_pieces_map and all_pieces_map[target][1] != color:
                            possible.append(target)
            elif piece_char in ('♞', '♘'):
                for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    target = (col + dx, row + dy)
                    if 0 <= target[0] < 8 and 0 <= target[1] < 8:
                        if target in all_pieces_map and all_pieces_map[target][1] != color:
                            possible.append(target)
            elif piece_char in ('♜', '♖', '♝', '♗', '♛', '♕'):
                if piece_char in ('♜', '♖', '♛', '♕'):
                    dirs = [(0,1),(0,-1),(1,0),(-1,0)]
                else:
                    dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
                if piece_char in ('♛', '♕'):
                    dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
                
                for dx, dy in dirs:
                    for i in range(1, 8):
                        target = (col + dx*i, row + dy*i)
                        if not (0 <= target[0] < 8 and 0 <= target[1] < 8):
                            break
                        if target in all_pieces_map:
                            if all_pieces_map[target][1] != color:
                                possible.append(target)
                            break
            
            for target in possible:
                if is_move_valid(pos, target, piece_char, color, all_pieces_map):
                    victim_value = piece_values.get(all_pieces_map[target][0], 0)
                    captures.append((pos, target, piece_char, victim_value))
    
    captures.sort(key=lambda x: x[3], reverse=True)
    return [(c[0], c[1], c[2]) for c in captures]

def generate_moves_fast(all_pieces, all_pieces_map, color):
    from ..chess.move_validation import is_move_valid
    piece_values = {'♙': 1, '♟': 1, '♘': 3, '♞': 3, '♗': 3, '♝': 3, '♖': 5, '♜': 5, '♕': 9, '♛': 9}
    moves = []
    
    for piece_char, positions in all_pieces[color].items():
        for pos in positions:
            col, row = pos
            possible = []
            
            if piece_char == '♟':
                if row < 7 and (col, row + 1) not in all_pieces_map:
                    possible.append((col, row + 1))
                for dx in [-1, 1]:
                    if 0 <= col + dx < 8 and (col + dx, row + 1) in all_pieces_map and all_pieces_map[(col + dx, row + 1)][1] != color:
                        possible.append((col + dx, row + 1))
            elif piece_char == '♙':
                if row > 0 and (col, row - 1) not in all_pieces_map:
                    possible.append((col, row - 1))
                for dx in [-1, 1]:
                    if 0 <= col + dx < 8 and (col + dx, row - 1) in all_pieces_map and all_pieces_map[(col + dx, row - 1)][1] != color:
                        possible.append((col + dx, row - 1))
            elif piece_char in ('♞', '♘'):
                for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nx, ny = col + dx, row + dy
                    if 0 <= nx < 8 and 0 <= ny < 8 and ((nx,ny) not in all_pieces_map or all_pieces_map[(nx,ny)][1] != color):
                        possible.append((nx, ny))
            elif piece_char in ('♜', '♖', '♝', '♗', '♛', '♕'):
                if piece_char in ('♜', '♖', '♛', '♕'):
                    dirs = [(0,1),(0,-1),(1,0),(-1,0)]
                else:
                    dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
                if piece_char in ('♛', '♕'):
                    dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
                
                for dx, dy in dirs:
                    for i in range(1, 8):
                        nx, ny = col + dx*i, row + dy*i
                        if not (0 <= nx < 8 and 0 <= ny < 8):
                            break
                        if (nx,ny) in all_pieces_map:
                            if all_pieces_map[(nx,ny)][1] != color:
                                possible.append((nx, ny))
                            break
                        possible.append((nx, ny))
            elif piece_char in ('♚', '♔'):
                for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                    nx, ny = col + dx, row + dy
                    if 0 <= nx < 8 and 0 <= ny < 8 and ((nx,ny) not in all_pieces_map or all_pieces_map[(nx,ny)][1] != color):
                        possible.append((nx, ny))
            
            for move_dest in possible:
                if is_move_valid(pos, move_dest, piece_char, color, all_pieces_map):
                    score = 0
                    if move_dest in all_pieces_map:
                        score = piece_values.get(all_pieces_map[move_dest][0], 0) * 10
                    moves.append((pos, move_dest, piece_char, score))
    
    moves.sort(key=lambda x: x[3], reverse=True)
    return [(m[0], m[1], m[2]) for m in moves]
def is_square_attacked(square, attacker_color, all_pieces_map):
    pawn_char = '♟' if attacker_color == 'black' else '♙'
    pawn_dir = -1 if attacker_color == 'white' else 1
    for dx in [-1, 1]:
        check_pos = (square[0] + dx, square[1] - pawn_dir)
        if all_pieces_map.get(check_pos) == (pawn_char, attacker_color):
            return True

    knight_char = '♞' if attacker_color == 'black' else '♘'
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dx, dy in offsets:
        check_pos = (square[0] + dx, square[1] + dy)
        if all_pieces_map.get(check_pos) == (knight_char, attacker_color):
            return True
    
    sliding_pieces = {
        'rook': (['♖', '♜'], [(0, 1), (0, -1), (1, 0), (-1, 0)]),
        'bishop': (['♗', '♝'], [(1, 1), (1, -1), (-1, 1), (-1, -1)]),
        'queen': (['♕', '♛'], [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)])
    }
    
    for piece_type, (chars, directions) in sliding_pieces.items():
        attacker_char = chars[0] if attacker_color == 'white' else chars[1]
        queen_char = '♕' if attacker_color == 'white' else '♛'
        
        for dx, dy in directions:
            for i in range(1, 8):
                check_pos = (square[0] + dx * i, square[1] + dy * i)
                if not (0 <= check_pos[0] < 8 and 0 <= check_pos[1] < 8):
                    break
                piece_at_pos = all_pieces_map.get(check_pos)
                if piece_at_pos:
                    if piece_at_pos[1] == attacker_color and (piece_at_pos[0] == attacker_char or piece_at_pos[0] == queen_char):
                        return True
                    break

    king_char = '♚' if attacker_color == 'black' else '♔'
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0: continue
            check_pos = (square[0] + dx, square[1] + dy)
            if all_pieces_map.get(check_pos) == (king_char, attacker_color):
                return True
                
    return False
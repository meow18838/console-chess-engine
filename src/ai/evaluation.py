def evaluate_position(all_pieces, all_pieces_map, is_in_check):
    piece_values = {'♙': 1, '♟': 1, '♘': 3, '♞': 3, '♗': 3, '♝': 3, '♖': 5, '♜': 5, '♕': 9, '♛': 9}
    
    score = 0
    for piece_char, positions in all_pieces['black'].items():
        if piece_char in piece_values:
            score += piece_values[piece_char] * len(positions) * 100
    
    for piece_char, positions in all_pieces['white'].items():
        if piece_char in piece_values:
            score -= piece_values[piece_char] * len(positions) * 100
    
    if is_in_check.get('white', False):
        score += 50
    if is_in_check.get('black', False):
        score -= 50
        
    return score

def calculate_material_advantage(all_pieces, is_in_check, all_pieces_map):
    piece_values = {
        '♙': 1, '♟': 1,
        '♘': 3, '♞': 3,
        '♗': 3, '♝': 3,
        '♖': 5, '♜': 5,
        '♕': 9, '♛': 9,
    }
    
    white_material = 0
    black_material = 0
    
    for piece_char, positions in all_pieces['white'].items():
        if piece_char in piece_values:
            white_material += piece_values[piece_char] * len(positions)
    
    for piece_char, positions in all_pieces['black'].items():
        if piece_char in piece_values:
            black_material += piece_values[piece_char] * len(positions)
    
    material_diff = white_material - black_material
    
    max_material = 39
    if material_diff > 0:
        advantage = min(1.0, material_diff / max_material)
    elif material_diff < 0:
        advantage = max(-1.0, material_diff / max_material)
    else:
        advantage = 0
    
    return advantage
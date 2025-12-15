from .transposition_table import TT_EXACT, TT_LOWER, TT_UPPER
from .evaluation import evaluate_position
from .move_generator import generate_moves_fast, generate_captures_only, simulate_move

def quiescence(all_pieces, all_pieces_map, alpha, beta, maximizing, is_in_check, nodes_checked, max_nodes, max_depth=4):
    if nodes_checked[0] >= max_nodes or max_depth <= 0:
        return evaluate_position(all_pieces, all_pieces_map, is_in_check)
    
    nodes_checked[0] += 1
    stand_pat = evaluate_position(all_pieces, all_pieces_map, is_in_check)
    
    if maximizing:
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
    else:
        if stand_pat <= alpha:
            return alpha
        if beta > stand_pat:
            beta = stand_pat
    
    color = 'black' if maximizing else 'white'
    captures = generate_captures_only(all_pieces, all_pieces_map, color)
    
    for pos, dest, piece_char in captures[:5]:
        new_pieces, new_map, _ = simulate_move(all_pieces, all_pieces_map, pos, dest, piece_char, color)
        score = quiescence(new_pieces, new_map, alpha, beta, not maximizing, is_in_check, nodes_checked, max_nodes, max_depth - 1)
        
        if maximizing:
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        else:
            if score <= alpha:
                return alpha
            if score < beta:
                beta = score
    
    return alpha if maximizing else beta

def minimax(all_pieces, all_pieces_map, depth, alpha, beta, maximizing, is_in_check, nodes_checked, max_nodes, zobrist_hash, transposition_table, has_moved, last_move):
    if nodes_checked[0] >= max_nodes:
        return quiescence(all_pieces, all_pieces_map, alpha, beta, maximizing, is_in_check, nodes_checked, max_nodes), None
    
    side_to_move = 'black' if maximizing else 'white'
    hash_key = zobrist_hash.compute_hash(all_pieces, side_to_move, has_moved, last_move)
    
    tt_score, tt_move = transposition_table.probe(hash_key, depth, alpha, beta)
    if tt_score is not None:
        return tt_score, tt_move
    
    if depth == 0:
        return quiescence(all_pieces, all_pieces_map, alpha, beta, maximizing, is_in_check, nodes_checked, max_nodes), None
    
    nodes_checked[0] += 1
    
    color = 'black' if maximizing else 'white'
    moves = generate_moves_fast(all_pieces, all_pieces_map, color)
    
    if not moves:
        return evaluate_position(all_pieces, all_pieces_map, is_in_check), None
    
    best_move = tt_move
    original_alpha = alpha
    
    if maximizing:
        max_eval = -999999
        for move in moves[:15]:
            pos, dest, piece_char = move
            new_pieces, new_map, captured = simulate_move(all_pieces, all_pieces_map, pos, dest, piece_char, color)
            
            eval_score, _ = minimax(new_pieces, new_map, depth - 1, alpha, beta, False, is_in_check, nodes_checked, max_nodes, zobrist_hash, transposition_table, has_moved, last_move)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
                
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        if max_eval <= original_alpha:
            flag = TT_UPPER
        elif max_eval >= beta:
            flag = TT_LOWER
        else:
            flag = TT_EXACT
        transposition_table.store(hash_key, depth, max_eval, flag, best_move)
        
        return max_eval, best_move
    else:
        min_eval = 999999
        for move in moves[:15]:
            pos, dest, piece_char = move
            new_pieces, new_map, captured = simulate_move(all_pieces, all_pieces_map, pos, dest, piece_char, color)
            
            eval_score, _ = minimax(new_pieces, new_map, depth - 1, alpha, beta, True, is_in_check, nodes_checked, max_nodes, zobrist_hash, transposition_table, has_moved, last_move)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        if min_eval <= original_alpha:
            flag = TT_UPPER
        elif min_eval >= beta:
            flag = TT_LOWER
        else:
            flag = TT_EXACT
        transposition_table.store(hash_key, depth, min_eval, flag, best_move)
        
        return min_eval, best_move
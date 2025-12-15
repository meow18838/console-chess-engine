TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

class TranspositionTable:
    def __init__(self, size_mb=64):
        self.max_entries = (size_mb * 1024 * 1024) // 32
        self.table = {}
    
    def store(self, hash_key, depth, score, flag, best_move=None):
        if hash_key not in self.table or self.table[hash_key]['depth'] <= depth:
            self.table[hash_key] = {
                'depth': depth,
                'score': score,
                'flag': flag,
                'best_move': best_move
            }
    
    def probe(self, hash_key, depth, alpha, beta):
        if hash_key not in self.table:
            return None, None
        
        entry = self.table[hash_key]
        
        if entry['depth'] < depth:
            return None, entry['best_move']
        
        score = entry['score']
        flag = entry['flag']
        
        if flag == TT_EXACT:
            return score, entry['best_move']
        elif flag == TT_LOWER and score >= beta:
            return score, entry['best_move']
        elif flag == TT_UPPER and score <= alpha:
            return score, entry['best_move']
        
        return None, entry['best_move']
    
    def clear(self):
        self.table.clear()
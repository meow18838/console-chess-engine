import random

class ZobristHash:
    def __init__(self):
        random.seed(42)
        self.piece_keys = {}
        self.side_key = random.getrandbits(64)
        self.castling_keys = {}
        self.en_passant_keys = [random.getrandbits(64) for _ in range(8)]
        
        pieces = ['♙', '♟', '♘', '♞', '♗', '♝', '♖', '♜', '♕', '♛', '♔', '♚']
        for piece in pieces:
            self.piece_keys[piece] = {}
            for square in range(64):
                self.piece_keys[piece][square] = random.getrandbits(64)
        
        self.castling_keys['white_king'] = random.getrandbits(64)
        self.castling_keys['black_king'] = random.getrandbits(64)
        self.castling_keys['white_rook_a'] = random.getrandbits(64)
        self.castling_keys['white_rook_h'] = random.getrandbits(64)
        self.castling_keys['black_rook_a'] = random.getrandbits(64)
        self.castling_keys['black_rook_h'] = random.getrandbits(64)
    
    def compute_hash(self, all_pieces, side_to_move, has_moved, last_move=None):
        hash_value = 0
        
        for color, piece_set in all_pieces.items():
            for piece_char, positions in piece_set.items():
                for col, row in positions:
                    square = row * 8 + col
                    hash_value ^= self.piece_keys[piece_char][square]
        
        if side_to_move == 'black':
            hash_value ^= self.side_key
        
        for key, value in has_moved.items():
            if not value:
                hash_value ^= self.castling_keys[key]
        
        if last_move and last_move.get('piece') in ('♙', '♟'):
            start = last_move.get('start')
            end = last_move.get('end')
            if start and end and abs(start[1] - end[1]) == 2:
                hash_value ^= self.en_passant_keys[end[0]]
        
        return hash_value
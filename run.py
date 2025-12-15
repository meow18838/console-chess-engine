import os
import sys

from src.core import Kernel
from src.ui import WindowManager
from src.ai import ZobristHash, TranspositionTable, get_best_ai_move, calculate_material_advantage
from src.chess import is_square_attacked, get_king_pos, is_move_valid, has_legal_moves
from src.config import load_settings, save_settings

cursor = WindowManager()
menu = WindowManager()

if __name__ == '__main__':
    exec(open('main.py', encoding='utf-8').read())
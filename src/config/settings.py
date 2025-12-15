import os
import json

def load_settings():
    try:
        if os.path.exists('chess_settings.json'):
            with open('chess_settings.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {'colorblind_mode': False, 'game_mode': 'pvp', 'ai_color': 'black'}

def save_settings(colorblind_mode, game_mode, ai_color='black'):
    try:
        with open('chess_settings.json', 'w') as f:
            json.dump({'colorblind_mode': colorblind_mode, 'game_mode': game_mode, 'ai_color': ai_color}, f)
    except:
        pass
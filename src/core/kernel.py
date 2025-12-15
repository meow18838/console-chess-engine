import os
import ctypes

class Kernel:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.attribute_buffer = [[0x0000 for _ in range(width)] for _ in range(height)]
        self.char_buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.game_state = 'IN_GAME'
        self.pixel_color = 0x00F0
        self.background_color = 0x0000

        self.h_stdout = ctypes.windll.kernel32.GetStdHandle(-11)
        self.csbi = ctypes.create_string_buffer(22)
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(self.h_stdout, self.csbi)

    def clear_screen(self):
        os.system('cls')

    def draw_buffer(self):
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
        
        coord = COORD(0, 0)
        written = ctypes.c_ulong(0)
        
        flat_attributes = [item for sublist in self.attribute_buffer for item in sublist]
        attribute_buffer_c = (ctypes.c_ushort * len(flat_attributes))(*flat_attributes)
        ctypes.windll.kernel32.WriteConsoleOutputAttribute(
            self.h_stdout, attribute_buffer_c, len(flat_attributes), coord, ctypes.byref(written)
        )

        flat_chars = "".join("".join(row) for row in self.char_buffer)
        ctypes.windll.kernel32.WriteConsoleOutputCharacterW(
            self.h_stdout, flat_chars, len(flat_chars), coord, ctypes.byref(written)
        )
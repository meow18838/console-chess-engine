class WindowManager:
    def clear_buffers(self, kernel):
        for r in range(kernel.height):
            for c in range(kernel.width):
                kernel.attribute_buffer[r][c] = kernel.background_color
                kernel.char_buffer[r][c] = ' '

    def draw_text(self, kernel, x, y, text, fg_color, bg_color, transparent_bg=False):
        for i, char in enumerate(text):
            if 0 <= x + i < kernel.width and 0 <= y < kernel.height:
                if transparent_bg:
                    existing_bg = kernel.attribute_buffer[y][x + i] & 0xFFF0
                    kernel.attribute_buffer[y][x + i] = fg_color | existing_bg
                else:
                    kernel.attribute_buffer[y][x + i] = fg_color | (bg_color << 4)
                kernel.char_buffer[y][x + i] = char
    
    def draw_window(self, kernel, x, y, width, height, bg_color):
        for r in range(height):
            for c in range(width):
                if 0 <= x + c < kernel.width and 0 <= y + r < kernel.height:
                    kernel.attribute_buffer[y + r][x + c] = bg_color
                    kernel.char_buffer[y + r][x + c] = ' '
        
        border_char_map = {'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝', 'h': '═', 'v': '║'}
        border_color = 0x00F0
        for r in range(height):
            for c in range(width):
                if not (0 < c < width - 1 and 0 < r < height - 1):
                    char = ''
                    if r == 0 and c == 0: char = border_char_map['tl']
                    elif r == 0 and c == width - 1: char = border_char_map['tr']
                    elif r == height - 1 and c == 0: char = border_char_map['bl']
                    elif r == height - 1 and c == width - 1: char = border_char_map['br']
                    elif r == 0 or r == height - 1: char = border_char_map['h']
                    elif c == 0 or c == width - 1: char = border_char_map['v']
                    
                    if char and 0 <= x + c < kernel.width and 0 <= y + r < kernel.height:
                        kernel.attribute_buffer[y + r][x + c] = border_color
                        kernel.char_buffer[y + r][x + c] = char

    def draw_menu(self, kernel, options, selection, title=None):
        menu_width = max(len(o) for o in options) + 6
        if title:
            menu_width = max(menu_width, len(title) + 6)
        
        menu_height = len(options) + 4
        if title:
            menu_height += 2
            
        start_x = kernel.width // 2 - menu_width // 2
        start_y = kernel.height // 2 - menu_height // 2

        menu_bg = 0x0070
        self.draw_window(kernel, start_x, start_y, menu_width, menu_height, menu_bg)

        if title:
            title_x = start_x + (menu_width - len(title)) // 2
            self.draw_text(kernel, title_x, start_y + 2, title, 0x0070, menu_bg)

        for i, option in enumerate(options):
            line_y = start_y + 2 + (2 if title else 0) + i
            text_x = start_x + (menu_width - len(option)) // 2

            if i == selection:
                fg_color = 0x00E0
                bg_color = 0x0080
            else:
                fg_color = 0x0070
                bg_color = menu_bg

            line_text = ' ' * (menu_width - 2)
            self.draw_text(kernel, start_x + 1, line_y, line_text, fg_color, bg_color)
            self.draw_text(kernel, text_x, line_y, option, fg_color, bg_color)

    def draw_filled_box(self, kernel, x, y, width, height, fg_color, bg_color=None):
        char = ' '
        if bg_color is None:
            bg_color = fg_color
        
        for r in range(height):
            for c in range(width):
                 if 0 <= x + c < kernel.width and 0 <= y + r < kernel.height:
                    kernel.attribute_buffer[y + r][x + c] = fg_color | (bg_color << 4)
                    kernel.char_buffer[y + r][x + c] = char

    def draw_wireframe_box(self, kernel, x, y, width, height, color):
        bg_color = kernel.background_color
        t_bg = True

        self.draw_text(kernel, x, y, '┌' + '─' * (width - 2) + '┐', color, bg_color, t_bg)
        self.draw_text(kernel, x, y + height - 1, '└' + '─' * (width - 2) + '┘', color, bg_color, t_bg)

        for i in range(1, height - 1):
            self.draw_text(kernel, x, y + i, '│', color, bg_color, t_bg)
            self.draw_text(kernel, x + width - 1, y + i, '│', color, bg_color, t_bg)

    def draw_bordered_box(self, kernel, x, y, width, height, border_color, fill_fg_color, fill_bg_color):
        self.draw_filled_box(kernel, x, y, width, height, border_color, border_color)
        self.draw_filled_box(kernel, x + 2, y + 1, width - 4, height - 2, fill_fg_color, fill_bg_color)
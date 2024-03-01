from button import Button
from ssd1306 import SSD1306_I2C
from asyncio import sleep_ms

from text_buffer import TextBuffer


class Display:
    MODES = ['text']

    def __init__(self, i2c, display_x=128, display_y=64, display_mode='text',
                 left_button=10, down_button=11, up_button=12, right_button=13):
        self.display_x = display_x
        self.display_y = display_y
        self.line_length = display_x // 8
        self.display_lines = (display_y // 8) - 1
        self.display_chars = self.line_length * self.display_lines
        self.display_page = 0

        self.display = SSD1306_I2C(display_x, display_y, i2c)
        self.text_lines = TextBuffer(line_length=self.line_length, display_lines=self.display_lines)

        self.right_button = Button(right_button)
        self.left_button = Button(left_button)
        self.up_button = Button(up_button)
        self.down_button = Button(down_button)
        self.mode = 'text'

        self.selection = 0

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode != 'select' and mode not in self.MODES:
            raise ValueError("Invalid mode: %s" % mode)
        if not (self, f'handle_{mode}'):
            raise ValueError("Mode missing required handler: handle_" % mode)
        if not (self, f'display_{mode}'):
            raise ValueError("Mode missing required display function: display_" % mode)
        self._mode = mode

    async def start(self):
        print("Starting display.")
        self.display.fill(0)
        self.text_lines += 'Starting...\n'
        self.display.show()

    async def runloop(self):
        await self.start()
        while True:
            buttons = {button: getattr(self, f"{button}_button").value
                       for button in ['left', 'right', 'up', 'down']}

            if buttons['right'] and buttons['left']:
                self.selection = 0
                self.mode = 'select'
            else:
                await getattr(self, f"handle_{self.mode}")([button for button, value in buttons.items() if value])

            await sleep_ms(100)
            await getattr(self, f"display_{self.mode}")()
            self.display.show()

    async def draw_base_display(self):
        self.display.fill(0)
        # Draw a bar at the bottom
        self.display.hline(0, self.display_y - 7, self.display_x, 1)
        # Draw sections for the sides
        self.display.vline(16, self.display_y - 7, 8, 1)
        self.display.vline(self.display_x - 16, self.display_y - 7, 8, 1)
        # Draw the current mode
        self.display.text(self.mode, 17, self.display_y - 7)

    async def handle_select(self, buttons):
        if 'right' in buttons:
            self.selection += 1
        elif 'left' in buttons:
            self.selection -= 1
        elif 'up' in buttons or 'down' in buttons:
            self.mode = self.MODES[self.selection]
        self.selection = max(0, min(self.selection, len(self.MODES) - 1))

    async def display_select(self):
        await self.draw_base_display()
        self.display.text(f'{self.selection + 1}', 0, self.display_y - 7)
        self.display.text(str(len(self.MODES)), self.display_x - 15, self.display_y - 7)
        self.display.hline(0, (self.selection + 1) * 8, len(self.MODES[self.selection]) * 8, 1)
        for line, mode in enumerate(self.MODES):
            await self.display_line(line, mode)

    async def handle_text(self, buttons):
        if 'up' in buttons and 'down' in buttons:
            print("Clearing the text buffer.")
            self.text_lines.clear()
        if 'right' in buttons:
            self.display_page += 1
        elif 'left' in buttons:
            self.display_page -= 1
        self.display_page = max(0, min(self.display_page, self.text_lines.pages - 1))

    async def display_text(self):
        await self.draw_base_display()
        self.display.text(f'{self.display_page + 1}', 0, self.display_y - 7)
        self.display.text(str(self.text_lines.pages), self.display_x - 15, self.display_y - 7)
        self.display.vline(self.display_x - 42, self.display_y - 7, 8, 1)
        self.display.text(str(self.text_lines.used) + "%", self.display_x - 40, self.display_y - 7)
        display_text = self.text_lines.get_page(self.display_page)
        for line_number, line in enumerate(display_text):
            await self.display_line(line_number, line)

    async def display_line(self, line_number, text):
        for char_number, char in enumerate(text):
            text_char = chr(char) if isinstance(char, int) else char
            self.display.text(text_char, char_number * 8, line_number * 8)



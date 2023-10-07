import curses
import curses.ascii
import os
import re
import sys
import time
from typing import (
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
)

from _shutil import load_json, save_json, slugify

DEBUG_KEY_PRESS = False


def get_hotkey_abbr(hotkey: str):
    return (
        hotkey.lower()
        .replace("win+", "#")
        .replace("ctrl+", "^")
        .replace("alt+", "!")
        .replace("shift+", "+")
    )


def to_ascii_hotkey(hotkey: str) -> Iterator[Union[int, str]]:
    hotkey = hotkey.lower()
    key = hotkey[-1].lower()
    if hotkey == "delete":
        yield curses.KEY_DC  # 330
    elif hotkey == "left":
        yield curses.KEY_LEFT
        yield 452  # curses.KEY_B1
    elif hotkey == "right":
        yield curses.KEY_RIGHT
        yield 454  # curses.KEY_B3
    elif "ctrl+" in hotkey:
        yield curses.ascii.ctrl(key)
    elif "shift+" in hotkey or "alt+" in hotkey:
        # HACK: use `shift+` in place of `alt+`
        yield key.upper()
    else:
        yield key


def _is_backspace_key(ch: Union[int, str]):
    return (
        ch == curses.KEY_BACKSPACE
        or ch == "\b"  # for windows
        or ch == "\x7f"  # for mac and linux
    )


class _Hotkey:
    def __init__(self, hotkey: str, func: Callable):
        self.hotkey = hotkey
        self.func = func

    def __str__(self) -> str:
        return "%s (%s)" % (self.func.__name__, get_hotkey_abbr(self.hotkey))


def _fuzzy_search_func(items, kw):
    kw = kw.lower()
    if not kw:
        for i, s in enumerate(items):
            yield i
    else:
        for i, item in enumerate(items):
            if all([(x in str(item).lower()) for x in kw.split(" ")]):
                yield i


class _InputWidget:
    def __init__(self, label="", text="", ascii_only=False):
        self.label = label
        self.set_text(text)
        self.ascii_only = ascii_only

    def set_text(self, text):
        self.text = text
        self.caret_pos = len(text)

    def on_update_screen(self, stdscr, row, cursor=False):
        stdscr.addstr(row, 0, self.label)

        text_start = len(self.label) + 1 if self.label else 0
        stdscr.attron(curses.color_pair(1))
        try:
            stdscr.addstr(row, text_start, self.text)
        except curses.error:
            pass
        stdscr.attroff(curses.color_pair(1))

        if cursor:
            try:
                stdscr.move(row, self.caret_pos + text_start)
            except curses.error:
                pass

    def clear(self):
        self.text = ""
        self.caret_pos = 0

    def on_char(self, ch):
        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT:
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT:
            self.caret_pos = min(self.caret_pos + 1, len(self.text))
        elif _is_backspace_key(ch):
            if self.caret_pos > 0:
                self.text = (
                    self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
                )
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.ascii.ctrl("a"):
            self.clear()
        elif ch == "\n":
            pass
        elif isinstance(ch, str):
            if not self.ascii_only or (self.ascii_only and re.match("[\x00-\x7F]", ch)):
                self.text = (
                    self.text[: self.caret_pos] + ch + self.text[self.caret_pos :]
                )
                self.caret_pos += 1


class _MenuItem:
    def __init__(
        self, name: str, callback: Optional[Callable[[], None]] = None
    ) -> None:
        self.name = name
        self.callback = callback

    def __str__(self):
        return self.name


T = TypeVar("T")


class Menu(Generic[T]):
    stdscr = None

    def __init__(
        self,
        items: List[T] = [],
        label="",
        text="",
        ascii_only=False,
        cancellable=True,
        close_on_selection=False,
        history: Optional[str] = None,
    ):
        self.items = items
        self.last_key_pressed_timestamp: float = 0.0
        self.prev_key: Union[int, str] = -1
        self.is_cancelled: bool = False

        self._cancellable: bool = cancellable
        self._close_on_selection: bool = close_on_selection
        self._closed: bool = False
        self._height: int = -1
        self._input = _InputWidget(label=label, text=text, ascii_only=ascii_only)
        self._last_input = None
        self._last_item_count = 0
        self._matched_item_indices: List[int] = []
        self._message: Optional[str] = None
        self._requested_selected_row: int = -1
        self._selected_row: int = 0
        self._should_update_items: bool = False
        self._width: int = -1

        # Only update screen when _should_update_screen is True. This is set to True to
        # trigger the initial draw.
        self._should_update_screen = True

        # History
        self.history = history
        if history:
            self.history_values = load_json(self.get_history_file(), [])
            sort_key = {val: i for i, val in enumerate(self.history_values)}
            sorted_items = sorted(
                zip(self.items, list(range(len(self.items)))),
                key=lambda x: sort_key.get(str(x[0]), sys.maxsize),
            )
            self.items = [x[0] for x in sorted_items]
            self.indices = [x[1] for x in sorted_items]

        # Hotkeys
        self._hotkeys: Dict[Union[int, str], _Hotkey] = {}
        self.add_hotkey("ctrl+p", self.__open_command_palette)

    def add_hotkey(self, hotkey: str, func: Callable):
        for ch in to_ascii_hotkey(hotkey):
            self._hotkeys[ch] = _Hotkey(hotkey=hotkey, func=func)

    def get_history_file(self):
        from _script import get_data_dir

        return os.path.join(get_data_dir(), "%s_history.json" % slugify(self.history))

    def item(self, name: Optional[str] = None):
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__
            self.items.append(_MenuItem(name=name, callback=func))
            return func

        return decorator

    def set_input(self, text: str):
        self._input.set_text(text)

    def get_input(self) -> str:
        return self._input.text

    def set_prompt(self, prompt: str):
        self._input.label = prompt

    def clear_input(self):
        self._input.clear()
        self.reset_selection()
        self._should_update_screen = True

    def call_func_without_curses(self, func: Callable[[], None]):
        Menu.destroy_curses()
        func()
        Menu.init_curses()

    def exec(self) -> int:
        if Menu.stdscr is None:
            try:
                Menu.init_curses()
                self._exec()
            finally:
                Menu.destroy_curses()
        else:
            self._exec()

        idx = self.get_selected_index()
        if self.history is not None and idx >= 0:
            try:
                self.history_values.remove(str(self.items[idx]))
            except ValueError:
                pass
            self.history_values.insert(0, str(self.items[idx]))
            save_json(self.get_history_file(), self.history_values)
            idx = self.indices[idx]

        return idx

    @staticmethod
    def init_curses():
        if Menu.stdscr is not None:
            return

        # Remove escape key delay for Linux system
        # See also: ESCDELAY in https://linux.die.net/man/3/ncurses
        os.environ.setdefault("ESCDELAY", "25")

        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()  # The default color is assigned to -1
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)

        stdscr.keypad(True)
        stdscr.nodelay(False)
        stdscr.timeout(1000)
        Menu.stdscr = stdscr

    @staticmethod
    def destroy_curses():
        if Menu.stdscr is None:
            return
        curses.endwin()
        Menu.stdscr = None

    def update_screen(self):
        assert Menu.stdscr is not None

        self._height, self._width = Menu.stdscr.getmaxyx()  # type: ignore

        if sys.platform == "win32":
            Menu.stdscr.clear()
        else:
            # Use erase instead of clear to prevent flickering
            Menu.stdscr.erase()
        self.on_update_screen(height=self._height)
        Menu.stdscr.refresh()

    def update_matched_items(self):
        # Search scripts
        self._matched_item_indices = list(
            _fuzzy_search_func(self.items, self.get_text())
        )
        self.reset_selection()

    def reset_selection(self):
        self._selected_row = 0

    def set_selected_row(self, selected_row: int):
        self._requested_selected_row = selected_row
        self.on_item_selected()

    def refresh(self):
        self._should_update_items = True

    # Returns false if we should exit main loop for the current window
    def process_events(self, blocking=False) -> bool:
        assert Menu.stdscr is not None

        if blocking:
            Menu.stdscr.timeout(1000)
        else:
            Menu.stdscr.timeout(0)

        self._should_update_items = (
            self._should_update_items
            or self._last_input != self.get_text()
            or self._last_item_count != len(self.items)
        )
        if not blocking or self._should_update_items:
            self._last_input = self.get_text()
            self._last_item_count = len(self.items)
            self.update_matched_items()
            self._should_update_items = False
            self._should_update_screen = True

        if self._requested_selected_row >= 0:
            self._selected_row = self._requested_selected_row
            self._requested_selected_row = -1

        if self._should_update_screen:
            self.update_screen()
            self._should_update_screen = False

        # Keyboard event
        try:
            ch = Menu.stdscr.get_wch()
        except curses.error:
            ch = -1
        except KeyboardInterrupt:
            sys.exit(0)

        if ch != -1:  # getch() will return -1 when timeout
            if DEBUG_KEY_PRESS:
                self.set_message(f"key={repr(ch)} type={type(ch)}")

            self.last_key_pressed_timestamp = time.time()
            if self.on_char(ch):
                self._should_update_screen = True

            elif ch == "\n":
                self.on_enter_pressed()

            elif ch == curses.KEY_UP or ch == 450:  # curses.KEY_A2
                self._selected_row = max(self._selected_row - 1, 0)
                self.on_item_selected()

            elif ch == curses.KEY_DOWN or ch == 456:  # curses.KEY_C2
                self._selected_row = min(
                    self._selected_row + 1, len(self._matched_item_indices) - 1
                )
                self.on_item_selected()

            elif ch == curses.KEY_PPAGE or ch == 451:  # curses.KEY_A3
                self._selected_row = max(
                    self._selected_row - self.get_items_per_page(), 0
                )
                self.on_item_selected()

            elif ch == curses.KEY_NPAGE or ch == 457:  # curses.KEY_C3
                self._selected_row = min(
                    self._selected_row + self.get_items_per_page(),
                    len(self._matched_item_indices) - 1,
                )
                self.on_item_selected()

            elif ch == "\x1b":  # escape key
                if self._cancellable:
                    self.is_cancelled = True
                    self._closed = True
                else:
                    self._input.clear()
                    self._should_update_screen = True

            elif ch != "\0":
                self._input.on_char(ch)
                self._should_update_screen = True

            self.prev_key = ch

        if ch == -1 and blocking:  # getch() is timed-out
            self.__on_idle()

        if self._closed:
            self.on_exit()
            return False
        else:
            return True

    def __on_idle(self):
        self.on_idle()

    def on_exit(self):
        pass

    def on_idle(self):
        pass

    def _exec(self):
        self.on_created()
        self.on_main_loop()
        while self.process_events(blocking=True):
            self.on_main_loop()

    def get_selected_index(self):
        if self.is_cancelled:
            return -1
        elif len(self._matched_item_indices) > 0:
            return self._matched_item_indices[self._selected_row]
        else:
            return -1

    def get_text(self):
        return self._input.text

    def get_items_per_page(self):
        return self._height - 2

    def draw_text(
        self, row: int, col: int, s: str, color_pair=0, wrap_text=False
    ) -> int:
        """_summary_

        Args:
            row (int): _description_
            col (int): _description_
            s (str): _description_

        Returns:
            int: The row number of the last line of text being drawn on the screen.
        """
        assert Menu.stdscr is not None

        if row >= self._height:
            return False

        if col < 0:
            s = ".." + s[-col + 2 :]
            col = 0

        if color_pair > 0:
            Menu.stdscr.attron(curses.color_pair(color_pair))

        y = row
        x = col
        last_row_index = row
        for i, ch in enumerate(s):
            try:
                Menu.stdscr.addstr(y, x, ch)
            except curses.error:
                # Tolerate "addwstr() returned ERR"
                pass

            last_y = y
            y, x = Menu.stdscr.getyx()  # type: ignore

            if wrap_text:
                if y >= self._height:
                    last_row_index = self._height - 1
                    break
            else:
                if y > last_y:
                    if i < len(s) - 1:
                        last_row_index = row
                        Menu.stdscr.attron(curses.color_pair(2))
                        Menu.stdscr.addstr(row, self._width - 1, ">")
                        Menu.stdscr.attroff(curses.color_pair(2))
                    break

            last_row_index = y

        if color_pair > 0:
            if y < self._height:
                space_len = self._width - x
                if space_len > 0:
                    try:
                        Menu.stdscr.addstr(y, x, " " * space_len)
                    except curses.error:
                        # addch() returns an error because it tries to wrap to
                        # the next line after adding a character, but this
                        # behavior is expected.
                        pass
            Menu.stdscr.attroff(curses.color_pair(color_pair))

        return last_row_index

    def on_update_screen(self, height: int):
        assert Menu.stdscr is not None

        if height < 0:
            height = self._height

        # Get matched scripts
        row = 2
        items_per_page = self.get_items_per_page()

        current_page_index = self._selected_row // items_per_page
        selected_index_in_page = self._selected_row % items_per_page
        indices_in_page = self._matched_item_indices[
            current_page_index * items_per_page :
        ]

        self._text_overflow = False
        next_i = 0
        for i, item_index in enumerate(indices_in_page):
            if row >= next_i:
                is_item_selected = i == selected_index_in_page
                # Draw item index and text
                s = "{:>4}".format(item_index + 1) + " " + str(self.items[item_index])

                next_i = (
                    self.draw_text(
                        row,
                        0,
                        s,
                        wrap_text=is_item_selected,
                        color_pair=2 if is_item_selected else 0,
                    )
                ) + 1

            row += 1
            if row >= height:
                break

        matched_item_str = "(%d/%d)" % (
            self._selected_row + 1,
            len(self._matched_item_indices),
        )
        self.draw_text(0, self._width - len(matched_item_str), matched_item_str)

        if self._message is not None:
            self.draw_text(1, 0, self._message)

        # Render input widget at the end, so the cursor will be move to the
        # correct position.
        self._input.on_update_screen(Menu.stdscr, 0, cursor=True)

    def get_selected_item(self, ignore_cancellation=False) -> Optional[T]:
        if not ignore_cancellation and self.is_cancelled:
            return None
        elif len(self._matched_item_indices) > 0:
            item_index = self._matched_item_indices[self._selected_row]
            return self.items[item_index]
        else:
            return None

    def on_char(self, ch: int):
        if ch == "\t":
            item = self.get_selected_item()
            if item is not None:
                self.set_input("%s" % item)
            return True

        elif ch == curses.ascii.ctrl("c"):
            sys.exit(0)

        elif ch in self._hotkeys:
            self._hotkeys[ch].func()
            return True

        else:
            return False

    def on_enter_pressed(self):
        item = self.get_selected_item()
        if item is not None and hasattr(item, "callback") and callable(item.callback):
            self.call_func_without_curses(lambda item=item: item.callback())
            if self._close_on_selection:
                self.close()
        else:
            self.close()
        self._should_update_screen = True

    def on_tab_pressed(self):
        pass

    def on_main_loop(self):
        pass

    def on_created(self):
        pass

    def close(self):
        self._closed = True

    def on_item_selected(self):
        self._should_update_screen = True

    def set_message(self, message: Optional[str] = None):
        self._message = message
        self._should_update_screen = True

    def __open_command_palette(self):
        w = Menu(label=": command palette", items=list(self._hotkeys.values()))
        w.exec()
        hotkey = w.get_selected_item()
        if hotkey is not None:
            hotkey.func()

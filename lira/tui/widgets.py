from functools import partial

from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import (
    ConditionalMargin,
    Dimension,
    FormattedTextControl,
    HSplit,
    ScrollbarMargin,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.widgets import Box
from prompt_toolkit.widgets import Button as ToolkitButton

from lira.tui.utils import set_title


class Button(ToolkitButton):

    """
    Override the default button to use a different style.

    By default buttons look like::

        < Button >

    Now they look like::

        [ Button ]
    """

    def _get_text_fragments(self):
        width = self.width - 2
        text = (f"{{:^{width}}}").format(self.text)

        def handler(mouse_event):
            if (
                self.handler is not None
                and mouse_event.event_type == MouseEventType.MOUSE_UP
            ):
                self.handler()

        return [
            ("class:button.arrow", "[", handler),
            ("[SetCursorPosition]", ""),
            ("class:button.text", text, handler),
            ("class:button.arrow", "]", handler),
        ]


class ListElement:

    """
    Element used by `List`.

    :param text: Text to be displayed.
    :param on_select: Function to be call when the element is selected.
    :param on_focus: Function to be call when the element gains focus.
    """

    def __init__(self, text: str = "", on_select=None, on_focus=None):
        self.text = text
        self.on_select = on_select
        self.on_focus = on_focus


class List:

    """
    List widget.

    :param title: Any formatted text to be used as the title of the list.
    :param elements: List of `ListElement`.
    :param get_bullet: A function (function(line)) to be called to get the
    bullet of the element in that line number.
    :param allow_select: If `True`, display an extra column indicating the
    current selected item. Util when you want to keep the list after the
    element is selected.
    """

    def __init__(
        self,
        title=None,
        elements=None,
        width=None,
        height=None,
        align=WindowAlign.LEFT,
        get_bullet=None,
        allow_select=True,
    ):
        self.index = 0
        self.get_bullet = get_bullet
        self.selected = -1
        self.elements = elements or []
        self.title = title
        self.allow_select = allow_select
        self.cursor = Point(0, 0)
        self.control = FormattedTextControl(
            text=self._get_text,
            focusable=True,
            get_cursor_position=lambda: self.cursor,
            key_bindings=self.get_key_bindings(),
        )

        # TODO: figure out how to the make it look nicer
        right_margins = [
            ConditionalMargin(
                ScrollbarMargin(display_arrows=True),
                filter=Condition(lambda: False),
            ),
        ]
        self.title_window = FormattedTextArea(text=self.title, wrap_lines=True)
        self.list_window = Window(
            content=self.control,
            width=width,
            height=height,
            always_hide_cursor=False,
            style="class:list",
            wrap_lines=True,
            dont_extend_height=True,
            dont_extend_width=False,
            cursorline=False,
            right_margins=right_margins,
            allow_scroll_beyond_bottom=True,
            get_line_prefix=self._get_line_prefix,
        )
        self.window = HSplit(
            children=[
                Box(
                    self.title_window,
                    padding=Dimension.exact(1),
                ),
                Box(
                    self.list_window,
                    padding=Dimension.exact(1),
                    padding_top=Dimension.exact(0),
                ),
            ],
            height=Dimension(min=1),
            width=Dimension(min=1),
        )

    def _get_line_prefix(self, line, wrap_count):
        bullet = self.get_bullet(line) if self.get_bullet else " "
        if self.allow_select:
            if self.selected == line:
                bullet = "• " + bullet
            else:
                bullet = "  " + bullet
        if wrap_count:
            return " " * len(bullet)
        return bullet

    def _get_text(self):
        formatted_text = []
        for i, element in enumerate(self.elements):
            text = element.text.replace("\n", " ")
            style = ""
            if i < len(self.elements) - 1:
                text += "\n"
            if i == self.index:
                style = "class:list-item.focused"
            formatted_text.append(
                (
                    style,
                    text,
                    partial(self.mouse_select, i),
                )
            )
        return formatted_text

    @property
    def current_element(self):
        return self.elements[self.index]

    def mouse_select(self, index, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            self.select(index)

    def select(self, index):
        self.index = index
        self.selected = self.index
        self.cursor = Point(0, self.index)
        element = self.current_element
        if element.on_select:
            element.on_select()

    def focus(self, index):
        self.index = index
        self.cursor = Point(0, self.index)
        element = self.current_element
        if element.on_focus:
            element.on_focus()

    def previous(self):
        index = max(self.index - 1, 0)
        self.focus(index)

    def next(self):
        index = min(self.index + 1, len(self.elements) - 1)
        self.focus(index)

    def get_key_bindings(self):
        keys = KeyBindings()

        @keys.add(Keys.Up)
        def _(event):
            self.previous()

        @keys.add(Keys.BackTab)
        def _(event):
            if self.index <= 0:
                focus_previous(event)
            else:
                self.previous()

        @keys.add(Keys.Down)
        def _(event):
            self.next()

        @keys.add(Keys.Tab)
        def _(event):
            if self.index >= len(self.elements) - 1:
                focus_next(event)
            else:
                self.next()

        @keys.add(" ")
        @keys.add(Keys.Enter)
        def _(event):
            self.select(self.index)

        return keys

    def __pt_container__(self):
        return self.window


class FormattedTextArea:

    """Just like text area, but it accepts formatted content."""

    def __init__(
        self,
        text="",
        focusable=False,
        wrap_lines=True,
        width=None,
        height=None,
        align=WindowAlign.LEFT,
        style="",
    ):
        self.text = text
        self.control = FormattedTextControl(
            text=lambda: self.text,
            focusable=focusable,
        )
        self.window = Window(
            content=self.control,
            width=width,
            height=height,
            style="class:formatted-text-area " + style,
            wrap_lines=wrap_lines,
            dont_extend_height=True,
            dont_extend_width=False,
        )

    def __pt_container__(self):
        return self.window


class LiraList:

    allow_select = False

    def __init__(self, tui):
        self.tui = tui
        self.lira = self.tui.lira
        self.container = List(
            title=self._get_title(),
            elements=self._get_elements(),
            get_bullet=self._get_bullet,
            allow_select=self.allow_select,
        )

    def _get_title(self):
        raise NotImplementedError

    def _get_elements(self):
        raise NotImplementedError

    def _get_bullet(self, line):
        return "• "

    def __pt_container__(self):
        return self.container


class BooksList(LiraList):
    def _get_title(self):
        return HTML("<title>{}</title>").format("Books")

    def _get_elements(self):
        elements = []
        for i, book in enumerate(self.lira.books):
            book.parse()
            title = book.metadata["title"]
            elements.append(
                ListElement(
                    text=title,
                    on_select=partial(self.select, book, i),
                )
            )
        return elements

    def select(self, book, index=0):
        widget = BookChaptersList(self.tui, book)
        set_title(book.metadata["title"])
        self.tui.menu.push(widget)


class BookChaptersList(LiraList):
    def __init__(self, tui, book):
        self.book = book
        super().__init__(tui)

    def _get_title(self):
        book_title = self.book.metadata["title"]
        return HTML("<title>{}</title>").format(book_title)

    def _get_bullet(self, line):
        return f"{line + 1}. "

    def _get_elements(self):
        elements = []
        for i, chapter in enumerate(self.book.chapters):
            chapter.parse()
            elements.append(
                ListElement(
                    text=chapter.title,
                    on_select=partial(self._select, chapter, i),
                )
            )
        return elements

    def _select(self, chapter, index):
        widget = ChapterSectionsList(self.tui, chapter, index)
        self.tui.menu.push(widget)


class ChapterSectionsList(LiraList):

    allow_select = True

    def __init__(self, tui, chapter, index):
        self.index = index
        self.chapter = chapter
        self.toc = self.chapter.toc(depth=1)
        super().__init__(tui)

        # Select first item automatically
        self.container.select(0)

    def _get_title(self):
        book_title = self.chapter.book.metadata["title"]
        title = HTML(
            "<title>{}</title> <separator>></separator> <title>{}</title>"
        ).format(book_title, self.chapter.title)
        return title

    def _get_bullet(self, line):
        return f"{self.index + 1}.{line + 1}. "

    def _get_elements(self):
        elements = []
        for section, _ in self.toc:
            elements.append(
                ListElement(
                    text=section.options.title,
                    on_select=partial(self._select, section),
                )
            )
        return elements

    def _select(self, section, index=0):
        self.tui.content.render_section(section)

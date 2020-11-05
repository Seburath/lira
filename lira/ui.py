from functools import partial

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text import merge_formatted_text, to_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, to_container
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Box, Button, Label, TextArea

from lira.app import LiraApp


def get_key_bindings():
    keys = KeyBindings()

    @keys.add("tab")
    @keys.add("down")
    def _(event):
        focus_next(event)

    @keys.add("s-tab")
    @keys.add("up")
    def _(event):
        focus_previous(event)

    @keys.add("c-c")
    @keys.add("c-q")
    def _(event):
        """Pressing Ctrl-Q or Ctrl-C will exit the user interface."""
        event.app.exit()

    return keys


themes = {
    "default": {
        "Text": "#fff",
        "Strong": "#fff bold",
        "Emphasis": "#fff italic",
        "Literal": "#fff",
        "Paragraph": "#fff",
        "CodeBlock": "#fff",
        "Prompt": "bg:#999999 #fff",
        "TestBlock": "#fff",
        "Section": "#fff",
        "Separator": "#fff",
    }
}

styles = themes["default"]


sections = {
    "menu": TextArea(height=40, width=20, style=styles["Text"], text=""),
    "status": TextArea(
        height=3,
        prompt=">>> ",
        style=styles["Text"],
        multiline=False,
        wrap_lines=False,
    ),
    "text": TextArea(height=10, width=40, style=styles["Text"], text="text"),
    "prompt": TextArea(height=10, width=40, style=styles["Prompt"], text=""),
    "vseparator": Window(height=0, width=1, char="│", style=styles["Separator"]),
    "hseparator": Window(height=1, char="─", style=styles["Separator"]),
}


class ContentArea:
    def __init__(self):
        self.welcome = Label("Welcome to Lira! :)")
        self.container = Box(
            height=20, width=80, body=self.welcome, padding=1, style=styles["Text"]
        )

    def get_label(self, contents):
        # TODO: parse and render individual nodes
        formated_content = []
        for node in contents.children:
            text = node.text()
            style = node.tagname
            formated_content.append(to_formatted_text(text, styles[style]))
            if node.tagname == "Paragraph":
                formated_content.append(to_formatted_text("\n", ""))

        label = Label(merge_formatted_text(formated_content))

        return label

    def get_sections_list(self):
        sections_list = []
        for section in ["text", "prompt"]:
            sections_list.append(sections[section])

        return sections_list

    def render(self, section):
        app = get_app()
        # TODO: access through the instance
        vsplit = app.layout.container.get_children()[0]
        content = vsplit.get_children()[2]

        label = self.get_label(section)

        content.children = [
            to_container(
                Box(height=20, width=80, body=label, padding=1, style=styles["Text"])
            )
        ]


class SidebarMenu:
    def __init__(self, lira, content):
        self.lira = lira
        self.content = content

        self.lira.books[0].parse()
        self.chapter = self.lira.books[0].chapters[0]
        self.chapter.parse()

        self.items = self.get_nested_items()
        self.buttons = self.get_buttons()

        self.container = HSplit(
            self.buttons, padding=1, height=40, width=25, style=styles["Text"]
        )

    def get_top_items(self):
        """Return the list of items on top of the current menu item."""
        # TODO: return top items
        return []

    def get_nested_items(self):
        """Return the list of items nested on the current menu item."""
        # TODO: read from current menu position
        nested_items = []

        for section, _ in self.chapter.toc(depth=1):
            nested_items.append(section.options.title)

        return nested_items

    def select_section(self, section):
        self.content.render(section)

    def get_buttons(self):
        """Return a list of buttons from  a list of items."""
        buttons = []

        # TODO: iterate over sections
        for i, item in enumerate(self.items):
            section = self.chapter.toc(depth=1)[i][0]
            buttons.append(
                Button(
                    f"{i + 1}. {item}", handler=partial(self.select_section, section)
                )
            )

        buttons.append(Button("Exit", handler=self.exit))
        return buttons

    def exit(self):
        get_app().exit()


class StatusBar:
    def __init__(self, lira):
        self.lira = lira
        self.container = sections["status"]


class TerminalUI:
    def __init__(self):
        self.lira = LiraApp()
        self.lira.setup()

        self.content = ContentArea()
        self.status = StatusBar(self.lira)
        self.menu = SidebarMenu(self.lira, self.content)

        self.container = HSplit(
            [
                VSplit(
                    [
                        self.menu.container,
                        sections["vseparator"],
                        self.content.container,
                    ]
                ),
                sections["hseparator"],
                self.status.container,
            ]
        )

    def run(self):
        self.app = Application(
            layout=Layout(self.container),
            key_bindings=get_key_bindings(),
            mouse_support=True,
            full_screen=True,
        )

        self.app.run()

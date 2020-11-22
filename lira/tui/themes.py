from prompt_toolkit.styles import Style

themes = {
    "default": {
        # Basic elements
        "text": "#fff",
        "strong": "#fff bold",
        "literal": "#fff",
        "emphasis": "#fff italic",
        "title": "#fff bold",
        "separator": "#aaa",
        # Widgets
        "list-item.focused": "bg:#0055aa #ffffff",
    }
}

theme = themes["default"]
style = Style.from_dict(theme)

import json
from datetime import datetime, timedelta
from types import SimpleNamespace

from PIL import ImageFont

from ui.layouts.base_layout import BaseLayout

DEFAULT_TODOS = """
[
  {"title": "Buy milk 2", "done": true, "due": "2023-11-04T00:05:23"},
  {"title": "Buy milk 1", "done": true, "due": "2021-11-04T00:05:23"},
  {"title": "Clean floor", "done": false, "due": "2024-08-01T00:05:23"}
]
"""


def todo_object_hook(d):
    if "due" in d:
        d["due"] = datetime.fromisoformat(d["due"])
    return SimpleNamespace(**d)


class Todos(BaseLayout):
    def __init__(self, size, data=None):
        super().__init__(size, data)
        todos = data.get("todos", DEFAULT_TODOS)
        self.todos = sorted(
            json.loads(todos, object_hook=todo_object_hook), key=lambda x: x.due
        )
        self.row_height = max(18, (self.size[1] - 10) // len(self.todos))

    def draw(self, draw):
        super().draw(draw)
        fnt = ImageFont.truetype("ui/fonts/Bookerly.ttf", self.row_height)
        draw.font = fnt
        draw.fontmode = "1"  # Disable antialiasing
        for i, todo in enumerate(self.todos):
            done = "[x]" if todo.done else "[  ]"
            if todo.due - timedelta(days=1) < datetime.now() and not todo.done:
                fill = "red"
            else:
                fill = "black"
            draw.text((0, i * self.row_height), f"{done} {todo.title}", fill=fill)

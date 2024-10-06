import json
import unicodedata
from datetime import datetime, timedelta
from types import SimpleNamespace

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from ui.layouts.base_layout import BaseLayout

DEFAULT_TODOS = """
[
  {"title": "Buy milk", "done": true, "due": "2023-11-04T00:05:23"},
  {"title": "Buy eggs", "done": true, "due": "2021-11-04T00:05:23"},
  {"title": "Clean floor", "done": false, "due": "2024-08-01T00:05:23"},
  {"title": "洗车", "done": false, "due": "2025-08-11T00:05:23"},
  {"title": "Clean sink", "done": false, "due": "2025-08-21T00:05:23"}
]
"""


def todo_object_hook(d):
    if "due" in d:
        d["due"] = datetime.fromisoformat(d["due"])
    return SimpleNamespace(**d)


class Todos(BaseLayout):
    text_start = (36, 10)

    def __init__(self, size, data=None, max_rows=5):
        super().__init__(size, data)
        todos = data.get("todos", DEFAULT_TODOS)
        self.max_rows = max_rows
        self.todos = self.process_todos(todos)
        self.row_height = min(
            40, max(18, (self.size[1] - self.text_start[1]) // len(self.todos))
        )

    def has_chinese(self, string):
        """Check if a character is Chinese."""
        return any("CJK" in unicodedata.name(char) for char in string)

    def draw(self, image_draw: ImageDraw):
        super().draw(image_draw)

        # Draw vertical lines
        image_draw.line(
            (self.text_start[0] - 2, 0, self.text_start[0] - 2, self.size[1]),
            fill="black",
            width=2,
        )

        # Draw text
        fnt = ImageFont.truetype("ui/fonts/Roboto-Regular.ttf", self.row_height)
        chn_fnt = ImageFont.truetype("ui/fonts/simhei.ttf", self.row_height)
        sym_fnt = ImageFont.truetype(
            "ui/fonts/NotoSansSymbols2-Regular.ttf", self.row_height
        )

        image_draw.fontmode = "1"  # Disable antialiasing
        for i, todo in enumerate(self.todos):
            row_y = self.text_start[1] + i * self.row_height
            done = "⮾ " if todo.done else "⭘ "

            if todo.due - timedelta(days=1) < datetime.now() and not todo.done:
                fill = "red"
            else:
                fill = "black"

            image_draw.text(
                (self.text_start[0], row_y), done, fill=fill, anchor="rt", font=sym_fnt
            )

            font = chn_fnt if self.has_chinese(todo.title) else fnt

            image_draw.text(
                (self.text_start[0], row_y),
                todo.title,
                fill=fill,
                anchor="lt",
                font=font,
            )
            if i > 0:
                line_y = row_y - 2
                image_draw.line(
                    (
                        0,
                        line_y,
                        self.size[0],
                        line_y,
                    ),
                    fill="black",
                    width=1,
                )

    def process_todos(self, todos):
        ordered = sorted(
            json.loads(todos, object_hook=todo_object_hook), key=lambda x: x.due
        )
        done = []
        presenting = []
        if len(ordered) > self.max_rows:
            for todo in ordered:
                if len(presenting) >= self.max_rows:
                    break
                if todo.done:
                    done.append(todo)
                else:
                    presenting.append(todo)
            while len(presenting) < self.max_rows and done:
                presenting.insert(0, done.pop())
            return presenting
        return ordered

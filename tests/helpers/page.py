from typing import Optional


class Page:

    "<html><head></head><body>ok</body></html>"

    def __init__(self, content: Optional[str]):
        self._unlocks = 0
        self._content = content
        self._exists = False
        self._mime_type = ""

    def __call__(self):
        """ return dict """
        return {
            'exists': self._exists,
            'unlocks': self._unlocks,
            'mime_type': self._mime_type,
            'content': self._content,
        }

    def content(self, data: str):
        self._content = data
        return self

    def page(self):
        return self

    def exists(self):
        self._exists = True
        return self

    def not_exists(self):
        self._exists = False
        return self

    def unlock_after(self, n: int):
        self._unlocks = n
        return self
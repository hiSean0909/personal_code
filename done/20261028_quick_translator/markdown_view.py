"""Small selectable Markdown view built on Tk's existing text widget."""

import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter.scrolledtext import ScrolledText
import unicodedata
import webbrowser


INLINE = re.compile(r"\\([\\`*_{}\[\]()#+.!>|-])|(`+)(.+?)\2(?!`)|\[([^\]]+)\]\((https?://[^\s)]+)\)|(\*\*|__)(?=\S)(.+?)\6|(\*|_)(?=\S)(.+?)\8")


class MarkdownText(ScrolledText):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fonts = {}
        self.links = []
        self.hbar = tk.Scrollbar(self.frame, orient="horizontal", command=self.xview)
        self.hbar.pack(side="bottom", fill="x", before=self._w)
        self.configure(xscrollcommand=self.hbar.set)
        self.tag_configure("quote", foreground="#666666", lmargin1=18, lmargin2=18)
        self.tag_configure("code", background="#f0f0f0", wrap="none")
        self.tag_configure("table", background="#f5f5f5", wrap="none")
        self.tag_configure("rule", foreground="#999999")

    def style(self, tags):
        styles = tuple(sorted(set(tags) & {"bold", "italic", "code", "table", *[f"h{i}" for i in range(1, 7)]}))
        name = "font:" + ":".join(styles)
        if name not in self.fonts:
            font = tkfont.Font(self, font=self.cget("font"))
            if "code" in styles or "table" in styles:
                font.configure(family="Consolas")
            heading = next((int(s[1:]) for s in styles if re.fullmatch(r"h[1-6]", s)), None)
            if heading:
                font.configure(size=max(11, 23 - heading * 2))
            font.configure(weight="bold" if heading or "bold" in styles else "normal",
                           slant="italic" if "italic" in styles else "roman")
            self.fonts[name] = font
            self.tag_configure(name, font=font)
        return name

    def write(self, text, tags=()):
        self.insert("end", text, (*tags, self.style(tags)))

    def inline(self, text, tags=()):
        position = 0
        for match in INLINE.finditer(text):
            self.write(text[position:match.start()], tags)
            escaped, ticks, code, label, url, strong, bold, emphasis, italic = match.groups()
            if escaped:
                self.write(escaped, tags)
            elif ticks:
                self.write(code, (*tags, "code"))
            elif label is not None:
                link = f"link:{len(self.links)}"
                self.links.append(link)
                self.tag_configure(link, foreground="#1466b8", underline=True)
                self.tag_bind(link, "<Button-1>", lambda event, target=url: webbrowser.open(target))
                self.tag_bind(link, "<Enter>", lambda event: self.configure(cursor="hand2"))
                self.tag_bind(link, "<Leave>", lambda event: self.configure(cursor="xterm"))
                self.inline(label, (*tags, link))
            elif strong:
                self.inline(bold, (*tags, "bold"))
            elif emphasis:
                self.inline(italic, (*tags, "italic"))
            position = match.end()
        self.write(text[position:], tags)

    @staticmethod
    def cells(line):
        return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]

    def table(self, lines):
        rows = [self.cells(line) for line in lines]
        rows.pop(1)  # Markdown alignment separator.
        width = lambda value: sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in value)
        # Strip inline syntax into a temporary range before measuring cell text.
        plain = []
        for row in rows:
            values = []
            for cell in row:
                start = self.index("end-1c")
                self.inline(cell)
                values.append(self.get(start, "end-1c"))
                self.delete(start, "end-1c")
            plain.append(values)
        columns = max(map(len, plain))
        widths = [max((width(row[i]) if i < len(row) else 0) for row in plain) for i in range(columns)]
        for number, row in enumerate(rows):
            tags = ("table", "bold") if number == 0 else ("table",)
            for i in range(columns):
                value = row[i] if i < len(row) else ""
                self.inline(value, tags)
                length = width(plain[number][i]) if i < len(plain[number]) else 0
                self.write(" " * (widths[i] - length + 2), tags)
            self.write("\n", tags)

    def render(self, markdown):
        self.configure(state="normal", cursor="xterm")
        self.delete("1.0", "end")
        for link in self.links:
            self.tag_delete(link)
        self.links.clear()
        lines = markdown.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            fence = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
            if fence:
                marker = fence[1]
                i += 1
                while i < len(lines) and not re.fullmatch(r"\s{0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*", lines[i]):
                    self.write(lines[i] + "\n", ("code",))
                    i += 1
            elif i + 1 < len(lines) and "|" in line and re.fullmatch(r"\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*", lines[i + 1]):
                end = i + 2
                while end < len(lines) and "|" in lines[end] and lines[end].strip():
                    end += 1
                self.table(lines[i:end])
                i = end
                continue
            elif re.fullmatch(r"\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})", line):
                self.write("────────────────────────\n", ("rule",))
            else:
                tags = ()
                heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$", line)
                if heading:
                    tags = (f"h{len(heading[1])}",)
                    line = heading[2]
                elif re.match(r"^\s*>\s?", line):
                    tags = ("quote",)
                    line = re.sub(r"^\s*>\s?", "", line)
                else:
                    line = re.sub(r"^(\s*)[-+*]\s+", r"\1• ", line)
                self.inline(line, tags)
                self.write("\n", tags)
            i += 1
        self.configure(state="disabled")
        self.yview_moveto(0)

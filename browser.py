import tkinter
import tkinter.font

from parser import HTMLParser
from layout import DocumentLayout, VSTEP, \
  paint_tree  # TODO: replace VSTEP with a layout_item height prop
from url import URL

WIDTH, HEIGHT = 800, 600


class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    self.canvas = tkinter.Canvas(
        self.window,
        width=WIDTH,
        height=HEIGHT
    )
    self.canvas.pack(fill=tkinter.BOTH, expand=1)
    self.scroll = 0
    self.max_scroll = 0
    self.nodes = None
    self.document: DocumentLayout | None = None
    self.display_list = []
    self.window.update()
    self.window.bind("<MouseWheel>", lambda e: self.do_scroll(-e.delta))
    self.window.bind("<Down>", lambda e: self.do_scroll(50))
    self.window.bind("<Up>", lambda e: self.do_scroll(-50))
    self.window.bind("<Next>", lambda e: self.do_scroll(500))
    self.window.bind("<Prior>", lambda e: self.do_scroll(-500))
    self.window.bind("<Configure>", self.resize)

  def resize(self, e):
    self.update_layout(e.width)
    self.draw()

  def do_scroll(self, amount):
    self.scroll = min(max(0, self.scroll + amount), self.max_scroll)
    self.draw()

  def draw(self):
    self.canvas.delete("all")
    if self.max_scroll > 0:
      scroll_ratio = float(self.scroll) / self.max_scroll
      screen_ratio = float(self.window.winfo_height()) / self.max_scroll
      scroll_bar_height = screen_ratio * self.window.winfo_height()
      self.canvas.create_rectangle(self.window.winfo_width() - 10,
                                   self.window.winfo_height() * scroll_ratio - scroll_bar_height / 2,
                                   self.window.winfo_width()-1,
                                   self.window.winfo_height() * scroll_ratio + scroll_bar_height / 2,
                                   fill="blue", outline="blue")
    for x, y, c, f in self.display_list:
      if y > self.scroll + self.window.winfo_height():
        continue
      if y + VSTEP < self.scroll:
        continue
      self.canvas.create_text(x, y - self.scroll, text=c, anchor=tkinter.NW, font=f)

  def load(self, url):
    body = url.request()
    self.nodes = HTMLParser(body).parse()
    self.document = DocumentLayout(self.nodes)
    self.update_layout(self.window.winfo_width())
    self.draw()

  def update_layout(self, width):
    self.document.layout(width)
    self.max_scroll = self.document.height
    self.display_list = []
    paint_tree(self.document, self.display_list)


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()


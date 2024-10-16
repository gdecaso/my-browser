import tkinter
import tkinter.font

from ast import lex
from layout import Layout, VSTEP # TODO: replace VSTEP with a layout_item height prop
from url import URL

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 50


class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    self.canvas = tkinter.Canvas(
        self.window,
        width=WIDTH,
        height=HEIGHT
    )
    self.canvas.pack(fill=tkinter.BOTH, expand=1)
    self.display_list = []
    self.scroll = 0
    self.max_scroll = 0
    self.tokens = []
    self.window.update()
    self.window.bind("<MouseWheel>", self.mousewheel)
    self.window.bind("<Down>", self.scrolldown)
    self.window.bind("<Up>", self.scrollup)
    self.window.bind("<Configure>", self.resize)

  def resize(self, e):
    self.display_list = Layout(self.tokens, e.width).display_list
    self.calculate_max_scroll()
    self.draw()

  def do_scroll(self, amount):
    self.scroll = min(max(0, self.scroll + amount), self.max_scroll)
    self.draw()

  def mousewheel(self, e):
    self.do_scroll(-e.delta)

  def scrolldown(self, e):
    self.do_scroll(SCROLL_STEP)

  def scrollup(self, e):
    self.do_scroll(-SCROLL_STEP)

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
    self.tokens = lex(body)
    self.display_list = Layout(self.tokens, self.window.winfo_width()).display_list
    self.calculate_max_scroll()
    self.draw()

  def calculate_max_scroll(self):
    self.max_scroll = 0
    for _, cursor_y, _, _ in self.display_list:
      self.max_scroll = max(cursor_y + VSTEP - self.window.winfo_height(), self.max_scroll)


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()


import tkinter
import tkinter.font

from css import CSSParser, cascade_priority, style
from parser import HTMLParser, tree_to_list, Element
from layout import DocumentLayout, paint_tree, VSTEP
from url import URL

WIDTH, HEIGHT = 800, 600
DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()


class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    self.canvas = tkinter.Canvas(
        self.window,
        width=WIDTH,
        height=HEIGHT,
        bg="white",
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
    for cmd in self.display_list:
      if cmd.top > self.scroll + self.window.winfo_height():
        continue
      if cmd.bottom < self.scroll:
        continue
      cmd.execute(self.scroll, self.canvas)

  def load(self, url):
    body = url.request()
    self.nodes = HTMLParser(body).parse()
    self.document = DocumentLayout(self.nodes)
    rules = self.fetch_css(url)
    style(self.nodes, sorted(rules, key=cascade_priority))
    self.update_layout(self.window.winfo_width())
    self.draw()

  def fetch_css(self, url):
    rules = DEFAULT_STYLE_SHEET.copy()
    links = [node.attributes["href"]
             for node in tree_to_list(self.nodes, [])
             if isinstance(node, Element)
             and node.tag == "link"
             and node.attributes.get("rel") == "stylesheet"
             and "href" in node.attributes]
    for link in links:
      style_url = url.resolve(link)
      try:
        body = style_url.request()
      except:
        continue
      rules.extend(CSSParser(body).parse())
    return rules

  def update_layout(self, width):
    self.document.layout(width)
    self.max_scroll = VSTEP + self.document.y + self.document.height - self.window.winfo_height()
    self.display_list = []
    paint_tree(self.document, self.display_list)


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()


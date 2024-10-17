import tkinter.font
from parser import Text, Element

HSTEP, VSTEP = 13, 18

FONTS = {}


def get_font(size, weight, style):
  key = (size, weight, style)
  if key not in FONTS:
    font = tkinter.font.Font(size=size, weight=weight,
                             slant=style)
    label = tkinter.Label(font=font)
    FONTS[key] = (font, label)
  return FONTS[key][0]


class BlockLayout:
  BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
  ]

  def __init__(self, node, parent, previous):
    self.node = node
    self.parent = parent
    self.previous = previous
    self.children = []
    self.x = None
    self.y = None
    self.width = None
    self.height = None
    self.display_list = []

  def layout(self):
    self.display_list = []
    self.children = []
    self.width = self.parent.width
    self.x = self.parent.x
    if self.previous:
      self.y = self.previous.y + self.previous.height
    else:
      self.y = self.parent.y
    mode = self.layout_mode()
    if mode == "block":
      previous = None
      for child in self.node.children:
        next = BlockLayout(child, self, previous)
        self.children.append(next)
        previous = next
    else:
      self.cursor_x = 0
      self.cursor_y = 0
      self.weight = "normal"
      self.style = "roman"
      self.size = 12
      self.line = []
      self.recurse(self.node)
      self.flush()
    for child in self.children:
      child.layout()
    if mode == "block":
      self.height = sum([child.height for child in self.children])
    else:
      self.height = self.cursor_y

  def layout_mode(self):
    if isinstance(self.node, Text):
      return "inline"
    elif any([isinstance(child, Element) and child.tag in self.BLOCK_ELEMENTS for child in self.node.children]):
      return "block"
    elif self.node.children:
      return "inline"
    else:
      return "block"

  def recurse(self, tree):
    if isinstance(tree, Text):
      for word in tree.text.split():
        self.word(word)
    else:
      self.open_tag(tree.tag)
      for child in tree.children:
        self.recurse(child)
      self.close_tag(tree.tag)

  def open_tag(self, tag):
    if tag == "i":
      self.style = "italic"
    elif tag == "b":
      self.weight = "bold"
    elif tag == "small":
      self.size -= 2
    elif tag == "big":
      self.size += 4
    elif tag == "br":
      self.flush()

  def close_tag(self, tag):
    if tag == "i":
      self.style = "roman"
    elif tag == "b":
      self.weight = "normal"
    elif tag == "small":
      self.size += 2
    elif tag == "big":
      self.size -= 4
    elif tag == "p":
      self.flush()
      self.cursor_y += VSTEP

  def token(self, tok):
    if isinstance(tok, Text):
      for word in tok.text.split():
        self.word(word)
    elif tok.tag == "i":
      self.style = "italic"
    elif tok.tag == "/i":
      self.style = "roman"
    elif tok.tag == "b":
      self.weight = "bold"
    elif tok.tag == "/b":
      self.weight = "normal"
    elif tok.tag == "small":
      self.size -= 2
    elif tok.tag == "/small":
      self.size += 2
    elif tok.tag == "big":
      self.size += 4
    elif tok.tag == "/big":
      self.size -= 4
    elif tok.tag == "br":
      self.flush()
    elif tok.tag == "/p":
      self.flush()
      self.cursor_y += VSTEP

  def word(self, word):
    font = get_font(self.size, self.weight, self.style)
    w = font.measure(word)
    if self.cursor_x + w > self.width:
      self.flush()
    self.line.append((self.cursor_x, word, font))
    self.cursor_x += w + font.measure(" ")

  def flush(self):
    if not self.line:
      return
    metrics = [font.metrics() for x, word, font in self.line]
    max_ascent = max([metric["ascent"] for metric in metrics])
    baseline = self.cursor_y + 1.25 * max_ascent
    for rel_x, word, font in self.line:
      x = self.x + rel_x
      y = self.y + baseline - font.metrics("ascent")
      self.display_list.append((x, y, word, font))
    max_descent = max([metric["descent"] for metric in metrics])
    self.cursor_y = baseline + 1.25 * max_descent
    self.cursor_x = 0
    self.line = []

  def paint(self):
    return self.display_list


class DocumentLayout:
  def __init__(self, node):
    self.node = node
    self.parent = None
    self.children = []
    self.x = None
    self.y = None
    self.width = None
    self.height = None

  def layout(self, width):
    child = BlockLayout(self.node, self, None)
    self.width = width - 2 * HSTEP
    self.x = HSTEP
    self.y = VSTEP
    self.children = [child]
    child.layout()
    self.height = child.height

  def paint(self):
    return []


def paint_tree(layout_object, display_list):
  display_list.extend(layout_object.paint())

  for child in layout_object.children:
    paint_tree(child, display_list)

import tkinter.font

from css import CSSParser
from draw import DrawText, DrawRect
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

  def recurse(self, node):
    if isinstance(node, Text):
      for word in node.text.split():
        self.word(node, word)
    else:
      self.open_tag(node.tag)
      for child in node.children:
        self.recurse(child)
      self.close_tag(node.tag)

  def open_tag(self, tag):
    if tag == "br":
      self.flush()

  def close_tag(self, tag):
    if tag == "p":
      self.flush()
      self.cursor_y += VSTEP

  def word(self, node, word):
    color = node.style["color"]
    weight = node.style["font-weight"]
    style = node.style["font-style"]
    if style == "normal":
      style = "roman"
    size = int(float(node.style["font-size"][:-2]) * .75)
    font = get_font(size, weight, style)
    w = font.measure(word)
    if self.cursor_x + w > self.width:
      self.flush()
    self.line.append((self.cursor_x, word, font, color))
    self.cursor_x += w + font.measure(" ")

  def flush(self):
    if not self.line:
      return
    metrics = [font.metrics() for x, word, font, color in self.line]
    max_ascent = max([metric["ascent"] for metric in metrics])
    baseline = self.cursor_y + 1.25 * max_ascent
    for rel_x, word, font, color in self.line:
      x = self.x + rel_x
      y = self.y + baseline - font.metrics("ascent")
      self.display_list.append((x, y, word, font, color))
    max_descent = max([metric["descent"] for metric in metrics])
    self.cursor_y = baseline + 1.25 * max_descent
    self.cursor_x = 0
    self.line = []

  def paint(self):
    cmds = []
    bgcolor = self.node.style.get("background-color", "transparent")
    if bgcolor != "transparent":
      x2, y2 = self.x + self.width, self.y + self.height
      rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
      cmds.append(rect)
    if self.layout_mode() == "inline":
      for x, y, word, font, color in self.display_list:
        cmds.append(DrawText(x, y, word, font, color))
    return cmds


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

import curses
from asciimatics.effects import Cycle, Snow, Print
from asciimatics.renderers import FigletText, Renderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen

# Tree definition
tree = """
       ${3,1}*
      / \\
     /${1}o${2}  \\
    /_   _\\
     /   \${4}b
    /     \\
   /   ${1}o${2}   \\
  /__     __\\
  ${1}d${2} / ${4}o${2}   \\
   /       \\
  / ${4}o     ${1}o${2}.\\
 /___________\\
      ${3}|||
      ${3}|||
""", """
       ${3}*
      / \\
     /${1}o${2}  \\
    /_   _\\
     /   \${4}b
    /     \\
   /   ${1}o${2}   \\
  /__     __\\
  ${1}d${2} / ${4}o${2}   \\
   /       \\
  / ${4}o     ${1}o${2} \\
 /___________\\
      ${3}|||
      ${3}|||
"""


def demo(win):
    screen = Screen.from_curses(win)
    effects = [
        Print(screen, Renderer(images=tree),
              x=screen.width - 15,
              y=screen.height - 15,
              colour=curses.COLOR_GREEN),
        Snow(screen),
        Cycle(
            screen,
            FigletText("HAPPY"),
            screen.height / 2 - 6,
            start_frame=300),
        Cycle(
            screen,
            FigletText("XMAS!"),
            screen.height / 2 + 1,
            start_frame=300),
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)

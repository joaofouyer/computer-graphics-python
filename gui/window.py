# coding: utf-8
from gui.button import SidebarButton
from gui.clipping import Clipping
from gui.icon import Icon
from gui.sidebar import Sidebar
from structures.action import Action
from structures.import_file import import_json
from structures.export_file import export_json
from primitives.point_graph import PointGraph
from primitives.circle_graph import CircleGraph
from primitives.line_graph import LineGraph
from primitives.rectangle_graph import RectangleGraph
from primitives.polygon_graph import PolygonGraph
from gui.viewport import Viewport
import sys
import os

# Importante para garantir que funcione em python2 e em python3.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info[0] < 3:
    from Tkinter import Tk, Canvas, mainloop, RIGHT
else:
    from tkinter import Tk, Canvas, mainloop, RIGHT, filedialog


class Window:

    def __init__(self, title="PUC-SP", width=500, height=500, background="#ffffff", actions=Action()):
        try:
            commands = {
                "draw_line": self.draw_line,
                "draw_circle": self.draw_circle,
                "draw_rectangle": self.draw_rectangle,
                "draw_polygon": self.draw_polygon,
                "undo": self.undo,
                "redo": self.redo,
                "import_file": self.import_file,
                "export_file": self.export_file,
                "set_clipping_area": self.set_clipping_area
            }

            self.title = title
            self.width = width
            self.height = height
            self.background = background
            self.root = Tk()
            self.root.title(self.title)
            self.root.resizable(width=False, height=False)
            self.canvas_width = self.width
            self.canvas = Canvas(self.root, width=self.canvas_width, height=self.height, bg=self.background)
            self.icon = Icon()
            self.actions = actions
            self.sidebar = Sidebar(height=self.height)
            self.btn = SidebarButton(root=self.root, icons=self.icon, commands=commands)
            self.viewport = Viewport(root=self.root, width=140, height=(self.height*0.15), background=self.background)
            self.viewport.canvas.place(x=5, y=(self.height - self.height*0.17))
            self.clipping = None
            self.clipping_canvas = None
            self.active_draw_mode = None
            self.canvas.old_coords = None

        except Exception as e:
            print("Exception on window constructor: {} {}".format(type(e), e))
            raise e

    def open(self):
        try:
            self.refresh()
            return self.canvas.pack(side=RIGHT)
        except Exception as e:
            print("Exception on open window: {} {}".format(type(e), e))
            raise e

    def mainloop(self):
        try:
            self.open()
            self.canvas.bind('<ButtonPress-1>', self.click_event)
            mainloop()
            return False
        except Exception as e:
            print("Exception on mainloop: {} {}".format(type(e), e))
            raise e

    def update_undo_btn_state(self):
        try:
            if len(self.actions.actions_stack):
                self.btn.undo.config(state="normal")
                self.btn.export.config(state="normal")
            else:
                self.btn.undo.config(state="disabled")
                self.btn.export.config(state="disabled")
            return False
        except Exception as e:
            print("Exception on update undo btn state: {} {}".format(type(e), e))
            raise e

    def update_redo_btn_state(self):
        self.btn.redo.config(state="normal") if len(self.actions.undo_stack) else self.btn.redo.config(state="disabled")
        return False

    def refresh(self):
        try:
            self.update_redo_btn_state()
            self.update_undo_btn_state()
        except Exception as e:
            print("Exception on refresh: {} {}".format(type(e), e))
            raise e

    def undo(self):
        try:
            return self.actions.undo(window=self)
        except Exception as e:
            print("Exception on undo: {} {}".format(type(e), e))
            raise e

    def redo(self):
        try:
            return self.actions.redo(window=self)
        except Exception as e:
            print("Exception on redo: {} {}".format(type(e), e))
            raise e

    def click_event(self, event):
        try:
            point = PointGraph(x=event.x, y=event.y, window=self)
            if self.active_draw_mode == "POINT":
                point.draw(append_action=True)
                self.canvas.old_coords = None
            else:
                if self.canvas.old_coords:
                    p1 = self.canvas.old_coords
                    p2 = point
                    if self.active_draw_mode == "LINE":
                        line = LineGraph(p1=p1, p2=p2)
                        line.draw(window=self, animation=False)
                        self.canvas.old_coords = None
                    elif self.active_draw_mode == "CIRCLE":
                        line = LineGraph(p1=p1, p2=p2)
                        circle = CircleGraph(center=p1, radius=line.length)
                        circle.draw(window=self)
                        self.canvas.old_coords = None
                    elif self.active_draw_mode == "RECTANGLE":
                        rectangle = RectangleGraph(p1=p1, p2=p2)
                        rectangle.draw(window=self)
                        self.canvas.old_coords = None
                    elif self.active_draw_mode == "POLYGON":
                        polygon = self.actions.active_polygon
                        first = polygon.points[0]
                        if first.x - 5 < p2.x < first.x + 5 and first.y - 5 < p2.y < first.y + 5:
                            self.actions.push(polygon)
                            self.canvas.create_rectangle(
                                first.x + 3,
                                first.y + 3,
                                first.x - 3,
                                first.y - 3,
                                outline=self.background
                            )
                            polygon.push(point=first)
                            polygon.draw(window=self, multiple_points=False)
                            polygon.points.pop()
                            self.canvas.old_coords = None

                        else:
                            polygon.push(point=p2)
                            polygon.draw(window=self, multiple_points=False)
                            self.canvas.old_coords = p2

                    elif self.active_draw_mode == "CLIPPING":
                        self.canvas.create_rectangle(
                            self.canvas.old_coords.x + 3,
                            self.canvas.old_coords.y + 3,
                            self.canvas.old_coords.x - 3,
                            self.canvas.old_coords.y - 3,
                            outline=self.background
                        )
                        self.canvas.create_rectangle(
                            self.canvas.old_coords.x,
                            self.canvas.old_coords.y,
                            p2.x,
                            p2.y,
                            outline="#000000",
                            dash=(1, 5)
                        )
                        self.canvas.old_coords = None
                        self.active_draw_mode = None

                        self.clipping = Clipping(
                            root=self.root,
                            min_x=p1.x,
                            min_y=p1.y,
                            max_x=p2.x,
                            max_y=p2.y,
                            background=self.background
                        )

                else:
                    self.canvas.old_coords = point
                    if self.active_draw_mode == "POLYGON":
                        self.actions.active_polygon = PolygonGraph()
                        self.actions.active_polygon.push(point)
                        self.canvas.create_rectangle(point.x+3, point.y+3, point.x-3, point.y-3)

                    elif self.active_draw_mode == "CLIPPING":
                        self.canvas.create_rectangle(point.x + 3, point.y + 3, point.x - 3, point.y - 3)

            return False
        except Exception as e:
            print("Exception on click event: {} {}".format(type(e), e))
            raise e

    def draw_point(self):
        try:
            self.active_draw_mode = "POINT"
            self.canvas.old_coords = None
            return False
        except Exception as e:
            print("Exception on draw point: {} {}".format(type(e), e))
            raise e

    def draw_line(self):
        try:
            self.active_draw_mode = "LINE"
            self.canvas.old_coords = None
            return False
        except Exception as e:
            print("Exception on draw line: {} {}".format(type(e), e))
            raise e

    def draw_circle(self):
        try:
            self.active_draw_mode = "CIRCLE"
            self.canvas.old_coords = None
            return False
        except Exception as e:
            print("Exception on draw circle: {} {}".format(type(e), e))
            raise e

    def draw_rectangle(self):
        try:
            self.active_draw_mode = "RECTANGLE"
            self.canvas.old_coords = None
            return False
        except Exception as e:
            print("Exception on draw rectangle: {} {}".format(type(e), e))
            raise e

    def draw_polygon(self):
        try:
            self.active_draw_mode = "POLYGON"
            self.canvas.old_coords = None
            return False
        except Exception as e:
            print("Exception on draw polygon: {} {}".format(type(e), e))
            raise e

    def import_file(self):
        try:
            filename = filedialog.askopenfilename(
                initialdir=BASE_DIR, title="Selecione o aquivo JSON.",
                filetypes=(("Arquivos JSON", "*.json"), ("todos os arquivos", "*.*"))
            )
            import_json(filename=filename, window=self)
            return False
        except Exception as e:
            print("Exception on import_file: {} {}".format(type(e), e))
            raise e

    def export_file(self):
        try:
            export_json(window=self)
        except Exception as e:
            print("Exception on export_file: {} {}".format(type(e), e))
            raise e

    def set_clipping_area(self):
        try:
            self.active_draw_mode = "CLIPPING"
            self.canvas.old_coords = None
            return False
        except Exception as e:
            print("Exception on set_clipping_area: {} {}".format(type(e), e))
            raise e

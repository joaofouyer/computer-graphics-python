
from math import cos, sin
from primitives.point import Point
from primitives.coordinate import Coordinate


class Circle:

    def __init__(self, center, radius):
        try:
            self.center = Point(coordinate=center)
            self.radius = radius
        except Exception as e:
            print("Circle init: ", e)

    def build_circle_x(self, angle):
            return self.center.x + self.radius * cos(angle)

    def build_circle_y(self, angle):
            return self.center.y + self.radius * sin(angle)

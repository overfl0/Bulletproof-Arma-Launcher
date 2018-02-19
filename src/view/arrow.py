#!/usr/bin/python
# The MIT License (MIT)
# Copyright (c) 2017 "Laxminarayan Kamath G A"<kamathln@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.


from kivy.properties import *
from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.metrics import *
from kivy.graphics import *
import math

piby180 = math.pi / 180.0


# ------------------ KVector -------------------- #

class KVector(EventDispatcher):
    o_x = NumericProperty(0)
    o_y = NumericProperty(0)
    #    to_x = NumericProperty(0)
    #    to_y = NumericProperty(0)
    #    to_pos = ReferenceListProperty(to_x,to_y)
    angle = NumericProperty(0)
    distance = NumericProperty(0)

    #    def get_angle(self):
    #        return ((math.atan2(self.to_x - self.o_x, self.o_y - self.to_y)/piby180)+630.0 ) % 360.0
    #
    #    def set_angle(self,angle):
    #        self.to_x = self.o_x + (math.cos(angle * piby180) * self.distance)
    #        self.to_y = self.o_y + (math.sin(angle * piby180) * self.distance)
    #
    #    def get_distance(self):
    #        absx = abs(self.to_x-self.o_x)
    #        absy = abs(self.to_y-self.o_y)
    #        return math.sqrt((absx*absx)+(absy*absy))
    #
    #    def set_distance(self, distance):
    #        self.to_x = self.o_x + ((math.cos(self.angle * piby180) * distance))
    #        self.to_y = self.o_y + ((math.sin(self.angle * piby180) * distance))
    #
    ##    angle = AliasProperty(
    #                          get_angle,
    #                          set_angle,
    #                          bind=['o_x','o_y','to_x', 'to_y']
    #                         )
    #    distance = AliasProperty(
    #                          get_distance,
    #                          set_distance,
    #                          bind=['o_x','o_y','to_x', 'to_y']
    #                         )
    def get_to_x(self):
        return self.o_x + (math.cos(self.angle * piby180) * self.distance)

    def get_to_y(self):
        return self.o_y + (math.sin(self.angle * piby180) * self.distance)

    def set_to_x(self, to_x):
        self.angle = ((math.atan2(to_x - self.o_x, self.o_y - self.to_y) / piby180) + 630.0) % 360.0
        absx = abs(to_x - self.o_x)
        absy = abs(self.to_y - self.o_y)
        self.distance = math.sqrt((absx * absx) + (absy * absy))

    def set_to_y(self, to_y):
        self.angle = ((math.atan2(self.to_x - self.o_x, self.o_y - to_y) / piby180) + 630.0) % 360.0
        absx = abs(self.to_x - self.o_x)
        absy = abs(to_y - self.o_y)
        self.distance = math.sqrt((absx * absx) + (absy * absy))

    to_x = AliasProperty(
        get_to_x,
        set_to_x,
        bind=['o_x', 'o_y', 'angle', 'distance']
    )

    to_y = AliasProperty(
        get_to_y,
        set_to_y,
        bind=['o_x', 'o_y', 'angle', 'distance']
    )


def move_point(x, y, angle, distance):
    return (
        x + (math.cos(angle * piby180) * distance),
        y + (math.sin(angle * piby180) * distance)
    )


# ------------ Arrow -------------- #

class Arrow(Widget, KVector):
    head_size = NumericProperty(cm(0.5))
    shaft_width = NumericProperty(cm(0.05))
    fletching_radius = NumericProperty(cm(0.1))
    main_color = ListProperty([1, 1, 1, 0.7])
    outline_color = ListProperty([0, 0, 0, 0.7])
    outline_width = NumericProperty(cm(0.01))
    head_angle = NumericProperty(45)

    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        KVector.__init__(self, *args, **kwargs)

        with self.canvas:
            self.icolor = Color(rgba=self.main_color)
            self.head = Mesh(mode='triangle_fan', indices=[0, 1, 2])
            self.shaft = Line(width=self.shaft_width)
            self.fletching = Ellipse()

            self.ocolor = Color(rgba=self.outline_color)
            self.head_outline = Line(width=self.outline_width)
            self.shaft_outline_left = Line(width=self.outline_width)
            self.shaft_outline_right = Line(width=self.outline_width)
            self.fletching_outline = Line()

        self.bind(
            o_x=self.update_dims,
            o_y=self.update_dims,
            to_x=self.update_dims,
            to_y=self.update_dims,
            head_size=self.update_dims,
            shaft_width=self.update_shaft_width,
            outline_color=self.update_outline_color,
            main_color=self.update_color,
            outline_width=self.update_outline_width,
        )
        self.update_dims()
        self.update_shaft_width()
        self.update_color()

    def update_shaft_width(self, *args):
        self.shaft.width = self.shaft_width

    def update_outline_width(self, *args):
        self.shaft_outline_right.width = self.outline_width
        self.shaft_outline_left.width = self.outline_width
        self.head_outline.width = self.outline_width

    def update_outline_color(self, *args):
        self.ocolor.rgba = self.outline_color

    def update_color(self, *args):
        self.icolor.rgba = self.main_color

    def update_dims(self, *args):
        shaft_x1, shaft_y1 = move_point(self.o_x, self.o_y, self.angle, self.fletching_radius / math.sqrt(2))
        #shaft_x2, shaft_y2 = move_point(self.to_x, self.to_y, self.angle, -self.head_size / math.sqrt(2.0))
        shaft_x2, shaft_y2 = move_point(self.to_x, self.to_y, self.angle, - math.cos(self.head_angle * piby180) * self.head_size)
        self.shaft.bezier = [
            shaft_x1,
            shaft_y1,
            (shaft_x1 + shaft_x2) / 2 + 0,
            (shaft_y1 + shaft_y2) / 2 + 40,
            shaft_x2,
            shaft_y2
        ]
        shaft_ol_x1, shaft_ol_y1 = move_point(shaft_x1, shaft_y1, self.angle - 90, self.shaft_width / 0.6)
        shaft_ol_x2, shaft_ol_y2 = move_point(shaft_x2, shaft_y2, self.angle - 90, self.shaft_width / 0.6)

        shaft_or_x1, shaft_or_y1 = move_point(shaft_x1, shaft_y1, self.angle + 90, self.shaft_width / 0.6)
        shaft_or_x2, shaft_or_y2 = move_point(shaft_x2, shaft_y2, self.angle + 90, self.shaft_width / 0.6)

        self.shaft_outline_left.bezier = [
            shaft_ol_x1,
            shaft_ol_y1,
            (shaft_ol_x1 + shaft_ol_x2) / 2 + 0,
            (shaft_ol_y1 + shaft_ol_y2) / 2 + 40,
            shaft_ol_x2,
            shaft_ol_y2,
        ]

        self.shaft_outline_right.bezier = [
            shaft_or_x1,
            shaft_or_y1,
            (shaft_or_x1 + shaft_or_x2) / 2 + 0,
            (shaft_or_y1 + shaft_or_y2) / 2 + 40,
            shaft_or_x2,
            shaft_or_y2,
        ]
        head_x1, head_y1 = move_point(self.to_x, self.to_y, self.angle + (180 - self.head_angle), self.head_size)
        head_x2, head_y2 = move_point(self.to_x, self.to_y, self.angle - (180 - self.head_angle), self.head_size)
        self.head.vertices = [
            self.to_x,
            self.to_y,
            0,
            0,
            head_x1,
            head_y1,
            0,
            0,
            head_x2,
            head_y2,
            0,
            0,
        ]

        self.head_outline.points = [
            self.to_x,
            self.to_y,
            head_x1,
            head_y1,
            head_x2,
            head_y2,
            self.to_x,
            self.to_y
        ]

        self.fletching.pos = move_point(self.o_x,
                                        self.o_y,
                                        225,
                                        self.fletching_radius)

        self.fletching.size = [self.fletching_radius * math.sqrt(2)] * 2
        self.fletching_outline.ellipse = (
            self.fletching.pos[0],
            self.fletching.pos[1],
            self.fletching_radius * math.sqrt(2),
            self.fletching_radius * math.sqrt(2),
        )

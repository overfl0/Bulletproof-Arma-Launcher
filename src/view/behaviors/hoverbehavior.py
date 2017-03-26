# Bulletproof Arma Launcher
# Copyright (C) 2016 Lukasz Taczuk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from __future__ import unicode_literals

from kivy.properties import BooleanProperty
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView

class HoverBehavior(object):
    """This whole class is a joke. Any normal UI library would have this
    functionality already built in by default.

    But not Kivy. Why?
    Supposedly a hover event on buttons is too niche in 2017...
    Don't know. Ask the Kivy devs!
    """

    mouse_hover = BooleanProperty(False)

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def point_visible(self, window_pos):
        """Check if the given point is in the visible region of all the parent
        widgets that are ScrollViews.

        Because Kivy devs can't be bothered to implement that themselves, huh?

        Nah, that's a TOTALLY not needed feature. Who in their right mind would
        ever want to know if you are hovering a VISIBLE button?!?
        """

        widget = self

        # Move up the parent tree and check all the ScrollView visibility
        while widget.parent is not None and widget.parent != widget:
            widget = widget.parent

            if issubclass(widget.__class__, ScrollView):
                # Check if the pointed pixel lies in the area that is visible
                widget_pos = widget.to_widget(*window_pos)
                widget_scroll_pos = widget.convert_distance_to_scroll(*widget_pos)

                widget_pos2 = widget_pos[0] - widget.width, widget_pos[1] - widget.height
                widget_scroll2 = widget.convert_distance_to_scroll(*widget_pos2)

                if (
                   widget_scroll_pos[0] >= widget.scroll_x and widget_scroll2[0] <= widget.scroll_x and
                   widget_scroll_pos[1] >= widget.scroll_y and widget_scroll2[1] <= widget.scroll_y
                   ):
                    # We're inside a visible area
                    continue

                else:
                    # We're inside an invisible area
                    return False

        return True

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return

        window_pos = args[1]
        widget_pos = self.to_widget(*window_pos)
        parent_pos = self.to_parent(*widget_pos)

        if self.collide_point(*parent_pos) and self.point_visible(window_pos):
            self.mouse_hover = True

        else:
            self.mouse_hover = False

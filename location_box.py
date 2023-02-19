import numpy as np


class LocationBox:
    def __init__(self, left=0, top=0, width=0, height=0, box=None, _box=None):
        if box:
            left = box.left
            top = box.top
            width = box.width
            height = box.height
        elif _box:
            left = _box._left
            top = _box._top
            width = _box._width
            height = _box._height

        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def to_array(self):
        return [self.left, self.top, self.width, self.height]

    def to_bounding(self):
        return [self.left, self.top, self.left+self.width, self.top+self.height]

    def translate(self, x, y):
        return LocationBox(self.left+x, self.top+y, self.width, self.height)

    def coord(self):
        return np.array([self.left, self.top])

    def size(self):
        return np.array([self.width, self.height])

    def stretch(self, value, axis=0, direction="right", in_place=False):
        new_box = LocationBox(box=self)
        if axis == 0:
            new_box.width += value
            if direction == "left":
                new_box.left -= value
        elif axis == 1:
            new_box.height += value
            if direction == "up":
                new_box.top -= value

        if in_place:
            if axis == 0:
                new_box.width -= self.width
                if direction == "left":
                    new_box.left -= self.width
                elif direction == "right":
                    new_box.left += self.width

            elif axis == 1:
                new_box.height -= self.height
                if direction == "up":
                    new_box.top -= self.height
                elif direction == "down":
                    new_box.top += self.height

        return new_box

    def __repr__(self):
        return f'LocationBox(left={self.left}, top={self.top}, width={self.width}, height={self.height})'

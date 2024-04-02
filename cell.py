'''
This file defines the Cell class, which represents a single cell in the cellular automaton.
'''
import random
import logging
class Cell:
    def __init__(self, color=None, is_new=True, is_ameba=False):
        self.color = color if color else self.random_color()
        self.is_new = is_new
        self.is_ameba = is_ameba  # New attribute to track if the cell is an ameba
    def random_color(self):
        # Generate a random color in hexadecimal format
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    def change_color(self):
        # Change the cell's color to a new random color
        old_color = self.color
        self.color = self.random_color()
        self.is_new = True  # Mark the cell as new after changing color
        logging.info(f'Cell color changed from {old_color} to {self.color}')
    def combine(self, other):
        # Combine this cell with another cell if they are both new
        if self.is_new and other.is_new:
            new_color = self.random_color()
            while new_color == self.color or new_color == other.color:  # Ensure the new color is different from both cells
                new_color = self.random_color()
            self.color = new_color
            other.color = new_color
            self.is_new = False  # The cell is no longer new after combining
            other.is_new = False  # The other cell is no longer new after combining
            self.is_ameba = True  # The cell becomes an ameba after combining
            other.is_ameba = True  # The other cell also becomes an ameba
            logging.info(f'Cells combined to form new color {self.color} and evolved into amoebas')
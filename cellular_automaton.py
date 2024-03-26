'''
This file defines the CellularAutomaton class, which manages the grid of cells and applies the rules of natural selection.
'''
from cell import Cell
class CellularAutomaton:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell() for _ in range(width)] for _ in range(height)]
    def step(self):
        # Apply the rules of natural selection to the grid
        # First, mark all cells as new
        for row in self.grid:
            for cell in row:
                cell.is_new = True
        # Change the color of all cells
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x].change_color()
        # Then, try to combine cells with their neighbors
        for y in range(self.height):
            for x in range(self.width):
                current_cell = self.grid[y][x]
                # Check right neighbor
                if x < self.width - 1:
                    self.try_combine(current_cell, self.grid[y][x + 1])
                # Check bottom neighbor
                if y < self.height - 1:
                    self.try_combine(current_cell, self.grid[y + 1][x])
                # Check bottom-right neighbor
                if x < self.width - 1 and y < self.height - 1:
                    self.try_combine(current_cell, self.grid[y + 1][x + 1])
                # Check bottom-left neighbor
                if x > 0 and y < self.height - 1:
                    self.try_combine(current_cell, self.grid[y + 1][x - 1])
    def try_combine(self, cell1, cell2):
        # Helper function to try to combine two adjacent cells of the same color
        if cell1.color == cell2.color:
            cell1.combine(cell2)
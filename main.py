'''
This file defines the Application class that creates the GUI for the cellular automaton and the main function to run the application.
'''
import tkinter as tk
from cellular_automaton import CellularAutomaton
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.automaton = CellularAutomaton(50, 50)
        self.running = False
    def create_widgets(self):
        # Create the canvas and step button
        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack()
        self.step_button = tk.Button(self, text="Step", command=self.step)
        self.step_button.pack(side="bottom")
        # Add a speed control slider
        self.speed_slider = tk.Scale(self, from_=0.01, to=1.0, resolution=0.01, orient='horizontal', label='Speed')
        self.speed_slider.set(0.5)  # Default speed
        self.speed_slider.pack(side="bottom")
        # Add a play button
        self.play_button = tk.Button(self, text="Play", command=self.play)
        self.play_button.pack(side="bottom")
        # Add a stop button
        self.stop_button = tk.Button(self, text="Stop", command=self.stop)
        self.stop_button.pack(side="bottom")
    def play(self):
        # Start the simulation
        if not self.running:
            self.running = True
            self.play_button.config(state='disabled')  # Disable the play button while running
            self.stop_button.config(state='normal')  # Enable the stop button
            self.run_simulation()
    def run_simulation(self):
        # Run the simulation steps in a loop until stopped
        if self.running:
            self.step()
            # Schedule the next step after a delay based on the speed slider
            self.canvas.after(int(self.speed_slider.get() * 1000), self.run_simulation)
    def stop(self):
        # Stop the simulation
        self.running = False
        self.play_button.config(state='normal')  # Re-enable the play button
        self.stop_button.config(state='disabled')  # Disable the stop button
    def step(self):
        # Perform one step in the automaton and update the canvas
        self.automaton.step()
        self.update_canvas()
    def update_canvas(self):
        # Update the canvas with the new colors of the cells
        cell_width = 500 / self.automaton.width
        cell_height = 500 / self.automaton.height
        self.canvas.delete("all")  # Clear the canvas before redrawing
        for y in range(self.automaton.height):
            for x in range(self.automaton.width):
                cell = self.automaton.grid[y][x]
                x1 = x * cell_width
                y1 = y * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height
                if cell.is_ameba:
                    # Draw an oval for amebas
                    self.canvas.create_oval(x1, y1, x2, y2, fill=cell.color, outline="")
                else:
                    # Draw a rectangle for normal cells
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=cell.color, outline="")
def main():
    # Create the main window and run the application
    root = tk.Tk()
    app = Application(master=root)
    root.protocol("WM_DELETE_WINDOW", app.stop)  # Handle window closing
    app.mainloop()
if __name__ == "__main__":
    main()
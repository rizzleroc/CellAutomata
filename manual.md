# Cellular Automaton Natural Selection Simulator

A simple and interactive simulation of natural selection using cellular automata.

## Quick Install

No external dependencies are required for this project. The project is compatible with Python 3.1 and above due to the use of tkinter.

To run the simulation, ensure you have Python installed on your system. You can download Python from the official website: [Python.org](https://www.python.org/downloads/)

Once Python is installed, you can download the source code files (`cell.py`, `cellular_automaton.py`, and `main.py`) from the provided repository or copy the code into local files.

## 🌱 What is this?

This cellular automaton simulates natural selection through simple rules that govern the behavior of cells on a grid. Cells change colors, combine to form new colors, and evolve into amebas based on the following rules:

1. Each cell takes on a random color.
2. Two adjacent cells of the same color can combine to create a new color.
3. A new cell can only combine with other new cells of any color.
4. When a new cell combines, it becomes an ameba.

The simulation includes a speed control slider and play/stop buttons to control the animation.

## 🚀 Getting Started

### Installation

No additional installation steps are required beyond having Python installed on your system.

### Running the Simulation

1. Open your terminal or command prompt.
2. Navigate to the directory where you saved the source code files.
3. Run the simulation by executing the following command:

```bash
python main.py
```

This will open a new window with the cellular automaton simulation.

## 🎮 How to Use/Play

Once the simulation window is open, you can interact with the simulation using the following controls:

- **Step Button**: Advances the simulation by one step.
- **Play Button**: Starts the continuous animation of the simulation.
- **Stop Button**: Stops the continuous animation.
- **Speed Slider**: Adjusts the speed of the animation when the simulation is playing.

Cells will automatically change color and combine according to the rules of the simulation. Amebas are represented as ovals, while regular cells are rectangles.

## 📝 Notes

- The simulation is designed to be a simple representation of natural selection principles.
- The grid size and canvas dimensions are set within the code and can be adjusted by modifying the `CellularAutomaton` class instantiation in `main.py`.
- The colors are randomly generated, and the combination of cells results in new colors that are also randomly chosen.

Enjoy exploring the dynamics of natural selection with this interactive cellular automaton simulator!
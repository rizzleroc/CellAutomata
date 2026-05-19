"""Inline tutorial copy for the GUI's Help > Start tutorial flow."""

TUTORIAL_STEPS: tuple[str, ...] = (
    "Welcome to cellauto. The grid above runs whichever rule you pick from the top-left dropdown.",
    "Rule 1 (color propagation): every step, each non-amoeba cell takes the color of a random neighbor. Watch the colors flow.",
    "Rule 2 (combination): when two adjacent cells share a color AND both just changed, they combine. The 16-color palette means this fires regularly.",
    "Rule 3 (newness): only cells that just got a new color in this step are eligible to combine. Settled cells must wait for color flow to reach them.",
    "Rule 4 (amoeba lifecycle): a combined pair turns into an oval amoeba with a fresh color. Amoebas stop changing color and die after 25 steps, freeing space for new cells.",
    "Try the Conway rule for the classic Game of Life, or Wolfram 1D to watch rule-30 chaos scroll up the grid.",
    "Use Record GIF to capture a clip of the live sim, or File > Save snapshot to freeze a state and reload it later. Press Tutorial again to dismiss this overlay.",
)

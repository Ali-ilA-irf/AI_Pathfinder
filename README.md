AI Pathfinder - Uninformed Search Visualization

A Python GUI application that visualizes six uninformed search algorithms navigating a grid. Users can interactively explore paths, compare algorithm performance, and view real-time statistics.

Features

Algorithms: BFS, DFS, UCS, DLS, IDDFS, Bidirectional Search

Visualization: Step-by-step animation of algorithm exploration

Movement: 8-directional (including diagonals)

Controls: Start, Pause/Resume, Reset, Clear Path

Statistics: Nodes explored, path length, frontier size, search time

Installation

Requirements: Python 3.8+, pip

# Clone the repository
git clone https://github.com/yourusername/ai-pathfinder.git
cd ai-pathfinder

# Install dependencies
pip install -r requirements.txt
# Or manually
pip install pygame

# Run the app
python ai_pathfinder_gui.py

Usage

Green Cell: Start position

Red Cell: Target position

Select an algorithm from the buttons

Start, Pause/Resume, Reset, or Clear Path to control visualization

Grid & Visualization Colors
Color	Meaning
Green	Start
Red	Target

Purple	Explored nodes
Blue	Frontier nodes
Yellow	Final path

Customization (in ai_pathfinder_gui.py)
GRID_SIZE = 20                  # Number of cells
step_delay = 50                 # Visualization speed in ms
dls_limit = 20                  # Depth limit for DLS

Algorithm Comparison
Algorithm	Complete?	Optimal?	Time Complexity	Space Complexity
BFS	✅	✅	O(b^d)	O(b^d)
DFS	✅	❌	O(b^m)	O(bm)
UCS	✅	✅	O(b^(C*/ε))	O(b^(C*/ε))
DLS	❌	❌	O(b^l)	O(bl)
IDDFS	✅	✅	O(b^d)	O(bd)
Bidirectional	✅	✅	O(b^(d/2))	O(b^(d/2))

b = branching factor, d = depth of solution, m = max depth, l = depth limit, C = optimal cost, ε = minimum cost*

Troubleshooting

App won’t start:

pip uninstall pygame
pip install pygame


Slow performance: Reduce GRID_SIZE, increase step_delay, or reduce dynamic_obstacle_probability

License

MIT License

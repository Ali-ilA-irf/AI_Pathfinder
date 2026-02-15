AI Pathfinder - Uninformed Search Visualization
GOOD PERFORMANCE TIME APP
A Python GUI application that visualizes 6 uninformed search algorithms navigating a grid with dynamic
obstacles.
Features
Algorithms Implemented: - BFS, DFS, UCS, DLS, IDDFS, Bidirectional Search
Key Features: - Step-by-step visualization of algorithms - 8-directional movement with diagonals - Dynamic
obstacles spawning during search - Interactive grid: click to add/remove walls - Pause/Resume, Reset, and
Clear Path controls - Real-time statistics: nodes explored, path length, time
Installation
Prerequisites: Python 3.8+, pip
# Clone the repository
git clone https://github.com/yourusername/ai-pathfinder.git
cd ai-pathfinder
# Install dependencies
pip install -r requirements.txt
# Or manually
pip install pygame
# Run the app
python ai_pathfinder_gui.py
Controls
Left Click: Toggle walls
Green Cell: Start
Red Cell: Target
Black Cells: Static walls
Dark Red: Dynamic obstacles
•
•
•
•
•
1
Algorithm Selection: Click buttons at top
Start / Pause / Resume / Reset / Clear Path
Grid & Visualization
Colors: | Color | Meaning | |-------|---------| | Green | Start | | Red | Target | | Black | Static walls | | Purple
| Explored nodes | | Blue | Frontier nodes | | Yellow | Final path | | Dark Red | Dynamic obstacles |
Stats Panel: Nodes Explored, Frontier Size, Path Length, Time
Parameters (Customizable in ai_pathfinder_gui.py )
GRID_SIZE = 25 # Grid cells
step_delay = 50 # Visualization speed (ms)
dynamic_obstacle_probability = 0.01
dls_limit = 10 # Depth limit for DLS
Algorithm Comparison
Algorithm Complete? Optimal? Time Complexity Space Complexity
BFS Yes Yes O(b^d) O(b^d)
DFS Yes No O(b^m) O(bm)
UCS Yes Yes O(b^(C*/ε)) O(b^(C*/ε))
DLS No No O(b^l) O(bl)
IDDFS Yes Yes O(b^d) O(bd)
Bidirectional Yes Yes O(b^(d/2)) O(b^(d/2))
Troubleshooting
App won’t start:
pip uninstall pygame
pip install pygame
•
•
•
2
Slow performance: Reduce GRID_SIZE , increase step_delay , reduce
dynamic_obstacle_probability
License
MIT License

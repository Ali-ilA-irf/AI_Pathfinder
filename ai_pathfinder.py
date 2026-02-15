"""
AI Pathfinder - Uninformed Search Visualization (IMPROVED VERSION)
GOOD PERFORMANCE TIME APP

Movement: 6 DIRECTIONS (Up, Right, Bottom, Bottom-Right, Left, Top-Left)
Note: Top-Right and Bottom-Left diagonals NOT included as per assignment

Improvements:
- More visible dynamic obstacles (higher probability + animation)
- Better start/goal distance (opposite corners)
- Fixed DFS/DLS algorithms
- Better visualization and debugging
- Adjustable parameters in UI
"""

import pygame
import random
import time
from collections import deque
import heapq
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200  # Reduced from 1400
WINDOW_HEIGHT = 800  # Increased to fit mode buttons
GRID_SIZE = 25  # Increased from 25 to 30
CELL_SIZE = 20  # Reduced from 22 to fit better
INFO_PANEL_WIDTH = 350  # Reduced from 400
CONTROL_PANEL_HEIGHT = 150

# Colors - Modern Color Scheme
COLOR_BG = (15, 23, 42)
COLOR_GRID = (30, 41, 59)
COLOR_EMPTY = (51, 65, 85)
COLOR_WALL = (30, 30, 30)
COLOR_START = (34, 197, 94)
COLOR_TARGET = (239, 68, 68)
COLOR_FRONTIER = (59, 130, 246)
COLOR_EXPLORED = (168, 85, 247)
COLOR_PATH = (250, 204, 21)
COLOR_DYNAMIC_OBSTACLE = (239, 68, 68)  # Bright red - more visible
COLOR_DYNAMIC_GLOW = (255, 100, 100)  # Glow effect
COLOR_TEXT = (248, 250, 252)
COLOR_BUTTON = (71, 85, 105)
COLOR_BUTTON_HOVER = (100, 116, 139)
COLOR_BUTTON_ACTIVE = (34, 197, 94)
COLOR_WARNING = (251, 146, 60)  # Orange for warnings

# Algorithm names
ALGORITHMS = ["BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional"]

# Movement directions - STRICT ORDER from assignment (6 DIRECTIONS ONLY)
# Order: Up, Right, Bottom, Bottom-Right, Left, Top-Left
# NOTE: "Do not check Top-Right or Bottom-Left diagonals"
DIRECTIONS = [
    (-1, 0),   # 1. Up
    (0, 1),    # 2. Right
    (1, 0),    # 3. Bottom
    (1, 1),    # 4. Bottom-Right (Main Diagonal)
    (0, -1),   # 5. Left
    (-1, -1),  # 6. Top-Left (Main Diagonal)
]
# Top-Right (-1, 1) and Bottom-Left (1, -1) are NOT included

class Node:
    """Represents a node in the grid"""
    def __init__(self, row, col, cost=0, parent=None):
        self.row = row
        self.col = col
        self.cost = cost
        self.parent = parent
        self.g = 0
        self.h = 0
        
    def __lt__(self, other):
        return self.cost < other.cost
    
    def __eq__(self, other):
        return self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))

class Button:
    """Simple button class"""
    def __init__(self, x, y, width, height, text, font_size=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.active = False
        self.hovered = False
        
    def draw(self, screen):
        color = COLOR_BUTTON_ACTIVE if self.active else (COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2, border_radius=8)
        
        text_surface = self.font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class PathfinderGUI:
    """Main application class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI Pathfinder - GOOD PERFORMANCE TIME APP")
        self.clock = pygame.time.Clock()
        
        # Grid initialization - START and GOAL at OPPOSITE CORNERS
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.start = (1, 1)  # Top-left corner
        self.target = (GRID_SIZE - 2, GRID_SIZE - 2)  # Bottom-right corner
        self.grid[self.start[0]][self.start[1]] = 2
        self.grid[self.target[0]][self.target[1]] = 3
        
        # Add some initial walls (but not too many to block path)
        self.add_random_walls(40)
        
        # Visualization state
        self.frontier = set()
        self.explored = set()
        self.path = []
        self.dynamic_obstacles = {}  # Now stores {position: spawn_time} for animation
        
        # Algorithm state
        self.current_algorithm = 0
        self.running = False
        self.paused = False
        self.step_delay = 30  # Faster for better visualization
        self.dynamic_obstacle_probability = 0.01  # 1% - Back to original
        self.dls_depth_limit = 50  # Increased from 10 to 50
        
        # Statistics
        self.stats = {
            'nodes_explored': 0,
            'path_length': 0,
            'time_elapsed': 0,
            'nodes_in_frontier': 0,
            'dynamic_obstacles_spawned': 0,
            'algorithm_status': 'Ready'
        }
        
        # UI Elements
        self.create_ui_elements()
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Edit Mode - can be 'place_start', 'place_target', 'place_wall', 'erase'
        self.edit_mode = 'place_wall'
        
    def create_ui_elements(self):
        """Create buttons and UI elements"""
        button_y = WINDOW_HEIGHT - 120
        button_width = 100
        button_spacing = 10
        start_x = 20
        
        self.buttons = {
            'start': Button(start_x, button_y, button_width, 40, "Start"),
            'pause': Button(start_x + (button_width + button_spacing), button_y, button_width, 40, "Pause"),
            'reset': Button(start_x + 2 * (button_width + button_spacing), button_y, button_width, 40, "Reset"),
            'clear': Button(start_x + 3 * (button_width + button_spacing), button_y, button_width, 40, "Clear"),
            'walls': Button(start_x + 4 * (button_width + button_spacing), button_y, button_width, 40, "Walls"),
            'speed_up': Button(start_x + 5 * (button_width + button_spacing), button_y, 50, 40, ">>"),
            'speed_down': Button(start_x + 5 * (button_width + button_spacing) + 55, button_y, 50, 40, "<<"),
        }
        
        # Edit mode buttons (Place Start, Place Target, Place Walls, Erase)
        mode_button_y = button_y + 50
        mode_button_width = 100
        self.mode_buttons = {
            'place_start': Button(start_x, mode_button_y, mode_button_width, 35, "Place Start", 18),
            'place_target': Button(start_x + (mode_button_width + button_spacing), mode_button_y, mode_button_width, 35, "Place Target", 18),
            'place_wall': Button(start_x + 2 * (mode_button_width + button_spacing), mode_button_y, mode_button_width, 35, "Place Wall", 18),
            'erase': Button(start_x + 3 * (mode_button_width + button_spacing), mode_button_y, mode_button_width, 35, "Erase", 18),
        }
        # Set default mode
        self.mode_buttons['place_wall'].active = True
        
        # Algorithm buttons
        algo_button_width = 110
        algo_start_x = 20
        algo_y = 40
        self.algo_buttons = []
        for i, algo in enumerate(ALGORITHMS):
            x = algo_start_x + (i % 3) * (algo_button_width + 10)
            y = algo_y if i < 3 else algo_y + 55
            btn = Button(x, y, algo_button_width, 45, algo, 18)
            if i == 0:
                btn.active = True
            self.algo_buttons.append(btn)
    
    def add_random_walls(self, count):
        """Add random walls to the grid"""
        added = 0
        attempts = 0
        max_attempts = count * 3
        
        while added < count and attempts < max_attempts:
            row = random.randint(3, GRID_SIZE - 4)
            col = random.randint(3, GRID_SIZE - 4)
            
            # Don't block start or target area
            if abs(row - self.start[0]) < 3 and abs(col - self.start[1]) < 3:
                attempts += 1
                continue
            if abs(row - self.target[0]) < 3 and abs(col - self.target[1]) < 3:
                attempts += 1
                continue
                
            if self.grid[row][col] == 0:
                self.grid[row][col] = 1
                added += 1
            attempts += 1
    
    def reset_search(self):
        """Reset the search state"""
        self.frontier = set()
        self.explored = set()
        self.path = []
        self.dynamic_obstacles = {}
        self.running = False
        self.paused = False
        self.stats = {
            'nodes_explored': 0,
            'path_length': 0,
            'time_elapsed': 0,
            'nodes_in_frontier': 0,
            'dynamic_obstacles_spawned': 0,
            'algorithm_status': 'Ready'
        }
    
    def clear_path(self):
        """Clear only the path visualization"""
        self.frontier = set()
        self.explored = set()
        self.path = []
        self.dynamic_obstacles = {}
        self.stats['nodes_explored'] = 0
        self.stats['path_length'] = 0
        self.stats['time_elapsed'] = 0
        self.stats['nodes_in_frontier'] = 0
        self.stats['dynamic_obstacles_spawned'] = 0
        self.stats['algorithm_status'] = 'Ready'
    
    def is_valid(self, row, col):
        """Check if a cell is valid and not blocked"""
        if row < 0 or row >= GRID_SIZE or col < 0 or col >= GRID_SIZE:
            return False
        if self.grid[row][col] == 1:
            return False
        if (row, col) in self.dynamic_obstacles:
            return False
        return True
    
    def get_neighbors(self, node):
        """Get valid neighbors of a node"""
        neighbors = []
        for dr, dc in DIRECTIONS:
            new_row, new_col = node.row + dr, node.col + dc
            if self.is_valid(new_row, new_col):
                cost = math.sqrt(2) if abs(dr) + abs(dc) == 2 else 1
                neighbors.append(Node(new_row, new_col, node.cost + cost, node))
        return neighbors
    
    def spawn_dynamic_obstacle(self):
        """Randomly spawn a dynamic obstacle with better visibility"""
        if random.random() < self.dynamic_obstacle_probability:
            attempts = 0
            while attempts < 10:
                row = random.randint(5, GRID_SIZE - 6)
                col = random.randint(5, GRID_SIZE - 6)
                
                # Don't spawn too close to start/goal
                if (abs(row - self.start[0]) > 4 and abs(col - self.start[1]) > 4 and
                    abs(row - self.target[0]) > 4 and abs(col - self.target[1]) > 4):
                    
                    if self.grid[row][col] == 0 and (row, col) not in self.dynamic_obstacles:
                        if (row, col) not in self.explored and (row, col) not in self.frontier:
                            self.dynamic_obstacles[(row, col)] = time.time()
                            self.stats['dynamic_obstacles_spawned'] += 1
                            # Warning message removed
                            return True
                attempts += 1
        return False
    
    def reconstruct_path(self, node):
        """Reconstruct path from start to target"""
        path = []
        current = node
        while current is not None:
            path.append((current.row, current.col))
            current = current.parent
        return path[::-1]
    
    def bfs(self):
        """Breadth-First Search - FIXED"""
        start_time = time.time()
        self.stats['algorithm_status'] = 'Running BFS...'
        
        queue = deque([Node(self.start[0], self.start[1])])
        visited = {self.start}
        
        while queue and self.running:
            self.spawn_dynamic_obstacle()
            
            if self.paused:
                pygame.time.wait(100)
                continue
            
            current = queue.popleft()
            self.explored.add((current.row, current.col))
            self.stats['nodes_explored'] += 1
            
            if (current.row, current.col) == self.target:
                self.path = self.reconstruct_path(current)
                self.stats['path_length'] = len(self.path)
                self.stats['time_elapsed'] = time.time() - start_time
                self.stats['algorithm_status'] = '✓ Path Found!'
                return True
            
            for neighbor in self.get_neighbors(current):
                pos = (neighbor.row, neighbor.col)
                if pos not in visited:
                    visited.add(pos)
                    queue.append(neighbor)
                    self.frontier.add(pos)
            
            # Remove current from frontier
            if (current.row, current.col) in self.frontier:
                self.frontier.remove((current.row, current.col))
            
            self.stats['nodes_in_frontier'] = len(queue)
            self.draw()
            pygame.time.wait(self.step_delay)
        
        self.stats['algorithm_status'] = '✗ No Path Found'
        return False
    
    def dfs(self):
        """Depth-First Search - Properly fixed to avoid long paths"""
        start_time = time.time()
        self.stats['algorithm_status'] = 'Running DFS...'
        
        start_node = Node(self.start[0], self.start[1])
        stack = [start_node]
        visited = {self.start}  # Mark start as visited immediately
        
        while stack and self.running:
            self.spawn_dynamic_obstacle()
            
            if self.paused:
                pygame.time.wait(100)
                continue
            
            current = stack.pop()
            pos = (current.row, current.col)
            
            # Mark as explored for visualization
            self.explored.add(pos)
            self.stats['nodes_explored'] += 1
            
            # Remove from frontier when we explore it
            if pos in self.frontier:
                self.frontier.remove(pos)
            
            # Check if we reached the goal
            if pos == self.target:
                self.path = self.reconstruct_path(current)
                self.stats['path_length'] = len(self.path)
                self.stats['time_elapsed'] = time.time() - start_time
                self.stats['algorithm_status'] = '✓ Path Found!'
                return True
            
            # Get neighbors and add unvisited ones to stack
            neighbors = self.get_neighbors(current)
            
            # Add neighbors to stack in REVERSE order
            # Mark them as visited IMMEDIATELY when adding to stack
            for neighbor in reversed(neighbors):
                neighbor_pos = (neighbor.row, neighbor.col)
                if neighbor_pos not in visited:
                    visited.add(neighbor_pos)  # Mark as visited NOW
                    stack.append(neighbor)
                    self.frontier.add(neighbor_pos)
            
            self.stats['nodes_in_frontier'] = len(stack)
            self.draw()
            pygame.time.wait(self.step_delay)
        
        self.stats['algorithm_status'] = '✗ No Path Found'
        return False
    
    def ucs(self):
        """Uniform-Cost Search"""
        start_time = time.time()
        self.stats['algorithm_status'] = 'Running UCS...'
        
        heap = [Node(self.start[0], self.start[1], 0)]
        visited = {self.start: 0}
        
        while heap and self.running:
            self.spawn_dynamic_obstacle()
            
            if self.paused:
                pygame.time.wait(100)
                continue
            
            current = heapq.heappop(heap)
            pos = (current.row, current.col)
            
            if pos in self.explored:
                continue
                
            self.explored.add(pos)
            self.stats['nodes_explored'] += 1
            
            if pos == self.target:
                self.path = self.reconstruct_path(current)
                self.stats['path_length'] = len(self.path)
                self.stats['time_elapsed'] = time.time() - start_time
                self.stats['algorithm_status'] = '✓ Path Found!'
                return True
            
            for neighbor in self.get_neighbors(current):
                neighbor_pos = (neighbor.row, neighbor.col)
                if neighbor_pos not in visited or neighbor.cost < visited[neighbor_pos]:
                    visited[neighbor_pos] = neighbor.cost
                    heapq.heappush(heap, neighbor)
                    self.frontier.add(neighbor_pos)
            
            if pos in self.frontier:
                self.frontier.remove(pos)
            
            self.stats['nodes_in_frontier'] = len(heap)
            self.draw()
            pygame.time.wait(self.step_delay)
        
        self.stats['algorithm_status'] = '✗ No Path Found'
        return False
    
    def dls(self, limit=None):
        """Depth-Limited Search - FIXED with proper depth tracking"""
        if limit is None:
            limit = self.dls_depth_limit
            
        start_time = time.time()
        self.stats['algorithm_status'] = f'Running DLS (limit={limit})...'
        
        def dls_recursive(node, depth, visited):
            if not self.running:
                return None
            
            self.spawn_dynamic_obstacle()
            
            if self.paused:
                while self.paused and self.running:
                    pygame.time.wait(100)
                    pygame.event.pump()
            
            pos = (node.row, node.col)
            
            # Mark as explored
            if pos not in self.explored:
                self.explored.add(pos)
                self.stats['nodes_explored'] += 1
            
            # Check if goal
            if pos == self.target:
                return node
            
            # Check depth limit
            if depth >= limit:
                return None
            
            # Explore neighbors
            for neighbor in self.get_neighbors(node):
                neighbor_pos = (neighbor.row, neighbor.col)
                if neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    self.frontier.add(neighbor_pos)
                    self.draw()
                    pygame.time.wait(self.step_delay)
                    
                    result = dls_recursive(neighbor, depth + 1, visited)
                    if result is not None:
                        return result
                    
                    # Remove from frontier if not solution
                    if neighbor_pos in self.frontier:
                        self.frontier.remove(neighbor_pos)
            
            return None
        
        visited = {self.start}
        result = dls_recursive(Node(self.start[0], self.start[1]), 0, visited)
        
        if result:
            self.path = self.reconstruct_path(result)
            self.stats['path_length'] = len(self.path)
            self.stats['time_elapsed'] = time.time() - start_time
            self.stats['algorithm_status'] = f'✓ Path Found! (depth={len(self.path)})'
            return True
        
        self.stats['algorithm_status'] = f'✗ No Path (limit={limit} too small)'
        return False
    
    def iddfs(self):
        """Iterative Deepening DFS"""
        start_time = time.time()
        max_depth = GRID_SIZE * 2
        
        for depth_limit in range(1, max_depth):
            self.clear_path()
            self.stats['algorithm_status'] = f'IDDFS: Trying depth {depth_limit}...'
            
            if self.dls(depth_limit):
                self.stats['time_elapsed'] = time.time() - start_time
                self.stats['algorithm_status'] = f'✓ Found at depth {depth_limit}!'
                return True
            
            if not self.running:
                return False
        
        self.stats['algorithm_status'] = '✗ No Path Found'
        return False
    
    def bidirectional_search(self):
        """Bidirectional Search"""
        start_time = time.time()
        self.stats['algorithm_status'] = 'Running Bidirectional...'
        
        forward_queue = deque([Node(self.start[0], self.start[1])])
        forward_visited = {self.start: Node(self.start[0], self.start[1])}
        
        backward_queue = deque([Node(self.target[0], self.target[1])])
        backward_visited = {self.target: Node(self.target[0], self.target[1])}
        
        while forward_queue and backward_queue and self.running:
            self.spawn_dynamic_obstacle()
            
            if self.paused:
                pygame.time.wait(100)
                continue
            
            # Expand from start
            if forward_queue:
                current_forward = forward_queue.popleft()
                pos_forward = (current_forward.row, current_forward.col)
                self.explored.add(pos_forward)
                self.stats['nodes_explored'] += 1
                
                if pos_forward in backward_visited:
                    forward_path = self.reconstruct_path(current_forward)
                    backward_node = backward_visited[pos_forward]
                    backward_path = self.reconstruct_path(backward_node)
                    self.path = forward_path + backward_path[::-1][1:]
                    self.stats['path_length'] = len(self.path)
                    self.stats['time_elapsed'] = time.time() - start_time
                    self.stats['algorithm_status'] = '✓ Paths Met!'
                    return True
                
                for neighbor in self.get_neighbors(current_forward):
                    neighbor_pos = (neighbor.row, neighbor.col)
                    if neighbor_pos not in forward_visited:
                        forward_visited[neighbor_pos] = neighbor
                        forward_queue.append(neighbor)
                        self.frontier.add(neighbor_pos)
            
            # Expand from target
            if backward_queue:
                current_backward = backward_queue.popleft()
                pos_backward = (current_backward.row, current_backward.col)
                self.explored.add(pos_backward)
                self.stats['nodes_explored'] += 1
                
                if pos_backward in forward_visited:
                    forward_node = forward_visited[pos_backward]
                    forward_path = self.reconstruct_path(forward_node)
                    backward_path = self.reconstruct_path(current_backward)
                    self.path = forward_path + backward_path[::-1][1:]
                    self.stats['path_length'] = len(self.path)
                    self.stats['time_elapsed'] = time.time() - start_time
                    self.stats['algorithm_status'] = '✓ Paths Met!'
                    return True
                
                for neighbor in self.get_neighbors(current_backward):
                    neighbor_pos = (neighbor.row, neighbor.col)
                    if neighbor_pos not in backward_visited:
                        backward_visited[neighbor_pos] = neighbor
                        backward_queue.append(neighbor)
                        self.frontier.add(neighbor_pos)
            
            self.stats['nodes_in_frontier'] = len(forward_queue) + len(backward_queue)
            self.draw()
            pygame.time.wait(self.step_delay)
        
        self.stats['algorithm_status'] = '✗ No Path Found'
        return False
    
    def run_algorithm(self):
        """Run the selected algorithm"""
        algorithm_name = ALGORITHMS[self.current_algorithm]
        self.clear_path()
        self.running = True
        
        success = False
        if algorithm_name == "BFS":
            success = self.bfs()
        elif algorithm_name == "DFS":
            success = self.dfs()
        elif algorithm_name == "UCS":
            success = self.ucs()
        elif algorithm_name == "DLS":
            success = self.dls()
        elif algorithm_name == "IDDFS":
            success = self.iddfs()
        elif algorithm_name == "Bidirectional":
            success = self.bidirectional_search()
        
        self.running = False
        return success
    
    def draw_grid(self):
        """Draw the grid with animated dynamic obstacles"""
        grid_offset_x = 50
        grid_offset_y = 150
        current_time = time.time()
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = grid_offset_x + col * CELL_SIZE
                y = grid_offset_y + row * CELL_SIZE
                
                pos = (row, col)
                
                # Animated dynamic obstacles
                if pos in self.dynamic_obstacles:
                    spawn_time = self.dynamic_obstacles[pos]
                    age = current_time - spawn_time
                    
                    # Pulse effect
                    pulse = abs(math.sin(age * 3))
                    color_r = int(239 + (255 - 239) * pulse)
                    color_g = int(68 + (100 - 68) * pulse)
                    color_b = int(68 + (100 - 68) * pulse)
                    color = (color_r, color_g, color_b)
                    
                    # Draw with glow
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    pygame.draw.rect(self.screen, COLOR_DYNAMIC_GLOW, (x, y, CELL_SIZE - 1, CELL_SIZE - 1), 2)
                    
                elif pos == self.start:
                    color = COLOR_START
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    # Draw "S"
                    text = self.small_font.render("S", True, COLOR_TEXT)
                    self.screen.blit(text, (x + CELL_SIZE//2 - 5, y + CELL_SIZE//2 - 8))
                    
                elif pos == self.target:
                    color = COLOR_TARGET
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    # Draw "T"
                    text = self.small_font.render("T", True, COLOR_TEXT)
                    self.screen.blit(text, (x + CELL_SIZE//2 - 5, y + CELL_SIZE//2 - 8))
                    
                elif pos in self.path:
                    color = COLOR_PATH
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    
                elif pos in self.explored:
                    color = COLOR_EXPLORED
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    
                elif pos in self.frontier:
                    color = COLOR_FRONTIER
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    
                elif self.grid[row][col] == 1:
                    color = COLOR_WALL
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                    
                else:
                    color = COLOR_EMPTY
                    pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))
                
                # Grid lines
                pygame.draw.rect(self.screen, COLOR_GRID, (x, y, CELL_SIZE - 1, CELL_SIZE - 1), 1)
    
    def draw_info_panel(self):
        """Draw the information panel"""
        panel_x = 50 + GRID_SIZE * CELL_SIZE + 30
        panel_y = 150
        
        # Title
        title = self.title_font.render("Statistics", True, COLOR_TEXT)
        self.screen.blit(title, (panel_x, panel_y))
        
        # Algorithm name
        algo_name = self.info_font.render(f"Algorithm: {ALGORITHMS[self.current_algorithm]}", True, COLOR_TEXT)
        self.screen.blit(algo_name, (panel_x, panel_y + 50))
        
        # Status
        status_color = COLOR_WARNING if '⚠️' in self.stats['algorithm_status'] else COLOR_TEXT
        status = self.small_font.render(f"Status: {self.stats['algorithm_status']}", True, status_color)
        self.screen.blit(status, (panel_x, panel_y + 80))
        
        # Stats
        stats_y = panel_y + 120
        line_height = 30
        
        stats_text = [
            f"Nodes Explored: {self.stats['nodes_explored']}",
            f"Frontier Size: {self.stats['nodes_in_frontier']}",
            f"Path Length: {self.stats['path_length']}",
            f"Time: {self.stats['time_elapsed']:.3f}s",
            f"Dynamic Obstacles: {self.stats['dynamic_obstacles_spawned']}",
            f"Speed: {self.step_delay}ms",
            f"DLS Depth Limit: {self.dls_depth_limit}",
        ]
        
        for i, text in enumerate(stats_text):
            surface = self.small_font.render(text, True, COLOR_TEXT)
            self.screen.blit(surface, (panel_x, stats_y + i * line_height))
        
        # Legend (removed dynamic obstacle explanation)
        legend_y = stats_y + len(stats_text) * line_height + 30
        legend_title = self.info_font.render("Legend:", True, COLOR_TEXT)
        self.screen.blit(legend_title, (panel_x, legend_y))
        
        legend_items = [
            ("Start (S)", COLOR_START),
            ("Target (T)", COLOR_TARGET),
            ("Wall", COLOR_WALL),
            ("Frontier", COLOR_FRONTIER),
            ("Explored", COLOR_EXPLORED),
            ("Path", COLOR_PATH),
            ("Dynamic!", COLOR_DYNAMIC_OBSTACLE),
        ]
        
        for i, (label, color) in enumerate(legend_items):
            y = legend_y + 30 + i * 25
            pygame.draw.rect(self.screen, color, (panel_x, y, 20, 20))
            text = self.small_font.render(label, True, COLOR_TEXT)
            self.screen.blit(text, (panel_x + 25, y + 2))
    
    def draw(self):
        """Main draw function"""
        self.screen.fill(COLOR_BG)
        
        # Draw title
        title = self.title_font.render("AI Pathfinder - GOOD PERFORMANCE TIME APP", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 10))
        
        # Draw algorithm buttons
        for button in self.algo_buttons:
            button.draw(self.screen)
        
        # Draw grid
        self.draw_grid()
        
        # Draw info panel
        self.draw_info_panel()
        
        # Draw control buttons
        for button in self.buttons.values():
            button.draw(self.screen)
        
        # Draw mode buttons
        for button in self.mode_buttons.values():
            button.draw(self.screen)
        
        # Draw current mode indicator
        mode_text = f"Edit Mode: {self.edit_mode.replace('_', ' ').title()}"
        mode_surface = self.small_font.render(mode_text, True, COLOR_WARNING)
        self.screen.blit(mode_surface, (700, WINDOW_HEIGHT - 60))
        
        pygame.display.flip()
    
    def handle_grid_click(self, pos):
        """Handle clicks on the grid"""
        grid_offset_x = 50
        grid_offset_y = 150
        
        x, y = pos
        if x < grid_offset_x or y < grid_offset_y:
            return
        
        col = (x - grid_offset_x) // CELL_SIZE
        row = (y - grid_offset_y) // CELL_SIZE
        
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            if self.edit_mode == 'place_start':
                # Remove old start
                old_start = self.start
                self.grid[old_start[0]][old_start[1]] = 0
                # Place new start
                self.start = (row, col)
                self.grid[row][col] = 2
                
            elif self.edit_mode == 'place_target':
                # Remove old target
                old_target = self.target
                self.grid[old_target[0]][old_target[1]] = 0
                # Place new target
                self.target = (row, col)
                self.grid[row][col] = 3
                
            elif self.edit_mode == 'place_wall':
                # Don't place wall on start or target
                if (row, col) != self.start and (row, col) != self.target:
                    self.grid[row][col] = 1 if self.grid[row][col] == 0 else 0
                    
            elif self.edit_mode == 'erase':
                # Don't erase start or target
                if (row, col) != self.start and (row, col) != self.target:
                    self.grid[row][col] = 0
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle button clicks
                if self.buttons['start'].handle_event(event):
                    if not self.running:
                        import threading
                        thread = threading.Thread(target=self.run_algorithm)
                        thread.daemon = True
                        thread.start()
                
                if self.buttons['pause'].handle_event(event):
                    self.paused = not self.paused
                    self.buttons['pause'].text = "Resume" if self.paused else "Pause"
                
                if self.buttons['reset'].handle_event(event):
                    self.reset_search()
                    self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    self.grid[self.start[0]][self.start[1]] = 2
                    self.grid[self.target[0]][self.target[1]] = 3
                    self.add_random_walls(40)
                
                if self.buttons['clear'].handle_event(event):
                    self.clear_path()
                
                if self.buttons['walls'].handle_event(event):
                    self.add_random_walls(20)
                
                if self.buttons['speed_up'].handle_event(event):
                    self.step_delay = max(5, self.step_delay - 10)
                
                if self.buttons['speed_down'].handle_event(event):
                    self.step_delay = min(200, self.step_delay + 10)
                
                # Handle algorithm selection
                for i, button in enumerate(self.algo_buttons):
                    if button.handle_event(event):
                        for btn in self.algo_buttons:
                            btn.active = False
                        button.active = True
                        self.current_algorithm = i
                        self.clear_path()
                
                # Handle mode selection (Place Start, Target, Wall, Erase)
                for mode_name, button in self.mode_buttons.items():
                    if button.handle_event(event):
                        # Deactivate all mode buttons
                        for btn in self.mode_buttons.values():
                            btn.active = False
                        # Activate clicked button
                        button.active = True
                        # Set edit mode
                        self.edit_mode = mode_name
                
                # Handle grid clicks
                if event.type == pygame.MOUSEBUTTONDOWN and not self.running:
                    self.handle_grid_click(event.pos)
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = PathfinderGUI()
    app.run()

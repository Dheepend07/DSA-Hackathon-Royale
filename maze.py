import csv
import random
import argparse
from collections import deque

import matplotlib.pyplot as plt


# ==================================================
# CONSTANTS
# ==================================================

KEYS = "abcdef"

# E is reserved for the exit.
# H represents the door corresponding to key e.
DOORS = "ABCDHG"

DOOR_FOR_KEY = {
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
    "e": "H",
    "f": "G"
}

KEY_FOR_DOOR = {
    door: key for key, door in DOOR_FOR_KEY.items()
}

PAIR_COLORS = {
    "a": "#f4a261",
    "b": "#2a9d8f",
    "c": "#e9c46a",
    "d": "#9b5de5",
    "e": "#f15bb5",
    "f": "#00bbf9"
}

DIRECTIONS = [
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1)
]


# ==================================================
# 1. READ MAZE FROM CSV
# ==================================================

def read_csv_grid(filename):
    grid = []

    with open(
        filename,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        for row in csv.reader(file):

            if not row:
                continue

            cells = [cell.strip() for cell in row]

            # Support rows written as S..#.
            if len(cells) == 1 and len(cells[0]) > 1:
                cells = list(cells[0])

            grid.append(cells)

    if not grid:
        raise ValueError("CSV file is empty.")

    n = len(grid)

    # Check whether the maze is square.
    if any(len(row) != n for row in grid):
        raise ValueError(
            "Maze must be an N x N square grid."
        )

    # Valid maze symbols.
    allowed = set(".#SEabcdef" + DOORS)

    for row in grid:
        for cell in row:

            if cell not in allowed:
                raise ValueError(
                    f"Invalid maze symbol: {cell}"
                )

    # Exactly one start.
    if sum(
        cell == "S"
        for row in grid
        for cell in row
    ) != 1:

        raise ValueError(
            "Maze must contain exactly one S."
        )

    # Exactly one exit.
    if sum(
        cell == "E"
        for row in grid
        for cell in row
    ) != 1:

        raise ValueError(
            "Maze must contain exactly one E."
        )

    return grid


# ==================================================
# 2. SAVE MAZE TO CSV
# ==================================================

def save_csv_grid(grid, filename):

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerows(grid)


# ==================================================
# 3. FIND START AND EXIT
# ==================================================

def find_start_exit(grid):

    start = None
    exit_pos = None

    for r, row in enumerate(grid):

        for c, cell in enumerate(row):

            if cell == "S":
                start = (r, c)

            elif cell == "E":
                exit_pos = (r, c)

    if start is None or exit_pos is None:
        raise ValueError(
            "Maze must contain both S and E."
        )

    return start, exit_pos


# ==================================================
# 4. BFS SHORTEST PATH
# ==================================================

def shortest_path(grid):

    n = len(grid)

    start, exit_pos = find_start_exit(grid)

    # State contains:
    # row, column, key bitmask.
    #
    # A bitmask records which keys have been collected.
    start_state = (
        start[0],
        start[1],
        0
    )

    queue = deque([
        (start_state, 0)
    ])

    visited = {start_state}

    parent = {
        start_state: None
    }

    while queue:

        (r, c, mask), distance = queue.popleft()

        # Check whether the exit has been reached.
        if (r, c) == exit_pos:

            path = []

            state = (r, c, mask)

            while state is not None:

                path.append(state)
                state = parent[state]

            path.reverse()

            return distance, path

        # Explore four neighbouring cells.
        for dr, dc in DIRECTIONS:

            nr = r + dr
            nc = c + dc

            # Check grid boundaries.
            if not (
                0 <= nr < n
                and 0 <= nc < n
            ):
                continue

            cell = grid[nr][nc]

            # Walls cannot be crossed.
            if cell == "#":
                continue

            # Check whether the cell is a door.
            if cell in KEY_FOR_DOOR:

                required_key = KEY_FOR_DOOR[cell]

                key_bit = (
                    1 << (ord(required_key) - ord("a"))
                )

                # Cannot enter the door without its key.
                if not (mask & key_bit):
                    continue

            # Update the key inventory.
            new_mask = mask

            if cell in KEYS:

                key_bit = (
                    1 << (ord(cell) - ord("a"))
                )

                new_mask |= key_bit

            next_state = (
                nr,
                nc,
                new_mask
            )

            # Avoid revisiting an identical state.
            if next_state not in visited:

                visited.add(next_state)

                parent[next_state] = (
                    r,
                    c,
                    mask
                )

                queue.append(
                    (
                        next_state,
                        distance + 1
                    )
                )

    # No valid path exists.
    return -1, []


# ==================================================
# 5. GENERATE A RANDOM MAZE
# ==================================================

def generate_maze(n, t, seed=None):

    if n < 5:
        raise ValueError(
            "N must be at least 5."
        )

    if not 1 <= t <= 6:
        raise ValueError(
            "T must be between 1 and 6."
        )

    rng = random.Random(seed)

    # Retry if the generated route is too short.
    for attempt in range(500):

        grid = [
            ["#" for _ in range(n)]
            for _ in range(n)
        ]

        start = (1, 1)

        grid[start[0]][start[1]] = "."

        # ------------------------------------------
        # Randomized Depth-First Search
        # ------------------------------------------

        stack = [start]
        visited = {start}

        while stack:

            r, c = stack[-1]

            neighbours = []

            for dr, dc in [
                (2, 0),
                (-2, 0),
                (0, 2),
                (0, -2)
            ]:

                nr = r + dr
                nc = c + dc

                if (
                    1 <= nr < n - 1
                    and 1 <= nc < n - 1
                    and (nr, nc) not in visited
                ):

                    neighbours.append(
                        (nr, nc, dr, dc)
                    )

            if neighbours:

                nr, nc, dr, dc = rng.choice(
                    neighbours
                )

                # Open the wall between the cells.
                grid[
                    r + dr // 2
                ][
                    c + dc // 2
                ] = "."

                grid[nr][nc] = "."

                visited.add((nr, nc))

                stack.append((nr, nc))

            else:
                stack.pop()

        # ------------------------------------------
        # Find the Farthest Reachable Cell
        # ------------------------------------------

        queue = deque([start])

        parent = {
            start: None
        }

        distance_map = {
            start: 0
        }

        while queue:

            r, c = queue.popleft()

            for dr, dc in DIRECTIONS:

                nr = r + dr
                nc = c + dc

                if not (
                    0 <= nr < n
                    and 0 <= nc < n
                ):
                    continue

                if grid[nr][nc] != ".":
                    continue

                next_pos = (nr, nc)

                if next_pos in parent:
                    continue

                parent[next_pos] = (r, c)

                distance_map[next_pos] = (
                    distance_map[(r, c)] + 1
                )

                queue.append(next_pos)

        exit_pos = max(
            distance_map,
            key=distance_map.get
        )

        # ------------------------------------------
        # Reconstruct a Route to the Exit
        # ------------------------------------------

        route = []

        cell = exit_pos

        while cell is not None:

            route.append(cell)
            cell = parent[cell]

        route.reverse()

        # We need 2 cells for every key-door pair,
        # plus the start and exit.
        if len(route) < 2 * t + 2:
            continue

        available = list(
            range(1, len(route) - 1)
        )

        if len(available) < 2 * t:
            continue

        # Choose distinct positions along the route.
        positions = sorted(
            rng.sample(
                available,
                2 * t
            )
        )

        # Mark the start and exit.
        grid[start[0]][start[1]] = "S"

        grid[
            exit_pos[0]
        ][
            exit_pos[1]
        ] = "E"

        # ------------------------------------------
        # Place Keys and Matching Doors
        # ------------------------------------------

        # Each key is placed before its matching door
        # along the guaranteed route.
        for i in range(t):

            key_r, key_c = route[
                positions[2 * i]
            ]

            door_r, door_c = route[
                positions[2 * i + 1]
            ]

            key = KEYS[i]

            door = DOOR_FOR_KEY[key]

            grid[key_r][key_c] = key

            grid[door_r][door_c] = door

        return grid

    raise ValueError(
        "Could not generate a route long enough for "
        f"{t} key-door pairs with N={n}. "
        "Increase N and try again."
    )


# ==================================================
# 6. MARK THE SHORTEST PATH
# ==================================================

def mark_path(grid, path):

    solution = [
        row[:]
        for row in grid
    ]

    for r, c, mask in path:

        # Mark ordinary path cells with x.
        # Preserve S, E, keys and doors.
        if solution[r][c] == ".":
            solution[r][c] = "x"

    return solution


# ==================================================
# 7. DRAW THE MAZE
# ==================================================

def draw_grid(
    ax,
    grid,
    path_positions=None,
    collected_keys=None,
    opened_doors=None,
    current=None,
    title="Maze with Keys and Doors"
):

    n = len(grid)

    path_positions = path_positions or set()
    collected_keys = collected_keys or set()
    opened_doors = opened_doors or set()

    ax.clear()

    ax.set_xlim(-0.5, n - 0.5)

    ax.set_ylim(n - 0.5, -0.5)

    ax.set_aspect("equal")

    ax.set_xticks([])
    ax.set_yticks([])

    # Draw grid lines.
    ax.set_xticks(
        [i - 0.5 for i in range(n + 1)],
        minor=True
    )

    ax.set_yticks(
        [i - 0.5 for i in range(n + 1)],
        minor=True
    )

    ax.grid(
        which="minor",
        color="gray",
        linewidth=0.7
    )

    ax.tick_params(
        which="both",
        length=0
    )

    # Draw each cell.
    for r, row in enumerate(grid):

        for c, cell in enumerate(row):

            color = "white"
            label = ""

            # Walls.
            if cell == "#":

                color = "black"

            # Start.
            elif cell == "S":

                color = "green"
                label = "S"

            # Exit.
            elif cell == "E":

                color = "red"
                label = "E"

            # Keys.
            elif cell in KEYS:

                if cell in collected_keys:

                    # The key disappears after collection.
                    # Keep the path highlighted if visited.
                    if (r, c) in path_positions:
                        color = "#ffe66d"
                        label = "x"
                    else:
                        color = "white"

                else:

                    color = PAIR_COLORS[cell]
                    label = cell

            # Doors.
            elif cell in KEY_FOR_DOOR:

                key = KEY_FOR_DOOR[cell]

                if cell in opened_doors:

                    color = "white"
                    label = "✓"

                else:

                    color = PAIR_COLORS[key]
                    label = cell

            # Ordinary path cells.
            elif cell in ".x":

                if (r, c) in path_positions:

                    color = "#ffe66d"
                    label = "x"

            # Highlight the current position.
            if current == (r, c):

                color = "orange"
                label = "▶"

            rect = plt.Rectangle(
                (c - 0.5, r - 0.5),
                1,
                1,
                facecolor=color,
                edgecolor="gray"
            )

            ax.add_patch(rect)

            if label:

                ax.text(
                    c,
                    r,
                    label,
                    ha="center",
                    va="center",
                    color="black",
                    fontweight="bold"
                )

    # Display collected keys.
    inventory = (
        ", ".join(sorted(collected_keys))
        if collected_keys
        else "Empty"
    )

    ax.set_title(title)

    ax.set_xlabel(
        "Key Inventory: " + inventory
    )


# ==================================================
# 8. ANIMATE THE SHORTEST PATH
# ==================================================

def visualize_maze(
    grid,
    path,
    animate=True,
    delay=0.3
):

    fig, ax = plt.subplots(
        figsize=(9, 9)
    )

    # No solution found.
    if not path:

        draw_grid(
            ax,
            grid,
            title="No Solution Found"
        )

        plt.show()
        return

    collected_keys = set()
    opened_doors = set()
    path_positions = set()

    # ----------------------------------------------
    # Display only the final result when animation
    # is disabled.
    # ----------------------------------------------

    if not animate:

        for r, c, mask in path:

            path_positions.add((r, c))

            cell = grid[r][c]

            if cell in KEYS:
                collected_keys.add(cell)

            if cell in KEY_FOR_DOOR:
                opened_doors.add(cell)

        draw_grid(
            ax,
            grid,
            path_positions=path_positions,
            collected_keys=collected_keys,
            opened_doors=opened_doors,
            current=None,
            title=f"Shortest Path: {len(path) - 1} Steps"
        )

        plt.show()
        return

    # ----------------------------------------------
    # Animate the path step by step.
    # ----------------------------------------------

    plt.ion()

    for step, (r, c, mask) in enumerate(path):

        path_positions.add((r, c))

        cell = grid[r][c]

        # Collect a key.
        if cell in KEYS:

            collected_keys.add(cell)

        # Unlock a door after entering it.
        if cell in KEY_FOR_DOOR:

            opened_doors.add(cell)

        draw_grid(
            ax,
            grid,
            path_positions=path_positions,
            collected_keys=collected_keys,
            opened_doors=opened_doors,
            current=(r, c),
            title=f"Shortest Path: Step {step}"
        )

        fig.canvas.draw_idle()

        plt.pause(max(0.01, delay))

    plt.ioff()

    plt.show()


# ==================================================
# 9. MAIN PROGRAM
# ==================================================

def main():

    parser = argparse.ArgumentParser(
        description="Maze with Keys and Doors"
    )

    parser.add_argument(
        "--mode",
        choices=["random", "csv"],
        default="random",
        help="Generate a random maze or load a CSV maze"
    )

    parser.add_argument(
        "--n",
        type=int,
        default=15,
        help="Size of the N x N maze"
    )

    parser.add_argument(
        "--t",
        type=int,
        default=3,
        help="Number of key-door pairs (1 to 6)"
    )

    parser.add_argument(
        "--input",
        default="maze.csv",
        help="Input CSV filename"
    )

    parser.add_argument(
        "--output",
        default="maze_solution.csv",
        help="Output solution CSV filename"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible mazes"
    )

    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Display the final solution without animation"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Animation delay in seconds"
    )

    args = parser.parse_args()

    try:

        # ------------------------------------------
        # Generate or load the maze.
        # ------------------------------------------

        if args.mode == "random":

            grid = generate_maze(
                args.n,
                args.t,
                args.seed
            )

            save_csv_grid(
                grid,
                "generated_maze.csv"
            )

            print(
                "Generated maze saved to "
                "generated_maze.csv"
            )

        else:

            grid = read_csv_grid(
                args.input
            )

            print("Maze loaded from CSV.")

        # ------------------------------------------
        # Find the shortest path.
        # ------------------------------------------

        distance, path = shortest_path(grid)

        print(
            "\nShortest path length:",
            distance
        )

        if distance == -1:

            print(
                "No valid path exists from S to E."
            )

        # ------------------------------------------
        # Save the solution.
        # ------------------------------------------

        solution = mark_path(
            grid,
            path
        )

        save_csv_grid(
            solution,
            args.output
        )

        print(
            "Solution saved to:",
            args.output
        )

        # ------------------------------------------
        # Print the solution grid.
        # ------------------------------------------

        print("\nSolution Grid:\n")

        for row in solution:

            print(" ".join(row))

        # ------------------------------------------
        # Visualize the solution.
        # ------------------------------------------

        visualize_maze(
            grid,
            path,
            animate=not args.no_animation,
            delay=args.delay
        )

    except (ValueError, OSError, csv.Error) as error:

        print("\nError:", error)


# ==================================================
# 10. EXECUTE THE PROGRAM
# ==================================================

if __name__ == "__main__":
    main()
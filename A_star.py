import abc
import itertools
import logging
import math
import pygame
import sys

from pygame.locals import *


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='%H:%M')

# initialise pygame
pygame.init()
# Set the display
pygame.display.set_caption('A*.')
display_info = pygame.display.Info()
WINDOWWIDTH = int(display_info.current_w * 4/5)
WINDOWHEIGHT = int(display_info.current_h * 4/5)
DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))

# Create a clock object and set the Frames Per Second.
FPS = 30
FPSCLOCK = pygame.time.Clock()

# RGB colour chart.
WHITE = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARKGREEN = (0, 155, 0)
DARKGRAY = (40, 40, 40)

# The pixel length of the Hexagon sides.
HEX_SIDE_LENGTH = 25
# The length of a perpendicular line from a Hexagon's flat edge to its center..
APOTHEM = int(HEX_SIDE_LENGTH * ((math.sqrt(3)) / 2))
# The size of the font will be based on the size of the Hexagons.
FONT = pygame.font.SysFont("Arial", HEX_SIDE_LENGTH // 2)

# Some global state control booleans.
GLOBALS = {
    "RunAlg": False,
    "isFinished": False,
    "StartHex": None,
    "EndHex": None,
    "CurrentHex": None,
}


class Node(abc.ABC):
    """The Abstract properties and functions for a node in an A* environment."""
    def __init__(self):
        # A list of adjacent nodes
        self.neighbours = []
        # The adjacent node with the shortest distance from the starting point.
        self.parent = None

        # Is the node non-traversable.
        self.is_barrier = False
        # Is this the start node.
        self.is_start = False
        # Is this the destination node.
        self.is_end = False

        # Is this node part of the chosen path.
        self.is_path = False

        # Is this node part of the Open/to-be-evaluated set.
        self.open = False
        # Has this node already been visited.
        self.closed = False

    @property
    def neighbour_distance(self) -> int:
        """The cost of moving between two nodes, for calculating a node's g value."""
        raise NotImplementedError

    @property
    def g(self) -> int:
        """The cost of getting from the start node to this node."""
        if self.is_start:
            return 0
        elif self.parent is not None:
            return self.parent.g + self.neighbour_distance

        # Return infinity by default (which is unfortunately a float.)
        return math.inf

    @property
    def h(self) -> int:
        """The estimated cost to the end node."""
        return -1

    @property
    def f(self) -> int:
        """f = g + h"""
        return self.h + self.g

    def evaluate_neighbours(self):
        """Update g values for all relevant neighbours."""
        for neighbour in self.neighbours:
            # Skip neighbours that cannot be traversed.
            if not neighbour.is_barrier:
                # Skip this node's parent.
                if neighbour != self.parent:
                    # If the cost of getting to the neighbour node is shorter from this node...
                    if neighbour.g > self.g + self.neighbour_distance:
                        # Make this node the neighbours parent.
                        neighbour.parent = self
                        # Add the node to the Open set if it has not already been visited.
                        if not neighbour.closed:
                            neighbour.open = True


class NodeList:
    """The Abstract properties and functions for the list of nodes in an A* environment."""
    def __init__(self):
        self.nodes = []

    def __iter__(self) -> Node:
        for node in self.nodes:
            yield node

    def a_star(self) -> bool:
        """The A8 algorithm itself.

        :returns: True if the end node was discovered on this iteration.
        """
        # Get the set of Open nodes.
        open_nodes = [node for node in self if node.open]
        # Get all nodes with the current lowest F value.
        lowest_f_value = sorted(open_nodes, key=lambda node: node.f)[0].f
        lowest_f_value_nodes = [node for node in open_nodes if node.f == lowest_f_value]

        for current_node in lowest_f_value_nodes:
            logger.debug(f"{current_node=}")
            # Close the node upon visiting it.
            current_node.open = False
            current_node.closed = True

            if current_node.is_end:
                # If the node under scrutiny is the end node, we have succeeded.
                # Mark path back to start and end the process.
                logger.info("End Hexagon Located!")
                current_node.is_path = True
                next_node = current_node.parent
                while not next_node.is_start:
                    next_node.is_path = True
                    next_node = next_node.parent
                return True
            else:
                # Otherwise, evaluate the neighbouring nodes.
                current_node.evaluate_neighbours()
        return False


class PyGameTile(Node, abc.ABC):
    """Abstract class for A* nodes as Polygons in PyGame."""
    @property
    @abc.abstractmethod
    def point_list(self):
        """The list of points making up this Polygon."""
        pass

    @property
    @abc.abstractmethod
    def width(self):
        """The width property of the polygon, to determine if the Polygon should be filled, or be an outline."""
        return 1

    @property
    @abc.abstractmethod
    def colour(self):
        """The colour of the Polygon."""
        return WHITE

    def draw(self):
        """Draw the Polygon to the screen."""
        pygame.draw.polygon(DISPLAYSURF, self.colour, self.point_list, self.width)
        # For debugging, I wanted to see each node's f value. Seemed worth keeping in.
        DISPLAYSURF.blit(FONT.render(str(self.f), True, BLACK), self.point_list[0])


class Hexagon(PyGameTile):
    """The chosen Polygon was a Hexagon, because it tessellates nicely, and the math was challenging."""
    def __init__(self, x, y):
        super(Hexagon, self).__init__()
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.x}, {self.y}"

    @property
    def neighbour_distance(self):
        return APOTHEM * 2

    @property
    def h(self):
        h = 0
        if GLOBALS["EndHex"]:
            x = GLOBALS["EndHex"].x
            y = GLOBALS["EndHex"].y
            h = euclidean_distance(self.x, self.y, x, y)
        return int(h)

    @property
    def point_list(self):
        a = (self.x - APOTHEM, self.y - int(HEX_SIDE_LENGTH / 2))
        b = (self.x, self.y - HEX_SIDE_LENGTH)
        c = (self.x + APOTHEM, self.y - int(HEX_SIDE_LENGTH / 2))
        d = (self.x + APOTHEM, self.y + int(HEX_SIDE_LENGTH / 2))
        e = (self.x, self.y + HEX_SIDE_LENGTH)
        f = (self.x - APOTHEM, self.y + int(HEX_SIDE_LENGTH / 2))
        return [a, b, c, d, e, f]

    @property
    def width(self):
        if any([self.is_start, self.is_end, self.is_barrier, self.open, self.closed, self.is_path]):
            return 0
        else:
            return 1

    @property
    def colour(self):
        if self.is_start:
            return GREEN
        elif self.is_end:
            return RED
        elif self.is_barrier:
            return DARKGRAY
        elif self.is_path:
            return WHITE
        elif self.open:
            return YELLOW
        elif self.closed:
            return BLUE
        else:
            return DARKGREEN

    def click(self):
        """Make adjustments to the Hexagon and GLOBAL properties when this Hexagon is clicked."""
        # If the start has not been set, clicked hexagon is now the start hexagon.
        if not GLOBALS["StartHex"] and not self.is_barrier:
            self.is_start = True
            self.open = True
            GLOBALS["StartHex"] = self
            GLOBALS["CurrentHex"] = self
            # If the end has not been set...
        # If the start has been set, but the end has not been set...
        elif not GLOBALS["EndHex"]:
            # If this Hexagon is the start, and is being deselected.
            if self.is_start:
                self.is_start = False
                self.open = False
                GLOBALS["StartHex"] = None
            # Otherwise, it is being set as the End.
            else:
                self.is_end = True
                GLOBALS["EndHex"] = self
        # Otherwise, if the start and end hexagons have been set.
        else:
            # Clicking start or end a second time deselects them.
            if self.is_start:
                self.is_start = False
                GLOBALS["StartHex"] = None
            elif self.is_end:
                self.is_end = False
                GLOBALS["EndHex"] = None
            # Otherwise they become a barrier hexagon, or are deselected as a barrier hexagon.
            elif self.is_barrier:
                self.is_barrier = False
            else:
                self.is_barrier = True


class HexagonList(NodeList):
    def __init__(self):
        super(HexagonList, self).__init__()
        self.set_start = True
        self.start_hexid = -1
        self.set_end = True
        self.end_hexid = -1

        self.current_hexid = -1
        self.set_hexagons()

    def __getitem__(self, item):
        return self.nodes[item]

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        for row in self.nodes:
            for node in row:
                yield node

    def set_hexagons(self):
        """Create the Hexagons to fill this list."""
        y = 0
        row_num = 0
        while y <= (WINDOWHEIGHT + HEX_SIDE_LENGTH):
            self.nodes.append([])

            # x-coordinate, for loop to scroll along the x-axis.
            x = APOTHEM * (row_num % 2)
            col_num = 0
            while x <= (WINDOWWIDTH + HEX_SIDE_LENGTH):
                logger.info(f"({row_num=}, {col_num=}): ({x=}, {y=})")
                self.nodes[row_num].append(Hexagon(x, y))
                x += 2 * APOTHEM
                col_num += 1
            row_num += 1
            y += int(HEX_SIDE_LENGTH * (3 / 2))

        for row_num in range(0, len(self.nodes)):
            hexagon_row = self.nodes[row_num]
            for col_num in range(0, len(hexagon_row)):
                hexagon = hexagon_row[col_num]
                neighbourlist = []
                neighbour_hexagons = find_hexagons(row_num, col_num, self)
                for neighbour_hex in neighbour_hexagons:
                    x2, y2 = neighbour_hex.x, neighbour_hex.y
                    dist = euclidean_distance(hexagon.x, hexagon.y, x2, y2)
                    if 0 < dist <= 2 * HEX_SIDE_LENGTH:
                        neighbourlist.append(neighbour_hex)
                hexagon.neighbours = neighbourlist

    def reset(self):
        """Reset the object."""
        self.set_start = True
        self.start_hexid = -1
        self.set_end = True
        self.end_hexid = -1

        self.nodes = []
        self.current_hexid = -1
        GLOBALS["StartHex"] = None
        GLOBALS["EndHex"] = None
        self.set_hexagons()

    def draw(self):
        """Draw all the Hexagons in this list."""
        for hexagon_row in self.nodes:
            for hexagon in hexagon_row:
                hexagon.draw()


def euclidean_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Distance between two coordinates (x1,y1) and (x2,y2)."""
    distance = math.sqrt((x1-x2)**2+(y1-y2)**2)
    return distance


def check_input(hexagon_list: HexagonList):
    """Monitor user input and react accordingly."""
    for event in pygame.event.get():
        # Exit if x is clicked.
        if event.type == QUIT:
            terminate()

        # Gets a mouseclick and coordinates.
        if event.type == pygame.MOUSEBUTTONDOWN:
            position = pygame.mouse.get_pos()
            if not GLOBALS["RunAlg"] and not GLOBALS["isFinished"]:
                hexagon = find_clicked_hex(position, hexagon_list)
                hexagon.click()

        if event.type == KEYDOWN:
            # Enter triggers the pathfinding.
            if event.key == K_RETURN and GLOBALS["StartHex"] and GLOBALS["EndHex"] and not GLOBALS["RunAlg"]:
                logger.warning("Running Algorithm")
                GLOBALS["RunAlg"] = True

            if event.key == K_BACKSPACE and not GLOBALS["RunAlg"]:
                logger.warning("Restarting")
                hexagon_list.reset()
                GLOBALS["isFinished"] = False

            # Sets escape to end game.
            if event.key == K_ESCAPE:
                terminate()


def find_clicked_hex(p: tuple, hexagon_list: HexagonList) -> Hexagon:
    """Given a coordinate p, find the Hexagon that was clicked."""
    x, y = p[0], p[1]
    row_num = y // int(HEX_SIDE_LENGTH * (3 / 2))
    col_num = (x + (APOTHEM * ((row_num + 1) % 2))) // (APOTHEM * 2)
    logger.warning(f"{p=}")

    best_hex = None
    c = max(WINDOWHEIGHT, WINDOWWIDTH)
    hexagons = find_hexagons(row_num, col_num, hexagon_list)

    for hexagon in hexagons:
        # Distance between mousclick and current hexagon being examined.
        dist = euclidean_distance(x, y, hexagon.x, hexagon.y)
        # Keeps BestHex up to date if a closer hexagon is found.
        if c > dist:
            c = dist
            best_hex = hexagon

    return best_hex


def find_hexagons(row_num: int, col_num: int, hexagon_list: HexagonList) -> list:
    """Return a list of the 9 Hexagons objects adjacent to a provided coordinate set.

    :param row_num:
    :param col_num:
    :param hexagon_list:
    :return: list of hexagons.
    """
    return_list = []
    for row_number, col_number in itertools.product([row_num, row_num+1, row_num-1], [col_num, col_num+1, col_num-1]):
        try:
            hexagon = hexagon_list[row_number][col_number]
            return_list.append(hexagon)
        except IndexError:
            pass
    return return_list


def terminate():
    """Terminate the program."""
    pygame.quit()
    sys.exit()


def main():
    """My handling of the pygame display loop was based on a Space Invaders example.
    In a future update, I'd like to try splitting the screen refresh, input monitoring, and HexagonList into separate
    threads.
    """
    # Fills the HexagonList
    hexagon_list = HexagonList()

    while True:
        # Clear screen and delay if screen is refreshing too fast.
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        # Set the background colour to black.
        DISPLAYSURF.fill(BLACK)
        # Tessellate the screen with Hexagons.
        hexagon_list.draw()

        if GLOBALS["RunAlg"]:
            if hexagon_list.a_star():
                GLOBALS["RunAlg"] = False
                GLOBALS["isFinished"] = True

        check_input(hexagon_list)


if __name__ == '__main__':
    main()

import os.path
import pdb
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

class Cell:
    """Class representing a cell in the layout."""

    def __init__(self, xloc, yloc):
        self.x = xloc
        self.y = yloc
        self.content = 'empty'
        self.net_num = 0
        self.label = 0
        self.dist_from_src = 0
        self.prev = None
        self.rect_id = None
        self.text_id = None

    def __str__(self):
        return "Cell(x=%s, y=%s, content=%s, net_num=%s, label=%s, prev=%s)" % (
                self.x, self.y, self.content, self.net_num, self.label, repr(self.prev))

    def is_empty(self):
        if self.content == 'empty':
            return True
        else:
            return False

    def is_obstacle(self):
        if self.content == 'obstacle':
            return True
        else:
            return False

    def is_sink(self):
        if self.content == 'net_sink':
            return True
        else:
            return False

    def is_source(self):
        if self.content == 'net_src':
            return True
        else:
            return False

    def set_label(self, label):
        self.label = label
        if label == 0:
            self.set_text('')
        else:
            self.set_text(str(label))

    def set_text(self, text):
        # create canvas text if needed
        if self.text_id == None:
            x, y = self._get_center()
            self.text_id = canvas.create_text(x, y, text=text)
        else:
            canvas.itemconfigure(self.text_id, text=text)

    def _get_center(self):
        """Returns (x, y) coordinates of center of Cell's canvas rectangle."""
        x1, y1, x2, y2 = canvas.coords(self.rect_id) # get rect coords
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return (center_x, center_y)

    def colourize(self):
        """Colour the cell according to contents."""
        net_colours = ['red', 'yellow', 'light grey', 'orange', 'magenta',
                'violet', 'green', 'purple']
        if self.is_obstacle():
            canvas.itemconfigure(self.rect_id, fill='blue')
        elif self.net_num != 0:
            colour = net_colours[(self.net_num - 1) % len(net_colours)]
            canvas.itemconfigure(self.rect_id, fill=colour)

    def estimate_dist(self, target):
        """Return the Manhatten distance between current and target Cells"""
        return abs(self.x - target.x) + abs(self.y - target.y)


class Net:
    """Class representing a net."""

    def __init__(self, num_pins, source, sinks, net_num):
        self.num_pins = num_pins
        self.source = source
        self.sinks = sinks
        self.route = []
        self.net_num = net_num

    def __str__(self):
        return "Net(num_pins=%s, source=%s, sinks=%s, net_num=%s)" % (
                self.num_pins, self.source, self.sinks, self.net_num)


class Layout:
    """Class representing a the grid layout"""

    def __init__(self):
        self.xsize = 0
        self.ysize = 0
        self.grid = [[]]
        self.netlist = []

    def init_grid(self, xsize, ysize):
        self.grid = [[Cell(x, y) for x in range(xsize)] for y in range(ysize)]
        self.xsize = xsize
        self.ysize = ysize

    def print_grid(self):
        for row in self.grid:
            for cell in row:
                if cell.is_source():
                    print('[{}s]'.format(cell.net_num), end='')
                elif cell.is_sink():
                    print('[{}t]'.format(cell.net_num), end='')
                elif cell.label != 0:
                    print('[{: >2}]'.format(cell.label), end='')
                elif cell.is_obstacle():
                    print('[**]', end='')
                else:
                    print('[  ]', end='')
            print()


def get_neighbours(cell, net_num):
    """Return a list of neighbours of a given cell.
    
    cell - the Cell instance for which to find neighbours
    net_num - the net number of the Net instance we are routing

    Does not include neighbour Cells that contain obstacles or cells that
    belong to other nets."""
    # list to return
    neighbours = []

    # coordinates of possible neighbours
    locs = [{'x' : cell.x,   'y' : cell.y-1}, # north
            {'x' : cell.x+1, 'y' : cell.y},   # east
            {'x' : cell.x,   'y' : cell.y+1}, # south
            {'x' : cell.x-1, 'y' : cell.y}]   # west

    for loc in locs:
        # check bounds of possible neighbours
        if (0 <= loc['x'] < layout.xsize) and (0 <= loc['y'] < layout.ysize):
            cell = layout.grid[loc['y']][loc['x']]
            # don't consider obstacles
            if cell.is_obstacle():
                continue
            # don't consider cells that belong to other nets
            if cell.net_num not in [0, net_num]:
                continue
            neighbours.append(cell)

    return neighbours


def route_net(net):
    """Route a net from source to first sink."""
    source = net.source
    target = net.sinks[0] # TODO route to multiple sinks
    expansion_list = [] # TODO better implementation of priority queue

    # label source with estimated distance to target, add to expansion list
    source.set_label(source.estimate_dist(target))
    expansion_list.append(source)

    # while expansion list is not empty:
    while expansion_list:
        # g = grid in expansion list with smallest label
        g = expansion_list[0]
        for cell in expansion_list:
            if cell.label < g.label:
                g = cell
        # remove g from expansion list
        expansion_list.remove(g)

        print('expanding on {}'.format(g))
        # layout.print_grid()
        # print()

        # if g is the target, exit the loop
        if g is target:
            break

        # for all neighbours of g:
        neighbours = get_neighbours(g, net.net_num)
        for neighbour in neighbours:
            # if neighbour is unlabelled:
            if neighbour.label == 0:
                # label neighbour with dist from source + estimate of dist to go
                neighbour.dist_from_src = g.dist_from_src + 1
                label = neighbour.dist_from_src + neighbour.estimate_dist(target)
                neighbour.set_label(label)
                # set previous cell of neighbour to current cell
                neighbour.prev = g
                # add neighbour to expansion list
                expansion_list.append(neighbour)

    # if loop terminates without hitting target, fail
    else:
        print("couldn't route net!")
        return

    # traceback():
    # - start at taget, walk back along prev cells
    print("routed net!")
    while g is not source:
        g.net_num = target.net_num
        g.content = 'net'
        net.route.append(g)
        g = g.prev

    # clear labels of empty cells, update colours
    for row in layout.grid:
        for cell in row:
            if cell.is_empty():
                cell.set_label(0)
            cell.colourize()


def parse_netlist(filepath):
    """Parse a netlist and populate the layout.grid.
    
    filepath - the full path of the netlist file to parse"""
    with open(filepath, 'r') as f:
        # first line is grid size
        line = f.readline().strip().split()
        xsize = int(line[0])
        ysize = int(line[1])
        layout.init_grid(xsize, ysize)

        # next lines are obstructed cells
        num_obstacles = int(f.readline().strip())
        for i in range(num_obstacles):
            line = f.readline().strip().split()
            xloc = int(line[0])
            yloc = int(line[1])
            cell = layout.grid[yloc][xloc]
            cell.x = xloc
            cell.y = yloc
            cell.content = 'obstacle'

        # next lines are wires to route
        # TODO cleanup parsing of nets (make more readable)
        num_wires = int(f.readline().strip())
        for i in range(num_wires):
            net_num = i + 1 # nets are numbered from 1

            line = list(map(int, f.readline().strip().split()))
            # first item in line is number of pins
            num_pins = line.pop(0)

            # second item is x, y coordinates of source
            xloc = line.pop(0)
            yloc = line.pop(0)
            source = layout.grid[yloc][xloc]
            source.content = 'net_src'
            source.net_num = net_num

            # next items are x, y coordinates of sinks
            sinks = []
            for j in range(num_pins-1):
                xloc = line.pop(0)
                yloc = line.pop(0)
                sink = layout.grid[yloc][xloc]
                sink.content = 'net_sink'
                sink.net_num = net_num
                sinks.append(sink)

            layout.netlist.append(Net(num_pins, source, sinks, net_num))


def open_benchmark(*args):
    """Function called when pressing Open button.
    
    Opens a dialog for user to select a netlist file, parses netlist
    file and sets up initial grid in the GUI."""
    openfilename = filedialog.askopenfilename()
    if openfilename == '':
        return
    filename.set(os.path.basename(openfilename))
    parse_netlist(openfilename)
    # layout.print_grid()

    # initialize canvas with rectangles for layout
    # TODO move into GUI related function?
    cw = canvas.winfo_width()
    ch = canvas.winfo_height()
    rw = cw // layout.xsize
    rh = ch // layout.ysize
    xoffset = (cw % rw) / 2
    yoffset = (ch % rh) / 2
    print(cw, ch, rw, rh, xoffset, yoffset)
    for row in layout.grid:
        for cell in row:
            x1 = cell.x * rw + xoffset
            x2 = x1 + rw + xoffset
            y1 = cell.y * rh + yoffset
            y2 = y1 + rh + yoffset
            cell.rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill='white')

            # colour cell and set text label
            cell.colourize()
            if cell.net_num != 0:
                # label source and sink with net number
                cell.set_text(str(cell.net_num))


def route(*args):
    """Function called when pressing Route button.

    Routes the first net in the netlist."""
    for net in layout.netlist:
        route_net(net)


def restart(*args):
    """Function called when pressing Restart button.

    Currently does nothing."""
    pass


# main function TODO put into class
if __name__ == '__main__':
    layout = Layout()

    root = Tk()
    root.title("Assignment1-Routing")

    # frames
    top_frame = ttk.Frame(root, padding="3 3 12 12")
    top_frame.grid(column=0, row=0, sticky=(N,E,S,W))
    top_frame.columnconfigure(0, weight=1)
    top_frame.rowconfigure(0, weight=1)
    canvas_frame = ttk.Frame(top_frame)
    canvas_frame.grid(column=0, row=0, sticky=(N,E,S,W))
    btn_frame = ttk.Frame(top_frame)
    btn_frame.grid(column=0, row=1, sticky=(N,E,S,W))

    # canvas frame (benchmark label + canvas)
    filename = StringVar()
    benchmark_lbl = ttk.Label(canvas_frame, textvariable=filename)
    benchmark_lbl.grid(column=0, row=0)
    canvas = Canvas(canvas_frame, width=640, height=480, bg="dark grey")
    canvas.grid(column=0, row=1, padx=5, pady=5)

    # button frame (buttons)
    open_btn = ttk.Button(btn_frame, text="Open", command=open_benchmark)
    open_btn.grid(column=0, row=0, padx=5, pady=5)
    route_btn = ttk.Button(btn_frame, text="Route", command=route)
    route_btn.grid(column=1, row=0, padx=5, pady=5)
    restart_btn = ttk.Button(btn_frame, text="Restart", command=restart)
    restart_btn.grid(column=2, row=0, padx=5, pady=5)

    # run mainloop
    root.mainloop()

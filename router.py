import os.path
import pdb
import random
from priorityq import *
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
        return "Cell({net} {content} ({x}, {y}) l={label}, prev={prev})".format(
                net=self.net_num, x=self.x, y=self.y, content=self.content,
                label=self.label, prev=repr(self.prev))

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
        if self.content == 'sink':
            return True
        else:
            return False

    def is_source(self):
        if self.content == 'src':
            return True
        else:
            return False

    def set_label(self, label):
        self.label = label
        if label == 0:
            self.set_text('')
        else:
            self.set_text(str(label))

    def clear_label(self):
        # don't clear labels from source or sinks
        if (not self.is_source()) and (not self.is_sink()):
            self.set_label(0)

    def set_text(self, text=''):
        # text for source is +, text for sink is -
        if self.is_source():
            text = '+'
        elif self.is_sink():
            text = '-'

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
        self.net_num = net_num
        self.routed = False

    def __str__(self):
        return "Net(pins=%s, src=%s, sinks=%s, net=%s)" % (
                self.num_pins, self.source, self.sinks, self.net_num)

    def is_routed(self):
        return self.routed


class Layout:
    """Class representing a the grid layout."""

    def __init__(self):
        self.xsize = 0
        self.ysize = 0
        self.grid = [[]]
        self.netlist = []

    def init_grid(self, xsize, ysize):
        """Initialize the grid to given size by populating with empty Cells."""
        self.grid = [[Cell(x, y) for x in range(xsize)] for y in range(ysize)]
        self.xsize = xsize
        self.ysize = ysize

    def print_grid(self):
        """Print the grid in text format."""
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
    
    Arguments:
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
    
    # get neighbours in random order
    random.shuffle(locs) 
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


def route_net(source, target=None):
    """Route a single net from source to optional target.
    
    If a target is given, uses A* algorithm to find a route between source
    and target. If no target is given, source is assumed to be a net sink
    and Lee-Moore algorithm is run to expand out from the sink looking for
    previously routed cells.

    Returns True if net is successfully routed, False otherwise."""
    if target == None:
        algorithm = 'Lee-Moore'
        print("routing sink {}".format(source))
    else:
        algorithm = 'A*'
        print("routing source: {} to target: {}".format(source, target))

    expansion_list = PriorityQueue()

    # set source label according to algorithm
    if algorithm == 'A*':
        # A*: source label is estimated distance to target
        label = source.estimate_dist(target)
    else:
        label = 1
    source.set_label(label)
    expansion_list.add(item=source, priority=source.label)

    # while expansion list is not empty:
    while not expansion_list.is_empty():
        # g = grid in expansion list with smallest label
        g = expansion_list.extract_min()

        # print('expanding on {}'.format(g))

        # for A*: if g is the target, exit the loop
        if algorithm == 'A*':
            if g is target:
                break
        # for Lee-More: if we reach a matching net, exit the loop
        else:
            if (g.net_num == source.net_num) and (g is not source):
                break

        # for all neighbours of g:
        neighbours = get_neighbours(g, source.net_num)
        for neighbour in neighbours:
            # if neighbour is unlabelled:
            if neighbour.label == 0:
                neighbour.dist_from_src = g.dist_from_src + 1
                if algorithm == 'A*':
                    # label neighbour with dist from source + estimate of dist to go
                    label = neighbour.dist_from_src + neighbour.estimate_dist(target)
                else: # Lee-More
                    # label neighbour with distance from source
                    label = neighbour.dist_from_src
                neighbour.set_label(label)
                # set previous cell of neighbour to current cell
                neighbour.prev = g
                # add neighbour to expansion list
                expansion_list.add(item=neighbour, priority=neighbour.label)

    # if loop terminates without hitting target, fail
    else:
        print("couldn't route net!")
        # clear labels of empty cells, update colours
        for row in layout.grid:
            for cell in row:
                cell.clear_label()
                cell.colourize()
        return False

    # traceback():
    # - start at taget, walk back along prev cells
    print("routed net!")
    while g is not source:
        # don't modify content for source and sink
        if not (g.is_source()) and (not g.is_sink()):
            g.net_num = source.net_num
            g.content = 'net'
        # clear the prev pointer
        prev = g.prev
        g.prev = None
        g = prev

    # clear labels of empty cells, update colours
    for row in layout.grid:
        for cell in row:
            cell.clear_label()
            cell.colourize()

    return True


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
        layout.netlist = []
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
            source.content = 'src'
            source.net_num = net_num

            # next items are x, y coordinates of sinks
            sinks = []
            for j in range(num_pins-1):
                xloc = line.pop(0)
                yloc = line.pop(0)
                sink = layout.grid[yloc][xloc]
                sink.content = 'sink'
                sink.net_num = net_num
                sinks.append(sink)

            layout.netlist.append(Net(num_pins, source, sinks, net_num))


def open_benchmark(*args):
    """Function called when pressing Open button.
    
    Opens a dialog for user to select a netlist file, parses netlist
    file and sets up initial grid in the GUI."""

    # open a select file dialog for user to choose a benchmark file
    openfilename = filedialog.askopenfilename()
    # return if user cancels out of dialog
    if not openfilename:
        return
    filename.set(os.path.basename(openfilename))
    parse_netlist(openfilename)

    # reset the statsistics label
    stats_text.set("")

    # enable the Route button
    route_btn.state(['!disabled'])

    # initialize canvas with rectangles for layout
    # TODO move into GUI related function?
    cw = canvas.winfo_width()
    ch = canvas.winfo_height()
    rw = cw // layout.xsize
    rh = ch // layout.ysize
    xoffset = (cw % rw) / 2
    yoffset = (ch % rh) / 2
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
                # label source and sink
                cell.set_text()


def route(*args):
    """Function called when pressing Route button.

    Routes each net in the netlist."""
    # disable the Route button after starting routing
    route_btn.state(['disabled'])

    # route nets in netlist
    nets_routed = 0
    for net in layout.netlist: # TODO intelligent net ordering
        print()
        # route from source to first sink
        route_net(net.source, net.sinks[0]) # TODO intelligent sink ordering

        # expand around sink looking for connection to trunk
        if len(net.sinks) > 1:
            print("multiple sinks...")
            for sink in net.sinks[1:]:
                route_net(sink)

        if net.is_routed():
            nets_routed = nets_routed + 1

    # display stats
    stats_text.set("Routed {}/{} nets".format(nets_routed, len(layout.netlist)))


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
    stats_frame = ttk.Frame(top_frame)
    stats_frame.grid(column=0, row=2)

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
    route_btn.state(['disabled'])
    restart_btn = ttk.Button(btn_frame, text="Restart", command=restart)
    restart_btn.grid(column=2, row=0, padx=5, pady=5)
    restart_btn.state(['disabled'])

    # stats frame
    stats_text = StringVar()
    stats_text.set("")
    stats_lbl = ttk.Label(stats_frame, textvariable=stats_text)
    stats_lbl.grid(column=0, row=0)

    # run mainloop
    root.mainloop()

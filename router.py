import os.path
import pdb
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

class Cell:
    def __init__(self, xloc, yloc):
        self.x = xloc
        self.y = yloc
        self.content = 'empty'
        self.net_num = 0
        self.label = 0
        self.prev = None
        self.rect_id = None
        self.text_id = None

    def __str__(self):
        return "Cell(x=%s, y=%s, content=%s, net_num=%s, label=%s, prev=%s)" % (
                self.x, self.y, self.content, self.net_num, self.label, repr(self.prev))


class Net:
    def __init__(self, num_pins, source, sinks):
        self.num_pins = num_pins
        self.source = source
        self.sinks = sinks
        self.route = []

    def __str__(self):
        return "Net(num_pins=%s, source=%s, sinks=%s)" % (
                self.num_pins, self.source, self.sinks)


class Layout:
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
            for c in row:
                if c.content == 'net_src':
                    print('[{}s]'.format(c.net_num), end='')
                elif c.content == 'net_sink':
                    print('[{}t]'.format(c.net_num), end='')
                elif c.label != 0:
                    print('[{: >2}]'.format(c.label), end='')
                elif c.content == 'obstacle':
                    print('[**]', end='')
                else:
                    print('[  ]', end='')
            print()


def get_neighbours(cell):
    neighbours = []

    # coordinates of possible neighbours
    locs = [{'x' : cell.x,   'y' : cell.y-1}, # north
            {'x' : cell.x+1, 'y' : cell.y},   # east
            {'x' : cell.x,   'y' : cell.y+1}, # south
            {'x' : cell.x-1, 'y' : cell.y}]   # west

    for loc in locs:
        # check bounds of possible neighbours
        if (0 <= loc['x'] < layout.xsize) and (0 <= loc['y'] < layout.ysize):
            c = layout.grid[loc['y']][loc['x']]
            # don't consider obstacles or other net's cells
            if c.content != 'obstacle':
                neighbours.append(c)

    return neighbours


def route_net(net):
    source = net.source
    target = net.sinks[0] # TODO route to multiple sinks
    expansion_list = [] # TODO better implementation of priority queue

    # label source with 1, add to expansion list
    source.label = 1
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
        neighbours = get_neighbours(g)
        for neighbour in neighbours:
            # if neighbour is unlabelled:
            if neighbour.label == 0:
                # label neighbour with g + 1
                neighbour.label = g.label + 1
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


def parse_netlist(filepath):
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

            layout.netlist.append(Net(num_pins, source, sinks))


def open_benchmark(*args):
    openfilename = filedialog.askopenfilename()
    if openfilename == '':
        return
    filename.set(os.path.basename(openfilename))
    parse_netlist(openfilename)
    layout.print_grid()

    # initialize canvas with rectangles for layout
    # TODO move into GUI related function
    rw = canvas.winfo_width() // layout.xsize
    rh = canvas.winfo_height() // layout.ysize
    for row in layout.grid:
        for cell in row:
            x1 = cell.x * rw
            x2 = x1 + rw
            y1 = cell.y * rh
            y2 = y1 + rh
            cell.rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill='white')

            # colour rectangles depending on content
            if cell.content == 'obstacle':
                canvas.itemconfigure(cell.rect_id, fill='blue')
            elif cell.net_num != 0:
                colour = net_colours[(cell.net_num - 1) % len(net_colours)]
                canvas.itemconfigure(cell.rect_id, fill=colour)

                # label source and sink with net number
                x1, y2, x2, y2 = canvas.coords(cell.rect_id) # get rect coords
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                canvas.create_text(center_x, center_y, text=str(cell.net_num))



def proceed(*args):
    route_net(layout.netlist[0]) # TODO route all nets


def restart(*args):
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

    net_colours = ['red', 'yellow', 'light grey', 'orange', 'magenta',
            'violet', 'green', 'purple']

    # button frame (buttons)
    open_btn = ttk.Button(btn_frame, text="Open", command=open_benchmark)
    open_btn.grid(column=0, row=0, padx=5, pady=5)
    proceed_btn = ttk.Button(btn_frame, text="Proceed", command=proceed)
    proceed_btn.grid(column=1, row=0, padx=5, pady=5)
    restart_btn = ttk.Button(btn_frame, text="Restart", command=restart)
    restart_btn.grid(column=2, row=0, padx=5, pady=5)

    # run mainloop
    root.mainloop()

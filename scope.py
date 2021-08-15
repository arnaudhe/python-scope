import sys
import numpy
import serial
import json
import socket
import threading
import pygame
import subprocess
import re

from pygame.locals import *

global lock
lock = threading.Lock()

class DataReader(threading.Thread):

    stop_thread = threading.Event()

    def __init__(self, dimension, regex, depth = 1000):
        threading.Thread.__init__(self)                     # Call constructor of parent
        self.data_buff_size = depth                         # Buffer size
        self.dimension = dimension
        self.regex = regex
        self.data = numpy.zeros((self.data_buff_size, self.dimension))   # Data buffer

    def run(self):
        while not self.stop_thread.isSet() :
            data = self.read()                          # Read incoming data
            if re.match(self.regex, data) != None:
                try:
                    values = re.match(self.regex, data).group(1).split(';')
                    if (len(values) == self.dimension):
                        values = [float(i) for i in values]
                    else:
                        raise Exception("Bad input length")
                except Exception as e:
                    print("Data input error")
                    print(e)
                else:
                    lock.acquire()
                    self.data = numpy.roll(self.data, -1, axis=0)
                    self.data[-1, :] = numpy.array(values).T
                    lock.release()
            else:
                print('Data input does not match regex')

        self.close()

    def stop(self):
        self.stop_thread.set()

class DataReaderUdp(DataReader):

    def __init__(self, port, dimension, regex, depth = 1000):
        super(DataReaderUdp, self).__init__(dimension, regex, depth)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        print('Socket bound on port {}'.format(port))
        self.start()

    def read(self):
        return self.sock.recv(1024).decode('utf-8')

    def close(self):
        print('Socket closed')
        self.sock.close()


class DataReaderSerial(DataReader):

    def __init__(self, port, baudrate, dimension, regex, depth = 1000):
        super(DataReaderSerial, self).__init__(dimension, regex, depth)
        self.ser = serial.Serial(port, baudrate)  # open serial port
        print('Serial port {} opened'.format(port))
        self.start()

    def read(self):
        return self.ser.readline()

    def close(self):
        print('Serial closed')
        self.ser.close()

class DataReaderProgramOutput(DataReader):

    def __init__(self, command, args, dimension, regex, depth = 1000):
        super(DataReaderProgramOutput, self).__init__(dimension, regex, depth)
        self.proc = subprocess.Popen([command] + args, stdout=subprocess.PIPE)
        print('Started program {}'.format(command))
        self.start()

    def read(self):
        return self.proc.stdout.readline()

    def close(self):
        print('Process terminate')
        self.proc.terminate()

class VerticalGradient():

    def __init__(self, screen, rect, top_color, bottom_color, steps):
        self.screen       = screen
        self.rect         = rect
        self.top_color    = top_color
        self.bottom_color = bottom_color
        self.steps        = steps
    
    def update(self):
        
        for i in range (self.steps):

            color_1 = self.top_color[0] - (((self.top_color[0] - self.bottom_color[0]) * i) / self.steps)
            color_2 = self.top_color[1] - (((self.top_color[1] - self.bottom_color[1]) * i) / self.steps)
            color_3 = self.top_color[2] - (((self.top_color[2] - self.bottom_color[2]) * i) / self.steps)

            color_cur = (int(color_1),int(color_2),int(color_3))
            step_size = self.rect.height / self.steps
            rect_cur = pygame.Rect(self.rect.left, self.rect.top + (i * step_size), self.rect.width, step_size)
            #print color_cur
            if color_1 in range(0,255) and color_2 in range(0,255) and color_3 in range(0,255):
                pygame.draw.rect(self.screen, color_cur, rect_cur)


class Oscilloscope():

    RED     = (229, 32,  57)
    ORANGE  = (255, 154, 4)
    BLUE    = (0,   162, 232)
    GREEN   = (102, 177, 33)

    FONT_COLOR             = (200, 200, 200)
    GRID_COLOR             = (150, 150, 150)
    BACKGROUND_LIGHT_COLOR = (50, 50, 50)
    BACKGOURND_DARK_COLOR  = (20, 20, 20)

    GRID_NB = 10
 
    colors  = [RED, BLUE, ORANGE, GREEN, RED, BLUE, ORANGE, GREEN, RED, BLUE, ORANGE, GREEN]
    
    def __init__(self, data_reader, dimension, width, height, x_depth, y_min, y_max, channels_desc):
        self.width       = width
        self.height      = height
        self.x_depth     = x_depth
        self.y_min       = y_min
        self.y_max       = y_max
        self.screen      = pygame.display.set_mode((width, height))
        self.clock       = pygame.time.Clock()
        self.data_reader = data_reader
        self.dimension   = dimension
        self.chan_desc   = channels_desc

        try:
            self.run()
        except:
            pygame.quit()
            self.data_reader.stop()
            sys.exit()


    def plot(self, x, y, xmin, xmax, ymin, ymax, color):
        w, h = self.screen.get_size()
        x = numpy.array(x)
        y = numpy.array(y)
        
        #Scale data
        xspan = abs(xmax-xmin)
        yspan = abs(ymax-ymin)
        xsc   = 1.0*(w+1)/xspan
        ysc   = 1.0*h/yspan
        xp    = (x-xmin)*xsc
        yp    = h-(y-ymin)*ysc

        # Plot data
        for i in range(len(xp)-1):
            pygame.draw.line(self.screen, color, (int(xp[i]),   int(yp[i])), 
                                                 (int(xp[i+1]), int(yp[i+1])), 2)


    def display_background(self):

        self.screen.fill(self.BACKGOURND_DARK_COLOR)
        self.gradient.update()


    def display_grid(self, xmin, xmax, ymin, ymax):

        w, h = self.screen.get_size()

        # Draw grid
        for i in range(self.GRID_NB):
            pygame.draw.line(self.screen, self.GRID_COLOR, (0, int(h*0.1*i)), (w-1, int(h*0.1*i)), 1)
            self.screen.blit(self.font.render("{}".format(ymax - ((float)(ymax - ymin) * i) / 10), 1, self.FONT_COLOR), (0, int(h*0.1*i)))
            pygame.draw.line(self.screen, self.GRID_COLOR, (int(w*0.1*i), 0), (int(w*0.1*i), h-1), 1)
            self.screen.blit(self.font.render("{}".format(xmin + ((float)(xmax - xmin) * i) / 10), 1, self.FONT_COLOR), (int(w*0.1*i), 0))


    def display_channel(self, channel_num):

        if not self.hold:
            lock.acquire()
            x = numpy.arange(self.x_depth)
            y = self.data_reader.data[:, channel_num]
            lock.release()
        self.plot(x, y, 0, self.x_depth, self.y_min, self.y_max, self.colors[channel_num])


    def display_fps(self):

        text = self.font.render('{} fps'.format(int(self.clock.get_fps())), 1, self.FONT_COLOR)
        self.screen.blit(text, (30, 30))


    def display_channels_description(self):

        for i in range(len(self.chan_desc)):
            text = self.font.render(self.chan_desc[i], 1, self.colors[i])
            self.screen.blit(text, (30, 60 + (i * 30)))


    def run(self):
        
        # Things we need in the main loop
        self.hold = False

        self.font = pygame.font.Font(None, 28)

        rect = pygame.Rect((0, 0), pygame.display.get_surface().get_size())
        self.gradient = VerticalGradient(self.screen,rect, self.BACKGROUND_LIGHT_COLOR, self.BACKGOURND_DARK_COLOR, self.height)

        while 1:

            #Process events
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                pygame.quit()
                self.data_reader.stop()
                sys.exit()
            if event.type == pygame.KEYDOWN :
                if event.key == pygame.K_h:
                    self.hold = not self.hold
            
            self.display_background()

            self.display_grid(0, self.x_depth, self.y_min, self.y_max)

            for i in range(self.dimension):
                self.display_channel(i)

            self.display_fps()

            self.display_channels_description()

            pygame.display.flip()
            self.clock.tick(0)


pygame.init()

if (len(sys.argv) < 2):
    sys.exit('usage : python {} <config>'.format(sys.argv[0]))

with open(sys.argv[1], 'r') as config_file:
    config = json.loads(config_file.read())

data_source_type   = config['source']['type']
data_source_params = config['source']['params']

if ('regex' in config['source']):
    data_source_regex = config['source']['regex']
else:
    data_source_regex = "(.+)"

channels_len       = len(config['channels'])
scope_x_depth      = config['scope']['x_depth']
scope_width        = config['scope']['width']
scope_height       = config['scope']['height']
scope_y_min        = config['scope']['y_min']
scope_y_max        = config['scope']['y_max']
channels_desc      = ['{} ({})'.format(channel, config['channels'][channel]['unit']) for channel in config['channels']]

if data_source_type == 'udp':
    data_reader = DataReaderUdp(data_source_params['port'], channels_len, data_source_regex, scope_x_depth)
elif data_source_type == 'serial':
    data_reader = DataReaderSerial(data_source_params['port'], data_source_params['baudrate'], channels_len, data_source_regex, scope_x_depth)
elif data_source_type == 'program_output':
    data_reader = DataReaderProgramOutput(data_source_params['command'], data_source_params['args'], channels_len, data_source_regex, scope_x_depth)
else:
    sys.exit("Unknown source type")

osc = Oscilloscope(data_reader, channels_len, scope_width, scope_height, scope_x_depth, scope_y_min, scope_y_max, channels_desc)
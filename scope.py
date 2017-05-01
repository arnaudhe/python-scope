import sys
import numpy
import serial
import json
import traceback
import socket
import threading
import pygame

from pygame.locals import *

global lock
lock = threading.Lock()

class DataReader(threading.Thread):

    stop_thread = threading.Event()

    def __init__(self, dimension, depth = 1000):
        threading.Thread.__init__(self)                     # Call constructor of parent
        self.data_buff_size = depth                         # Buffer size
        self.dimension = dimension
        self.data = numpy.zeros((self.data_buff_size, self.dimension))   # Data buffer

    def run(self):

        val = 0                                         # Read value
        
        while not self.stop_thread.isSet() :
            data = self.read()                          # Read incoming data
            try:
                values = data.split(';')
                if (len(values) == self.dimension):
                    values = [float(i) for i in values]
                else:
                    raise Exception("Bad input length")
            except Exception, e:
                print "input data error"
            
            lock.acquire()
            self.data = numpy.roll(self.data, -1, axis=0)
            self.data[-1, :] = numpy.array(values).T
            lock.release()

        self.close()

    def stop(self):
        self.stop_thread.set()

class DataReaderUdp(DataReader):

    def __init__(self, port, dimension, depth = 1000):
        super(DataReaderUdp, self).__init__(dimension, depth)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        print 'Socket bound on port {}'.format(port)
        self.start()

    def read(self):
        return self.sock.recv(1024)

    def close(self):
        print 'Socket closed'
        self.sock.close()


class DataReaderSerial(DataReader):

    def __init__(self, port, baudrate, dimension, depth = 1000):
        super(DataReaderSerial, self).__init__(dimension, depth)
        self.ser = serial.Serial(port, baudrate)  # open serial port
        print 'Serial port {} opened'.format(port)
        self.start()

    def read(self):
        self.ser.readline()

    def close(self):
        print 'Serial closed'
        self.ser.close()


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

    colors  = [RED, BLUE, ORANGE, GREEN, RED, BLUE, ORANGE, GREEN, RED, BLUE, ORANGE, GREEN]
    
    def __init__(self, data_reader, dimension):
        self.screen      = pygame.display.set_mode((800, 600))
        self.clock       = pygame.time.Clock()
        self.data_reader = data_reader
        self.dimension   = dimension
        self.run()

    def generate_gradient(self, from_color, to_color, height, width):
        channels = []
        for channel in range(3):
            from_value, to_value = from_color[channel], to_color[channel]
            channels.append(
                numpy.tile(
                    numpy.linspace(from_value, to_value, width), [height, 1],
                ),
            )
        return numpy.dstack(channels)
        
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

        font = pygame.font.Font(pygame.font.match_font(u'mono'), 16)
        
        #Draw grid
        for i in range(10):
            pygame.draw.line(self.screen, (150, 150, 150), (0,int(h*0.1*i)), (w-1,int(h*0.1*i)), 1)
            self.screen.blit(font.render("{}".format(ymax - ((float)(ymax - ymin) * i) / 10), 1, (200, 200, 200)), (0,int(h*0.1*i)))
            pygame.draw.line(self.screen, (150, 150, 150), (int(w*0.1*i),0), (int(w*0.1*i),h-1), 1)
            self.screen.blit(font.render("{}".format(xmin + ((float)(xmax - xmin) * i) / 10), 1, (200, 200, 200)), (int(w*0.1*i),0))
            
        #Plot data
        for i in range(len(xp)-1):
            pygame.draw.line(self.screen, color, (int(xp[i]),   int(yp[i])), 
                                                 (int(xp[i+1]), int(yp[i+1])), 2)

    def run(self):
        
        #Things we need in the main loop
        font = pygame.font.Font(pygame.font.match_font(u'mono'), 24)
        data_buff_size = self.data_reader.data_buff_size        
        hold = False

        rect = pygame.Rect((0, 0), pygame.display.get_surface().get_size())
        gradient = VerticalGradient(self.screen,rect,(50, 50, 50), (20, 20, 20), 400)

        while 1:
            #Process events
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                pygame.quit()
                self.data_reader.stop()
                sys.exit()
            if event.type == pygame.KEYDOWN :
                if event.key == pygame.K_h:
                    hold = not hold

            self.screen.fill((20,20,20))
            gradient.update()

            # Plot current buffer
            for i in range(self.dimension):
                if not hold:
                    lock.acquire()
                    x = numpy.arange(data_buff_size)
                    y = self.data_reader.data[:, i]
                    lock.release()
                self.plot(x, y, 0, data_buff_size, 0, 10, self.colors[i])

            # Display fps
            text = font.render("%d fps"%self.clock.get_fps(), 1, (200, 200, 200))
            self.screen.blit(text, (30, 30))

            pygame.display.flip()
            self.clock.tick(0)


pygame.init()

if (len(sys.argv) < 2):
    sys.exit('usage : python {} <config>'.format(sys.argv[0]))

with open(sys.argv[1], 'r') as config_file:
    config = json.loads(config_file.read())

data_source_type   = config['source']['type']
data_source_params = config['source']['params']
channels_len       = len(config['channels'])
plot_depth         = config['plot']['depth']

if data_source_type == 'udp':
    data_reader = DataReaderUdp(data_source_params['port'], channels_len, plot_depth)
elif data_source_type == 'serial':
    data_reader = DataReaderUdp(data_source_params['port'], data_source_params['baudrate'], channels_len, plot_depth)
else:
    sys.exit("Unknown source type")

osc = Oscilloscope(data_reader, channels_len)

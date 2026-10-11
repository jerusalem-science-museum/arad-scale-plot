#!/usr/bin/python3

import time
import serial
import pygame
import numpy as np

import constants


time_per_sample = 0.0 # to be calculate acording to time take to read data
time_per_draw = 0.0 # to be calculate acording to time take to update draw
time_per_plot_update = 0.0 # need to to be larger then time per draw * safe margine

x = []
y = []
new_y = []
tara = 0
mean_y = 100.0
number_of_points = constants.NUM_OF_PLOT_POINTS

images = []
#frames =[]
#current_frame = 0
current_image = 0

def fill_images():
    global images
    del images[:]
    for j in range(constants.NUMBER_OF_IMAGES):
        images.append(pygame.image.load(constants.RES_PATH + '/image_' + str(j) + '.png'))
    print (images)


def clear_screen(color):
    screen_surface.fill(color)
    main_screen.blit(screen_surface, (0,0))
    pygame.display.flip()


def update_plot_area():
    x1 = constants.P_A_X
    y1 = constants.P_A_Y
    x2 = x1 + constants.P_A_W
    y2 = y1 + constants.P_A_H
    
    color = constants.P_A_C
    plot_surface.fill(color)
    main_screen.blit(plot_surface, (x1,y1))
    color = constants.P_A_F_C
    thick = constants.P_A_F_T
    pygame.draw.lines(main_screen,color, True,( (x1, y1), (x2,y1), (x2,y2),(x1,y2)), thick)
    
           
    pygame.display.flip()

def update_image(image_number, x, y):
    image_surface.fill(constants.IMAGE_BK_COLOR)
    main_screen.blit(image_surface, constants.IMAGE_X_Y)
    main_screen.blit(images[image_number], (x,y))
    #pygame.display.flip()

# fill initial value and meausre read time 
def fill_data():
    global current_image
    global time_per_sample
    global time_per_plot_update
    global x
    global y
    global tara
    global number_of_points
    global mean_y
    del x[:]
    del y[:]
    t_start = time.time()
    for i in range(number_of_points):
        #print(i)
        x.append(i)
        while (arduinoData.inWaiting()==0): #Wait here until there is data
            pass #do nothing
        arduinoString = arduinoData.readline() #read the line of text from the serial port
        try:
            y.append(float(arduinoString))
        except:
            y.append(0)
        #current_image = (current_image+1) % constants.NUMBER_OF_IMAGES
        #update_image(current_image, constants.IMAGE_X, constants.IMAGE_Y - current_image*constants.DH)
    time_per_sample = ((time.time()-t_start)/number_of_points)
    print( 'time per sample = ' , time_per_sample)
    tara = np.mean(y)
    print ('tara = ', tara)
    mean_y = np.mean(y)


def update_plot_data(new_data):
    global y
    global new_y
    global mean_y
    global tara
    y.append(new_data)
    y.pop(0)
    new_y = [(x / mean_y) for x in y]
    #mean_y = np.mean(y)


def update_plot():
    global x
    global y
    global new_y
    global mean_y
    global number_of_points
    global time_per_draw
    thick = constants.LINE_WIDTH
    color = constants.LINE_COLOR
    mean_y= np.mean(y)
    #print (mean_y)
    #print (np.mean(y))
    #print (np.max(y))
    #print (np.min(y))
    
    x_l = constants.P_A_X # x left
    dx = constants.P_A_W/(number_of_points-1)
   
    y_up = constants.P_A_Y
    y_dn = y_up+constants.P_A_H
    #y_range = mean_y*2*constants.SCALE_FACTOR
    y_range = mean_y*(constants.SCALE_FACTOR_UP+constants.SCALE_FACTOR_DN)
    if y_range == 0:
        y_range = 100 # make sure not divide with zero 
    ymin = mean_y*(1 - constants.SCALE_FACTOR_UP)
    #ymax = mean_y*(1 + constants.SCALE_FACTOR)
    scale = constants.P_A_H/y_range
    #y0 = y0+(y[0]-y_min)*scale
    x1 = x_l
    y1 = y_up+(y[0]-ymin)*scale
    if y1 < y_up:
        y1 = y_up 
    if y1 > y_dn:
        y1 = y_dn
    
    update_plot_area() #clean area
    for i in range(1, number_of_points):
        x2 = x_l+i*dx
        y2 = y_up+(y[i]-ymin)*scale
        if y2 < y_up:
            y2 = y_up 
        if y2 > y_dn:
            y2 = y_dn
        pygame.draw.line(main_screen,color, (x1, y1), (x2,y2), thick)
        x1 = x2
        y1 = y2
    current_image = int(constants.NUMBER_OF_IMAGES*((y[number_of_points-1]-ymin))/y_range)
    if current_image <=0 :
        current_image = 0
    if current_image >= (constants.NUMBER_OF_IMAGES-1):
        current_image = (constants.NUMBER_OF_IMAGES-1)
    #print ('current image is ' , current_image)
    #current_image = (current_image+1) % constants.NUMBER_OF_IMAGES
    update_image(current_image, constants.PICTURE_X, constants.PICTURE_Y - current_image*constants.DH)
    pygame.display.flip()
 
#---------------------------------
#---------------------------
# progran start here

#fill initial images for animations
fill_images()

# initialize the pygame module
pygame.init()
clock = pygame.time.Clock()
infoObject = pygame.display.Info()
# load and set the logo
# logo = pygame.image.load('icon.png')
# pygame.display.set_icon(logo)
pygame.display.set_caption('in case of problem call amir 972-542406559') 
# define image and plot area surfaces on screen
main_screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h))
screen_surface = pygame.Surface((constants.SCREEN_W,constants.SCREEN_H))
image_surface = pygame.Surface((constants.IMAGE_W,constants.IMAGE_H))
plot_surface = pygame.Surface((constants.P_A_W,constants.P_A_H))

myfont = pygame.font.SysFont(constants.FONT_TYPE, constants.FONT_SIZE)
label = myfont.render(constants.LABEL, 1, constants.FONT_COLOR)

if (constants.FULL_SCREEN == True):
    pygame.display.toggle_fullscreen() 


# open UART
is_UART_connect = False # define flag about UART state
try:
    arduinoData = serial.Serial('/dev/ttyUSB0', constants.BOUDRATE)
    print ('port opend')
    print(constants.BOUDRATE)
    is_UART_connect = True
except Exception as e:
    is_UART_connect = False
    print (e)
    raise SystemExit() # end program

clear_screen(constants.SCREEN_COLOR) 
main_screen.blit(label, constants.LABEL_X_Y )
pygame.display.flip()
# fill initial data vector, also use to calibrate min  Yaxis
fill_data()# constants.NUM_OF_PLOT_POINTS - 1) #fill initial data and calculae reading rate
a_time = time.time()
update_plot()
b_time =time.time()
time_per_draw = b_time - a_time # calculate time per update screen with new fig
print ('draw time =', time_per_draw)
time_per_plot_update = constants.TIME_SAFE_MARGINE*max(time_per_sample*constants.NUM_OF_UPDATE_POINT, time_per_draw)
print ('time_per_sample*constants.NUM_OF_UPDATE_POINT  = ', time_per_sample*constants.NUM_OF_UPDATE_POINT)
print ('time_per_draw  = ', time_per_draw)
print ('time per plot update  = ', time_per_plot_update)

clear_screen(constants.SCREEN_COLOR) 
pygame.display.flip()


running = True

pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

# main loop
while running:
    t_plot_update = time.time()
    while time.time() - t_plot_update < time_per_plot_update: # interal read sensor loop
        while (arduinoData.inWaiting()==0): #Wait here until there is data
            pass #do nothing
        arduinoString = arduinoData.readline() #read the line of text from the serial port
        #print('{:,}'.format(float(arduinoString)))
        update_plot_data(float(arduinoString))
    #clock.tick(20)
    update_plot()
    #clock.tick(20)
    # event handling, gets all event from the event queue
    for event in pygame.event.get():
        
       
        # only do something if the event is of type QUIT
        #if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
       #     print('done')
       #     running = False
       #     pygame.quit()
        pressed = pygame.key.get_pressed()
    if pressed[pygame.K_q]:
        print('quit')
        running = False
        pygame.quit()
    if pressed[pygame.K_t]:pygame.display.toggle_fullscreen()
    if pressed[pygame.K_f]: update_plot_area()
    if pressed[pygame.K_d]: update_plot_area()
    if pressed[pygame.K_r]: fill_data()     
    if pressed[pygame.K_c]: clear_screen(constants.SCREEN_COLOR)
    if pressed[pygame.K_p]: update_plot()
    

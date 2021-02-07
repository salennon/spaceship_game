'''
Simple sidescrolling shooter using pygame
'''

from pygame.locals import * #import key commands
import pygame
import time
import numpy as np
import itertools

class Player:
    '''
    Player spaceship
    '''
    x = 0
    y = 0
    speed = 3
    image = None

    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape

    def appearance(self, image):
        '''Default graphic for player'''
        self.image = pygame.image.load(image).convert()

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))
    
    def move_right(self):
        self.x = self.x + self.speed
 
    def move_left(self):
        self.x = self.x - self.speed
        
    def move_up(self):
        self.y = self.y - self.speed
        
    def move_down(self):
        self.y = self.y + self.speed

    def shoot(self, bullets):
        #Shoot a bullet
        bullets.add_bullet(self.x + self.shape[0]/2, self.y + self.shape[1]/2)

class Bullets:
    '''
    Handle multiple bullets using numpy arrays
    '''
    speed = np.array([0,0])

    def __init__(self, max_bullets, speed):
        '''
        Speed should be a numpy array: [x_speed, y_speed]
        '''

        #Set up array for bullet locations + movement info
        self.locations = np.full((max_bullets, 2), -100, dtype = int)
        self.max_bullets = max_bullets
        self.speed = speed

        #Iterator to cycle through bullet indices
        self.bullet_cycler = itertools.cycle(range(len(self.locations)))

    def appearance(self, image):
        '''Default graphic for each bullet'''
        self.image = pygame.image.load(image).convert()
    
    def add_bullet(self, x, y):
        '''Add bullet at x,y'''
        bullet_index = next(self.bullet_cycler)
        self.locations[bullet_index, 0] = x
        self.locations[bullet_index, 1] = y

    def update(self):
        self.locations = self.locations + self.speed

    def draw(self, surface, x_region, y_region):
        '''
        Draw bullets within a given x and y region. x_region and y_region should be tuples.
        Note: need to investigate efficiency of drawing all bullets vs filtering numpy array and drawing some
        '''
        # lower_filter = self.locations > np.array([x_region[0], y_region[0]])
        # upper_filter = self.locations < np.array([x_region[1], y_region[1]])
        # region_filter = lower_filter * upper_filter
        # draw_locations = self.locations[region_filter]

        for loc in self.locations:
            surface.blit(self.image, loc)



class App:
    '''
    Application loops
    '''
    
    window_width = 1080
    window_height = 600
    
    def __init__(self):
        self._display_surf = None
        self._running = False

        self.player = Player(0, 0, (60,60))
        self.player_bullets = Bullets(100, np.array([10,0]))
    
    def on_init(self):
        pygame.init()
        pygame.display.set_caption('Sidescrolling shooter')
    
        #Create display surface
        self._display_surf = pygame.display.set_mode((self.window_width,\
                                    self.window_height), pygame.HWSURFACE)

        #Set graphics for various objects
        self.player.appearance('graphics/ship.png')
        self.player_bullets.appearance('graphics/player_bullet.png')

        self._running = True
        
    def on_event(self, event):
        if event.type == QUIT:
            self._running = False
            
    def on_loop(self):     
        self.player_bullets.update()
    
    def on_render(self):
        self._display_surf.fill((0,0,0))
        self.player.draw(self._display_surf)
        self.player_bullets.draw(self._display_surf, (0, self.window_width), (0, self.window_height))
        pygame.display.flip()
        
    def on_cleanup(self):
        pygame.quit()
        
    def on_execute(self):

        self.on_init()
        
        while(self._running):
            #Event handling
            pygame.event.pump()
            keys = pygame.key.get_pressed()
            
            #Handle key presses
                        #Handle key presses
            if(keys[K_d]):
                self.player.move_right()
                
            if(keys[K_a]):
                self.player.move_left()
            
            if(keys[K_w]):
                self.player.move_up()
                
            if(keys[K_s]):
                self.player.move_down()

            if(keys[K_SPACE]):
                self.player.shoot(self.player_bullets)
                
            if(keys[K_ESCAPE]):
                self._running = False


            self.on_loop()
            self.on_render()
            time.sleep(0.01)
            
        self.on_cleanup()

if __name__ == "__main__":
    app = App()
    app.on_execute()
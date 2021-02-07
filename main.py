'''
Simple sidescrolling shooter using pygame
'''

from pygame.locals import * #import key commands
import pygame
import time
import numpy as np
import itertools

'''
To do:
Add collison detection
Unit testing
'''


class Player:
    '''
    Player spaceship
    '''
    x = 0
    y = 0
    shape = (60,60)
    speed = 5
    image = None
    last_shot_time = 0
    shot_delay = 100
    x_bounds = (0, 1080)
    y_bounds = (0, 600)

    def __init__(self, x, y, shape, image):
        self.x = x
        self.y = y
        self.shape = shape
        self.image = image

    def move_to_start_pos(self):
        '''Move to default starting position'''
        self.x = int(self.x_bounds[1]/10)
        self.y = int(self.y_bounds[1]/2) - self.shape[1]/2

    def appearance(self, image):
        '''Load graphic from file'''
        self.image = pygame.image.load(image).convert_alpha()

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))
    
    def move_right(self):
        if self.x + self.speed < self.x_bounds[1] - self.shape[0]:
            self.x = self.x + self.speed
 
    def move_left(self):
        if self.x - self.speed > self.x_bounds[0]:
            self.x = self.x - self.speed
        
    def move_up(self):
        if self.y - self.speed > self.y_bounds[0] - self.shape[1]/2:
            self.y = self.y - self.speed
        
    def move_down(self):
        if self.y + self.speed < self.y_bounds[1] - self.shape[1]/2:
            self.y = self.y + self.speed

    def shoot(self, bullets, current_time):

        #Shoot a bullet if enough time has passed since last shot
        if current_time - self.last_shot_time > self.shot_delay:
            bullets.add_bullet(self.x + self.shape[0]/1.5, self.y + self.shape[1]/2 - bullets.bullet_size[1]/2)

            #Update record of last shot
            self.last_shot_time = current_time

class Bullets:
    '''
    Handle multiple bullets using numpy arrays
    '''
    speed = np.array([0,0])
    bullet_size = (50, 10)

    def __init__(self, max_bullets, speed, image):
        '''
        Speed should be a numpy array: [x_speed, y_speed]
        '''

        #Set up array for bullet locations + movement info
        self.locations = np.full((max_bullets, 2), -100, dtype = int)
        self.max_bullets = max_bullets
        self.speed = speed

        #Iterator to cycle through bullet indices
        self.bullet_cycler = itertools.cycle(range(len(self.locations)))

        #Image for each bullet
        self.image = image

    def appearance(self, image):
        '''Load graphic from file'''
        self.image = pygame.image.load(image).convert_alpha()
    
    def add_bullet(self, x, y):
        '''Add bullet at x,y'''
        bullet_index = next(self.bullet_cycler)
        self.locations[bullet_index, 0] = x
        self.locations[bullet_index, 1] = y

    def update(self):
        self.locations = self.locations + self.speed

    def draw(self, surface):
        '''
        Draw bullets
        '''
        for loc in self.locations:
            surface.blit(self.image, loc)


class EnemyCircles:
    '''
    Handle a wave of circle-type enemies using numpy arrays
    '''
    yvel_spread = 2
    xvel_spread = 1
    shape = (60,60)

    def __init__(self, num_enemies, x_spawn_region, y_spawn_region, avg_velocity, image):
        '''
        Generate a wave of num_enemies circle enemies in a spawn region specifed by x_spawn_region and y_spawn_region
        '''
        self.num_enemies = num_enemies

        #Generate at random positions within spawn region
        xpos = np.random.randint(x_spawn_region[0], x_spawn_region[1], size = self.num_enemies)
        ypos = np.random.randint(y_spawn_region[0], y_spawn_region[1], size = self.num_enemies)
        self.locations = np.vstack((xpos, ypos)).transpose()

        #Assign velocity to each circle, giving a random spread
        xvel = np.random.randint(avg_velocity[0] - self.xvel_spread,
                 avg_velocity[0] + self.xvel_spread, size = self.num_enemies)
        yvel = np.random.randint(avg_velocity[1] - self.yvel_spread,
                 avg_velocity[1] + self.yvel_spread, size = self.num_enemies)
        self.velocities = np.vstack((xvel, yvel)).transpose()

        #Image for each circle
        self.image = image

    def appearance(self, image):
        '''Default graphic for each circle'''
        self.image = pygame.image.load(image).convert_alpha()

    def update(self):
        self.locations = self.locations + self.velocities

    def draw(self, surface):
        for loc in self.locations:
            surface.blit(self.image, loc)
    
    def on_screen(self, window_width, window_height):
        '''Return False if none of the enemies in the wave are on screen, True otherwise'''
        #Use an area slightly bigger than window to prevent freshly spawned waves being deleted
        in_width = (self.locations[:,0] > -200) * (self.locations[:,0] < window_width + 200)
        in_height = (self.locations[:,1] > -200) * (self.locations[:,1] < window_height + 200)
        in_bounds = in_width*in_height
        
        if True in in_bounds:
            return True
        else:
            return False

    

class App:
    '''
    Application loops
    '''
    
    window_width = 1080
    window_height = 600
    last_spawn = 0
    last_flush = 0
    enemies = []
    
    def __init__(self):
        self._display_surf = None
        self._running = False
    
    def on_init(self):
        pygame.init()
        pygame.display.set_caption('Sidescrolling shooter')
    
        #Create display surface
        self._display_surf = pygame.display.set_mode((self.window_width,\
                                    self.window_height), pygame.HWSURFACE)

        #Load in graphics
        self.player_graphic = pygame.image.load('graphics/ship.png').convert_alpha()
        self.player_bullet_graphic = pygame.image.load('graphics/player_bullet.png').convert_alpha()
        self.enemy_circle_graphic = pygame.image.load('graphics/circle.png').convert_alpha()
 
        #Player instance, properties etc.
        self.player = Player(0, 0, (60,60), self.player_graphic)
        self.player.x_bounds = (0, self.window_width)
        self.player.y_bounds = (0, self.window_height)
        self.player.move_to_start_pos()

        self.player_bullets = Bullets(20, np.array([20,0]), self.player_bullet_graphic)

        self.game_clock = pygame.time.Clock()
        self._running = True
        
    def on_event(self, event):
        if event.type == QUIT:
            self._running = False
            
    def on_loop(self):     
        #Compute positions
        self.player_bullets.update()

        for enemy in self.enemies:
            enemy.update()

        #Check for off-screen enemies to remove from memory/processing
        if (pygame.time.get_ticks() - self.last_flush) > 10000:
            self.flush_enemies()
            self.last_flush = pygame.time.get_ticks()
        
        #Spawn enemies
        if pygame.time.get_ticks() - self.last_spawn > 1000:
            self.enemies.append(EnemyCircles(10, (1080, 1200), (200,400), (-2,0), self.enemy_circle_graphic))
            self.last_spawn = pygame.time.get_ticks()


    def flush_enemies(self):
        '''Remove enemies no longer on the screen'''
        enemies_to_keep = []
        for enemy in self.enemies:
            if enemy.on_screen(self.window_width, self.window_height) == True:
                enemies_to_keep.append(enemy)
        
        self.enemies = enemies_to_keep
    
    def on_render(self):
        self._display_surf.fill((0,0,0))
        self.player_bullets.draw(self._display_surf)
        self.player.draw(self._display_surf)

        #Render enemies
        for enemy in self.enemies:
            enemy.draw(self._display_surf)

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
    
            if(keys[K_d]):
                self.player.move_right()
                
            if(keys[K_a]):
                self.player.move_left()
            
            if(keys[K_w]):
                self.player.move_up()
                
            if(keys[K_s]):
                self.player.move_down()

            if(keys[K_SPACE]):
                self.player.shoot(self.player_bullets, pygame.time.get_ticks())
                
            if(keys[K_ESCAPE]):
                self._running = False

            self.on_loop()
            self.on_render()
            self.game_clock.tick(60)
            
        self.on_cleanup()

if __name__ == "__main__":
    app = App()
    app.on_execute()
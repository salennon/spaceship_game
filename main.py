'''
Simple sidescrolling shooter using pygame
'''

from pygame.locals import * #import key commands
import pygame
import time
import numpy as np
import itertools
import os
import re

'''
To do:
Death animation for circles
Need to add time for death animation to finish before removing enemies
Collision detection for player
Bullet removal
Unit testing
Refactoring - class polymorphism
'''


class Player:
    '''Player spaceship'''
    x = 0
    y = 0
    shape = (60,60)
    speed = 5
    image = None
    last_shot_time = 0
    shot_delay = 100
    x_bounds = (0, 1080)
    y_bounds = (0, 600)

    def __init__(self, x, y, graphics, hitbox):
        self.x = x
        self.y = y

        self.graphics = graphics
        self.shape = self.graphics.image.get_size()

        self.hitbox = hitbox

    def move_to_start_pos(self):
        '''Move to default starting position'''
        self.x = int(self.x_bounds[1]/10)
        self.y = int(self.y_bounds[1]/2) - self.shape[1]/2

    def draw(self, surface):
        surface.blit(self.graphics.image, (self.x, self.y))
    
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
            bullets.add_bullet(self.x + self.shape[0]/2, self.y + self.shape[1]/2 - bullets.bullet_size[1]/2)

            #Update record of last shot
            self.last_shot_time = current_time

class Bullets:
    '''Handle multiple bullets using numpy arrays'''
    speed = np.array([0,0])
    bullet_size = (50, 10)

    def __init__(self, max_bullets, speed, graphics, hitbox):
        '''
        Speed should be a numpy array: [x_speed, y_speed]
        '''

        #Set up array for bullet locations + movement info
        self.locations = np.full((max_bullets, 2), 1000, dtype = int)
        self.max_bullets = max_bullets
        self.speed = speed

        #Iterator to cycle through bullet indices
        self.bullet_cycler = itertools.cycle(range(len(self.locations)))

        #Image for each bullet
        self.graphics = graphics
        self.bullet_size = self.graphics.image.get_size()

        self.hitbox = hitbox
    
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
            surface.blit(self.graphics.image, loc)

    def absorb_bullets(self, collisions):
        '''Make enemies absorb bullets on collisions'''
        self.locations[collisions, :] = np.array([1000, 1000])

class EnemyCircles:
    '''Handle a wave of circle-type enemies using numpy arrays'''
    yvel_spread = 2
    xvel_spread = 1
    shape = (60,60)
    health_per_enemy = 1

    def __init__(self, num_enemies, x_spawn_region, y_spawn_region, avg_velocity, graphics, hitbox):
        '''
        Generate a wave of num_enemies circle enemies in a spawn region specifed by x_spawn_region and y_spawn_region
        '''
        self.num_enemies = num_enemies

        #Arrays for handling death animations
        self.death_locations = np.full((num_enemies, 2), -1000)
        self.death_frames = np.full(num_enemies, 0)
        self.num_death_frames = graphics.num_death_frames

        #Generate health for each enemy in wave
        self.health = np.full(self.num_enemies, self.health_per_enemy)

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

        #Graphics for each circle
        self.graphics = graphics
        self.shape = self.graphics.image.get_size()

        self.hitbox = hitbox

    def update(self):
        self.locations = self.locations + self.velocities

        #Cycle through death animation frames
        self.death_frames = (self.death_frames + 1)

    def draw(self, surface):
        for loc in self.locations:
            surface.blit(self.graphics.image, loc)

        for i, d_loc in enumerate(self.death_locations):
            #get death frames for each animation - don't let frame exceed number
            #of frames animation actually has
            death_frame = min(self.death_frames[i], self.num_death_frames - 1)
            death_image = self.graphics.death_animation[death_frame]
            surface.blit(death_image, d_loc) 
    
    def on_screen(self, window_width, window_height):
        '''
        Return False if none of the enemies in the wave are on screen, True otherwise
        Note: consider giving this x dependence only
        '''
        #Use an area slightly bigger than window to prevent freshly spawned waves being deleted
        in_width = (self.locations[:,0] > -200) * (self.locations[:,0] < window_width + 200)
        in_height = (self.locations[:,1] > -200) * (self.locations[:,1] < window_height + 200)
        in_bounds = in_width*in_height
        
        if True in in_bounds:
            return True
        else:
            return False
    
    def take_damage(self, collisions, damage_amount):
        '''
        Make enemies take damage based on collisions
        '''
        #Check for already dead enemies
        self.dead_enemies = self.health < 1

        damage_taken = collisions*damage_amount
        self.health = self.health - damage_taken

        new_deaths = (self.health < 1) * np.logical_not(self.dead_enemies)

        #Record locations of deaths for death animation
        self.death_locations[new_deaths, :] = self.locations[new_deaths, :]
        self.death_frames[new_deaths] = 0

        #Move rendering of live enemy off-screen
        self.locations[new_deaths, :] = np.array([-1000,-1000])


class Game:
    ''' Handle game logic'''

    def __init__(self):
        pass

    def detect_bullet_collision(self, bullets, enemy):
        ''' 
        Detect collision between player bullets and wave of enemies
        Returns boolean array with True values for collisions
        '''

        #Define upper and lower limits for hitbox collision
        # lower_limit = np.array([enemy.hitbox[0][0] - bullets.hitbox[0][1], 
        #                         enemy.hitbox[1][0] - bullets.hitbox[1][1]])
        # upper_limit = np.array([enemy.hitbox[0][1] - bullets.hitbox[0][0], 
        #                         enemy.hitbox[1][1] - bullets.hitbox[1][0]])

        x_lower_limit = enemy.hitbox[0][0] - bullets.hitbox[0][1]
        y_lower_limit = enemy.hitbox[1][0] - bullets.hitbox[1][1]
        x_upper_limit = enemy.hitbox[0][1] - bullets.hitbox[0][0]
        y_upper_limit =  enemy.hitbox[1][1] - bullets.hitbox[1][0]
        
        enemy_collisions = np.full(len(enemy.locations), False)
        bullet_collisions = np.full(len(bullets.locations), False)

        for i, enemy_loc in enumerate(enemy.locations):
            proximity = bullets.locations - enemy_loc
            x_proximity = proximity[:,0]
            y_proximity = proximity[:,1]

            #Detect collisions
            x_collision = (x_proximity > x_lower_limit)*(x_proximity < x_upper_limit)
            y_collision = (y_proximity > y_lower_limit)*(y_proximity < y_upper_limit)
            is_collision = x_collision*y_collision

            #Register enemy that collided
            if True in is_collision:
                enemy_collisions[i] = True

            #Register bullet that collided
            bullet_collisions += is_collision
        
        return enemy_collisions, bullet_collisions
    

class Graphics:

    graphic = None

    def __init__(self, image_file):
        
        #Load default appearance
        self.image = pygame.image.load(image_file).convert_alpha()

    def load_death_animation(self, directory):
        '''
        Load series of death animation images from a directory
        '''
        #Get png images in directory and sort
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        png_files = [f for f in files if f.endswith('.png')]
        png_files = Graphics.sort_files(png_files)
        filepaths = [f'{directory}/{fname}' for fname in png_files]

        #Load files into pygame
        death_frames = [pygame.image.load(f).convert_alpha() for f in filepaths]
        self.death_animation = death_frames
    
    @property
    def num_death_frames(self):
        return len(self.death_animation)
            
    @staticmethod
    def sort_files(files):
        '''
        Sort list of filenames alpha-numerically
        Method credit: https://stackoverflow.com/questions/4836710/is-there-a-built-in-function-for-string-natural-sort
        ''' 
        convert = lambda text: int(text) if text.isdigit() else text 
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
        return sorted(files, key = alphanum_key)







































class App:
    '''Application loops'''
    
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
        self.player_graphic = Graphics('graphics/ship.png')
        self.player_bullet_graphic = Graphics('graphics/player_bullet.png')
        self.enemy_circle_graphic = Graphics('graphics/circle.png')

        self.enemy_circle_graphic.load_death_animation('graphics/circle_death')

        #Player instance, properties etc.
        self.player = Player(0, 0, self.player_graphic, ((20,60),(20,60)))
        self.player.x_bounds = (0, self.window_width)
        self.player.y_bounds = (0, self.window_height)
        self.player.move_to_start_pos()

        #Note hitbox of bullets leans to left, makes enemy hits 'feel right'
        self.player_bullets = Bullets(20, np.array([20,0]), self.player_bullet_graphic, ((10,45),(8, 16)))
        
        #Game logic
        self.game = Game()

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
        
        #Spawn circle enemies at periodic intervals
        if pygame.time.get_ticks() - self.last_spawn > 1000:
            self.enemies.append(EnemyCircles(10, (1080, 1200), (200,400),
                 (-2,0), self.enemy_circle_graphic, ((16,62),(16,62))))
            self.last_spawn = pygame.time.get_ticks()

        #Collision detection
        for enemy in self.enemies:
            enemy_collisions, bullet_collisions = self.game.detect_bullet_collision(self.player_bullets, enemy)
            enemy.take_damage(enemy_collisions, 1)
            self.player_bullets.absorb_bullets(bullet_collisions)

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
'''
Simple sidescrolling shooter using pygame
'''

from pygame.locals import * #import key commands
import pygame
import time

class Player:
    '''
    Player spaceship
    '''
    x = 0
    y = 0
    speed = 3
    image = None
    

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def appearance(self, image):
        '''Set the visual appearance of the player'''
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


class App:
    '''
    Application loops
    '''
    
    window_width = 1080
    window_height = 600
    
    def __init__(self):
        self._display_surf = None
        self._running = False

        self.player = Player(0, 0)
    
    def on_init(self):
        pygame.init()
        pygame.display.set_caption('Sidescrolling shooter')
    
        #Create display surface
        self._display_surf = pygame.display.set_mode((self.window_width,\
                                    self.window_height), pygame.HWSURFACE)

        #Player graphics
        self.player.appearance('graphics/ship.png')

        self._running = True
        
    def on_event(self, event):
        if event.type == QUIT:
            self._running = False
            
    def on_loop(self):     
        pass
    
    def on_render(self):
        self._display_surf.fill((0,0,0))
        self.player.draw(self._display_surf)
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
                
            if(keys[K_ESCAPE]):
                self._running = False


            self.on_loop()
            self.on_render()
            time.sleep(0.01)
            
        self.on_cleanup()

if __name__ == "__main__":
    app = App()
    app.on_execute()
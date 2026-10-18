class Scene:
   
    #Handle inputs or events
    def handle_event(self, event):
        pass

    #Advance animations, timers, or changing states
    def update(self, dt):
        pass

        #Rendering
    def draw(self, screen):
        raise NotImplementedError
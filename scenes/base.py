"""Define the event, update, and drawing interface implemented by scenes.

Operation:
    Define event, timed-update, and rendering hooks without additional policy.
Input:
    Pygame events, elapsed seconds, and destination surfaces from Game.
Output:
    No-op event/update defaults; abstract drawing raises NotImplementedError.
"""
class Scene:
    """Expose no-op event/update hooks and a required drawing hook.

    Operation:
        Provide the common scene hooks without imposing input or timing behavior.
    Input:
        Events, elapsed seconds, and a destination surface supplied by Game.
    Output:
        Subclasses may override hooks; no session state is owned here.
    """

    def handle_event(self, event):
        """Handle a Pygame event; scenes without controls may ignore it.

        Operation:
            Ignore events unless a subclass supplies controls.
        Input:
            event: Pygame event.
        Output:
            Returns None; no effects in the base class.
        """
        pass

    def update(self, dt):
        """Advance scene state by dt seconds; static scenes may ignore it.

        Operation:
            Leave static scene state unchanged unless overridden.
        Input:
            dt: elapsed seconds.
        Output:
            Returns None; no effects in the base class.
        """
        pass

    def draw(self, screen):
        """Render onto screen or raise NotImplementedError in an abstract scene.

        Operation:
            Require a concrete renderer from a subclass.
        Input:
            screen: destination surface.
        Output:
            Raises NotImplementedError in the base class.
        """
        raise NotImplementedError

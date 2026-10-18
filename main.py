"""Launch the desktop game using the asynchronous application loop.

Operation:
    Run Game through asyncio only when invoked as the launcher.
Input:
    Project imports and desktop Pygame environment.
Output:
    Starts the desktop game when executed; importing the module does not start a loop.
"""
import asyncio
from game import Game


if __name__ == '__main__':
    asyncio.run(Game().run())

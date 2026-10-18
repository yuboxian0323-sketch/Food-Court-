
import asyncio
import time
import pygame
import settings as s
from game import Game
from scenes.base import Scene
from systems.question_bank import QuestionBank, ContentError
from systems.session import Session
from entities.tomato import Tomato
from systems.scene_assets import SceneAssets
from ui.widgets import UI


if __name__ == '__main__':
     asyncio.run(Game().run())
    
        

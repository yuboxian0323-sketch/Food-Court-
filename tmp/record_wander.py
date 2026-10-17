import json,random
from pathlib import Path
import pygame
from game import Game
import settings as s

game=Game()
game.bank.rng=random.Random(42)
game.session.number=29
game.session.next_round()
game.session.acknowledge_unlock()
game.session.ready()
paths=[[] for t in game.session.targets]
for frame in range(300):
 game.frame([],1/30)
 for t,path in zip(game.session.targets,paths):path.append([t.position.x,t.position.y,t.velocity.x,t.velocity.y])
 pygame.image.save(game.screen,f'tmp/wander-frames/{frame:03}.png')
metrics={'corrections':sum(t.bounds_corrections for t in game.session.targets),'paths':paths,'bounds':[t.bounds for t in game.session.targets],'sizes':[(t.width,t.height) for t in game.session.targets]}
Path('tmp/wander-frames/paths.json').write_text(json.dumps(metrics))
print('Recorded 300 actual game frames; safety corrections:',metrics['corrections'])
pygame.quit()

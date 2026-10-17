import json,random
from pathlib import Path
import pygame
import settings as s
from game import Game

for count in (2,8):
 game=Game();game.bank.rng=random.Random(42);game.session.restart()
 if count==8:game.session.number=29;game.session.next_round()
 game.session.acknowledge_unlock();game.frame([],0);game.session.ready()
 root=Path(f'tmp/shared-box-{count}');root.mkdir(exist_ok=True)
 paths=[[] for t in game.session.targets];gaps=0;outside=0;speed_total=0
 for frame in range(600):
  game.frame([],1/60)
  for i,(target,path) in enumerate(zip(game.session.targets,paths)):
   path.append([target.position.x,target.position.y,target.velocity.x,target.velocity.y])
   speed_total+=target.velocity.length()
   outside+=not pygame.Rect(s.LABEL_REGION).contains(target.rect)
   gaps+=sum(target.rect.inflate(12,12).colliderect(other.rect) for other in game.session.targets[i+1:])
  pygame.image.save(game.screen.subsurface(s.LABEL_REGION),str(root/f'{frame:03}.png'))
  if frame in (0,120,300,480,599):pygame.image.save(game.screen,str(root/f'court-{frame:03}.png'))
 report={'choices':count,'gap_violations':gaps,'outside_frames':outside,'average_speed':speed_total/count/600,'paths':paths,'sizes':[(t.width,t.height) for t in game.session.targets]}
 (root/'paths.json').write_text(json.dumps(report))
 print(count,'choices:',gaps,'gap violations;',outside,'outside frames; avg speed',round(report['average_speed'],1),'px/s',flush=True)
 pygame.quit()

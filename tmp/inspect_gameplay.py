import pygame
from game import Game
from scenes.results import Results
import settings as s

game=Game()
def frame(dt=0):game.frame([],dt)
def save(name):pygame.image.save(game.screen,'tmp/'+name+'.png')
def click(rect,dt=0):game.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pygame.Rect(rect).center)],dt)
def answer(correct):
    target=next(t for t in game.session.targets if (t.fallacy_id==game.session.question.fallacy)==correct)
    click(target.rect)
frame();save('core-reading')
click(s.ACTION);frame(2);save('core-answering')
answer(True);frame(.55);save('core-objection')
frame(.65);save('core-correct')
assert game.session.stage=='FEEDBACK'
click(s.ACTION);click(s.ACTION);answer(False);save('core-mistake')
frame(.5);save('core-wrong-feedback')
click(s.ACTION);click(s.ACTION);frame(10);save('core-timeout')
while game.session.hp>0:
    click(s.ACTION);click(s.ACTION);frame(10)
click(s.ACTION);assert isinstance(game.scene,Results);save('core-results')
click(Results.again);assert game.session.hp==100;save('core-restarted')
# Drive the real round lifecycle to the final unlock, preserving actual bag rules.
while game.session.number < 80:
    if game.session.new_fallacies:click(s.ACTION)
    click(s.ACTION);answer(True);frame(s.OBJECTION_DURATION);click(s.ACTION)
assert len(game.session.unlocked)==18
save('core-unlock-80')
click(s.ACTION);click(s.ACTION);frame(1.5);save('core-eight-targets')
answer(False);frame(.5);save('core-eight-feedback')
pygame.quit()
print('Inspected round loop, all outcomes, results, restart, and actual progression to Q80.')

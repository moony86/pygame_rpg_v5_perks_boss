"""Seeded autonomous attempts, NOT a human playtest or balance certification.

Uses normal stats, offered cards, collisions, damage, enemies and cooldowns.
Only input devices are mocked. No invulnerability, free perks, teleports or kills.
The simple bot aims and walks; it deliberately has no dash policy.
"""
import argparse
import json
import math
import os
import random
import heapq
import sys
from collections import defaultdict, deque
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from game import Game
from game_state import GameState
from states.menu_state import handle_menu_events
from states.perk_state import choose_perk
from states.combat_state import handle_combat_events
from states.end_state import handle_end_screen_events


def navigation_waypoint(pos, goal, solids):
    """Bot-only grid routing around authored cover; never moves game objects."""
    cells={(x,y) for x in range(1,40) for y in range(1,22)
           if not any(pygame.Rect(x*48-30,y*48-30,60,60).colliderect(r) for r in solids)}
    if not cells:
        return goal
    start=min(cells,key=lambda c:pos.distance_squared_to((c[0]*48,c[1]*48)))
    end=min(cells,key=lambda c:goal.distance_squared_to((c[0]*48,c[1]*48)))
    queue=[(0,start)]
    cost={start:0}
    parents={}
    while queue:
        _,cell=heapq.heappop(queue)
        if cell==end:
            path=[cell]
            while path[-1]!=start:
                path.append(parents[path[-1]])
            for item in reversed(path):
                waypoint=pygame.Vector2(item[0]*48,item[1]*48)
                if pos.distance_to(waypoint)>40:
                    return waypoint
            return goal
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt=(cell[0]+dx,cell[1]+dy)
            new=cost[cell]+1
            if nxt in cells and new<cost.get(nxt,float('inf')):
                cost[nxt]=new
                parents[nxt]=cell
                heuristic=abs(nxt[0]-end[0])+abs(nxt[1]-end[1])
                heapq.heappush(queue,(new+heuristic,nxt))
    return goal


def door_toward_uncleared(stage):
    start=stage.current_pos
    queue=deque([(start,None)])
    seen={start}
    boss=None
    while queue:
        pos,first=queue.popleft()
        node=stage.node_by_pos[pos]
        if pos!=start and not node.cleared:
            if not node.room.boss:
                return first
            boss=first
        for door,target in node.neighbors.items():
            if target not in seen:
                seen.add(target)
                queue.append((target,first or door))
    return boss


def attempt(seed,seconds):
    random.seed(seed)
    game=Game()
    handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    # Starting the stage is the same public stage entry used by the hub portal.
    game.stage.start_stage()
    inputs=defaultdict(bool)
    aim=[960,540]
    firing=[True]
    choices=[]
    trace=[]
    room_results={}
    last_room=None
    elapsed=0.
    stuck=0
    lastpos=game.player.rect.center
    waypoint=None
    with patch('pygame.key.get_pressed',side_effect=lambda:inputs), \
         patch('pygame.mouse.get_pressed',side_effect=lambda:(firing[0],False,False)), \
         patch.object(game,'game_mouse_pos',side_effect=lambda:tuple(aim)):
        for frame in range(round(seconds*60)):
            if game.state==GameState.GAME_OVER or game.stage.completed:
                break
            if game.state==GameState.PERK_SELECT:
                options=game.perks.current_options
                priority=('rapid_fire','power_rounds','impact_drive','blade_drone','bomber_drone','vital_core')
                index=min(range(len(options)),key=lambda i:priority.index(options[i]['key']) if options[i]['key'] in priority else 99)
                choices.append(options[index]['key'])
                choose_perk(game,index)
                continue
            elapsed+=1/60
            pos=pygame.Vector2(game.player.rect.center)
            node=game.stage.current_node
            if node.cleared and node.room.index not in room_results:
                room_results[node.room.index]={'room':node.room.index,'type':node.room.label,
                    'clear_room_seconds':round(game.rooms.room_time,2),'hp_at_clear':game.player.health,
                    'level_at_clear':game.player.level}
            if node.grid_pos!=last_room:
                trace.append({'room':node.room.index,'type':node.room.label,'at_seconds':round(elapsed,2),
                              'hp':game.player.health,'level':game.player.level})
                last_room=node.grid_pos
                print(f'seed={seed} entered room={node.room.index} hp={game.player.health}',flush=True)
            living=[e for e in game.enemies if e.alive]
            if living:
                targetable=[e for e in living if not (getattr(e,'encounter',None) and e.encounter.airborne)]
                objectives=[e for e in targetable if getattr(e,'is_boss_eye',False)]
                if targetable:
                    target=min(objectives or targetable,key=lambda e:pos.distance_squared_to(e.rect.center))
                    aim[:]=target.rect.center
            firing[0]=not node.cleared
            if node.cleared:
                if node.room.boss:
                    goal=pygame.Vector2(game.room_exit_rect.center)
                else:
                    door=door_toward_uncleared(game.stage)
                    if door is None:
                        break
                    goal=pygame.Vector2(game.stage.door_rect(door).center)
                if pos.distance_to(goal)<60:
                    handle_combat_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
            else:
                phase=elapsed*.36 + seed
                goal=pygame.Vector2(960+690*math.cos(phase),540+330*math.sin(phase))
            desired=goal-pos
            solids=game.collision.get_colliders()
            if node.cleared:
                if frame%12==0 or waypoint is None:
                    waypoint=navigation_waypoint(pos,goal,solids)
                desired=waypoint-pos
            else:
                waypoint=None
            if desired.length_squared():
                desired=desired.normalize()
            best=None
            bestscore=-float('inf')
            for dx,dy in ((0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                direction=pygame.Vector2(dx,dy)
                if direction.length_squared():
                    direction=direction.normalize()
                nextpos=pos+direction*(32 if node.cleared else 90)
                box=game.player.rect.copy()
                box.center=nextpos
                if not (42<nextpos.x<1878 and 42<nextpos.y<1038) or any(box.colliderect(r) for r in solids):
                    continue
                score=direction.dot(desired)*70
                for enemy in living:
                    distance=nextpos.distance_to(enemy.rect.center)
                    score-=max(0,230-distance)*2
                for bullet in game.enemy_bullets:
                    score-=max(0,100-nextpos.distance_to(bullet.rect.center))*1.4
                if stuck>90:
                    score+=direction.dot(pygame.Vector2(1,0).rotate(seed*33+elapsed*150))*110
                if score>bestscore:
                    bestscore=score
                    best=(dx,dy)
            dx,dy=best or (0,0)
            inputs.clear()
            inputs.update({pygame.K_d:dx>0,pygame.K_a:dx<0,pygame.K_s:dy>0,pygame.K_w:dy<0})
            game.update(1/60)
            stuck=stuck+1 if game.player.rect.center==lastpos else 0
            lastpos=game.player.rect.center
            if frame%120==0:
                # Draw periodically to exercise visual paths, not benchmark FPS.
                game.draw()
    result={'seed':seed,'outcome':'stage_complete' if game.stage.completed else 'death' if game.state==GameState.GAME_OVER else 'timeout_or_navigation_limit',
            'simulated_seconds':round(elapsed,2),'post_outcome_hp':game.player.health,'kills':game.total_kills,
            'cleared_rooms':sum(n.cleared for n in game.stage.nodes),'total_rooms':len(game.stage.nodes),
            'choices':choices,'trace':trace,'rooms':list(room_results.values()),'bot_has_dash_policy':False}
    game.draw()
    pygame.image.save(game.screen,str(ROOT/f'debug_screenshots/front-end/attempt-{seed}.png'))
    # End-of-attempt reset is tested even after a bot timeout (explicit reset).
    if game.state==GameState.GAME_OVER:
        handle_end_screen_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
    else:
        game.reset_run()
    result['reset_clean']=(game.player.health==game.player.max_health and game.player.gold==0
                           and not game.projectiles and not game.player.perk_counts
                           and game.player.enemy_time_stop_timer==0)
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seconds',type=int,default=600)
    parser.add_argument('--seeds',type=int,nargs='+',default=[17,38,91])
    args=parser.parse_args()
    results=[attempt(seed,args.seconds) for seed in args.seeds]
    output=ROOT/'debug_screenshots/front-end/attempt-results-boss-trial.json'
    output.write_text(json.dumps({'limitations':'Simple shooting/walking bot, no dash. Not a human balance verdict.',
                                 'attempts':results},indent=2),encoding='utf-8')
    print(output)

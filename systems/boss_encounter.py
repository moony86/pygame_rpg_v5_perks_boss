"""Three-phase Warden trial. Shared damage gateway covers every damage source."""
import json
import math
import pygame
from systems.asset_loader import ASSET_ROOT
from systems.room_bounds import current_room_rect
from systems.object_catalog import sprite

TUNING=json.loads((ASSET_ROOT/'data/boss_trial.json').read_text(encoding='utf-8'))
PHASE_NAMES=('BREAK THE GUARD','SEVER THE EYES','TURN THE STRIKE')
PATTERNS=(('fan','ring'),('ring','cross','fan'),('parry_orb','ring','fan','parry_orb','cross'))


class BossEncounter:
    def __init__(self,boss):
        self.boss=boss
        self.state='intro'
        self.timer=1.0
        self.phase=1
        self.next_phase=None
        self.attack_index=0
        self.pattern='fan'
        self.eyes=[]
        self.eyes_spawned=False
        self.started=False
        self.budget_clock=0.
        self.budget_used=0.
        self.block_feedback_timer=0.
        self.heal_sound_timer=0.
        self.last_damage=0
        self.damage_total=0.
        self.reflections=0
        self.last_player_pos=None
        self.player_velocity=pygame.Vector2()
        self.guards=[]
        self.spawn_points=[]
        self.air_age=0.
        self.lift=0.
        self.summon_count=0
        self.followups=[]
        self.turrets=[]
        boss.shield=0

    def advance_damage_budget(self,dt):
        self.budget_clock+=dt
        self.block_feedback_timer=max(0.,self.block_feedback_timer-dt)
        if self.budget_clock>=TUNING['damage_quantum_seconds']:
            self.budget_clock%=TUNING['damage_quantum_seconds']
            self.budget_used=0.

    def living_eyes(self):
        return [eye for eye in self.eyes if eye.alive]

    @property
    def airborne(self):
        return self.state in ('ascending','summoning','airborne','landing')

    def living_guards(self):
        return [guard for guard in self.guards if guard.alive]

    def damage(self,amount,reflected=False):
        boss=self.boss
        self.last_damage=0
        if not boss.alive or self.state in ('intro','transition') or self.airborne:
            return False
        amount=max(0.,float(amount))
        if reflected:
            amount=min(amount,boss.max_health*TUNING['reflected_damage_ratio'])
        else:
            exposed=self.state=='exposed'
            if not exposed:
                amount*=TUNING['guard_damage_multiplier']
            ratio=TUNING['exposed_budget_ratio'] if exposed else TUNING['guard_budget_ratio']
            available=max(0.,boss.max_health*ratio-self.budget_used)
            amount=min(amount,available)
        floor=math.ceil(boss.max_health*(2/3 if self.phase==1 else 1/3 if self.phase==2 else 0))
        if self.phase==2 and self.living_eyes():
            floor+=1  # Eyes must be destroyed before phase three, regardless of burst DPS.
        dealt=min(amount,max(0,boss.health-floor))
        boss.health=max(floor,boss.health-dealt)
        self.last_damage=dealt
        self.damage_total+=dealt
        if not reflected:
            self.budget_used+=dealt
        if dealt:
            boss.hit_flash=.08
        if boss.health<=0:
            boss.alive=False
            for eye in self.eyes+self.guards:
                eye.alive=False
            return True
        if boss.health<=floor and self.phase<3 and not (self.phase==2 and self.living_eyes()):
            self.next_phase=self.phase+1
            self.state='transition'
            self.timer=TUNING['transition_seconds']
            boss.windup_timer=0.
            boss.windup_action=None
        return False

    def parried(self):
        self.reflections+=1
        if self.state not in ('intro','transition') and not self.airborne:
            self.state='exposed'
            self.timer=max(self.timer,TUNING['parry_exposed_seconds'])
            self.boss.windup_timer=0.
            self.boss.windup_action=None

    def update(self,dt,player_rect):
        boss=self.boss
        player_pos=pygame.Vector2(player_rect.center)
        if self.last_player_pos is not None and dt>0:
            instant=(player_pos-self.last_player_pos)/dt
            if instant.length()>500:
                instant.scale_to_length(500)
            self.player_velocity=self.player_velocity.lerp(instant,.25)
        self.last_player_pos=player_pos
        self.timer=max(0.,self.timer-dt)
        self.heal_sound_timer=max(0.,self.heal_sound_timer-dt)
        if not self.started:
            self.started=True
            return self.action('intro')
        # Healing and all encounter clocks freeze with the boss under Time Stop.
        eyes=self.living_eyes()
        if self.phase==2 and eyes:
            ceiling=math.ceil(boss.max_health*2/3)
            boss.health=min(ceiling,boss.health+boss.max_health*TUNING['eye_heal_ratio_per_second']*len(eyes)*dt)
        if self.state=='transition':
            self.turrets.clear()
            self.followups.clear()
            if self.timer<=0:
                self.state='ascending'
                self.timer=TUNING['rise_seconds']
                return self.action('rise')
            return None
        if self.state=='ascending':
            self.lift=100*(1-self.timer/TUNING['rise_seconds'])
            if self.timer<=0:
                self.state='summoning'
                self.timer=TUNING['summon_warning_seconds']
                return self.action('summon_warning')
            return None
        if self.state=='summoning':
            self.lift=100.
            if self.timer<=0:
                self.state='airborne'
                self.air_age=0.
                return self.action('reinforcements')
            return None
        if self.state=='airborne':
            self.lift=100+4*math.sin(boss._anim*3)
            self.air_age+=dt
            if self.air_age>=TUNING['airborne_min_seconds'] and (not self.living_guards() or self.air_age>=TUNING['airborne_max_seconds']):
                # Bounded intermission: no immortal wait if a guard gets stuck.
                for guard in self.guards:
                    guard.alive=False
                self.state='landing'
                self.timer=TUNING['landing_seconds']
                return self.action('landing')
            return None
        if self.state=='landing':
            self.lift=100*self.timer/TUNING['landing_seconds']
            if self.timer<=0:
                self.lift=0.
                self.phase=self.next_phase
                boss.phase=self.phase
                boss.rage=self.phase==3
                self.next_phase=None
                self.attack_index=0
                self.state='exposed'
                self.timer=TUNING['landing_exposed_seconds']
                self.budget_used=0.
                return self.action('phase')
            return None
        if self.state=='windup':
            boss.windup_timer=self.timer
            # Track early, then lock the final 350ms: a visible tell, not homing fire.
            if self.timer>.35:
                aim=player_pos+self.player_velocity*.45-pygame.Vector2(boss.rect.center)
                if aim.length_squared():
                    boss.windup_direction=aim.normalize()
            if self.timer<=0:
                self.state='exposed'
                self.timer=TUNING['exposed_seconds'][self.phase-1]
                boss.windup_timer=0.
                boss.windup_action=None
                boss.visual_release_timer=.24
                return self.action('attack')
            return None
        if self.state in ('intro','exposed'):
            if self.timer<=0:
                self.state='guard'
                self.timer=TUNING['guard_seconds'][self.phase-1]
            if self.state=='exposed':
                self.approach(player_pos,dt,0.65)
            return None
        if self.timer<=0:
            patterns=PATTERNS[self.phase-1]
            self.pattern=patterns[self.attack_index%len(patterns)]
            self.attack_index+=1
            direction=pygame.Vector2(player_rect.center)-boss.rect.center
            if direction.length_squared()==0:
                direction=pygame.Vector2(1,0)
            self.state='windup'
            self.timer=TUNING['windup_seconds'][self.phase-1]
            boss._start_windup(self.timer,direction.normalize(),'boss_'+self.pattern)
            return self.action('warning')
        # No untelegraphed dash-on-hit. Approach at a readable speed during guard only.
        self.approach(player_pos,dt,1.)
        if eyes and self.heal_sound_timer<=0:
            self.heal_sound_timer=1.4
            return self.action('healing')
        return None

    def approach(self,player_pos,dt,factor):
        direction=player_pos-pygame.Vector2(self.boss.rect.center)
        if direction.length()>240:
            self.boss._move(direction.normalize()*TUNING['approach_multiplier'][self.phase-1]*factor,dt)

    def tick_hazards(self,dt,player,bullets):
        """Called only on active AI frames; Time Stop and pause freeze hazards."""
        if not self.boss.alive or self.state in ('intro','transition','ascending','summoning','airborne','landing'):
            self.followups.clear()
            self.turrets.clear()
            return
        from entities.enemy_bullet import EnemyBullet
        for shot in self.followups[:]:
            shot['timer']-=dt
            if shot['timer']<=0:
                self.emit_ring(bullets,shot['direction'],offset=15,speed=260)
                self.followups.remove(shot)
        for turret in self.turrets[:]:
            turret['life']-=dt
            turret['timer']-=dt
            if turret['life']<=0:
                self.turrets.remove(turret)
                continue
            # Lock aim during the warning; not a hidden homing shot.
            if turret['timer']>TUNING['turret_warning']:
                direction=pygame.Vector2(player.rect.center)-turret['pos']
                turret['direction']=direction.normalize() if direction.length_squared() else pygame.Vector2(1,0)
            if turret['timer']<=0:
                for angle in (-12,0,12):
                    bullet=EnemyBullet(*turret['pos'],turret['direction'].rotate(angle),16,
                        speed=TUNING['turret_speed'],owner_id=id(self.boss))
                    bullet.remaining_life=5.
                    bullets.append(bullet)
                turret['timer']=TUNING['turret_cooldown']

    def emit_ring(self,bullets,base,offset=0,speed=330):
        from entities.enemy_bullet import EnemyBullet
        # Opposed 60-degree escape sectors remain open in both volleys.
        for angle in range(0,360,20):
            if 60<=angle<120 or 240<=angle<300:
                continue
            bullets.append(EnemyBullet(*self.boss.rect.center,base.rotate(angle+offset),
                15+self.phase*2,speed=speed,owner_id=id(self.boss)))

    def spawn_turrets(self,player):
        self.turrets=[]
        bounds=current_room_rect()
        solids=getattr(self,'arena_solids',())
        candidates=[]
        for y in range(bounds.top+250,bounds.bottom-170,130):
            for x in range(bounds.left+330,bounds.right-300,130):
                box=pygame.Rect(x-52,y-52,104,104)
                if any(box.colliderect(s) for s in solids) or pygame.Vector2(x,y).distance_to(player.rect.center)<270:
                    continue
                candidates.append(pygame.Vector2(x,y))
        for i in range(min(TUNING['turret_count'],len(candidates))):
            point=max(candidates,key=lambda p:min([p.distance_squared_to(t['pos']) for t in self.turrets] or [p.distance_squared_to(player.rect.center)]))
            candidates.remove(point)
            direction=pygame.Vector2(player.rect.center)-point
            self.turrets.append({'pos':point,'direction':direction.normalize() if direction.length_squared() else pygame.Vector2(1,0),
                'timer':1.8+i*.7,'life':TUNING['turret_seconds']})

    def action(self,event):
        return {'type':'boss_trial','event':event,'encounter':self,'phase':self.phase,
                'x':self.boss.rect.centerx,'y':self.boss.rect.centery,
                'direction':self.boss.windup_direction.copy(),'owner_id':id(self.boss)}

    def spawn_eyes(self,enemies):
        if self.eyes_spawned:
            return
        from entities.enemy import Enemy,EnemyType
        self.eyes_spawned=True
        bounds=current_room_rect()
        solids=getattr(self,'arena_solids',getattr(self.boss,'solid_rects',()))
        spawn_exclusions=[self.boss.rect.inflate(160,160)]
        if getattr(self.boss,'player_rect',None) is not None:
            spawn_exclusions.append(self.boss.player_rect.inflate(180,180))
        candidates=[]
        for fy in (.22,.5,.78):
            for fx in (.18,.5,.82):
                point=(round(bounds.left+bounds.width*fx),round(bounds.top+bounds.height*fy))
                rect=pygame.Rect(0,0,64,64)
                rect.center=point
                if bounds.contains(rect) and not any(rect.inflate(24,24).colliderect(s) for s in solids) and not any(rect.colliderect(s) for s in spawn_exclusions):
                    candidates.append(point)
        # Fall back to a dense free grid for heavily authored arenas.
        if len(candidates)<TUNING['eye_count']:
            for y in range(bounds.top+100,bounds.bottom-80,96):
                for x in range(bounds.left+100,bounds.right-80,96):
                    rect=pygame.Rect(x-40,y-40,80,80)
                    if not any(rect.colliderect(s) for s in (*solids,*spawn_exclusions)):
                        candidates.append((x,y))
        chosen=[]
        for _ in range(min(TUNING['eye_count'],len(candidates))):
            point=max(candidates,key=lambda p:min([pygame.Vector2(p).distance_squared_to(q) for q in chosen] or
                                                  [pygame.Vector2(p).distance_squared_to(bounds.center)]))
            candidates.remove(point)
            chosen.append(point)
        for point in chosen:
            eye=Enemy(*point,EnemyType.RANGED)
            eye.is_boss_eye=True
            eye.guardian_owner_id=id(self.boss)
            eye.rect=pygame.Rect(0,0,54,54)
            eye.rect.center=point
            eye.health=eye.max_health=TUNING['eye_health']
            eye.speed=0
            self.eyes.append(eye)
            enemies.append(eye)

    def resolve(self,action,enemies,bullets,effects,audio,player):
        event=action['event']
        if event=='rise':
            for bullet in bullets:
                if bullet.owner_id==id(self.boss):
                    bullet.kill()
            if audio:
                audio.play('boss_warning')
            return
        if event=='summon_warning':
            bounds=current_room_rect()
            solids=getattr(self,'arena_solids',())
            points=[]
            for y in range(bounds.top+110,bounds.bottom-100,100):
                for x in range(bounds.left+110,bounds.right-100,100):
                    box=pygame.Rect(x-40,y-40,80,80)
                    if any(box.colliderect(s) for s in solids) or pygame.Vector2(x,y).distance_to(player.rect.center)<190:
                        continue
                    points.append((x,y))
            self.spawn_points=[]
            count=TUNING['reinforcement_counts'][self.phase-1]
            for i in range(count):
                ideal=pygame.Vector2(bounds.center)+pygame.Vector2(360,0).rotate(i*360/count+30)
                available=[p for p in points if all(pygame.Vector2(p).distance_to(q)>130 for q in self.spawn_points)]
                if not available:
                    break
                self.spawn_points.append(min(available,key=lambda p:ideal.distance_squared_to(p)))
            if audio:
                audio.play('boss_phase')
            return
        if event=='reinforcements':
            from entities.enemy import Enemy,EnemyType
            self.guards=[]
            self.summon_count+=1
            for i,point in enumerate(self.spawn_points):
                # Authored enemy assets/AI are reused; no rewards or infinite waves.
                kind=(EnemyType.CHASER_FAST,EnemyType.RANGED_THREE,EnemyType.HUNTER,EnemyType.BRUTE,EnemyType.JUMPER_FAST,EnemyType.RANGED_FIVE)[i%6]
                guard=Enemy(*point,kind,difficulty=TUNING['reinforcement_difficulty'][self.phase-1])
                guard.is_boss_guard=True
                guard.guardian_owner_id=id(self.boss)
                self.guards.append(guard)
                enemies.append(guard)
            return
        if event=='landing':
            if effects:
                effects.ring(self.boss.rect.center,color=(100,230,255),radius=140,life=.5,width=3)
            if audio:
                audio.play('boss_exposed')
            return
        if event in ('intro','phase'):
            if event=='phase':
                self.spawn_turrets(player)
                if effects:
                    effects.message('SIEGE TURRETS — dodge until they fade',self.boss.rect.midbottom,color=(255,175,110))
            if event=='phase' and self.phase==2:
                self.spawn_eyes(enemies)
            if effects:
                effects.message(PHASE_NAMES[self.phase-1],self.boss.rect.midtop,color=(125,235,245))
            return
        if event=='healing':
            if audio:
                audio.play('boss_eye_heal')
            return
        if event=='warning':
            if audio:
                audio.play('boss_parry_ready' if self.pattern=='parry_orb' else 'boss_warning')
            return
        if event!='attack':
            return
        from entities.enemy_bullet import EnemyBullet
        base=self.boss.windup_direction
        if self.pattern=='parry_orb':
            bullet=EnemyBullet(action['x'],action['y'],base,24,speed=340,owner_id=id(self.boss))
            bullet.parryable=True
            bullet.radius=14
            bullet.rect=pygame.Rect(0,0,28,28)
            bullet.rect.center=bullet.pos
            bullet.remaining_life=5.
            bullets.append(bullet)
        elif self.pattern=='ring':
            self.emit_ring(bullets,base,speed=330+self.phase*20)
            if self.phase>=2:
                self.followups.append({'timer':TUNING['followup_delay'],'direction':base.copy()})
        else:
            if self.pattern=='fan':
                angles=(-28,-14,0,14,28)
            elif self.pattern=='cross':
                angles=(0,90,180,270)
            else:
                # Two deliberately empty sectors, not a solid unavoidable ring.
                angles=tuple(a for a in range(0,360,30) if a not in (60,90,240,270))
            for angle in angles:
                bullets.append(EnemyBullet(action['x'],action['y'],base.rotate(angle),
                                           15+self.phase*2,speed=310+self.phase*20,owner_id=id(self.boss)))
        if effects:
            effects.ring(self.boss.rect.center,color=(100,235,255),radius=130,life=.3,width=3)
        if audio:
            audio.play('boss_exposed')

    def draw(self,surface,camera):
        center=camera.apply_pos(pygame.Vector2(self.boss.rect.center))
        turret_art=sprite('boss_turret')
        for turret in self.turrets:
            pos=camera.apply_pos(turret['pos'])
            if turret_art:
                image=pygame.transform.flip(turret_art,True,False) if turret['direction'].x>0 else turret_art
                surface.blit(image,image.get_rect(midbottom=(round(pos.x),round(pos.y)+25)))
            pygame.draw.rect(surface,(55,35,35),(pos.x-24,pos.y+30,48,4))
            pygame.draw.rect(surface,(245,155,95),(pos.x-24,pos.y+30,48*max(0,turret['life']/TUNING['turret_seconds']),4))
            if turret['timer']<=TUNING['turret_warning']:
                from systems.ranged_presentation import draw_telegraph
                draw_telegraph(surface,pos,turret['direction'],600,turret['timer'],
                    TUNING['turret_warning'],self.boss._anim,palette=((240,110,80),(255,210,150)))
        if self.followups:
            pygame.draw.circle(surface,(255,185,110),center,110,3)
        if self.airborne:
            pygame.draw.ellipse(surface,(55,105,135),(center.x-65,center.y-14,130,28),2)
            center.y-=self.lift
            pygame.draw.circle(surface,(150,205,245),center,85,2)
            for point in self.spawn_points if self.state=='summoning' else ():
                pos=camera.apply_pos(pygame.Vector2(point))
                pygame.draw.circle(surface,(235,145,90),pos,38,3)
        if self.state=='windup':
            from systems.ranged_presentation import draw_telegraph
            colors=((75,220,245),(205,255,255)) if self.pattern=='parry_orb' else ((230,90,75),(255,200,155))
            if self.pattern=='ring':
                for angle in range(0,360,20):
                    if not (60<=angle<120 or 240<=angle<300):
                        v=self.boss.windup_direction.rotate(angle)
                        pygame.draw.circle(surface,colors[0],center+v*130,4)
            else:
                angles=(-28,0,28) if self.pattern=='fan' else (0,90,180,270) if self.pattern=='cross' else (0,)
                for angle in angles:
                    draw_telegraph(surface,center,self.boss.windup_direction.rotate(angle),650,
                        self.timer,TUNING['windup_seconds'][self.phase-1],self.boss._anim,palette=colors)
        if self.state in ('guard','windup','transition','intro'):
            color=(105,180,235) if self.state!='transition' else (210,160,245)
            pygame.draw.circle(surface,color,center,82,2)
        elif self.state=='exposed':
            for angle in range(0,360,90):
                v=pygame.Vector2(1,0).rotate(angle+self.boss._anim*30)
                pygame.draw.line(surface,(255,205,110),center+v*72,center+v*84,4)
        for eye in self.living_eyes():
            origin=camera.apply_pos(pygame.Vector2(eye.rect.center))
            direction=center-origin
            for i in range(1,10):
                p=origin+direction*((i+self.boss._anim*.8)%10/10)
                pygame.draw.circle(surface,(85,220,160),p,2)


def draw_hud(surface,font,boss):
    encounter=boss.encounter
    rect=pygame.Rect(surface.get_width()//2-320,24,640,98)
    pygame.draw.rect(surface,(9,17,29),rect,border_radius=9)
    phase=encounter.phase
    color=((110,195,245),(115,235,170),(210,150,255))[phase-1]
    title=font.render(f'RIFT WARDEN   /   {phase}: {PHASE_NAMES[phase-1]}',True,color)
    surface.blit(title,title.get_rect(midtop=(rect.centerx,rect.y+8)))
    track=pygame.Rect(rect.x+20,rect.y+42,600,12)
    pygame.draw.rect(surface,(45,35,49),track,border_radius=5)
    pygame.draw.rect(surface,(220,74,100),(track.x,track.y,round(track.w*boss.health/boss.max_health),12),border_radius=5)
    for ratio in (1/3,2/3):
        pygame.draw.line(surface,(230,235,245),(track.x+round(track.w*ratio),track.y),
                         (track.x+round(track.w*ratio),track.bottom),2)
    if encounter.airborne:
        hint=f'AIRBORNE — defeat the guards ({len(encounter.living_guards())})' if encounter.state=='airborne' else 'SUMMONING — boss is out of reach' if encounter.state!='landing' else 'LANDING — prepare to attack the core'
    elif encounter.state=='transition':
        hint='PHASE SHIFT — guard is closed'
    elif phase==2 and encounter.living_eyes():
        hint=f'{len(encounter.living_eyes())} HEALING EYES — shoot the eyes to stop healing'
    elif encounter.followups:
        hint='SECOND BURST — keep moving through an open sector'
    elif encounter.state=='exposed':
        hint=f'CORE EXPOSED  {encounter.timer:.1f}s — attack now'
    elif encounter.pattern=='parry_orb' and encounter.state=='windup':
        hint='Dodge sideways / Ninja: dash INTO the cyan orb'
    else:
        hint='GUARDED — dodge the tell, punish the recovery'
    label=font.render(hint,True,(210,225,232))
    surface.blit(label,label.get_rect(midtop=(rect.centerx,rect.y+65)))

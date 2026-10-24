"""Reproducible original synthesized WAV cues; no third-party recordings."""
import math
import random
import struct
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RATE=22050
SPECS={
 'heal_pickup':(.48,(523,659,784,1046),'warm'),
 'boost_pickup':(.42,(170,340,680,1200),'rise'),
 'time_stop_pickup':(.65,(950,700,440,220),'swell'),
 'time_stop_tick':(.085,(1700,),'tick'),
 'time_stop_tock':(.095,(1150,),'tick'),
 'time_stop_end':(.48,(220,440,880,660),'warm'),
 'boss_warning':(.55,(110,165,220),'swell'),
 'boss_exposed':(.28,(330,660,990),'rise'),
 'boss_guard':(.12,(180,),'tick'),
 'boss_eye_break':(.34,(1200,900,450),'glass'),
 'boss_eye_heal':(.20,(440,554),'warm'),
 'boss_parry_ready':(.65,(550,740,990),'swell'),
 'ninja_parry':(.42,(1600,2100,1050),'glass'),
 'player_hurt':(.22,(145,95),'glass'),
 'low_health':(.28,(110,85),'warm'),
}


def render(name, seconds, notes, texture):
    rng=random.Random(name)
    samples=[]
    for i in range(round(seconds*RATE)):
        t=i/RATE
        fraction=t/seconds
        note=min(len(notes)-1,int(fraction*len(notes)))
        f=notes[note]
        local=(fraction*len(notes))%1
        env=min(1,t/.008)*max(0,1-fraction)**1.6
        if texture=='tick':
            env=math.exp(-t*65)*min(1,t/.001)
            signal=.48*math.sin(2*math.pi*f*t)+.40*(rng.random()*2-1)
        elif texture=='rise':
            phase=2*math.pi*(140*t+950*t*t/seconds)
            signal=.6*math.sin(phase)+.18*(rng.random()*2-1)*(1-fraction)
        elif texture=='swell':
            env*=.3+.7*math.sin(math.pi*fraction)
            signal=.58*math.sin(2*math.pi*f*t)+.22*math.sin(2*math.pi*f*.5*t)
        elif texture=='glass':
            signal=sum(math.sin(2*math.pi*f*k*t)/k for k in (1,2.73,4.11))*.45
            env*=math.exp(-local*3)
        else:
            signal=.6*math.sin(2*math.pi*f*t)+.15*math.sin(2*math.pi*f*2*t)
            env*=.5+.5*math.sin(math.pi*local)
        samples.append(signal*env)
    peak=max(.001,max(abs(s) for s in samples))
    path=ROOT/'assets/sounds'/f'{name}.wav'
    with wave.open(str(path),'wb') as out:
        out.setparams((1,2,RATE,0,'NONE','not compressed'))
        out.writeframes(b''.join(struct.pack('<h',round(s/peak*24000)) for s in samples))
    print(path.name)


if __name__=='__main__':
    for name,(duration,notes,texture) in SPECS.items():
        render(name,duration,notes,texture)
    preview=ROOT/'debug_screenshots/pickup-audio-preview.wav'
    with wave.open(str(preview),'wb') as out:
        out.setparams((1,2,RATE,0,'NONE','not compressed'))
        for key in ('heal_pickup','boost_pickup','time_stop_pickup','time_stop_tick',
                    'time_stop_tock','time_stop_tick','time_stop_tock','time_stop_end','ninja_parry'):
            with wave.open(str(ROOT/'assets/sounds'/f'{key}.wav'),'rb') as clip:
                out.writeframes(clip.readframes(clip.getnframes()))
            out.writeframes(b'\x00\x00'*round(RATE*.32))
    print(preview)

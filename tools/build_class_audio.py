"""Original deterministic foley-like synthesis; no recordings or external licenses."""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100


def samples(kind, impact=False):
    duration = {'ninja': .16, 'engineer': .18, 'vampire': .24, 'gunslinger': .14}[kind]
    rng = random.Random(kind + str(impact))
    output, filtered = [], 0.
    for index in range(round(RATE * duration)):
        t = index / RATE
        p = t / duration
        noise = rng.uniform(-1, 1)
        filtered += .13 * (noise-filtered)
        attack = min(1., t/.003)
        decay = (1-p)**2
        if kind == 'ninja':
            phase = 2*math.pi*(1700*t-4500*t*t)
            value = .48*(noise-filtered)*math.sin(math.pi*p)**.6 + .25*math.sin(phase)*math.exp(-t*24)
            if impact:
                value += .45*math.sin(2*math.pi*2400*t)*math.exp(-t*35)
        elif kind == 'engineer':
            value = .34*math.sin(2*math.pi*(320*t+900*t*t))*math.exp(-t*18)
            value += filtered * (.8 if impact else .5)
            for onset in (.0, .028, .058):
                if t >= onset:
                    value += .28*noise*math.exp(-(t-onset)*160)
        elif kind == 'vampire':
            value = .5*math.sin(2*math.pi*(145*t-190*t*t))
            value += .55*filtered*math.sin(math.pi*p) + .12*math.sin(2*math.pi*440*t)*math.exp(-t*18)
            if impact:
                value += .32*noise*math.exp(-t*22)
        else:
            value = .65*noise*math.exp(-t*70) + .32*math.sin(2*math.pi*(110*t-120*t*t))*math.exp(-t*24)
            value += .18*math.sin(2*math.pi*(1800 if impact else 850)*t)*math.exp(-t*45)
        output.append(value*attack*decay)
    peak = max(.001, max(abs(value) for value in output))
    return b''.join(struct.pack('<h', round(value/peak*23000)) for value in output)


def main():
    directory = ROOT / 'assets/sounds'
    directory.mkdir(exist_ok=True)
    clips = []
    for kind in ('ninja', 'engineer', 'vampire', 'gunslinger'):
        for impact in (False, True):
            name = ('impact_' if impact else 'shoot_') + kind
            data = samples(kind, impact)
            with wave.open(str(directory / (name + '.wav')), 'wb') as output:
                output.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
                output.writeframes(data)
            clips.append(data)
            print(name)
    preview = ROOT / 'debug_screenshots/class-audio-preview.wav'
    preview.parent.mkdir(exist_ok=True)
    with wave.open(str(preview), 'wb') as output:
        output.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        for data in clips:
            output.writeframes(data + b'\x00\x00'*round(RATE*.35))


if __name__ == '__main__':
    main()

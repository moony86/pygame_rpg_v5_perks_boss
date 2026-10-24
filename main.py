import os
import sys


if __name__ == "__main__":
    if '--smoke-test' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--smoke-test', action='store_true')
        parser.add_argument('--smoke-report', required=True)
        args = parser.parse_args()
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        os.environ['BLUECUBE_DEV_TOOLS'] = '0'
        from systems.desktop_smoke import run
        run(args.smoke_report)
    else:
        from game import Game
        Game().run()

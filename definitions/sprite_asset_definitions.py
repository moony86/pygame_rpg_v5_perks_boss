SPRITE_FRAME_SIZE = (192, 192)


SPRITE_ANIMATION_DEFINITIONS = {
    "archer": {
        "scale": 0.36,
        "anchor": (0.5, 0.86),
        "states": {
            "idle": {
                "path": "Archer/Archer_Idle.png",
                "frames": 6,
                "fps": 7,
                "loop": True,
                "frame_size": SPRITE_FRAME_SIZE,
            },
            "run": {
                "path": "Archer/Archer_Run.png",
                "frames": 4,
                "fps": 12,
                "loop": True,
                "frame_size": SPRITE_FRAME_SIZE,
            },
            "shoot": {
                "path": "Archer/Archer_Shoot.png",
                "frames": 8,
                "fps": 14,
                "loop": False,
                "frame_size": SPRITE_FRAME_SIZE,
            },
        },
        "projectile": {
            "path": "Archer/Arrow.png",
            "frame_size": (64, 64),
        },
    },
    "warrior": {
        "scale": 0.36,
        "anchor": (0.5, 0.86),
        "states": {
            "idle": {
                "path": "Warrior/Warrior_Idle.png",
                "frames": 8,
                "fps": 7,
                "loop": True,
                "frame_size": SPRITE_FRAME_SIZE,
            },
            "run": {
                "path": "Warrior/Warrior_Run.png",
                "frames": 6,
                "fps": 12,
                "loop": True,
                "frame_size": SPRITE_FRAME_SIZE,
            },
            "attack1": {
                "path": "Warrior/Warrior_Attack1.png",
                "frames": 4,
                "fps": 14,
                "loop": False,
                "frame_size": SPRITE_FRAME_SIZE,
            },
            "attack2": {
                "path": "Warrior/Warrior_Attack2.png",
                "frames": 4,
                "fps": 14,
                "loop": False,
                "frame_size": SPRITE_FRAME_SIZE,
            },
            "attack": {
                "alias": "attack1",
            },
            "guard": {
                "path": "Warrior/Warrior_Guard.png",
                "frames": 6,
                "fps": 7,
                "loop": True,
                "frame_size": SPRITE_FRAME_SIZE,
            },
        },
    },
}

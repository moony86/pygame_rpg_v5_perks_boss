PERK_DEFINITIONS = [
    {"key": "rapid_fire", "name": "Fire Rate Boost", "desc": "+30% faster shooting", "legendary_desc": "+55% faster shooting", "tags": ["offense", "fire_rate", "gunslinger"], "build": "Gunslinger"},
    {"key": "power_rounds", "name": "Power Rounds", "desc": "+14 bullet damage, -10% fire rate", "legendary_desc": "+32 bullet damage, restores fire rate", "tags": ["offense", "damage", "gunslinger"], "build": "Gunslinger"},
    {"key": "hollow_point", "name": "Hollow Point", "desc": "+20 bullet damage, pierce becomes 0", "legendary_desc": "+45 bullet damage, pierce 0, +0.25 crit damage", "tags": ["offense", "damage", "crit", "tradeoff", "gunslinger"], "build": "Gunslinger"},
    {"key": "glass_cannon", "name": "Blood Pact", "desc": "+25 bullet damage, -40 max health, feeds Blood on risky combat", "legendary_desc": "+60 bullet damage, -40 max health, improves Blood overflow", "tags": ["offense", "damage", "tradeoff", "vampire", "shared"], "build": "Shared/Utility", "build_roles": ["Vampire", "Shared/Utility"]},
    {"key": "split_shot", "name": "Extra Projectile", "desc": "+1 bullet per shot, lower bullet damage", "legendary_desc": "+1 bullet per shot, improves split damage", "tags": ["offense", "projectile", "gunslinger"], "build": "Gunslinger"},
    {"key": "needle_rounds", "name": "Piercing Bullets", "desc": "+1 enemy pierced per bullet", "legendary_desc": "+3 pierce, +8 bullet damage", "tags": ["offense", "pierce", "gunslinger"], "build": "Gunslinger"},
    {"key": "kinetic_rounds", "name": "Kinetic Tuning", "desc": "+8 bullet damage, +70 bullet speed, improves helper damage if deployed", "legendary_desc": "+24 bullet damage, +180 bullet speed, stronger helper shots", "tags": ["offense", "damage", "speed", "engineer", "gunslinger"], "build": "Engineer", "build_roles": ["Engineer", "Gunslinger"]},
    {"key": "critical_spark", "name": "Critical Spark", "desc": "+30% critical hit chance", "legendary_desc": "+80% critical chance, +0.35 crit damage", "tags": ["offense", "crit", "gunslinger"], "build": "Gunslinger"},
    {"key": "overclock", "name": "Overclock", "desc": "+40% faster shooting, faster helper cadence, builds Ninja momentum, -15 max health", "legendary_desc": "+70% faster shooting, faster helper cadence, -20% skill cooldown", "tags": ["offense", "fire_rate", "tradeoff", "engineer", "ninja", "gunslinger"], "build": "Engineer", "build_roles": ["Engineer", "Ninja", "Gunslinger"]},
    {"key": "explosive_rounds", "name": "Explosive Rounds", "desc": "Explosive bullets; later picks improve blast radius and splash", "legendary_desc": "Bigger, stronger explosions and restores fire rate", "tags": ["offense", "explosive", "tradeoff", "gunslinger", "engineer"], "build": "Gunslinger", "build_roles": ["Gunslinger", "Engineer"]},
    {"key": "impact_drive", "name": "Impact Drone", "desc": "+45% bullet pushback and deploys a slow auto-helper", "legendary_desc": "+120% bullet pushback, +8 bullet damage, helper fires faster", "tags": ["offense", "utility", "engineer"], "build": "Engineer"},
    {"key": "blade_drone", "name": "Blade Drone", "desc": "Unlocks an orbiting close-range machine zone", "legendary_desc": "Second synchronized blade and faster contact control", "tags": ["offense", "utility", "engineer"], "build": "Engineer"},
    {"key": "bomber_drone", "name": "Bomber Drone", "desc": "Unlocks a rebuilding anti-group bomber machine", "legendary_desc": "Larger blast and a bounded second bombing run", "tags": ["offense", "explosive", "engineer"], "build": "Engineer"},
    {"key": "vital_core", "name": "Vital Core", "desc": "+48 max health, heal 24, increases Blood capacity", "legendary_desc": "+110 max health, full heal, more Blood capacity", "tags": ["defense", "health", "vampire", "shared"], "build": "Vampire"},
    {"key": "battle_recovery", "name": "Blood Recovery", "desc": "+24 room healing, gain Blood and heal on kills; unlocks Feast bursts", "legendary_desc": "+70 room healing, +35 max health, stronger Blood healing and Feast", "tags": ["defense", "regen", "heal", "vampire"], "build": "Vampire"},
    {"key": "scout_boots", "name": "Scout Boots", "desc": "+30 movement speed and light dash-strike damage", "legendary_desc": "+70 movement speed, resets dash cooldown, stronger dash reward", "tags": ["mobility", "speed", "dash", "ninja"], "build": "Ninja"},
    {"key": "phantom_step", "name": "Phantom Step", "desc": "+20 movement speed, -20 max health, improves dash-strike", "legendary_desc": "+50 movement speed, +0.20s dash invulnerability, dash cooldown restore", "tags": ["mobility", "speed", "dash", "tradeoff", "ninja"], "build": "Ninja"},
    {"key": "shadow_shuriken", "name": "Shadow Shuriken", "desc": "Dash hits throw a quick shuriken and improve momentum", "legendary_desc": "Stronger shuriken and higher Dash refund cap", "tags": ["mobility", "dash", "projectile", "ninja"], "build": "Ninja"},
    {"key": "sanguine_rounds", "name": "Sanguine Rounds", "desc": "Projectile hits wound enemies; wounded deaths drop Blood Orbs", "legendary_desc": "More wound stacks, Blood from bosses, and better orb yield", "tags": ["offense", "heal", "vampire"], "build": "Vampire"},
    {"key": "blood_bat", "name": "Blood Bat", "desc": "A single bat seeks wounded targets and returns carried Blood", "legendary_desc": "Bat dives faster, feeds harder, and rests for less time", "tags": ["offense", "summon", "vampire"], "build": "Vampire"},
    {"key": "blood_trail", "name": "Blood Trail", "desc": "Dashing through wounded enemies harvests Blood once per dash", "legendary_desc": "Improves harvest cap and unlocks Blood Moon surges", "tags": ["mobility", "dash", "vampire"], "build": "Vampire"},
]


PERK_SYNERGY_PAIRS = [
    ({"offense", "damage"}, {"offense", "crit"}, "CRIT SYNERGY"),
    ({"offense", "fire_rate"}, {"offense", "damage"}, "DPS SYNERGY"),
    ({"offense", "projectile"}, {"offense", "damage"}, "MULTI-HIT SYNERGY"),
    ({"offense", "explosive"}, {"offense", "damage"}, "BLAST SYNERGY"),
    ({"defense", "health"}, {"defense", "regen"}, "TANK SYNERGY"),
    ({"mobility", "speed"}, {"offense", "fire_rate"}, "RUSH SYNERGY"),
]

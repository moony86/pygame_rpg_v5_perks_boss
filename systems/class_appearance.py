"""Class skin selection is cosmetic and stable across hybrid perk choices."""
SKINS = {'Ninja': 'hero_ninja', 'Vampire': 'hero_vampire',
         'Engineer': 'hero_engineer', 'Gunslinger': 'hero_gunslinger'}


def hero_key(player):
    return SKINS.get(getattr(player, 'starter_build', ''), 'hero')

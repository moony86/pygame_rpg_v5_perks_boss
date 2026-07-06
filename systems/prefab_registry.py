from definitions.prefab_definitions import PREFAB_DEFINITIONS
from systems.prefab_factory import PrefabFactory


class PrefabRegistry:
    def __init__(self, factory=None, definitions=None):
        self.factory = factory or PrefabFactory()
        self.definitions = definitions or PREFAB_DEFINITIONS

    def require(self, prefab_id):
        try:
            return self.definitions[prefab_id]
        except KeyError as error:
            raise KeyError(f"Unknown prefab id: {prefab_id!r}") from error

    def spawn_prefab(self, prefab_id, **overrides):
        definition = self.require(prefab_id)
        return self.factory.create(definition, **overrides)

    def ids_for_type(self, prefab_type):
        return [
            prefab_id
            for prefab_id, definition in self.definitions.items()
            if definition.prefab_type == prefab_type
        ]

    def validate(self):
        seen = set()
        for prefab_id, definition in self.definitions.items():
            if not prefab_id:
                raise ValueError("Prefab definition has an empty registry key")
            if definition.id != prefab_id:
                raise ValueError(f"Prefab {prefab_id!r} stores mismatched id {definition.id!r}")
            if definition.id in seen:
                raise ValueError(f"Duplicate prefab id: {definition.id!r}")
            if not definition.prefab_type:
                raise ValueError(f"Prefab {prefab_id!r} has an empty prefab_type")
            seen.add(definition.id)
        return True

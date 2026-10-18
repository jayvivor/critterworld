from .core import *
import random


HABITAT_NAMES = [
    "pond",
    "meadow",
    "forest",
    "beach",
    "jungle",
    "mountain",
    "cave",
    "burrow",
]

LIFE_STAGE_NAMES = [
    "baby",
    "adult",
    "senior",
]


HABITATS = [Habitat(name=name) for name in HABITAT_NAMES]

ANIMAL_LIFE_STAGES = [
    LifeStage(
        name="baby",
        length=24*30,
        modifier_map={"size": -2, "smarts": -10},
    ),
    LifeStage(
        name="adult",
        length=24*30*12*10,
        modifier_map={},
    ),
    LifeStage(
        name="senior",
        length=24*30*12*5,
        modifier_map={"speed": -5},
    )
]

PLANT_LIFE_STAGES = [
    LifeStage(
        name="seed",
        length=24*30,
        modifier_map={"size": -2},
    ),
    LifeStage(
        name="sprouted",
        length=24*30*12*100,
        modifier_map={},
    ),
]


COLORS = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "indigo",
    "violet",
]


def get_random_plant(name: Optional[str]=None):
    name = name or f"{str(uuid4()).split("-")[0]} (Plant)"
    return Critter(
        name=name,
        size=random.randint(1, 100),
        habitat=random.choice(HABITATS),
        life_stages=PLANT_LIFE_STAGES,
        traits=[],
        color=random.choice(COLORS)
    )

def get_random_animal(name: Optional[str]=None):
    name = name or f"{str(uuid4()).split("-")[0]} (Animal)"
    return Critter(
        name=name,
        size=random.randint(1, 100),
        habitat=random.choice(HABITATS),
        life_stages=ANIMAL_LIFE_STAGES,
        traits=[],
        color=random.choice(COLORS)
    )

def get_random_critter_instance():
    if random.random() > 0.3:
        return AnimalInstance(
            behavior_machine=get_animal_machine(),
            source=get_random_animal(),
        )
    return PlantInstance(
        behavior_machine=get_plant_machine(),
        source=get_random_plant()
    )


def get_arena(radius: int=10000, critter_count: int=1000):

    arena = Arena(
        name="EZ Arena",
        critter_instance_map={
            Coordinates(
                x=float(random.randint(-radius, radius)),
                y=float(random.randint(-radius, radius)),
                z=float(random.randint(-radius, radius)),
            ): get_random_critter_instance()
            for _ in range(critter_count)
        },
        resource_instance_map={},
    )
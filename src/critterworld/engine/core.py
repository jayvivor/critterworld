from enum import Enum
from typing import Generic, TypeVar

from critterworld.engine.base import BehaviorCondition, BehaviorTrigger

from .base import *



class Replenishable(Base):

    sources: list[type]
    bar: int = bounded_int()
    threshold: int = 20



class PlantInstance(CritterInstance): ...

    # They don't do much...


class Carcass[Critter](Resource):

    source: Critter
    stored_energy: int = bounded_int()


class Water(Resource): ...


class AnimalInstance(CritterInstance):

    flee_injury_threshold: int = 20
    flee_distance: float = 50
    melee_distance: float = 1.0
    default_need_threshold: int = 20

    modifiers: list[PropertyModifier] = Field(default_factory=list)

    sex: bool = Field(default_factory=lambda: random.choice([True, False])) # For now, let's just do "is_male" out of respect for the patriarchy

    # Typically need to sleep, eat, drink...
    hunger: Replenishable = Field(default_factory=lambda: Replenishable(sources=[Carcass]))
    thirst: Replenishable = Field(default_factory=lambda: Replenishable(sources=[Water]))
    tiredness: int = bounded_int()  # A sort of replenishable, but this doesn't require any resources, just rest

    # Mood ought to be optimized
    happiness: int = bounded_int()


    @property
    def should_flee(self):
        # For now, just checks if the critter CAN flee
        return self.injury < self.flee_injury_threshold

    @property
    def is_healthy(self):
        return not self.injury

    @property
    def needs(self):
        other_bars: list[str] = ["tiredness"]
        stat_names = {
            k for k, v in self.model_dump().items() 
            if (
                isinstance(v, Replenishable) 
                and v.bar <= v.threshold
            )
            or (
                isinstance(v, int)
                and k in other_bars
                and v <= self.default_need_threshold
            )
        }
        return stat_names



# Simple/example behaviors, triggers, and conditions
# TODO: It should be possible for an "AnimalInstance" class or instance to override one of these with their own
class DetectPredator(BehaviorTrigger):
    
    description = "Notice a larger, animal-ish critter in the vicinity."

    def evaluate(self, critter_instance, arena):
        detected: list[CritterInstance] = []

        nearby = critter_instance.detect_vicinity(arena)

        for distance, other_ci in nearby.items():
            match other_ci:
                case PlantInstance():
                    continue
                case AnimalInstance():
                    if critter_instance.get_modified_stat("size") < other_ci.get_modified_stat("size"):
                        detected.append(critter_instance)

        return bool(detected)


class DetectPrey(BehaviorTrigger):
    
    description = "Notice a smaller, animal-ish critter in the vicinity."

    def evaluate(self, critter_instance, arena):
        detected: list[CritterInstance] = []

        nearby = critter_instance.detect_vicinity(arena)

        for distance, other_ci in nearby.items():
            match other_ci:
                case PlantInstance():
                    continue
                case AnimalInstance():
                    if critter_instance.get_modified_stat("size") > other_ci.get_modified_stat("size"):
                        detected.append(critter_instance)

        return bool(detected)


class DetectResource(BehaviorTrigger):

    description = "Notice a consumable resource in the vicinity."

    def evaluate(self, critter_instance, arena):
        detected: list[ResourceInstance] = []

        nearby = critter_instance.resource_vicinity(arena)

        for distance, ri in nearby.items():
            if critter_instance.can_detect_resource(ri, distance):
                detected.append(ri)

        return bool(detected)


# Baselines
class Idle(Behavior):

    description = "Do nothing."

    cost: dict[str, float] = {"energy":0.01}
    triggers: list[BehaviorTrigger] = []
    conditions: list[BehaviorCondition] = []

    def act(self, critter_instance, arena):
        return None


# Proactives
class Play(Behavior):

    description = "Sharpen skills in a safe environment."

    cost: dict[str, float] = {"energy":1.0}
    triggers: list[BehaviorTrigger] = []
    conditions: list[BehaviorCondition] = []

    def act(self, critter_instance, arena):
        return None


class Hunt(Behavior):

    description = "Search for resources to consume and/or critters to turn into consumable resources."


class Rest(Behavior):

    description = "Recover energy by resting."


# Reactives
class Chase(Behavior):

    description = "Pursue another critter. By default, use maximum speed and effort."


class Fight(Behavior):

    description = "Engage in combat with another critter. By default, fight until it is dead."


class Flee(Behavior):

    description = "Leave the vicinity."


class Consume(Behavior):

    description = "Take resources from an entity or critter."


class Hide(Behavior):

    description = "Stay in the general area, but try not to be detected by other critters."


class Mate(Behavior):

    description = "Fuck."


class Reproduce(Behavior):

    description = "Spawn a new critter, with a slight chance at mutation."


class AnimalBehaviors(Enum):

    # Baseline
    IDLE = Idle

    # Proactive
    PLAY = Play
    HUNT = Hunt
    REST = Rest

    # Reactive
    CHASE = Chase
    FIGHT = Fight
    FLEE = Flee
    CONSUME = Consume
    HIDE = Hide

    # Long-Term
    MATE = Mate
    REPRODUCE = Reproduce


class PlantBehaviors(Enum):

    # Baseline
    IDLE = Idle



def get_plant_machine(behavior_overrides: Optional[dict[type[Behavior], Behavior]]=None):
    behavior_overrides = behavior_overrides or {}
    behaviors = [behavior_overrides.get(behavior_type.value) or behavior_type.value.default() for behavior_type in PlantBehaviors]
    
    machine = Machine(
        states=[b.name for b in behaviors],
        initial=PlantBehaviors.IDLE.value.default().name,
    )

    for behavior in behaviors:
        behavior.add_transitions(machine)
    
    return machine


def get_animal_machine(behavior_overrides: Optional[dict[type[Behavior], Behavior]]=None):
    behavior_overrides = behavior_overrides or {}
    behaviors = [behavior_overrides.get(behavior_type.value) or behavior_type.value.default() for behavior_type in AnimalBehaviors]
    
    machine = Machine(
        states=[b.name for b in behaviors],
        initial=AnimalBehaviors.IDLE,
    )

    for behavior in behaviors:
        behavior.add_transitions(machine)

    # # Fight/Flight
    # machine.add_transition(trigger="detect_predator", source="*", dest="flee", conditions=["should_flee"])
    # machine.add_transition(trigger="detect_predator", source="*", dest="hide")
    # machine.add_transition(trigger="attacked", source="*", dest="fight")
    # machine.add_transition(trigger="")

    # machine.add_transition(trigger="detect_prey")


    return machine
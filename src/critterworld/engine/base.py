from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Protocol, Optional, ClassVar, Self, Iterable
# from statemachine import State, StateChart
# from statemachine.transition_list import TransitionList
# from statemachine.transition import Transition
from transitions import Machine, Transition
import random
from abc import ABC, abstractmethod
from enum import Enum
from uuid import UUID, uuid4


def bounded_int(upper: int=100, lower: int=0):
    return Field(le=upper, ge=lower)

def bounded_float(upper: float=100.0, lower: float=0.0):
    return Field(le=upper, ge=lower)


class Base(BaseModel):

    hash_id: UUID = Field(exclude=True, default_factory=uuid4)

    def __hash__(self):
        return hash(self.hash_id)


# class TrafficLightMachine(StateChart):
#     "A traffic light machine"
#     green = State(initial=True)
#     yellow = State()
#     red = State()
#     ...
#     cycle: TransitionList = (
#         green.to(yellow)
#         | yellow.to(red)
#         | red.to(green)
#     )
#     ...
#     def before_cycle(self, event: str, source: State, target: State):
#         return f"Running {event} from {source.id} to {target.id}"
#     ...
#     def on_enter_red(self):
#         print("Don't move.")
#     ...
#     def on_exit_red(self):
#         print("Go ahead!")

class Critter(Base):

    # Function
    # behavior_chart: BehaviorChart
    traits: list[Trait]
    habitat: Habitat
    life_stages: list[LifeStage]
    size: float = bounded_float()
    speed: float = bounded_float()
    smarts: float = bounded_float()
    combat: float = bounded_float()
    perception: float = bounded_float()
    stealth: float = bounded_float()

    # Cosmetic
    name: str
    color: str
    

    @property
    def scurry(self):
        return self.speed

    @property
    def trick(self):
        return self.smarts

    def __str__(self):
        return f"{self.name} (Critter)"


class Resource(Base):
    
    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()


# class BehaviorChart(StateChart):

    # cycle: TransitionList


# DEFAULT_ANIMAL_CYCLE = (

# )


class Habitat(Base):

    name: str


class PropertyModifier(Base):
    
    modifier_map: dict[str, float] # Ex: a "slow" critter might have great "scurry" bc of a trait. Eventually this should map to functions for conditions and flexibility; for now, just a +/-



class Trait(PropertyModifier):

    name: str
    description: str

    def mutate(self) -> Self: ...


class LifeStage(PropertyModifier):

    name: str
    description: Optional[str] = None
    length: int  # Number of "turns". Let's say each turn is 1 hour.


class ArenaContext(Protocol):

    def critter_vicinity(self, ci, range=None) -> dict[float, "CritterInstance"]: ...
    def resource_vicinity(self, ci, range=None) -> dict[float, "ResourceInstance"]: ...


class CritterInstance(Base):

    id: UUID = Field(default_factory=uuid4)
    source: Critter
    behavior_machine: Machine

    @property
    def state(self):
        return self.behavior_machine.state

    # statuses
    energy: int = bounded_int()
    injury: int = bounded_int()

    def get_modified_stat(self, stat: str) -> int | float:

        # sum all property mods
        base_stat = getattr(self.source, stat)
        if not isinstance(base_stat, float) or not isinstance(base_stat, int):
            # TODO: This can technically return a non-number
            return base_stat

        modifiers: list[PropertyModifier] = [v for _k, v in self.model_dump().items() if isinstance(v, PropertyModifier)]
        iterable_modifiers: list[Iterable[PropertyModifier]] = [v for _k, v in self.model_dump().items() if isinstance(v, Iterable) and all(isinstance(pm, PropertyModifier) for pm in v)]
        for im in iterable_modifiers:
            modifiers.extend(im)
        return base_stat + sum(m.modifier_map.get(stat) or 0 for m in modifiers)


    # abilities
    def can_detect(self, other: CritterInstance, distance: float, fuzz: Optional[float]=5.0):

        perception = self.get_modified_stat("perception")
        stealth = other.get_modified_stat("stealth")

        if fuzz is not None:
            perception = perception + random.gauss(sigma=fuzz)
            stealth = stealth + random.gauss(sigma=fuzz)

        return perception > stealth

    def can_detect_resource(self, resource: ResourceInstance, distance: float, fuzz: Optional[float]=5.0):
        # TODO: This could be a fun lever to pull later
        return True


    def detect_vicinity(self, ctx: ArenaContext):
        nearby = ctx.critter_vicinity(self)

        return {
            distance: ci for distance, ci in ctx.critter_vicinity(self).items()
            if self.can_detect(ci, distance)
        }

    def resource_vicinity(self, ctx: ArenaContext):
        nearby = ctx.resource_vicinity(self)

        return {
            distance: ri for distance, ri in ctx.resource_vicinity(self).items()
            if self.can_detect_resource(ri, distance)
        }
    

    # def behave(self, ctx: ArenaContext):
    #     self.behavior_machine

    def __str__(self):
        return f"Instance (ID: {self.id}) for {self.source}"


class ResourceInstance(Base):

    source: Resource


class Coordinates(Base):

    x: float
    y: float
    z: float

    def distance_to(self, other: Self):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5


class Arena(Base):

    name: Optional[str] = None
    critter_instance_map: dict[Coordinates, CritterInstance]
    resource_instance_map: dict[Coordinates, ResourceInstance]
    default_vicinity_range: float = 100  # Let's say it's in meters


    def critter_vicinity(self, ci: CritterInstance, range: Optional[float]=None) -> dict[float, CritterInstance]:

        # Get specific critter
        ci_coords = None
        for coords, c in self.critter_instance_map.items():
            if ci == c:
                ci_coords = coords
                break

        if not ci_coords:
            raise KeyError(f"Critter instance {ci} not found in arena '{self}'.")

        return {
            ci_coords.distance_to(other_coords): other_ci
            for other_coords, other_ci in self.critter_instance_map.items()
            if other_ci != ci_coords
            and ci_coords.distance_to(other_coords) <= range
        }


    def resource_vicinity(self, ci: CritterInstance, range: Optional[float]=None) -> dict[float, ResourceInstance]:
        # Get specific critter
        ci_coords = None
        for coords, c in self.critter_instance_map.items():
            if ci == c:
                ci_coords = coords
                break

        if not ci_coords:
            raise KeyError(f"Critter instance {ci} not found in arena '{self}'.")

        return {
            ci_coords.distance_to(ri_coords): ri
            for ri_coords, ri in self.resource_instance_map.items()
            if ri != ci_coords
            and ci_coords.distance_to(ri_coords) <= range
        }



    def __str__(self):
        return self.name or "Unnamed Arena"



class Species(Base):

    # Function
    name: str
    template: Critter
    deviation_range: int = 10  # How far from the template a trait can go before it's a different species

    def includes(self, critter: Critter):

        deviation_atts = [
            "size",
            "speed",
            "smarts",
            "combat",
        ]

        return all(abs(getattr(self.template, da) - getattr(critter, da)) <= self.deviation_range for da in deviation_atts)


    def spawn(self, mutation_chance: float, mutation_std: float) -> CritterInstance: ...


class BehaviorTrigger(Base, ABC):

    description: ClassVar[Optional[str]] = None

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @abstractmethod
    def evaluate(self, critter_instance: CritterInstance, arena: Arena) -> bool: ...

    @property
    def state_trigger(self) -> str:
        return f"trigger_{self.name.lower().replace(" ","_")}"


class BehaviorCondition(Base, ABC):

    description: ClassVar[Optional[str]] = None

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @abstractmethod
    def evaluate(self, critter_instance: CritterInstance, arena: Arena) -> bool: ...

    @property
    def state_condition(self) -> str:
        return f"condition_{self.name.lower().replace(" ","_")}"


class Behavior(Base, ABC):
    
    description: ClassVar[Optional[str]] = None
    cost: dict[str, float] = {}
    from_states: Optional[list[Self]] = None
    triggers: list[BehaviorTrigger] = []
    conditions: list[BehaviorCondition] = []

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    def check(self, critter_instance: CritterInstance, arena: Arena) -> bool:
        return all(c.evaluate(critter_instance, arena) for c in self.conditions)

    @abstractmethod
    def act(self, critter_instance: CritterInstance, arena: Arena): ...

    def add_transitions(self, machine: Machine):
        for trigger in self.triggers:
            machine.add_transition(
                trigger=trigger.state_trigger,
                source=[state.name for state in self.from_states] if self.from_states is not None else "*",
                dest=self.name,
                conditions=["_".join([self.name, c.state_condition]) for c in self.conditions],
            )
        return machine


    @classmethod
    def default(cls):
        return cls()
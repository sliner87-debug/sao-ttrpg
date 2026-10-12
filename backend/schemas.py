from pydantic import BaseModel, Field
from typing import List, Optional

class ActorActionSchema(BaseModel):
    actor_id: str = Field(description="The ID of the actor making the move (e.g. companion_ren, enemy_01)")
    intended_action: str = Field(description="The narrative action the actor wants to take")
    target: Optional[str] = Field(None, description="The ID of the target, if any")
    internal_thought: str = Field(description="Brief internal thought explaining their reasoning based on their personality and fears")

class VisibleEntity(BaseModel):
    id: str
    name: str
    type: str = Field(description="'hostile', 'friendly', or 'neutral'")
    status: List[str] = Field(description="Visible status conditions like 'Bloodied', 'Prone', 'Intact'")

class VisibleEnvironment(BaseModel):
    location: str
    description: str
    environmental_effects: List[str]

class VisibleRoomSchema(BaseModel):
    turn_number: int
    environment: VisibleEnvironment
    entities: List[VisibleEntity]

class PlayerStateUpdates(BaseModel):
    xp_change: Optional[int] = Field(0, description="Amount of XP gained")
    col_change: Optional[int] = Field(0, description="Amount of Col gained or lost")
    inventory_add: Optional[List[str]] = Field([], description="Items to add to inventory")
    inventory_remove: Optional[List[str]] = Field([], description="Items to remove from inventory")
    location: Optional[str] = Field(None, description="New location name if moved")
    hp_change: Optional[int] = Field(0, description="HP gained or lost by the human player")

class EntityHpChange(BaseModel):
    entity_id: str = Field(description="Target entity ID e.g. player, enemy_01, companion_ren")
    hp_delta: int = Field(description="HP change (negative for damage, positive for healing)")

class EntityStatusUpdate(BaseModel):
    entity_id: str = Field(description="Target entity ID")
    statuses: List[str] = Field(description="Current list of status conditions")

class TurnResolutionSchema(BaseModel):
    narrative_recap: str = Field(description="Exciting narrative paragraph describing how the turn played out without raw math formulas")
    combat_logs: List[str] = Field(default=[], description="List of all mechanical dice rolls, saving throws, AC checks, and damage calculations (e.g. 'Attack: 1d20+5 = 17 vs AC 14 | Hit!', 'Damage: 1d10+3 = 9 Slashing')")
    hp_changes: List[EntityHpChange] = Field(description="List of HP changes for entities")
    status_updates: List[EntityStatusUpdate] = Field(description="List of updated statuses for entities")
    encounter_active: bool = Field(description="True if the fight continues, False if it is over")
    player_state_updates: Optional[PlayerStateUpdates] = Field(None, description="Updates to the human player's sheet")

class EntityPersonaSchema(BaseModel):
    id: str = Field(description="Unique entity identifier (e.g. enemy_01, npc_barkeep)")
    name: str = Field(description="The distinctive name or moniker of the entity")
    species_or_type: str = Field(description="Species or construct archetype (e.g. Runic Quarry Golem, Grafted Splicer)")
    role: str = Field(description="'hostile_monster', 'neutral_npc', 'ally', 'merchant', etc.")
    backstory_interview: str = Field(description="The entity's direct, first-person narrative answer to: 'What has your life been up to now in this terraformed crucible?'")
    personality: str = Field(description="Core demeanor, temperament, and emotional tendencies")
    quirks: List[str] = Field(description="Unique sensory ticks, physical habits, or vocal quirks")
    dreams_and_desires: str = Field(description="What this entity yearns for, seeks, or strives toward")
    fears_and_dreads: str = Field(description="What terrifies them, what breaks their morale, existential dread")
    tactical_style: str = Field(description="How they fight or survive when threatened")
    behavior_prompt: str = Field(description="The exact system prompt to govern this entity's independent turn-by-turn AI actions")

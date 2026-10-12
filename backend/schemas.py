from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ActorActionSchema(BaseModel):
    actor_id: str = Field(description="The ID of the actor making the move (e.g. companion_ren)")
    intended_action: str = Field(description="The narrative action the actor wants to take")
    target: Optional[str] = Field(None, description="The ID of the target, if any")
    internal_thought: str = Field(description="Brief tactical reasoning for this action based on their behavior_prompt")

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

class TurnResolutionSchema(BaseModel):
    narrative_recap: str = Field(description="Exciting narrative paragraph describing how the turn played out")
    hp_changes: Dict[str, int] = Field(description="Dictionary mapping entity_ids to their HP delta (e.g. {'enemy_01': -15})")
    status_updates: Dict[str, List[str]] = Field(description="Dictionary mapping entity_ids to their new status lists")
    encounter_active: bool = Field(description="True if the fight continues, False if it is over")
    player_state_updates: Optional[PlayerStateUpdates] = Field(None, description="Updates to the human player's sheet")

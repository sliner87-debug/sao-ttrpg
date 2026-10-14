from pydantic import BaseModel, Field
from typing import List, Optional

class ActorActionSchema(BaseModel):
    actor_id: str = Field(description="The ID of the actor making the move (e.g. companion_ren, enemy_01)")
    intended_action: str = Field(description="The narrative action the actor wants to take")
    target: Optional[str] = Field(None, description="The ID of the target, if any")
    internal_thought: str = Field(description="Brief internal thought explaining their reasoning based on their personality and fears")

class ActiveDebuffSchema(BaseModel):
    debuff_id: str = Field(description="Unique ID for the debuff (e.g. 'hydraulic_armor_shred', 'corrosive_slag_dr_zero')")
    name: str = Field(description="Display name of the debuff")
    ac_penalty: int = Field(default=0, description="Negative adjustment to Armor Class (e.g. -4 for -4 AC)")
    dr_override: Optional[int] = Field(default=None, description="If set (e.g. 0), overrides the target's Damage Reduction (DR) to this value")
    turns_remaining: int = Field(default=3, description="Number of combat turns remaining (-1 for permanent)")
    source: Optional[str] = Field(default="", description="Source ability or Dual-Tech that applied the debuff")

class VisibleEntity(BaseModel):
    id: str
    name: str
    type: str = Field(description="'hostile', 'friendly', or 'neutral'")
    status: List[str] = Field(description="Visible status conditions like 'Bloodied', 'Prone', 'Intact'")
    active_debuffs: Optional[List[ActiveDebuffSchema]] = Field(default=[], description="Active mechanical debuffs (e.g. -4 AC, 0 DR) currently affecting this entity")

class VisibleEnvironment(BaseModel):
    location: str
    description: str
    environmental_effects: List[str]

class VisibleRoomSchema(BaseModel):
    turn_number: int
    environment: VisibleEnvironment
    entities: List[VisibleEntity]

class SkillMasteryUpdate(BaseModel):
    name: str = Field(description="Skill name (e.g. Battleaxe Mastery, Arcana, Perception)")
    mastery_change: int = Field(default=1, description="Mastery points gained (1-1000 scale)")
    description: Optional[str] = Field(default="", description="Updated description or milestone perk")

class GraftInstallation(BaseModel):
    slot: str = Field(description="Anatomical slot: 'head', 'torso', 'left_arm', 'right_arm', 'legs', or 'spine'")
    name: str = Field(description="Name of the graft installed")
    strain: int = Field(default=1, description="Strain cost of this graft (typically 1 to 3)")
    effect: Optional[str] = Field(default="", description="Mechanical perks and stat adjustments")

class PlayerStateUpdates(BaseModel):
    xp_change: Optional[int] = Field(0, description="Amount of XP gained")
    col_change: Optional[int] = Field(0, description="Amount of Col gained or lost")
    inventory_add: Optional[List[str]] = Field([], description="Items to add to inventory")
    inventory_remove: Optional[List[str]] = Field([], description="Items to remove from inventory")
    location: Optional[str] = Field(None, description="New location name if moved")
    coord_x: Optional[int] = Field(None, description="New X coordinate (0-100) on Sector 1 map if position changed")
    coord_y: Optional[int] = Field(None, description="New Y coordinate (0-100) on Sector 1 map if position changed")
    hp_change: Optional[int] = Field(0, description="HP gained or lost by the human player")
    spells_add: Optional[List[str]] = Field(default=[], description="New spells learned (e.g. from ability fusion or spell slates)")
    feats_add: Optional[List[str]] = Field(default=[], description="New feats or fused techniques learned")
    skill_updates: Optional[List[SkillMasteryUpdate]] = Field(default=[], description="Skill mastery improvements from actions")
    grafts_installed: Optional[List[GraftInstallation]] = Field(default=[], description="Grafts surgically installed into anatomical slots")
    weather_change: Optional[str] = Field(default=None, description="Weather condition shift (e.g. runic_mist, glitch_freeze, clear)")
    time_minutes_advanced: Optional[int] = Field(default=0, description="Minutes advanced by actions or travel")
    boss_break_gauge_damage: Optional[int] = Field(default=0, description="Damage dealt to boss Break Gauge")
    boss_staggered: Optional[bool] = Field(default=False, description="True if boss has been staggered this turn")
    homestead_action: Optional[str] = Field(default=None, description="Homestead action summary if safe-zone resting or facility used")
    raid_floor_advance: Optional[int] = Field(default=0, description="Number of floors advanced in the active 1-50 Floor Raid")
    anti_crystal_triggered: Optional[bool] = Field(default=False, description="True if a Crimson Anti-Crystal Trap Room was triggered or disabled")
    last_attack_claimed: Optional[bool] = Field(default=False, description="True if the player claimed the Last Attack (LA) bonus on a Raid Boss")
    unique_skill_awakened: Optional[str] = Field(default=None, description="ID or name of a 1-of-1 Unique Skill awakened this turn")



class EntityHpChange(BaseModel):
    entity_id: str = Field(description="Target entity ID e.g. player, enemy_01, companion_ren")
    hp_delta: int = Field(description="HP change (negative for damage, positive for healing)")

class EntityStatusUpdate(BaseModel):
    entity_id: str = Field(description="Target entity ID")
    statuses: List[str] = Field(description="Current list of status conditions")

class EntityDebuffUpdate(BaseModel):
    entity_id: str = Field(description="Target entity ID receiving the mechanical debuff")
    debuff: ActiveDebuffSchema = Field(description="The structured mechanical debuff applied to the entity")

class TurnResolutionSchema(BaseModel):
    narrative_recap: str = Field(description="Exciting narrative paragraph describing how the turn played out without raw math formulas")
    tactical_state_footer: Optional[str] = Field(default="", description="Clinical Cardinal System Tactical State Footer summarizing Current Node, Salvageable/Interactive Objects, Party Condition, and awaiting player input")
    combat_logs: List[str] = Field(default=[], description="List of all mechanical dice rolls, saving throws, AC checks, and damage calculations (e.g. 'Attack: 1d20+5 = 17 vs AC 14 | Hit!', 'Damage: 1d10+3 = 9 Slashing')")
    hp_changes: List[EntityHpChange] = Field(description="List of HP changes for entities")
    status_updates: List[EntityStatusUpdate] = Field(description="List of updated statuses for entities")
    debuff_updates: Optional[List[EntityDebuffUpdate]] = Field(default=[], description="Mechanical debuffs applied to entities this turn (e.g. -4 AC from Foundry Hydraulic Overdrive, 0 DR from Corrosive Slag-Shatter)")
    encounter_active: bool = Field(description="True if the fight continues, False if it is over")
    environment_update: Optional[VisibleEnvironment] = Field(default=None, description="Updated room location, description, and environmental effects if the party moved or the environment changed")
    cleared_entities: Optional[List[str]] = Field(default=[], description="List of entity IDs that are permanently dead, destroyed, or departed from the room")
    new_entities: Optional[List[VisibleEntity]] = Field(default=[], description="New NPCs or entities present in the new location (e.g. Doc Mercer, Quartermaster Vane, townsfolk)")
    image_prompt: Optional[str] = Field(default="", description="A highly detailed prompt for an anime-style image generation of the current scene")
    global_news_add: Optional[List[str]] = Field(default=[], description="1-2 global or regional news blurbs if a rest, boss defeat, or faction event occurred")
    weather: Optional[str] = Field(default=None, description="Current ambient weather condition")
    time_of_day: Optional[str] = Field(default=None, description="Current time of day / diurnal period")
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

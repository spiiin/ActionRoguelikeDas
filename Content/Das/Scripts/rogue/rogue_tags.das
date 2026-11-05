options gen2
module rogue_tags public
require ue_gameplay_tags public

// Resolve on use, after UE has initialized its tag registry. Keep tag paths here
// rather than storing runtime-owned GameplayTag values in global initializers.

def rogue_tag_primary_attack() : GameplayTag { return ue_tag("Action.PrimaryAttack") }

def rogue_tag_secondary_attack() : GameplayTag { return ue_tag("Action.SecondaryAttack") }

def rogue_tag_special_attack() : GameplayTag { return ue_tag("Action.SpecialAttack") }

def rogue_tag_sprint() : GameplayTag { return ue_tag("Action.Sprint") }

def rogue_tag_drop_loot() : GameplayTag { return ue_tag("Action.DropLoot") }

def rogue_tag_attacking() : GameplayTag { return ue_tag("StatusEffect.Attacking") }

def rogue_tag_sprinting() : GameplayTag { return ue_tag("StatusEffect.Sprinting") }

def rogue_tag_stunned() : GameplayTag { return ue_tag("StatusEffect.Stunned") }

def rogue_tag_health() : GameplayTag { return ue_tag("Attribute.Health") }

def rogue_tag_health_max() : GameplayTag { return ue_tag("Attribute.HealthMax") }

def rogue_tag_rage() : GameplayTag { return ue_tag("Attribute.Rage") }

def rogue_tag_move_speed() : GameplayTag { return ue_tag("Attribute.MoveSpeed") }

def rogue_tag_move_speed_multiplier() : GameplayTag { return ue_tag("Attribute.MoveSpeedMultiplier") }

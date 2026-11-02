options gen2
module rogue_presentation_refs public
require rogue_presentation_types public

[ue_object_ref(script="rogue_presentation_profile.das", type= "RoguePresentationProfile")]
struct RoguePresentationProfileRef { handle : UObjectHandle }

[ue_object_ref(script="rogue_action_projectile_attack.das", type= "RogueActionProjectileAttack")]
struct RogueProjectileAttackRef { handle : UObjectHandle }

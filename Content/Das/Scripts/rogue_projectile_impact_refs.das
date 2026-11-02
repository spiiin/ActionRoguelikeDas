options gen2
module rogue_projectile_impact_refs public
require ue_projectile_components public

[ue_interface_ref(path="/Game/DasRogue/Types/RogueImpactHandler.RogueImpactHandler_C", id="rogue.RogueImpactHandler")]
struct RogueImpactHandlerRef { handle : UObjectHandle }

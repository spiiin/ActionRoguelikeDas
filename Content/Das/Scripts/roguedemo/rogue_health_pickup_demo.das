options gen2
module rogue_health_pickup_demo public
require rogue_health_pickup public

// Explicit demo variation: E to use, then a five-second respawn.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueHealthPickupDemo : RogueHealthPickup {
    defaults = ue_defaults() {
        self.RequireInteraction = true
        self.RespawnDelay = 5.0f
    }
}

options gen2
module rogue_attribute_types public
require ue_native_gameplay public

[ue_enum(module_id="rogue", BlueprintType)]
enum RogueAttributeModifyType {
    Base = 0
    Modifier = 1
    OverrideBase = 2
}

// A script snapshot; reflected sets expose their base/modifier maps and query methods.
struct RogueAttribute {
    Base : float = 0.0f
    Modifier : float = 0.0f
}

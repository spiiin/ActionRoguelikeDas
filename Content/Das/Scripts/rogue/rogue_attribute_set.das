options gen2
module rogue_attribute_set public
require rogue_attribute_types public
require rogue_attribute_events public
require daslib/option public
require daslib/match
require math public

// Base + Modifier, notification and post-change policy from course commit 992f860.
// Reflected maps keep designer base overrides and strong UObject state; snapshots are script values.
[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueAttributeSet : ScriptObject {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Attributes") {
        var BaseValues : table<string; float>
    }

    state = ue_properties(BlueprintReadWrite, Category="Attributes") {
        var Modifiers : table<string; float>
        var AttributesInitialized : bool = false
    }

    events = ue_properties(BlueprintAssignable, Category="Attributes") {
        var OnAttributeChanged : RogueAttributeChanged
    }

    [ue_function(BlueprintCallable)]
    def InitializeAttributes() : void {
        if (self.AttributesInitialized) { return }
        self.DefineDefaults()
        var bases := self.BaseValues
        for (value in values(bases)) { verify(is_finite(value), "Attribute bases must be finite") }
        self.AttributesInitialized = true
        self.Reconcile()
    }

    [ue_function(BlueprintEvent)]
    def DefineDefaults() : void {}

    [ue_function(BlueprintEvent)]
    def Reconcile() : void {}

    [ue_function(BlueprintCallable)]
    def DefineAttribute(tag : GameplayTag; base : float) : bool {
        if (!ue_tag_valid(tag) || !is_finite(base)) { return false }
        let name = ue_tag_name(tag)
        if (!key_exists(self.BaseValues, name)) { self.BaseValues[name] = base }
        if (!key_exists(self.Modifiers, name)) { self.Modifiers[name] = 0.0f }
        return true
    }

    [ue_function(BlueprintPure)]
    def HasAttribute(tag : GameplayTag) : bool {
        self.InitializeAttributes()
        return key_exists(self.BaseValues, ue_tag_name(tag))
    }

    def TryGetAttribute(tag : GameplayTag) : Option<RogueAttribute> {
        self.InitializeAttributes()
        let name = ue_tag_name(tag)
        var bases := self.BaseValues
        if (!key_exists(bases, name)) { return none(type<RogueAttribute>) }
        var modifiers := self.Modifiers
        let modifier = key_exists(modifiers, name) ? modifiers[name] : 0.0f
        return some(RogueAttribute(Base=bases[name], Modifier=modifier))
    }

    [ue_function(BlueprintPure)]
    def GetBaseValue(tag : GameplayTag) : float {
        let attribute = self.TryGetAttribute(tag) ?? RogueAttribute()
        return attribute.Base
    }

    [ue_function(BlueprintPure)]
    def GetModifierValue(tag : GameplayTag) : float {
        let attribute = self.TryGetAttribute(tag) ?? RogueAttribute()
        return attribute.Modifier
    }

    [ue_function(BlueprintPure)]
    def GetValue(tag : GameplayTag) : float {
        let attribute = self.TryGetAttribute(tag) ?? RogueAttribute()
        return attribute.Base + attribute.Modifier
    }

    [ue_function(BlueprintCallable)]
    def ModifyAttribute(tag : GameplayTag; amount : float; kind : RogueAttributeModifyType; instigator : ActorRef) : bool {
        if (!is_finite(amount)) { return false }
        let found = self.TryGetAttribute(tag)
        if (is_none(found)) { return false }
        var attribute = unwrap(found)
        let oldValue = attribute.Base + attribute.Modifier
        let healthTag = ue_tag("Attribute.Health")
        let oldHealth = self.GetValue(healthTag)
        match (kind) {
            if (RogueAttributeModifyType.Base) { attribute.Base += amount }
            if (RogueAttributeModifyType.Modifier) { attribute.Modifier += amount }
            if (RogueAttributeModifyType.OverrideBase) { attribute.Base = amount }
            if (_) { return false }
        }
        if (!is_finite(attribute.Base) || !is_finite(attribute.Modifier) || !is_finite(attribute.Base + attribute.Modifier)) { return false }
        let name = ue_tag_name(tag)
        if (name == "Attribute.HealthMax" && attribute.Base + attribute.Modifier < 0.0f) { return false }
        self.BaseValues[name] = attribute.Base
        self.Modifiers[name] = attribute.Modifier
        self.Reconcile()
        let newValue = self.GetValue(tag)
        let health = self.GetValue(healthTag)
        // Capture every affected value before notifying observers; callbacks may re-enter.
        if (newValue != oldValue) { self.OnAttributeChanged.Broadcast(tag, newValue, oldValue, instigator) }
        if (name != "Attribute.Health" && health != oldHealth) {
            self.OnAttributeChanged.Broadcast(healthTag, health, oldHealth, instigator)
        }
        return newValue != oldValue
    }
}

[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueHealthAttributeSet : RogueAttributeSet {
    [ue_function(BlueprintEvent)]
    def override DefineDefaults() : void {
        Super.DefineDefaults()
        self.DefineAttribute(ue_tag("Attribute.Health"), 100.0f)
        self.DefineAttribute(ue_tag("Attribute.HealthMax"), 100.0f)
    }

    [ue_function(BlueprintEvent)]
    def override Reconcile() : void {
        Super.Reconcile()
        let maximum = max(self.GetValue(ue_tag("Attribute.HealthMax")), 0.0f)
        self.BaseValues["Attribute.Health"] = clamp(self.GetBaseValue(ue_tag("Attribute.Health")), 0.0f, maximum)
    }
}

[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RoguePawnAttributeSet : RogueHealthAttributeSet {
    pawnDefaults = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Attributes") {
        var DefaultMoveSpeed : float = 550.0f
    }

    [ue_function(BlueprintEvent)]
    def override DefineDefaults() : void {
        Super.DefineDefaults()
        self.DefineAttribute(ue_tag("Attribute.MoveSpeed"), self.DefaultMoveSpeed)
        self.DefineAttribute(ue_tag("Attribute.MoveSpeedMultiplier"), 1.0f)
    }

    [ue_function(BlueprintEvent)]
    def override Reconcile() : void {
        Super.Reconcile()
        let owner = ue_component_owner(ue_object_outer(ue_self_object()))
        if (!ue_object_valid(owner) || !ue_object_is_a(owner, "/Script/Engine.Character")) { return }
        let speed = self.GetValue(ue_tag("Attribute.MoveSpeed")) * self.GetValue(ue_tag("Attribute.MoveSpeedMultiplier"))
        let character = ue_ref(type<CharacterRef>, owner)
        character.CharacterMovement.MaxWalkSpeed = max(speed, 0.0f)
    }
}

[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RoguePlayerAttributeSet : RoguePawnAttributeSet {
    [ue_function(BlueprintEvent)]
    def override DefineDefaults() : void {
        Super.DefineDefaults()
        self.DefineAttribute(ue_tag("Attribute.Rage"), 0.0f)
    }
}

[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueMonsterAttributeSet : RoguePawnAttributeSet {
    defaults = ue_defaults() { self.DefaultMoveSpeed = 450.0f }
}

typedef RogueAttributeSetRef = UEObjectRef("rogue.RogueAttributeSet")
typedef RogueHealthAttributeSetRef = UEObjectRef("rogue.RogueHealthAttributeSet")
typedef RoguePawnAttributeSetRef = UEObjectRef("rogue.RoguePawnAttributeSet")
typedef RoguePlayerAttributeSetRef = UEObjectRef("rogue.RoguePlayerAttributeSet")
typedef RogueMonsterAttributeSetRef = UEObjectRef("rogue.RogueMonsterAttributeSet")

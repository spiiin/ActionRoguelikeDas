options gen2
module rogue_attribute_component public
require rogue_attribute_set public
require math

// Native damage/event adapter. AttributeSet owns the authoritative Base/Modifier values.
[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueAttributeComponent : ActorComponent {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Attributes") {
        var DefaultAttributeSetClass : ObjectClass
        var HealthMax : float = 100.0f
    }

    state = ue_properties(BlueprintReadWrite, Category="Attributes") {
        // Health/HealthMax are live editor views, seeded once when the set is created.
        var Health : float = 100.0f
        var LastInstigator : ActorRef
        var HealthChanges : int = 0
        var AttributeSet : RogueAttributeSetRef
        var AttributeSetClass : ObjectClass
    }

    events = ue_properties(BlueprintAssignable, Category="Attributes") {
        var OnHealthChanged : RogueHealthChanged
        var OnAttributeChanged : RogueAttributeChanged
    }

    // A reflected class reference loads and retains this dependency with the Blueprint.
    defaults = ue_defaults() {
        self.DefaultAttributeSetClass = ue_class_default("/Game/DasRogue/Attributes/BP_RogueHealthAttributeSet.BP_RogueHealthAttributeSet_C")
    }

    def BeginPlay() : void {
        if (ue_is_valid(self.AttributeSet)) { self.RefreshHealthViews() }
        else { self.HealthMax = max(self.HealthMax, 0.0f); self.Health = self.HealthMax }
        self.SetComponentTickEnabled(false)
    }

    [ue_function(BlueprintCallable)]
    def ConfigureAttributeSet(kind : ObjectClass) : bool {
        if (!ue_class_valid(kind)) { return false }
        let previous = self.AttributeSet
        if (ue_is_valid(previous) && ue_class_path(self.AttributeSetClass) == ue_class_path(kind)) { return true }
        var oldBases : table<string; float>
        var oldModifiers : table<string; float>
        let replacing = ue_is_valid(previous)
        if (replacing) {
            oldBases := previous.BaseValues
            oldModifiers := previous.Modifiers
            self.AttributeSet.OnAttributeChanged -= self.HandleAttributeChanged
        }
        let next = ue_object_new(type<RogueAttributeSetRef>, kind, ue_ref(type<ObjectRef>, ue_self_object()))
        // Outer does not retain an object: establish strong ownership before initialization.
        self.AttributeSet = next
        self.AttributeSetClass = kind
        next.InitializeAttributes()
        var bases := next.BaseValues
        var modifiers := next.Modifiers
        if (replacing) {
            for (name, value in keys(oldBases), values(oldBases)) { if (key_exists(bases, name)) { bases[name] = value } }
            for (name, value in keys(oldModifiers), values(oldModifiers)) { if (key_exists(bases, name)) { modifiers[name] = value } }
        } else {
            bases["Attribute.HealthMax"] = max(self.HealthMax, 0.0f)
            bases["Attribute.Health"] = clamp(self.Health, 0.0f, bases["Attribute.HealthMax"])
        }
        next.BaseValues := bases
        next.Modifiers := modifiers
        next.Reconcile()
        self.AttributeSet.OnAttributeChanged += self.HandleAttributeChanged
        self.RefreshHealthViews()
        return true
    }

    [ue_function(BlueprintCallable)]
    def GetAttributeSet() : RogueAttributeSetRef {
        if (!ue_is_valid(self.AttributeSet)) { self.ConfigureAttributeSet(self.DefaultAttributeSetClass) }
        return self.AttributeSet
    }

    def RefreshHealthViews() : void {
        self.Health = self.AttributeSet.GetValue(ue_tag("Attribute.Health"))
        self.HealthMax = self.AttributeSet.GetValue(ue_tag("Attribute.HealthMax"))
    }

    def HandleAttributeChanged(tag : GameplayTag; value : float; oldValue : float; instigator : ActorRef) : void {
        self.RefreshHealthViews()
        self.OnAttributeChanged.Broadcast(tag, value, oldValue, instigator)
        if (ue_tag_name(tag) == "Attribute.Health" && value != oldValue) {
            self.LastInstigator = instigator
            self.HealthChanges += 1
            self.OnHealthChanged.Broadcast(instigator, value, value - oldValue)
        }
    }

    [ue_function(BlueprintCallable, Category="Attributes")]
    def IsAlive() : bool { return self.Health > 0.0f }

    [ue_function(BlueprintCallable)]
    def ModifyAttribute(tag : GameplayTag; amount : float; kind : RogueAttributeModifyType; instigator : ActorRef) : bool {
        let changed = self.GetAttributeSet().ModifyAttribute(tag, amount, kind, instigator)
        self.RefreshHealthViews()
        return changed
    }

    [ue_function(BlueprintCallable, Category="Attributes")]
    def ApplyHealthChange(instigator : ActorRef; delta : float) : bool {
        return self.ModifyAttribute(ue_tag("Attribute.Health"), delta, RogueAttributeModifyType.Base, instigator)
    }

    [ue_event(source=owner, source_type=ActorRef, name=OnTakeAnyDamage)]
    def OnOwnerDamage(damaged : ActorRef; amount : float; kind : ObjectRef; controller : ObjectRef; source : ActorRef) : void {
        if (!is_finite(amount) || amount <= 0.0f || !self.IsAlive()) { return }
        let instigator = self.ResolveDamageInstigator(source)
        self.ApplyHealthChange(instigator, -amount)
        let attributes = self.GetAttributeSet()
        let rage = ue_tag("Attribute.Rage")
        if (attributes.HasAttribute(rage)) {
            self.ModifyAttribute(rage, amount * 0.75f, RogueAttributeModifyType.Modifier, instigator)
        }
    }

    def ResolveDamageInstigator(source : ActorRef) : ActorRef {
        if (!ue_is_valid(source)) { return source }
        let pawn = source.Instigator
        return ue_is_valid(pawn) ? ue_ref(type<ActorRef>, pawn.handle) : source
    }
}

typedef RogueAttributeComponentRef = UEObjectRef("rogue.RogueAttributeComponent")

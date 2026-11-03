options gen2
module rogue_action_system_component public
require rogue_action public
require rogue_action_events public
require rogue_attribute_component public
require math
require daslib/match
require daslib/linq
require daslib/linq_boost

let ROGUE_MAX_COIN_BALANCE : int64 = 9223372036854775807l

[ue_class(module_id="rogue", Blueprintable),
 ue_implements(interface="/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C")]
class RogueActionSystemComponent : ActorComponent {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Actions") {
        var DefaultActions : array<ObjectClass>
        var BaseMoveSpeed : float = 450.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        // Reflected strong ownership: Outer and standalone script handles do not retain actions.
        var Actions : array<RogueActionRef>
        var ActiveGameplayTags : GameplayTagContainer
        var Resources : table<string; float>
        var MoveSpeedMultiplier : float = 1.0f
        var Enabled : bool = true
        // Currency is integral; generic combat attributes remain floating point.
        var Coins : int64 = 0l
    }

    events = ue_properties(BlueprintAssignable) {
        var OnCoinsChanged : RogueCoinsChanged
        var OnActionAdded : RogueActionChanged
        var OnActionRemoved : RogueActionChanged
        var GameplayTagUpdated : RogueGameplayTagUpdated
    }

    def BeginPlay() : void {
        self.Enabled = true
        self.Resources["Attribute.Rage"] = 0.0f
        self.Coins = 0l
        for (kind in self.DefaultActions) {
            if (ue_class_valid(kind)) {
                self.GrantAction(kind)
            }
        }
    }

    def EndPlay(reason : int) : void {
        self.Shutdown()
        clear(self.Actions)
        self.ActiveGameplayTags = ue_tags()
    }

    [ue_function(BlueprintCallable)]
    def GrantAction(kind : ObjectClass) : RogueActionRef {
        if (!self.Enabled || !ue_class_valid(kind)) { return default<RogueActionRef> }
        var actions := self.Actions
        let existing = _fold <| each(actions)._where(
            _.IsEffect() && ue_class_path(_.GrantedClass) == ue_class_path(kind)
        ).first_or_default(default<RogueActionRef>)
        if (ue_is_valid(existing)) {
            existing.IncrementStackSize()
            return existing
        }
        let action = ue_object_new(type<RogueActionRef>, kind, ue_ref(type<ObjectRef>, ue_self_object()))
        push(self.Actions, action)
        action.GrantedClass = kind
        action.Setup()
        if (action.IsEffect()) {
            if (!action.CanStart()) {
                self.RemoveAction(action)
                return default<RogueActionRef>
            }
            action.StartAction()
            if (!action.IsRunning()) {
                self.RemoveAction(action)
                return default<RogueActionRef>
            }
        }
        self.OnActionAdded.Broadcast(ue_ref(type<ObjectRef>, action.handle))
        return action
    }

    [ue_function(BlueprintCallable)]
    def FindAction(name : GameplayTag) : RogueActionRef {
        var actions := self.Actions
        return _fold <| each(actions)._where(ue_tag_matches(_.ActionName, name, true)).first_or_default(default<RogueActionRef>)
    }

    [ue_function(BlueprintCallable)]
    def StartAction(name : GameplayTag) : bool {
        if (!self.Enabled) { return false }
        let action = self.FindAction(name)
        if (!ue_is_valid(action) || !action.CanStart()) { return false }
        action.StartAction()
        return true
    }

    [ue_function(BlueprintCallable)]
    def StopAction(name : GameplayTag) : bool {
        let action = self.FindAction(name)
        if (!ue_is_valid(action) || !action.IsRunning()) { return false }
        action.StopAction()
        return true
    }

    [ue_function(BlueprintCallable)]
    def RemoveAction(removed : RogueActionRef) : bool {
        var next : array<RogueActionRef>
        var found = false
        for (action in self.Actions) {
            if (!found && ue_same_object(action, removed)) {
                found = true
            } else { push(next, action) }
        }
        if (!found) { return false }
        // Detach before callbacks: an effect also removes itself when stopped.
        self.Actions := next
        if (removed.IsRunning()) { removed.StopAction() }
        self.OnActionRemoved.Broadcast(ue_ref(type<ObjectRef>, removed.handle))
        return true
    }

    [ue_function(BlueprintCallable)]
    def AppendActiveTags(tags : GameplayTagContainer) : void {
        var active = self.ActiveGameplayTags
        for (name in ue_tags_names(tags)) { ue_tags_add(active, ue_tag(name)) }
        self.ActiveGameplayTags = active
        var actions := self.Actions
        for (action in actions) {
            if (action.IsRunning() && ue_tags_has_any(tags, action.BlockedTags)) { action.StopAction() }
        }
        for (name in ue_tags_names(tags)) { self.GameplayTagUpdated.Broadcast(ue_tag(name), 1) }
    }

    [ue_function(BlueprintCallable)]
    def RemoveActiveTags(tags : GameplayTagContainer) : void {
        var active = self.ActiveGameplayTags
        for (name in ue_tags_names(tags)) { ue_tags_remove(active, ue_tag(name)) }
        self.ActiveGameplayTags = active
        for (name in ue_tags_names(tags)) { self.GameplayTagUpdated.Broadcast(ue_tag(name), 0) }
    }

    [ue_function(BlueprintCallable)]
    def GetActiveTags() : GameplayTagContainer { return self.ActiveGameplayTags }

    [ue_function(BlueprintCallable)]
    def IsActionOwnerAlive() : bool { return self.Enabled }

    [ue_function(BlueprintPure)]
    def CanReceiveCoins(amount : int64) : bool {
        return self.Enabled && amount >= 0l && self.Coins >= 0l && self.Coins <= ROGUE_MAX_COIN_BALANCE - amount
    }

    [ue_function(BlueprintCallable)]
    def GrantCoins(amount : int64) : bool {
        if (!self.CanReceiveCoins(amount)) { return false }
        self.Coins += amount
        self.OnCoinsChanged.Broadcast(self.Coins)
        return true
    }

    [ue_function(BlueprintCallable)]
    def GetAttributeValue(tag : GameplayTag) : float {
        let name = ue_tag_name(tag)
        match (name) {
            if ("Attribute.MoveSpeed") { return self.BaseMoveSpeed }
            if ("Attribute.MoveSpeedMultiplier") { return self.MoveSpeedMultiplier }
            if ("Attribute.Health" || "Attribute.HealthMax") {
                let attributes = ue_component_get(type<RogueAttributeComponentRef>, ue_self_actor(), "Attributes")
                return name == "Attribute.Health" ? attributes.Health : attributes.HealthMax
            }
        }
        return key_exists(self.Resources, name) ? self.Resources[name] : 0.0f
    }

    [ue_function(BlueprintCallable)]
    def ApplyAttributeChange(tag : GameplayTag; delta : float) : void {
        let name = ue_tag_name(tag)
        match (name) {
            if ("Attribute.MoveSpeed") {
                self.BaseMoveSpeed += delta
                self.ApplyMoveSpeed()
            }
            if ("Attribute.MoveSpeedMultiplier") {
                self.MoveSpeedMultiplier += delta
                self.ApplyMoveSpeed()
            }
            if ("Attribute.Health") {
                let attributes = ue_component_get(type<RogueAttributeComponentRef>, ue_self_actor(), "Attributes")
                attributes.ApplyHealthChange(ue_self_actor(), delta)
            }
            if (_) { self.Resources[name] = self.GetAttributeValue(tag) + delta }
        }
    }

    [ue_function(BlueprintCallable)]
    def SetBaseMoveSpeed(value : float) : void {
        self.BaseMoveSpeed = value
        self.ApplyMoveSpeed()
    }

    def ApplyMoveSpeed() : void {
        let owner = ue_ref(type<CharacterRef>, ue_component_owner(ue_self_object()))
        owner.CharacterMovement.MaxWalkSpeed = max(0.0f, self.BaseMoveSpeed * self.MoveSpeedMultiplier)
    }

    [ue_function(BlueprintCallable)]
    def Shutdown() : void {
        self.Enabled = false
        var actions := self.Actions
        for (action in actions) {
            if (action.IsRunning()) {
                action.StopAction()
            }
        }
    }
}

typedef RogueActionSystemComponentRef = UEObjectRef("rogue.RogueActionSystemComponent")

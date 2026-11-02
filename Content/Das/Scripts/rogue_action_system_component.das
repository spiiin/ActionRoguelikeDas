options gen2
module rogue_action_system_component public
require rogue_action_refs public
require rogue_action_events public
require rogue_attribute_refs public
require math

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
    }

    events = ue_properties(BlueprintAssignable) {
        var OnActionAdded : RogueActionChanged
        var OnActionRemoved : RogueActionChanged
        var GameplayTagUpdated : RogueGameplayTagUpdated
    }

    def BeginPlay() : void {
        self.Enabled = true
        self.Resources["Attribute.Rage"] = 0.0f
        self.Resources["Attribute.Coins"] = 0.0f
        for (kind in self.DefaultActions) {
            if (ue_class_valid(kind)) {
                self.GrantAction(kind)
            }
        }
    }

    def EndPlay(reason : int) : void {
        self.Enabled = false
        clear(self.Actions)
        self.ActiveGameplayTags = ue_tags()
    }

    [ue_function(BlueprintCallable)]
    def GrantAction(kind : ObjectClass) : RogueActionRef {
        let action = ue_object_new(type<RogueActionRef>, kind, ue_ref(type<ObjectRef>, ue_self_object()))
        push(self.Actions, action)
        action.Setup()
        self.OnActionAdded.Broadcast(ue_ref(type<ObjectRef>, action.handle))
        return action
    }

    [ue_function(BlueprintCallable)]
    def FindAction(name : GameplayTag) : RogueActionRef {
        for (action in self.Actions) {
            if (ue_tag_matches(action.ActionName, name, true)) { return action }
        }
        return default<RogueActionRef>
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
                if (action.IsRunning()) { action.StopAction() }
                found = true
            } else { push(next, action) }
        }
        if (!found) { return false }
        self.Actions := next
        self.OnActionRemoved.Broadcast(ue_ref(type<ObjectRef>, removed.handle))
        return true
    }

    [ue_function(BlueprintCallable)]
    def AppendActiveTags(tags : GameplayTagContainer) : void {
        var active = self.ActiveGameplayTags
        for (name in ue_tags_names(tags)) { ue_tags_add(active, ue_tag(name)) }
        self.ActiveGameplayTags = active
        for (action in self.Actions) {
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

    [ue_function(BlueprintCallable)]
    def GetAttributeValue(tag : GameplayTag) : float {
        let name = ue_tag_name(tag)
        if (name == "Attribute.MoveSpeed") { return self.BaseMoveSpeed }
        if (name == "Attribute.MoveSpeedMultiplier") { return self.MoveSpeedMultiplier }
        if (name == "Attribute.Health" || name == "Attribute.HealthMax") {
            let attributes = ue_component_get(type<RogueAttributeComponentRef>, ue_self_actor(), "Attributes")
            return name == "Attribute.Health" ? attributes.Health : attributes.HealthMax
        }
        return key_exists(self.Resources, name) ? self.Resources[name] : 0.0f
    }

    [ue_function(BlueprintCallable)]
    def ApplyAttributeChange(tag : GameplayTag; delta : float) : void {
        let name = ue_tag_name(tag)
        if (name == "Attribute.MoveSpeed") {
            self.BaseMoveSpeed += delta
            self.ApplyMoveSpeed()
            return
        }
        if (name == "Attribute.MoveSpeedMultiplier") {
            self.MoveSpeedMultiplier += delta
            self.ApplyMoveSpeed()
            return
        }
        if (name == "Attribute.Health") {
            let attributes = ue_component_get(type<RogueAttributeComponentRef>, ue_self_actor(), "Attributes")
            attributes.ApplyHealthChange(ue_self_actor(), delta)
            return
        }
        self.Resources[name] = self.GetAttributeValue(tag) + delta
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
        for (action in self.Actions) {
            if (action.IsRunning()) {
                action.StopAction()
            }
        }
    }
}

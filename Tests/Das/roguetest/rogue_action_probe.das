options gen2
module rogue_action_probe public
require ue_vector_math public
require ue_native_gameplay public
require rogue_action public
require ue_call_scope
require daslib/rtti
require strings
require rogue_attribute_component public

typedef ProbeAIClassRef = UEObjectRef("rogue.RogueAICharacter")

// Opaque handles are weak. This observer must never be an owning UPROPERTY.
var watched : UObjectHandle

[ue_class(module_id="roguetest", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueActionProbe : Actor {

    def BeginPlay() : void { ue_self_actor().SetActorTickEnabled(false) }

    [ue_function(BlueprintCallable)]
    def CheckCallScope(early : bool) : bool {
        var saved : UCallHandle
        with_ue_call(ue_self_object(), "K2_GetActorLocation") $(call) {
            saved = call
            if (early) { return }
            ue_invoke_call(call)
        }
        var released = false
        try { ue_invoke_call(saved) } recover { released = true }
        return released
    }

    [ue_function(BlueprintCallable)]
    def CheckFailedCallScope() : bool {
        var saved : UCallHandle
        var caught = false
        try {
            with_ue_call(ue_self_object(), "K2_GetActorLocation") $(call) {
                saved = call
                panic("Expected scope failure")
            }
        } recover { caught = rtrim(this_context().last_exception) == "Expected scope failure" }
        var released = false
        try { ue_invoke_call(saved) } recover { released = true }
        return caught && released
    }

    // Change live state through runtime property access, without editor reconstruction.
    [ue_function(BlueprintCallable)]
    def ConfigureHealth(attributes : RogueAttributeComponentRef; maximum : float) : void {
        attributes.ModifyAttribute(ue_tag("Attribute.HealthMax"), maximum, RogueAttributeModifyType.OverrideBase, default<ActorRef>)
        attributes.ModifyAttribute(ue_tag("Attribute.Health"), maximum, RogueAttributeModifyType.OverrideBase, default<ActorRef>)
    }

    [ue_function(BlueprintCallable)]
    def Watch(action : ObjectRef) : void { watched = action.handle }

    [ue_function(BlueprintCallable)]
    def WatchAlive() : bool { return ue_object_valid(watched) }

    [ue_function(BlueprintCallable)]
    def CreateOrphan(kind : ObjectClass; outer : ObjectRef) : void {
        watched = ue_object_new(type<ObjectRef>, kind, outer).handle
    }

    [ue_function(BlueprintCallable)]
    def RejectCreation(kind : ObjectClass; outer : ObjectRef) : bool {
        var rejected = false
        try { let result = ue_object_new(type<ObjectRef>, kind, outer) } recover { rejected = true }
        return rejected
    }

    [ue_function(BlueprintCallable)]
    def RejectTypedCreation(kind : ObjectClass; outer : ObjectRef) : bool {
        var rejected = false
        try { let result = ue_object_new(type<RogueActionRef>, kind, outer) } recover { rejected = true }
        return rejected
    }

    [ue_function(BlueprintCallable)]
    def Spawn(kind : ActorClass; position : UEVector; rotation : UERotator) : ActorRef {
        return ue_actor_spawn(type<ActorRef>, kind,
            ue_transform(position, rotation, UE_VECTOR_ONE), default<ActorRef>, "AlwaysSpawn")
    }

    [ue_function(BlueprintCallable)]
    def ConfigureAimBlocker(actor : ActorRef; projectile : bool; visibility : bool) : void {
        let mesh = ue_component_find(type<StaticMeshComponentRef>, actor)
        mesh.SetCollisionResponseToAllChannels(ECollisionResponse.ECR_Ignore)
        mesh.SetCollisionEnabled(ECollisionEnabled.QueryOnly)
        mesh.SetCollisionResponseToChannel(ECollisionChannel.ECC_GameTraceChannel2,
            projectile ? ECollisionResponse.ECR_Block : ECollisionResponse.ECR_Ignore)
        mesh.SetCollisionResponseToChannel(ECollisionChannel.ECC_Visibility,
            visibility ? ECollisionResponse.ECR_Block : ECollisionResponse.ECR_Ignore)
    }

    [ue_function(BlueprintCallable)]
    def RejectAIClass(kind : ObjectClass) : bool {
        var rejected = false
        try { let checked = ue_class_loaded(type<ProbeAIClassRef>, ue_class_path(kind)) } recover { rejected = true }
        return rejected
    }

}

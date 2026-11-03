options gen2
module rogue_attribute_probe public
require rogue_action_system_component public
require ue_vector_math public

typedef RogueAttributeProbeRef = UEObjectRef("roguetest.RogueAttributeProbe")

var weak_attribute_set : UObjectHandle

[ue_class(module_id="roguetest", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueAttributeProbe : Actor {
    @ue_component
    Attributes : RogueAttributeComponentRef

    @ue_component
    System : RogueActionSystemComponentRef

    state = ue_properties(BlueprintReadWrite) {
        var Watched : RogueActionSystemComponentRef
        var Events : int = 0
        var HealthEvents : int = 0
        var RageEvents : int = 0
        var LastTag : string
        var LastOld : float = 0.0f
        var LastNew : float = 0.0f
        var LastInstigator : ActorRef
        var Reenter : bool = false
        var Reentered : bool = false
    }

    def BeginPlay() : void {
        self.System.ConfigureAttributeSet(ue_class_loaded(type<ObjectClass>, "/Game/DasRogue/Attributes/BP_RoguePlayerAttributeSet.BP_RoguePlayerAttributeSet_C"))
        ue_self_actor().SetActorTickEnabled(false)
    }

    [ue_function(BlueprintCallable)]
    def Watch(target : ActorRef) : void {
        if (ue_is_valid(self.Watched)) { self.Watched.OnAttributeChanged -= self.RecordChange }
        self.Watched = ue_component_find(type<RogueActionSystemComponentRef>, target)
        self.Watched.OnAttributeChanged += self.RecordChange
        self.Events = 0
        self.HealthEvents = 0
        self.RageEvents = 0
        self.Reentered = false
    }

    def RecordChange(tag : GameplayTag; value : float; previous : float; instigator : ActorRef) : void {
        self.Events += 1
        self.LastTag = ue_tag_name(tag)
        self.LastOld = previous
        self.LastNew = value
        self.LastInstigator = instigator
        if (self.LastTag == "Attribute.Health") { self.HealthEvents += 1 }
        if (self.LastTag == "Attribute.Rage") {
            self.RageEvents += 1
            if (self.Reenter && !self.Reentered) {
                self.Reentered = true
                self.Watched.ModifyAttribute(tag, 1.0f, RogueAttributeModifyType.Modifier)
            }
        }
    }

    [ue_function(BlueprintCallable)]
    def AddBase(target : ActorRef; tag : GameplayTag; amount : float) : bool {
        return ue_component_find(type<RogueActionSystemComponentRef>, target).ModifyAttribute(tag, amount, RogueAttributeModifyType.Base)
    }

    [ue_function(BlueprintCallable)]
    def AddModifier(target : ActorRef; tag : GameplayTag; amount : float) : bool {
        return ue_component_find(type<RogueActionSystemComponentRef>, target).ModifyAttribute(tag, amount, RogueAttributeModifyType.Modifier)
    }

    [ue_function(BlueprintCallable)]
    def OverrideBase(target : ActorRef; tag : GameplayTag; amount : float) : bool {
        return ue_component_find(type<RogueActionSystemComponentRef>, target).ModifyAttribute(tag, amount, RogueAttributeModifyType.OverrideBase)
    }

    [ue_function(BlueprintCallable)]
    def UseMonster(target : ActorRef) : bool {
        return ue_component_find(type<RogueActionSystemComponentRef>, target).ConfigureAttributeSet(ue_class_loaded(type<ObjectClass>, "/Game/DasRogue/Attributes/BP_RogueMonsterAttributeSet.BP_RogueMonsterAttributeSet_C"))
    }

    [ue_function(BlueprintCallable)]
    def UsePlayer(target : ActorRef) : bool {
        return ue_component_find(type<RogueActionSystemComponentRef>, target).ConfigureAttributeSet(ue_class_loaded(type<ObjectClass>, "/Game/DasRogue/Attributes/BP_RoguePlayerAttributeSet.BP_RoguePlayerAttributeSet_C"))
    }

    [ue_function(BlueprintCallable)]
    def WatchSet(target : ActorRef) : void {
        weak_attribute_set = ue_component_find(type<RogueActionSystemComponentRef>, target).GetAttributeSet().handle
    }

    [ue_function(BlueprintCallable)]
    def WatchedSetAlive() : bool { return ue_object_valid(weak_attribute_set) }

    [ue_function(BlueprintCallable)]
    def SpawnCopy(location : UEVector) : ActorRef {
        return ue_actor_spawn(type<ActorRef>, ue_class_loaded(type<RogueAttributeProbeRef>, "/Game/DasRogue/Tests/BP_RogueAttributeProbe.BP_RogueAttributeProbe_C"),
            ue_transform(location, UE_ROTATOR_ZERO, UE_VECTOR_ONE))
    }
}

options gen2
module rogue_course_stun_zone public
require rogue_action_system_component public
require ue_native_gameplay public
require ue_projectile_components public

typedef CourseBoxRef = UENativeObjectRef("/Script/Engine.BoxComponent")

// BP_ApplyZone grants ActionEffect_Stunned to an overlapping action owner.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueCourseStunZone : Actor {
    @ue_component
    @RootComponent
    Box : CourseBoxRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite) {
        var ActionClass : ObjectClass
    }

    defaults = ue_defaults() {
        self.ActionClass = ue_class_default("/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C")
    }

    def BeginPlay() : void { self.SetActorTickEnabled(false) }

    [ue_event(source=Box, name=OnComponentBeginOverlap)]
    def OnOverlap(component : ObjectRef; other : ActorRef; otherComponent : ObjectRef;
        bodyIndex : int; swept : bool; hit : CollisionHit) : void {
        let system = ue_component_find(type<RogueActionSystemComponentRef>, other)
        if (ue_is_valid(system) && ue_class_valid(self.ActionClass)) { system.GrantAction(self.ActionClass) }
    }
}

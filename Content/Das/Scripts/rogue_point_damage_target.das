options gen2
module rogue_point_damage_target public
require rogue_target_dummy public
require rogue_attribute_refs public
require ue_vector_math public

[ue_class(module_id="roguetest", Blueprintable)]
class RoguePointDamageTarget : RogueTargetDummy {
    state = ue_properties(BlueprintReadWrite) {
        var PointHits : int = 0
        var PointDamage : float = 0.0f
        var HitLocation : UEVector
        var ShotDirection : UEVector
        var HitComponent : ObjectRef
        var HitBone : UENameValue
        var DamageSource : ActorRef
        var DamageController : ObjectRef
    }

    [ue_event(name="OnTakePointDamage")]
    def OnPointDamage(victim : ActorRef; damage : float; controller : ObjectRef;
        location : UEVector; component : ObjectRef; bone : UENameValue;
        direction : UEVector; kind : ObjectRef; source : ActorRef) : void {
        self.PointHits += 1
        self.PointDamage = damage
        self.HitLocation = location
        self.ShotDirection = direction
        self.HitComponent = component
        self.HitBone = bone
        self.DamageSource = source
        self.DamageController = controller
    }
}

options gen2
module rogue_presentation_profile public
require ue_animation public
require ue_effects public
require ue_vector_math public

typedef RogueSkeletalMeshRef = UENativeObjectRef("/Script/Engine.SkeletalMesh")

// Instances with licensed third-party references are generated locally, outside Git.
[ue_class(module_id="rogue", Blueprintable)]
class RoguePresentationProfile : DataAsset {

    properties = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Presentation") {
        var CharacterMesh : RogueSkeletalMeshRef
        var AnimationClass : ObjectClass
        var AttackMontage : AnimMontageRef
        var DeathMontage : AnimMontageRef
        var CastEffect : NiagaraSystemRef
        var CastSound : SoundBaseRef
        var ProjectileEffect : NiagaraSystemRef
        var ProjectileSound : SoundBaseRef
        var ImpactEffect : NiagaraSystemRef
        var ImpactSound : SoundBaseRef
        var MuzzleSocket : string = "Muzzle_01"
        var MeshLocation : UEVector = ue_vector(0.0lf, 0.0lf, -90.0lf)
        var MeshRotation : UERotator = ue_rotator(0.0lf, -90.0lf, 0.0lf)
    }
}

typedef RoguePresentationProfileRef = UEObjectRef("rogue.RoguePresentationProfile")

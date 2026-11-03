options gen2
module rogue_presentation public
require rogue_presentation_profile public
require rogue_action_projectile_attack public
require ue_native_gameplay public
require ue_asset_optional public
require ue_vector_math public
require daslib/option public

let ROGUE_PRESENTATION_PROFILE = "/Game/DasRogueExternal/DA_Presentation.DA_Presentation"

def rogue_load_presentation(path : string) : Option<RoguePresentationProfileRef> {
    let asset = ue_asset_load_optional(path)
    if (!ue_is_valid(asset)) { return none(type<RoguePresentationProfileRef>) }
    return some(ue_ref(type<RoguePresentationProfileRef>, asset.handle))
}

def rogue_apply_mesh(mesh : SkeletalMeshComponentRef; profile : RoguePresentationProfileRef) : void {
    mesh.SetSkeletalMeshAsset(profile.CharacterMesh)
    mesh.SetAnimInstanceClass(profile.AnimationClass)
    ue_scene_set_relative_transform(ue_ref(type<SceneComponentRef>, mesh.handle),
        ue_transform(profile.MeshLocation, profile.MeshRotation, UE_VECTOR_ONE))
}

def rogue_apply_attack(action : RogueProjectileAttackRef; profile : RoguePresentationProfileRef) : void {
    action.AttackMontage = profile.AttackMontage
    action.AttackDelay = profile.AttackDelay
    action.CastingEffect = profile.CastEffect
    action.CastingSound = profile.CastSound
    action.MuzzleSocketName = profile.MuzzleSocket
}

def rogue_load_presentation() : Option<RoguePresentationProfileRef> {
    return rogue_load_presentation(ROGUE_PRESENTATION_PROFILE)
}

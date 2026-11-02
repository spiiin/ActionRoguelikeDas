options gen2
module rogue_presentation public
require rogue_presentation_refs public
require ue_asset_optional public
require ue_vector_math public

let ROGUE_PRESENTATION_PROFILE = "/Game/DasRogueExternal/DA_Presentation.DA_Presentation"

def rogue_load_presentation(path : string) : RoguePresentationProfileRef {
    let asset = ue_asset_load_optional(path)
    if (!ue_is_valid(asset)) { return default<RoguePresentationProfileRef> }
    return ue_ref(type<RoguePresentationProfileRef>, asset.handle)
}

def rogue_apply_mesh(mesh : SkeletalMeshComponentRef; profile : RoguePresentationProfileRef) : void {
    let setMesh = ue_begin_call(mesh.handle, "SetSkeletalMeshAsset")
    ue_arg_object(setMesh, "newmesh", profile.CharacterMesh.handle)
    ue_invoke_call(setMesh)
    ue_release_call(setMesh)
    let setAnimation = ue_begin_call(mesh.handle, "SetAnimInstanceClass")
    ue_arg_class(setAnimation, "newclass", ue_class_handle(profile.AnimationClass))
    ue_invoke_call(setAnimation)
    ue_release_call(setAnimation)
    ue_scene_set_relative_transform(ue_ref(type<SceneComponentRef>, mesh.handle),
        ue_transform(profile.MeshLocation, profile.MeshRotation, UE_VECTOR_ONE))
}

def rogue_apply_attack(action : RogueProjectileAttackRef; profile : RoguePresentationProfileRef) : void {
    action.AttackMontage = profile.AttackMontage
    action.CastingEffect = profile.CastEffect
    action.CastingSound = profile.CastSound
    action.MuzzleSocketName = profile.MuzzleSocket
}

def rogue_load_presentation() : RoguePresentationProfileRef {
    return rogue_load_presentation(ROGUE_PRESENTATION_PROFILE)
}

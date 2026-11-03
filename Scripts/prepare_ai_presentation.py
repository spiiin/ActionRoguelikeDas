"""Generate local-only Paragon Minion presentation. Run in the editor outside PIE."""
import json
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[1]
receipt=json.loads((ROOT/'Saved/ExternalAssets/install.json').read_text(encoding='utf-8'))
assert receipt.get('minions') and receipt.get('ai_assets'), 'Install assets with --with-minions first'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world and not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'Prepare outside PIE'
assert unreal.load_class(None,'/Script/AnimationData.AnimationSequencerDataModel'), 'AnimationData must be enabled'
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_presentation_profile.das /Game/DasRogue/Types/BP_RoguePresentationProfile rogue.RoguePresentationProfile')
assets={key:unreal.load_asset(path) for key,path in receipt['ai_assets'].items()}
assert all(assets.values()), 'A Minion resource failed to load'
skeleton=assets['CharacterMesh'].get_editor_property('skeleton')
assert all(a.get_editor_property('skeleton')==skeleton for a in assets.values() if a!=assets['CharacterMesh'])
slot='DefaultSlot'
animation,error=unreal.DasAnimationAssetLibrary.create_locomotion_blueprint(
    '/Game/DasRogueExternal/ABP_MinionLocomotion',skeleton,assets['Locomotion'],1,0,slot)
assert animation,error
tools=unreal.AssetToolsHelpers.get_asset_tools()
packages=[animation.get_outer()]

def montage(name,sequence,hold=False):
    package='/Game/DasRogueExternal/'+name
    if (ROOT/'Content/DasRogueExternal'/f'{name}.uasset').is_file():
        result=unreal.load_asset(package+'.'+name)
    else:
        factory=unreal.AnimMontageFactory()
        factory.set_editor_property('target_skeleton',skeleton)
        factory.set_editor_property('source_animation',sequence)
        result=tools.create_asset(name,'/Game/DasRogueExternal',unreal.AnimMontage,factory)
    assert result,name
    result.modify(True)
    tracks=list(result.get_editor_property('slot_anim_tracks'))
    assert tracks,name
    for track in tracks:track.set_editor_property('slot_name',slot)
    result.set_editor_property('slot_anim_tracks',tracks)
    result.set_editor_property('enable_auto_blend_out',not hold)
    packages.append(result.get_outer())
    return result

montages={
    'AttackMontage':montage('AM_MinionAttack',assets['AttackAnimation']),
    'HitReactMontage':montage('AM_MinionHit',assets['HitAnimation']),
    'DeathMontage':montage('AM_MinionDeath',assets['DeathAnimation'],True),
    'StunMontage':montage('AM_MinionStun',assets['StunAnimation'],True),
}
profile_path='/Game/DasRogueExternal/DA_MinionPresentation.DA_MinionPresentation'
if (ROOT/'Content/DasRogueExternal/DA_MinionPresentation.uasset').is_file():
    profile=unreal.load_asset(profile_path)
else:
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Asset.Create /Game/DasRogue/Types/BP_RoguePresentationProfile /Game/DasRogueExternal/DA_MinionPresentation')
    profile=unreal.find_object(None,profile_path)
assert profile
profile.modify(True)
profile.set_editor_property('CharacterMesh',assets['CharacterMesh'])
profile.set_editor_property('AnimationClass',animation.generated_class())
profile.set_editor_property('MeshLocation',unreal.Vector(0,0,-90))
profile.set_editor_property('MeshRotation',unreal.Rotator(pitch=0,yaw=-90,roll=0))
profile.set_editor_property('MuzzleSocket','Muzzle_01')
profile.set_editor_property('AttackDelay',.4)
for name,value in montages.items():profile.set_editor_property(name,value)
for name in ['CastEffect','CastSound','ProjectileEffect','ProjectileSound','ImpactEffect','ImpactSound']:
    path=receipt['assets'].get(name)
    profile.set_editor_property(name,unreal.load_asset(path) if path else None)
packages.extend([profile.get_outer(),skeleton.get_outer(),unreal.load_asset('/Game/DasRogue/Types/BP_RoguePresentationProfile').get_outer()])
assert unreal.EditorLoadingAndSavingUtils.save_packages(packages,False)
result={'profile':profile.get_path_name(),'mesh':assets['CharacterMesh'].get_path_name(),
        'animation_class':animation.generated_class().get_path_name(),'montages':{k:v.get_path_name() for k,v in montages.items()},
        'attack_delay':.4,'muzzle_socket':'Muzzle_01','source_revision':receipt['source_revision']}
(ROOT/'Saved/ExternalAssets/ai_prepared.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
unreal.log('DAS_MINION_PRESENTATION_PREPARED '+json.dumps(result))

for filename,name in [('rogue_ai_presentation_probe.das','RogueAIPresentationProbe'),('rogue_ai_missing_presentation.das','RogueAIMissingPresentation'),('rogue_ai_visual_test_character.das','RogueAIVisualTestCharacter')]:
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {filename} /Game/DasRogue/Tests/BP_{name} roguetest.{name}')
    assert unreal.load_class(None,f'/Game/DasRogue/Tests/BP_{name}.BP_{name}_C'),name
# Script-derived fixtures import their own base Blueprint under /Tests. Wire their
# editor defaults explicitly, just as prepare_ai.py wires the gameplay variant.
base_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
base_defaults=unreal.get_default_object(base_kind)
for name in ['RogueAIMissingPresentation','RogueAIVisualTestCharacter']:
    asset=unreal.load_asset(f'/Game/DasRogue/Tests/BP_{name}')
    asset.modify(True)
    defaults=unreal.get_default_object(asset.generated_class())
    for field in ['ai_controller_class','auto_possess_ai','AttackClass']:
        defaults.set_editor_property(field,base_defaults.get_editor_property(field))

# Hidden-window test runs need fresh component-space bones. Restrict this cost to the test subclass.
test_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueAIVisualTestCharacter.BP_RogueAIVisualTestCharacter_C')
unreal.load_asset('/Game/DasRogue/Tests/BP_RogueAIVisualTestCharacter').modify(True)
unreal.get_default_object(test_kind).get_editor_property('mesh').set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)

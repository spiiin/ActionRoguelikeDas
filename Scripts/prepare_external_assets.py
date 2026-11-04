"""Run outside PIE after setup_external_assets.py. Generates local presentation only."""
import json
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[1]
# Fail before loading animation packages if their serialization modules are absent.
assert unreal.load_class(None,'/Script/AnimationData.AnimationSequencerDataModel'), 'Enable and build AnimationData before loading course animations'
assert unreal.load_class(None,'/Script/ControlRig.ControlRig'), 'Enable and build ControlRig before loading course animations'
receipt=json.loads((ROOT/'Saved/ExternalAssets/install.json').read_text())
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(['/Game/'+n for n in json.loads((ROOT/'ExternalAssets.json').read_text())['allowed_roots']],True)
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_presentation_profile.das /Game/DasRogue/Types/BP_RoguePresentationProfile rogue.RoguePresentationProfile')
profile_class=unreal.load_class(None,'/Game/DasRogue/Types/BP_RoguePresentationProfile.BP_RoguePresentationProfile_C')
assert profile_class,'Profile definition failed to import'
loaded={key:unreal.load_asset(path) for key,path in receipt['assets'].items()}
assert all(loaded.values()),'A required external asset failed to load'
mesh=loaded['CharacterMesh']
skeleton=mesh.get_editor_property('skeleton')
# Keep the skeleton preview configuration supplied by the resource pack.
blend=loaded['Locomotion']
assert blend.get_editor_property('skeleton')==skeleton,'Locomotion skeleton mismatch'
montage=loaded['AttackMontage']
tracks=montage.get_editor_property('slot_anim_tracks')
assert tracks,'Attack montage contains no slot track'
slot=tracks[0].get_editor_property('slot_name')
# Course Run_Direction uses direction on X and ground speed on Y.
course_animation=receipt.get('course_animation',False)
if course_animation:
    assert unreal.load_class(None,'/Script/PropertyAccessNode.K2Node_PropertyAccess'), 'Enable PropertyAccessNode before loading the course Anim Blueprint'
    config=json.loads((ROOT/'ExternalAssets.json').read_text())['course_animation']
    assert (ROOT/'Saved/ExternalAssets/course_animation.json').is_file(), 'Run Scripts/export_course_animation.py in the source course editor first'
    anim=unreal.load_asset(config['adapted_blueprint'])
    assert anim and unreal.BlueprintEditorLibrary.compile_blueprint(anim), 'Adapted course Anim Blueprint failed to compile'
    assert anim.get_editor_property('target_skeleton')==skeleton, 'Course Anim Blueprint skeleton mismatch'
else:
    anim,error=unreal.DasAnimationAssetLibrary.create_locomotion_blueprint(
        '/Game/DasRogueExternal/ABP_Locomotion',skeleton,blend,1,0,slot)
    assert anim,error
# The course death montage uses DefaultSlot, while its attack uses UpperBody.
# Adapt a local duplicate to our one-slot graph, preserving the acquired original.
if loaded.get('DeathMontage') and not course_animation:
    if (ROOT/'Content/DasRogueExternal/AM_Death.uasset').is_file():
        death=unreal.load_asset('/Game/DasRogueExternal/AM_Death.AM_Death')
    else:
        death=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('AM_Death','/Game/DasRogueExternal',loaded['DeathMontage'])
    assert death
    death.modify(True)
    death_tracks=list(death.get_editor_property('slot_anim_tracks'))
    for track in death_tracks:track.set_editor_property('slot_name',slot)
    death.set_editor_property('slot_anim_tracks',death_tracks)
    death.set_editor_property('enable_auto_blend_out',False)
    loaded['DeathMontage']=death
profile_path='/Game/DasRogueExternal/DA_Presentation.DA_Presentation'
if (ROOT/'Content/DasRogueExternal/DA_Presentation.uasset').is_file():
    profile=unreal.load_asset(profile_path)
else:
    # A failed LoadObject can create an empty UPackage; do not load before Create.
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Asset.Create /Game/DasRogue/Types/BP_RoguePresentationProfile /Game/DasRogueExternal/DA_Presentation')
    profile=unreal.find_object(None,profile_path)
assert profile
profile.modify(True)
if loaded.get('ProjectileSound'):
    loaded['ProjectileSound'].set_editor_property('looping',True)
for name,value in loaded.items():
    if name!='Locomotion':profile.set_editor_property(name,value)
profile.set_editor_property('AnimationClass',anim.generated_class())
profile.set_editor_property('UseCourseAnimationBlueprint',course_animation)
profile.set_editor_property('MeshLocation',unreal.Vector(0,0,-90))
profile.set_editor_property('MeshRotation',unreal.Rotator(pitch=0,yaw=-90,roll=0))
profile.set_editor_property('MuzzleSocket','Muzzle_01')
packages=[profile.get_outer(),anim.get_outer(),loaded['DeathMontage'].get_outer(),unreal.load_asset('/Game/DasRogue/Types/BP_RoguePresentationProfile').get_outer()]
if loaded.get('ProjectileSound'):packages.append(loaded['ProjectileSound'].get_outer())
assert unreal.EditorLoadingAndSavingUtils.save_packages(packages,False)
result={'profile':profile.get_path_name(),'mesh':mesh.get_path_name(),'animation_class':anim.generated_class().get_path_name(),'montage_slot':str(slot),'course_animation':course_animation,'assets':receipt['assets']}
dest=ROOT/'Saved/ExternalAssets/prepared.json';dest.write_text(json.dumps(result,indent=2))
unreal.log('DAS_EXTERNAL_PRESENTATION_PREPARED '+json.dumps(result))

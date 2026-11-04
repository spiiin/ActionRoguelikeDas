"""Original pose graph + DAS state bridge, exercised in real PIE."""
from pathlib import Path
import json,time,traceback,math
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
controller=unreal.GameplayStatics.get_player_controller(world,0)
system=pawn.get_editor_property('ActionSystem')
bridge=pawn.get_editor_property('AnimationState')
mesh=pawn.get_editor_property('mesh')
anim=mesh.get_anim_instance()
assert anim and anim.get_class().get_path_name()=='/Game/DasRogueExternal/ABP_CoursePlayer.ABP_CoursePlayer_C'
assert anim.get_editor_property('OwningCharacter')==pawn
assert pawn.get_editor_property('Presentation').get_editor_property('UseCourseAnimationBlueprint')
assert bridge.get_editor_property('Enabled') and not bridge.is_component_tick_enabled()
assert unreal.SystemLibrary.get_class_display_name(anim.get_class())
inputs=max([v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer'],key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_course_animation_pie.json'

def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value

def tags(*names):return unreal.GameplayTagLibrary.make_gameplay_tag_container_from_array([tag(n) for n in names])

def now():return unreal.GameplayStatics.get_time_seconds(world)

def inject(name,value=unreal.Vector(1,0,0)):
    inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),value,[],[])

def foot():
    t=mesh.get_socket_transform('foot_l',unreal.RelativeTransformSpace.RTS_COMPONENT)
    return t.translation

s={'phase':'move','at':now(),'started':time.perf_counter(),'done':False,'checks':['original_graph_initializes_on_DAS_character','event_driven_state_bridge_has_no_tick'],'foot':foot()}

def phase(name):s.update(phase=name,at=now())

def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<45,s['phase']
        for obj in [pawn,system,bridge]:assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        age=now()-s['at'];name=s['phase']
        if name=='move':
            inject('IA_Move')
            if age<.6:return
            assert pawn.get_velocity().length()>100
            assert anim.get_editor_property('Speed')>100, 'Original thread-safe speed update did not run'
            assert (foot()-s['foot']).length()>1, 'Locomotion pose remained frozen'
            s['checks'].append('original_locomotion_updates_speed_and_bone_pose')
            pawn.get_editor_property('character_movement').stop_movement_immediately()
            phase('jump');return
        if name=='jump':
            if age<.2:inject('IA_Jump');return
            if anim.get_editor_property('IsInAir'):
                s['checks'].append('original_jump_state_follows_DAS_character')
                phase('land');return
            assert age<1.5,'Jump animation state never became airborne';return
        if name=='land':
            if anim.get_editor_property('IsInAir'):
                assert age<3,'Jump did not land';return
            controller.set_control_rotation(unreal.Rotator(pitch=25,yaw=45,roll=0))
            phase('aim');return
        if name=='aim':
            if age<.3:return
            assert abs(anim.get_editor_property('Pitch'))>5, 'Original aim pitch did not update'
            assert math.isfinite(anim.get_editor_property('Yaw'))
            s['checks'].append('original_aim_offset_updates_from_control_rotation')
            assert system.call_method('StartAction',args=(tag('Action.Sprint'),))
            phase('sprint');return
        if name=='sprint':
            if age<.15:return
            assert anim.get_editor_property('DasIsSprinting')
            assert system.call_method('StopAction',args=(tag('Action.Sprint'),))
            assert not anim.get_editor_property('DasIsSprinting')
            s['checks'].append('DAS_sprint_tags_update_original_animation_branch')
            system.call_method('AppendActiveTags',args=(tags('StatusEffect.Stunned'),))
            phase('stun');return
        if name=='stun':
            if age<.15:return
            assert anim.get_editor_property('DasIsStunned')
            system.call_method('RemoveActiveTags',args=(tags('StatusEffect.Stunned'),))
            assert not anim.get_editor_property('DasIsStunned')
            count=bridge.get_editor_property('StateUpdates')
            system.call_method('AppendActiveTags',args=(tags('Action.PrimaryAttack'),))
            system.call_method('RemoveActiveTags',args=(tags('Action.PrimaryAttack'),))
            assert bridge.get_editor_property('StateUpdates')==count, 'Unrelated tags triggered animation writes'
            s['checks'].append('stun_and_unrelated_tags_are_handled_without_polling')
            montage=pawn.get_editor_property('Presentation').get_editor_property('AttackMontage')
            assert pawn.play_anim_montage(montage,1.0,'None')>0
            assert anim.montage_is_playing(montage)
            s['checks'].append('original_UpperBody_attack_montage_plays')
            phase('montage');return
        if name=='montage':
            if age<.2:return
            montage=pawn.get_editor_property('Presentation').get_editor_property('DeathMontage')
            assert str(montage.get_editor_property('slot_anim_tracks')[0].get_editor_property('slot_name'))=='DefaultSlot'
            assert pawn.play_anim_montage(montage,1.0,'None')>0
            assert anim.montage_is_playing(montage)
            s['checks'].append('original_DefaultSlot_death_montage_plays')
            phase('finish');return
        if name=='finish':
            if age<.2:return
            registry=unreal.AssetRegistryHelpers.get_asset_registry()
            options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=False,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
            config=json.loads((Path(unreal.Paths.project_dir())/'ExternalAssets.json').read_text())
            roots=config['allowed_roots']+['DasRogueExternal']
            for asset in registry.get_assets_by_path('/Game/DasRogue',recursive=True):
                for dependency in registry.get_dependencies(asset.package_name,options):
                    assert not any(str(dependency).startswith('/Game/'+root+'/') for root in roots),(asset.package_name,dependency)
            s['checks'].append('public_gameplay_assets_do_not_hard_reference_licensed_content')
            probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
            for name in ['RogueWithoutPresentation','RogueMissingPresentation']:
                kind=unreal.load_class(None,f'/Game/DasRogue/Tests/BP_{name}.BP_{name}_C')
                fallback=probe.call_method('Spawn',args=(kind,unreal.Vector(-1200,2000,200),unreal.Rotator()))
                assert fallback and not fallback.get_editor_property('LastDasError')
                assert not fallback.get_editor_property('UsingExternalPresentation')
                assert not fallback.get_editor_property('AnimationState').get_editor_property('Enabled')
                fallback.destroy_actor()
            s['checks'].append('disabled_and_missing_external_profiles_keep_basic_fallback')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False

s['handle']=unreal.register_slate_post_tick_callback(tick)

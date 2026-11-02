"""Real PIE: licensed local resources, animation graph, cast and projectile VFX."""
import json,time,traceback
from pathlib import Path
import unreal

# Public gameplay packages must work without locally acquired resources.
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(['/Game/DasRogue'],True)
options=unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=False,include_hard_package_references=True,
    include_searchable_names=False,include_soft_management_references=False,
    include_hard_management_references=False)
external=json.loads((Path(__file__).resolve().parents[1]/'ExternalAssets.json').read_text())['allowed_roots']+['DasRogueExternal']
for asset in registry.get_assets_by_path('/Game/DasRogue',recursive=True):
    for dependency in registry.get_dependencies(asset.package_name,options):
        assert not any(str(dependency).startswith('/Game/'+name+'/') for name in external), (asset.package_name,dependency)

w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
system=p.get_editor_property('ActionSystem')
profile=p.get_editor_property('Presentation')
assert p.get_editor_property('UsingExternalPresentation') and profile
mesh=p.get_editor_property('mesh')
assert mesh.get_skeletal_mesh_asset()==profile.get_editor_property('CharacterMesh')
assert mesh.get_anim_instance() and mesh.get_anim_instance().get_class()==profile.get_editor_property('AnimationClass')
assert p.get_editor_property('Visual').get_editor_property('hidden_in_game')
assert mesh.does_socket_exist('Muzzle_01'),'Course muzzle socket missing'
assert unreal.DasAssetLibrary.load_optional_asset('/Game/DoesNotExist/Optional.Optional') is None
assert unreal.DasAssetLibrary.load_optional_asset('invalid') is None
tag=unreal.GameplayTag();assert tag.import_text('Action.PrimaryAttack')
attack=system.call_method('FindAction',args=(tag,))
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
def spawn_variant(name):
    kind=unreal.load_class(None,f'/Game/DasRogue/Tests/BP_{name}.BP_{name}_C')
    assert kind,name
    return probe.call_method('Spawn',args=(kind,unreal.Vector(-1000,1000,200),unreal.Rotator()))
assert attack.get_editor_property('AttackMontage')==profile.get_editor_property('AttackMontage')
inputs=max([v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer'],key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
def inject(name):inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),unreal.Vector(1,0,0),[],[])
def game_time():return unreal.GameplayStatics.get_time_seconds(w)
pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0))
s={'phase':'move','at':game_time(),'start':time.perf_counter(),'done':False,'start_location':p.get_actor_location(),
   'checks':[{'external_mesh_and_anim_instance':True,'muzzle_socket':True,'missing_optional_asset_quiet':True}]}
receipt=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_presentation_pie.json')
def phase(value):s['phase']=value;s['at']=game_time()
def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'elapsed_seconds':time.perf_counter()-s['start']},indent=2))
def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['start']<60,'Presentation check timed out'
        for obj in (p,pc,system):assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        age=game_time()-s['at'];name=s['phase']
        if name=='move':
            inject('IA_Move')
            if age<.4:return
            assert (p.get_actor_location()-s['start_location']).length()>20
            assert p.get_velocity().length()>100 and mesh.get_anim_instance()
            s['checks'].append({'movement_with_external_anim_graph':True})
            p.get_editor_property('character_movement').stop_movement_immediately()
            phase('settle');return
        if name=='settle':
            if age<.15:return
            inject('IA_Fire');phase('cast');return
        if name=='cast':
            if not attack.call_method('IsRunning'):
                assert age<1,'Input did not start attack';return
            assert mesh.get_anim_instance().montage_is_playing(profile.get_editor_property('AttackMontage'))
            assert any(c.get_editor_property('asset')==profile.get_editor_property('CastEffect') for c in p.get_components_by_class(unreal.NiagaraComponent))
            s['checks'].append({'attack_montage_active':True,'course_cast_niagara_attached':True})
            phase('projectile');return
        if name=='projectile':
            if attack.get_editor_property('ProjectilesFired')==0:
                assert age<2,'Cast failed to spawn projectile';return
            shot=attack.get_editor_property('LastProjectile')
            assert unreal.SystemLibrary.is_valid(shot)
            assert shot.get_editor_property('LoopedNiagaraComponent').get_editor_property('asset')==profile.get_editor_property('ProjectileEffect')
            assert shot.get_editor_property('LoopedAudioComponent').get_editor_property('sound')==profile.get_editor_property('ProjectileSound')
            assert shot.get_editor_property('ExplosionEffect')==profile.get_editor_property('ImpactEffect')
            assert shot.get_editor_property('Visual').get_editor_property('hidden_in_game')
            s['checks'].append({'projectile_niagara_sound_and_impact_profile':True,'shot_count':attack.get_editor_property('ProjectilesFired')})
            # Also exercise the cone fallback in the same installed project.
            fallback=spawn_variant('RogueWithoutPresentation')
            assert not fallback.get_editor_property('LastDasError'),fallback.get_editor_property('LastDasError')
            assert not fallback.get_editor_property('UsingExternalPresentation')
            assert not fallback.get_editor_property('Visual').get_editor_property('hidden_in_game')
            assert fallback.get_editor_property('mesh').get_skeletal_mesh_asset() is None
            fallback.destroy_actor()
            missing=spawn_variant('RogueMissingPresentation')
            assert not missing.get_editor_property('UsingExternalPresentation')
            assert not missing.get_editor_property('LastDasError')
            missing.destroy_actor()
            s['checks'].append({'missing_profile_uses_fallback':True})
            s['checks'].append({'explicit_fallback_without_external_visuals':True})
            phase('cooldown');return
        if name=='cooldown':
            if attack.call_method('GetCooldownTimeRemaining')>0:return
            assert system.call_method('StartAction',args=(tag,))
            system.call_method('Shutdown')
            phase('cancel');return
        if name=='cancel':
            if age<.3:return
            assert attack.get_editor_property('ProjectilesFired')==1
            s['checks'].append({'cast_cancelled_with_external_montage':True})
            p.get_editor_property('Attributes').call_method('ApplyHealthChange',args=(p,-100.0))
            phase('death');return
        if name=='death':
            if age<.15:return
            assert p.get_editor_property('Dead')
            assert mesh.get_anim_instance().montage_is_playing(profile.get_editor_property('DeathMontage'))
            s['checks'].append({'death_montage_in_compatible_slot':True})
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)

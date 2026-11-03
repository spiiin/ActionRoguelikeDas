"""Real PIE: local Minion resources, animated poses, timed shots and reactions."""
import json,time,traceback
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
player=unreal.GameplayStatics.get_player_controller(world,0)
player.set_control_rotation(unreal.Rotator(0,0,0))
registry=unreal.AssetRegistryHelpers.get_asset_registry()
options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=False,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
for asset in registry.get_assets_by_path('/Game/DasRogue',recursive=True):
    dependencies=registry.get_dependencies(asset.package_name,options)
    assert not [str(x) for x in dependencies if str(x).startswith(('/Game/ParagonMinions/','/Game/DasRogueExternal/','/Game/ControlRig/'))],asset.package_name
base_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
for old in unreal.GameplayStatics.get_all_actors_of_class(world,base_kind):
    controller=old.get_controller()
    if controller:controller.destroy_actor()
    old.destroy_actor()
base_probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
probe_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueAIPresentationProbe.BP_RogueAIPresentationProbe_C')
probe=base_probe.call_method('Spawn',args=(probe_kind,unreal.Vector(0,0,300),unreal.Rotator()))
assert probe
# Capture the PIE scene directly: console screenshots can select an editor viewport.
camera=probe.call_method('Spawn',args=(unreal.SceneCapture2D.static_class(),unreal.Vector(2900,-500,240),unreal.Rotator(-11.5,45,0)))
assert camera
capture=camera.get_component_by_class(unreal.SceneCaptureComponent2D)
capture.capture_every_frame=False
capture.capture_on_movement=False
capture.capture_source=unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
capture.fov_angle=55.0
render_target=unreal.RenderingLibrary.create_render_target2d(world,1280,720,unreal.TextureRenderTargetFormat.RTF_RGBA8)
capture.texture_target=render_target

def capture_frame(name):
    folder=Path(unreal.Paths.project_saved_dir())/'Tests'
    folder.mkdir(parents=True,exist_ok=True)
    assert capture==camera.get_component_by_class(unreal.SceneCaptureComponent2D), 'Capture component replaced'
    origin=unreal.Vector(2900,-500,240)
    rotation=unreal.MathLibrary.find_look_at_rotation(origin,enemy.get_actor_location())
    camera.set_actor_location_and_rotation(origin,rotation,False,True)
    assert (capture.get_world_location()-origin).length()<1,'Capture transform lost'
    print('MINION_CAPTURE',name,capture.get_world_location(),capture.get_world_rotation(),enemy.get_actor_location())
    capture.capture_scene()
    unreal.RenderingLibrary.export_render_target(world,render_target,str(folder),name+'.png')
    assert (folder/(name+'.png')).is_file(),name

probe.call_method('ConfigureHealth',args=(pawn.get_editor_property('Attributes'),1000.0))
pawn.set_actor_location(unreal.Vector(2800,0,96),False,True)
pawn.get_editor_property('character_movement').disable_movement()
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueAIVisualTestCharacter.BP_RogueAIVisualTestCharacter_C')
enemy=probe.call_method('Spawn',args=(kind,unreal.Vector(4000,0,96),unreal.Rotator(0,180,0)))
assert enemy
def controller_details(actor):
    controller=actor.get_controller()
    return {'class':actor.get_class().get_path_name(),
            'configured_controller':str(actor.get_editor_property('ai_controller_class')),
            'auto_possess':str(actor.get_editor_property('auto_possess_ai')),
            'controller':str(controller),
            'controller_class':controller.get_class().get_path_name() if controller else None}
print('MINION_FIXTURE_ENEMY',controller_details(enemy))
assert enemy.get_controller(),str(controller_details(enemy))
mesh=enemy.get_editor_property('mesh');profile=enemy.get_editor_property('Presentation')
assert enemy.get_editor_property('UsingExternalPresentation') and profile
assert mesh.get_skeletal_mesh_asset()==profile.get_editor_property('CharacterMesh')
anim=mesh.get_anim_instance()
assert anim and anim.get_class()==profile.get_editor_property('AnimationClass')
assert mesh.does_socket_exist('Muzzle_01')
assert enemy.get_editor_property('Visual').get_editor_property('hidden_in_game')
system=enemy.get_editor_property('ActionSystem')
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value
attack=system.call_method('FindAction',args=(tag('Action.PrimaryAttack'),))
assert attack, f'Missing attack: class={enemy.get_editor_property("AttackClass")}'
assert attack.get_editor_property('AttackMontage')==profile.get_editor_property('AttackMontage'), 'Minion attack montage differs from profile'
assert abs(attack.get_editor_property('AttackDelay')-.4)<.001

missing_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueAIMissingPresentation.BP_RogueAIMissingPresentation_C')
fallback=probe.call_method('Spawn',args=(missing_kind,unreal.Vector(5000,1800,96),unreal.Rotator()))
assert fallback and not fallback.get_editor_property('UsingExternalPresentation')
assert not fallback.get_editor_property('Visual').get_editor_property('hidden_in_game')
assert not fallback.get_editor_property('LastDasError')
print('MINION_FIXTURE_FALLBACK',controller_details(fallback))
assert fallback.get_controller(),str(controller_details(fallback))
probe.call_method('FreezeBrain',args=(fallback,pawn))

bone=next((n for n in ['foot_l','ball_l','calf_l','spine_01'] if mesh.get_bone_index(n)>=0),None)
assert bone,'No locomotion bone found'
def pose(name):return mesh.get_socket_transform(name,unreal.RelativeTransformSpace.RTS_COMPONENT).translation
def now():return unreal.GameplayStatics.get_time_seconds(world)
def active(name):return anim.montage_is_active(profile.get_editor_property(name))
result=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_ai_presentation_pie.json')
s={'phase':'locomotion','at':now(),'start':time.perf_counter(),'done':False,'actors':[probe,enemy,fallback,camera],
   'origin':enemy.get_actor_location(),'pose':pose(bone),
   'checks':[{'minion_mesh_graph_socket_and_attack_profile':True},{'missing_profile_preserves_fallback':True}]}

def phase(name):s.update(phase=name,at=now())
def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in s['actors']:
        if unreal.SystemLibrary.is_valid(actor):
            if isinstance(actor,unreal.Pawn):
                controller=actor.get_controller()
                if controller:controller.destroy_actor()
            actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['start']<35,'Presentation timeout in '+s['phase']
        if unreal.SystemLibrary.is_valid(enemy):assert not enemy.get_editor_property('LastDasError'),enemy.get_editor_property('LastDasError')
        age=now()-s['at'];state=s['phase']
        if state=='locomotion':
            if age<.8:return
            assert (enemy.get_actor_location()-s['origin']).length()>25, str({'message':'Minion did not pursue player','controller':controller_details(enemy),'sight':enemy.get_controller().get_editor_property('SightEvents'),'moves':enemy.get_controller().get_editor_property('MoveRequests'),'target':str(enemy.get_editor_property('Target'))})
            assert (pose(bone)-s['pose']).length()>.01,'Locomotion graph did not animate the pose'
            s['checks'].append({'pursuit_updates_locomotion_pose':True})
            probe.call_method('FreezeBrain',args=(enemy,pawn))
            enemy.set_actor_location(unreal.Vector(3400,0,96),False,True)
            enemy.set_actor_rotation(unreal.Rotator(0,180,0),True)
            s['shots']=attack.get_editor_property('ProjectilesFired')
            assert system.call_method('StartAction',args=(tag('Action.PrimaryAttack'),))
            phase('windup');return
        if state=='windup':
            if age<.14:return
            assert active('AttackMontage'),'Attack montage is not active during windup'
            assert attack.get_editor_property('ProjectilesFired')==s['shots'],'Shot fired before windup'
            s['checks'].append({'attack_telegraph_precedes_projectile':True})
            phase('shot')
            capture_frame('MinionAttack')
            return
        if state=='shot':
            if age<.4:return
            assert attack.get_editor_property('ProjectilesFired')==s['shots']+1,'Timed projectile missing'
            muzzle=attack.get_editor_property('LastMuzzleLocation')
            assert (muzzle-mesh.get_socket_location('Muzzle_01')).length()<50,'Projectile did not originate at animated weapon socket'
            s['checks'].append({'shot_uses_animated_muzzle':True})
            phase('cooldown');return
        if state=='cooldown':
            if age<.6:return
            assert system.call_method('StartAction',args=(tag('Action.PrimaryAttack'),))
            s['shots']=attack.get_editor_property('ProjectilesFired')
            phase('hit_pending');return
        if state=='hit_pending':
            if age<.08:return
            unreal.GameplayStatics.apply_damage(enemy,5.0,player,pawn,None)
            phase('hit');return
        if state=='hit':
            if age<.12:return
            assert enemy.get_editor_property('HitReactions')==1 and active('HitReactMontage'),'Missing full-body hit reaction'
            assert not attack.call_method('IsRunning'),'Hit left the pending attack active'
            unreal.GameplayStatics.apply_damage(enemy,5.0,player,pawn,None)
            phase('hit_cancelled');return
        if state=='hit_cancelled':
            if age<.5:return
            assert enemy.get_editor_property('HitReactions')==1,'Rapid hits restarted the reaction'
            assert attack.get_editor_property('ProjectilesFired')==s['shots'],'Cancelled shot still fired'
            s['checks'].append({'hit_reaction_cancels_windup_and_limits_restarts':True})
            stun=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
            assert system.call_method('GrantAction',args=(stun,))
            phase('stun');return
        if state=='stun':
            if age<.15:return
            assert enemy.get_editor_property('Stunned') and enemy.get_editor_property('StunAnimations')==1
            assert active('StunMontage'),'Stun montage missing'
            phase('recover');return
        if state=='recover':
            if enemy.get_editor_property('Stunned'):
                assert age<4,'Stun did not expire';return
            phase('blend_out');return
        if state=='blend_out':
            if age<.4:return
            assert not active('StunMontage'),'Stun pose remained after recovery'
            s['checks'].append({'stun_animation_stops_on_recovery':True})
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            phase('death');return
        if state=='death':
            if age<.6:return
            assert enemy.get_editor_property('Dead') and enemy.get_editor_property('DeathAnimations')==1
            assert not system.get_editor_property('Enabled') and not unreal.SystemLibrary.is_valid(enemy.get_controller())
            assert active('DeathMontage'),'Death pose blended back to idle'
            s['death_pose']=pose(bone)
            phase('hold')
            capture_frame('MinionDeath')
            return
        if state=='hold':
            if age<.3:return
            assert (pose(bone)-s['death_pose']).length()<.1,'Death pose is not held'
            s['checks'].append({'death_holds_pose_and_stops_combat':True})
            phase('cleanup');return
        if state=='cleanup':
            if unreal.SystemLibrary.is_valid(enemy):
                assert age<3,'Dead actor did not expire';return
            s['checks'].append({'death_lifespan_cleans_actor':True})
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False

s['handle']=unreal.register_slate_post_tick_callback(tick)

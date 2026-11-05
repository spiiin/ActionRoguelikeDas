"""Real audio and Niagara lifecycle on the original-layout DAS map."""
from pathlib import Path
import unreal,json,time,traceback
root=Path(__file__).resolve().parents[1]
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
player=unreal.GameplayStatics.get_player_controller(w,0)
pawn=unreal.GameplayStatics.get_player_pawn(w,0)
system=pawn.get_editor_property('ActionSystem')
profile=pawn.get_editor_property('Presentation')
actors={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)}
probe=actors['Course effects test probe'];barrel=actors['BP_ExplosiveBarrel']
inputs=max([o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if o.get_outer().get_class().get_name()=='LocalPlayer'],key=lambda o:int(o.get_outer().get_name().rsplit('_',1)[-1]))
s=dict(done=False,phase='ready',at=time.perf_counter(),started=time.perf_counter(),checks=[])
receipt=root/'Saved/Tests/rogue_course_effects_pie.json'
def prop(o,n):return o.get_editor_property(n)
def valid(o):
    if o is None:return False
    try:
        o.get_path_name()
        return unreal.SystemLibrary.is_valid(o)
    except Exception:return False
def tag(n):
    v=unreal.GameplayTag();assert v.import_text(n);return v
def action(n):return system.call_method('FindAction',args=(tag(n),))
def phase(n):s.update(phase=n,at=time.perf_counter())
def inject(n,value=1):inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+n),unreal.Vector(value,0,0),[],[])
def check(n):s['checks'].append(n)
def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    receipt.write_text(json.dumps(dict(passed=error is None,error=error,checks=s['checks'],coin_ms=s.get('coin_ms')),indent=2))
def niagara(asset):
    return [c for c in unreal.ObjectIterator(unreal.NiagaraComponent) if c.get_path_name().startswith(w.get_path_name()) and c.get_asset()==asset]

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<65,s['phase']
        for obj in [pawn,system,probe,barrel]:
            if valid(obj):assert not prop(obj,'LastDasError'),prop(obj,'LastDasError')
        age=time.perf_counter()-s['at']
        if s['phase']=='ready':
            if age<.5:return
            for field in ['CastSound','ProjectileSound','ImpactSound','BlackholeSound','TeleportImpactSound','SprintSound','StunSound']:
                assert prop(profile,field).get_class().get_name()=='MetaSoundSource',field
            check('original_MetaSound_graphs_replace_individual_waves')
            pawn.character_movement.disable_movement()
            s['sprint']=action('Action.Sprint');assert s['sprint']
            inject('IA_Sprint');phase('sprint');return
        if s['phase']=='sprint':
            a=s['sprint'];inject('IA_Sprint')
            if not a.call_method('IsRunning'):assert age<1;return
            left=prop(a,'LeftHandEffect');right=prop(a,'RightHandEffect');audio=prop(a,'HoverSound')
            assert valid(left) and valid(right) and valid(audio),dict(left=str(left),right=str(right),audio=str(audio),effect=str(prop(a,'SprintEffect')),sound=str(prop(a,'SprintSound')))
            for component,socket in [(left,'Muzzle_02'),(right,'Muzzle_01')]:
                assert component.get_asset()==prop(profile,'SprintEffect')
                assert component.get_attach_parent()==pawn.mesh
                assert str(component.get_attach_socket_name())==socket
                if not component.is_active():
                    assert age<4,dict(component=str(component),auto_activate=str(prop(component,'auto_activate')))
                    return
            assert prop(audio,'sound')==prop(profile,'SprintSound') and audio.is_playing()
            s['hover']=audio
            check('Shift_spawns_two_original_hand_systems_on_original_sockets_and_hover_audio')
            phase('release');return
        if s['phase']=='release':
            inject('IA_Sprint',0)
            a=s['sprint']
            if a.call_method('IsRunning'):assert age<1;return
            assert not valid(prop(a,'LeftHandEffect')) and not valid(prop(a,'RightHandEffect'))
            assert not valid(prop(a,'HoverSound'))
            audio=s['hover']
            if valid(audio) and audio.is_playing():assert age<4,'StopHovering did not finish sound';return
            check('Shift_release_returns_Niagara_to_pool_and_finishes_MetaSound')
            inject('IA_Sprint');phase('repeat');return
        if s['phase']=='repeat':
            a=s['sprint'];inject('IA_Sprint')
            if not a.call_method('IsRunning'):assert age<1;return
            assert valid(prop(a,'LeftHandEffect')) and valid(prop(a,'RightHandEffect'))
            system.call_method('StopAction',args=(tag('Action.Sprint'),))
            check('sprint_can_restart_after_release')
            pawn.set_actor_location(unreal.Vector(19600,0,1000),False,True)
            phase('teleport_aim');return
        if s['phase']=='teleport_aim':
            if age<.2:return
            kind=unreal.load_class(None,'/Game/DasRogue/Projectiles/BP_TeleportDemo.BP_TeleportDemo_C')
            s['shot']=probe.call_method('Spawn',args=(kind,unreal.Vector(19800,0,1000),pawn))
            s['shot_name']=s['shot'].get_name()
            s['shot_kind']=kind
            phase('teleport_hit');return
        if s['phase']=='teleport_hit':
            shot=s['shot'];assert valid(shot)
            if not prop(shot,'HasImpacted'):assert age<.2;return
            assert prop(shot,'ImpactCount')==1
            assert prop(shot,'LastImpactActor')==actors['Teleport effect test wall']
            assert prop(shot,'ExplosionEffect')==prop(profile,'TeleportImpactEffect')
            assert prop(shot,'ExplosionSound')==prop(profile,'TeleportImpactSound')
            assert niagara(prop(profile,'TeleportImpactEffect')),'No world-space portal impact component'
            assert not shot.get_actor_enable_collision()
            check('real_surface_hit_spawns_original_portal_effect_before_delayed_teleport')
            phase('teleport_done');return
        if s['phase']=='teleport_done':
            if any(a.get_name()==s['shot_name'] for a in unreal.GameplayStatics.get_all_actors_of_class(w,s['shot_kind'])):
                assert age<1,'Teleport projectile remained in the world'
                return
            pawn.set_actor_location(barrel.get_actor_location()+unreal.Vector(0,-350,150),False,True)
            barrel.set_editor_property('ExplosionDelay',2.0)
            unreal.GameplayStatics.apply_damage(barrel,1.0,player,pawn,None)
            phase('barrel_fuse');return
        if s['phase']=='barrel_fuse':
            if not prop(barrel,'Burning'):assert age<.4;return
            if not prop(barrel,'BurningEffectComponent').is_active():
                assert age<1.5,'Flames did not activate during fuse'
                return
            assert prop(barrel,'BurningAudioComponent').is_playing()
            assert prop(barrel,'BurningEffectComponent').get_asset()==prop(barrel,'BurningEffect')
            check('barrel_plays_original_flames_and_burning_MetaSound_during_fuse')
            phase('barrel_explosion');return
        if s['phase']=='barrel_explosion':
            if not prop(barrel,'Exploded'):assert age<2;return
            assert not prop(barrel,'BurningAudioComponent').is_playing()
            assert niagara(prop(barrel,'ExplosionEffect')),'No barrel explosion Niagara'
            check('barrel_stops_fuse_audio_and_spawns_original_explosion')
            source=actors['RogueCoinTestActor']
            start=time.perf_counter();assert source.call_method('SpawnCoins',args=(1000,))
            s['coin_ms']=(time.perf_counter()-start)*1000
            assert s['coin_ms']<150,s['coin_ms']
            check('clean_gameplay_code_spawns_1000_coins_without_multisecond_hitch')
            kind=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
            s['stun']=system.call_method('GrantAction',args=(kind,));s['stun'].call_method('StartAction')
            phase('stun');return
        if s['phase']=='stun':
            a=s['stun']
            assert valid(prop(a,'StunnedSound')) and prop(a,'StunnedSound').is_playing()
            assert prop(a,'ActiveSoundMix')==prop(profile,'StunMix')
            a.call_method('StopAction')
            assert not valid(prop(a,'StunnedSound')) and not valid(prop(a,'ActiveSoundMix'))
            check('local_player_stun_plays_MetaSound_and_balances_sound_mix_on_stop')
            a.call_method('StartAction')
            check('active_stun_is_left_for_EndPIE_cleanup')
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)

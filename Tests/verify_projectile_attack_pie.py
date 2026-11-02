"""Real PIE: primary input, delayed firing, cooldown and action cancellation."""
import json
import time
import traceback
from pathlib import Path
import unreal

w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
system=p.get_editor_property('ActionSystem')

def tag(name):
    value=unreal.GameplayTag()
    assert value.import_text(name)
    return value

primary=tag('Action.PrimaryAttack')
stunned=unreal.GameplayTagLibrary.make_gameplay_tag_container_from_array([tag('StatusEffect.Stunned')])
attack=system.call_method('FindAction',args=(primary,))
assert attack and attack.get_outer()==system
assert abs(attack.get_editor_property('AttackDelay')-.2)<.001
assert abs(attack.get_editor_property('CooldownTime')-.5)<.001
assert attack.get_editor_property('ProjectilesFired')==0
cast_effect=unreal.load_asset('/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst')
cast_sound=unreal.load_asset('/Engine/EngineSounds/1kSineTonePing.1kSineTonePing')
assert cast_effect and cast_sound
attack.set_editor_property('CastingEffect',cast_effect)
attack.set_editor_property('CastingSound',cast_sound)
# Exercise the reflected montage call on the placeholder mesh (no AnimInstance => duration zero).
if not p.get_editor_property('UsingExternalPresentation'):
    attack.set_editor_property('AttackMontage',unreal.new_object(unreal.AnimMontage))
inputs=max([v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer'],key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
fire=unreal.load_asset('/Game/DasRogue/Input/IA_Fire')
pc.set_control_rotation(unreal.Rotator(pitch=10,yaw=180,roll=0))
s={'phase':'press','at':unreal.GameplayStatics.get_time_seconds(w),'start':time.perf_counter(),'done':False,'checks':[]}
receipt=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_projectile_attack_pie.json')

def phase(name):s['phase']=name;s['at']=unreal.GameplayStatics.get_time_seconds(w)

def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'elapsed_seconds':time.perf_counter()-s['start']},indent=2),encoding='utf-8')

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['start']<30,'Attack checks timed out'
        for obj in (p,pc,system):assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        age=unreal.GameplayStatics.get_time_seconds(w)-s['at']
        name=s['phase']
        if name=='press':
            inputs.inject_input_vector_for_action(fire,unreal.Vector(1,0,0),[],[])
            if not attack.call_method('IsRunning'):return
            assert attack.get_editor_property('ProjectilesFired')==0
            assert not system.call_method('StartAction',args=(primary,))
            effects=p.get_components_by_class(unreal.NiagaraComponent)
            assert any(c.get_editor_property('asset')==cast_effect and c.get_attach_parent()==p.get_editor_property('mesh') for c in effects),'Cast Niagara was not attached to character mesh'
            s['checks'].append({'attached_cast_effect':True,'sound_call_without_runtime_error':True})
            phase('windup');return
        if name=='windup':
            inputs.inject_input_vector_for_action(fire,unreal.Vector(1,0,0),[],[])
            count=attack.get_editor_property('ProjectilesFired')
            if age<.15:assert count==0,'Shot fired before windup'
            if count==0:return
            assert age>=.17,'AttackDelay ignored'
            assert count==1 and not attack.call_method('IsRunning')
            assert attack.call_method('GetCooldownTimeRemaining')>.35
            assert not system.call_method('StartAction',args=(primary,))
            s['checks'].append({'delayed_shot_seconds':age,'cooldown_blocks_restart':True})
            phase('hold');return
        if name=='hold':
            inputs.inject_input_vector_for_action(fire,unreal.Vector(1,0,0),[],[])
            assert attack.get_editor_property('ProjectilesFired')==1,'Held LMB repeats Started'
            if age<.65:return
            s['checks'].append({'held_input_fires_once':True})
            phase('release');return
        if name=='release':
            if age<.1:return
            assert system.call_method('StartAction',args=(primary,))
            system.call_method('AppendActiveTags',args=(stunned,))
            assert not attack.call_method('IsRunning')
            phase('stun');return
        if name=='stun':
            if age<.8:return
            assert attack.get_editor_property('ProjectilesFired')==1,'Stunned cast still fired'
            assert not system.call_method('StartAction',args=(primary,))
            system.call_method('RemoveActiveTags',args=(stunned,))
            s['checks'].append({'stun_cancels_timer':True})
            assert system.call_method('StartAction',args=(primary,))
            phase('second');return
        if name=='second':
            if attack.get_editor_property('ProjectilesFired')<2:return
            assert attack.get_editor_property('Starts')==3
            s['checks'].append({'restart_after_cooldown':True})
            phase('wait_remove');return
        if name=='wait_remove':
            if attack.call_method('GetCooldownTimeRemaining')>0:return
            assert system.call_method('StartAction',args=(primary,))
            assert system.call_method('RemoveAction',args=(attack,))
            phase('remove');return
        if name=='remove':
            if age<.35:return
            assert attack.get_editor_property('ProjectilesFired')==2,'Removed action fired'
            assert not attack.call_method('IsRunning')
            s['checks'].append({'removal_cancels_timer':True})
            kind=attack.get_class()
            s['death_attack']=system.call_method('GrantAction',args=(kind,))
            assert system.call_method('StartAction',args=(primary,))
            p.get_editor_property('Attributes').call_method('ApplyHealthChange',args=(p,-100.0))
            phase('death');return
        if name=='death':
            if age<.4:return
            a=s['death_attack']
            assert p.get_editor_property('Dead') and not system.get_editor_property('Enabled')
            assert not a.call_method('IsRunning') and a.get_editor_property('ProjectilesFired')==0
            s['checks'].append({'death_cancels_pending_shot':True})
            finish()
    except Exception:finish(traceback.format_exc())

s['handle']=unreal.register_slate_post_tick_callback(tick)

"""Real Slate widgets, DAS subscriptions/effects, world projection and teardown in PIE."""
import json,time,traceback,unreal
from pathlib import Path
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
player=unreal.GameplayStatics.get_player_controller(world,0)
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
hud=player.get_editor_property('HUD')
system=pawn.get_editor_property('ActionSystem')
attributes=pawn.get_editor_property('Attributes')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
def prop(o,n):return o.get_editor_property(n)
def tag(n):
    t=unreal.GameplayTag();assert t.import_text(n);return t
def change(n,v):system.call_method('ApplyAttributeChange',args=(tag(n),float(v)))
def now():return unreal.GameplayStatics.get_time_seconds(world)
def child(widget,n):
    tree=next(t for t in unreal.ObjectIterator(unreal.load_class(None,'/Script/UMG.WidgetTree')) if t.get_outer()==widget)
    return unreal.find_object(tree,n)
def text(widget,n):return str(child(widget,n).get_text())
def valid(o):
    try:return o is not None and unreal.SystemLibrary.is_valid(o)
    except TypeError:return False
s={'phase':'ready','at':now(),'started':time.perf_counter(),'done':False,'checks':[]}
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_hud_pie.json'
def phase(n):s['phase']=n;s['at']=now()
def check(n):s['checks'].append(n)
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))
def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<45,'HUD scenario timed out: '+s['phase']
        age=now()-s['at']
        if s['phase']=='ready':
            if age<.3:return
            widget=prop(hud,'HUD');assert widget and widget.is_in_viewport()
            assert prop(hud,'Pawn')==pawn and prop(hud,'System')==system
            s['widget']=widget
            check('local_HUD_created_and_bound_to_possessed_pawn')
            probe.call_method('ConfigureHealth',args=(attributes,100.0))
            change('Attribute.Health',-25)
            change('Attribute.Rage',40)
            system.call_method('GrantCoins',args=(5000000000,))
            hud.call_method('RefreshVitals')
            assert abs(child(widget,'HealthBar').get_editor_property('percent')-.75)<.001
            assert abs(child(widget,'RageBar').get_editor_property('percent')-.4)<.001
            assert '75 / 100' in text(widget,'HealthText')
            assert '5000000000' in text(widget,'CoinsText')
            check('health_rage_and_int64_coins_update_through_DAS_events')
            hud.call_method('BindPawn',args=(None,))
            assert child(widget,'HealthBar').get_editor_property('percent')==0
            check('unpossessed_HUD_clears_vitals_with_finite_zero_maximum')
            hud.call_method('BindPawn',args=(pawn,))
            probe.call_method('ConfigureHealth',args=(attributes,100.0))
            kind=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
            defaults=unreal.get_default_object(kind)
            old_icon=prop(defaults,'IconPath')
            defaults.set_editor_property('IconPath','/Engine/EngineResources/DefaultTexture.DefaultTexture')
            try:s['effect']=system.call_method('GrantAction',args=(kind,))
            finally:defaults.set_editor_property('IconPath',old_icon)
            assert s['effect']
            phase('effect');return
        if s['phase']=='effect':
            if age<.25:return
            rows=list(prop(hud,'EffectWidgets'));assert len(rows)==1
            row=rows[0];assert text(row,'EffectName')=='Stunned'
            texture=child(row,'Icon').get_editor_property('brush').get_editor_property('resource_object')
            if not texture and age<1.5:return
            assert texture and texture.get_path_name()=='/Engine/EngineResources/DefaultTexture.DefaultTexture',str(texture)
            if not s.get('capture_requested'):
                s['capture_requested']=True
                unreal.SystemLibrary.execute_console_command(world,'Shot showui nosuffix filename='+str(Path(unreal.Paths.project_saved_dir())/'Tests/rogue_hud_ui.png'))
                return
            check('soft_icon_texture_is_applied_asynchronously_to_the_effect_row')
            assert 'x1' in text(row,'Details') and 's' in text(row,'Details')
            assert row.get_desired_size().y>0
            check('effect_row_constructed_with_name_stack_duration_and_nonzero_size')
            count=prop(hud,'EffectsCreated')
            assert system.call_method('GrantAction',args=(s['effect'].get_class(),))==s['effect']
            hud.call_method('RefreshEffects')
            assert prop(hud,'EffectsCreated')==count and 'x2' in text(row,'Details')
            unreal.SystemLibrary.collect_garbage()
            assert valid(row) and valid(s['effect'])
            check('stack_reuses_row_and_reflected_ownership_survives_GC')
            system.call_method('RemoveAction',args=(s['effect'],))
            hud.call_method('RefreshEffects')
            assert len(prop(hud,'EffectWidgets'))==0
            check('effect_removal_releases_its_row')
            # Spawn a real game enemy with its data-defined widget class.
            kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
            camera=player.player_camera_manager.get_camera_location()
            direction=unreal.MathLibrary.get_forward_vector(player.get_control_rotation())
            s['enemy']=probe.call_method('Spawn',args=(kind,camera+direction*700,unreal.Rotator()))
            enemy=s['enemy'];assert enemy
            ai=enemy.get_controller()
            if ai:
                ai.stop_movement()
                ai.set_actor_tick_enabled(False)
            data=unreal.load_asset('/Game/DasRogue/AI/DA_RangedMinion')
            assert enemy.call_method('ConfigureMonsterData',args=(data,))
            s['health']=prop(enemy,'HealthWidget');s['enemy_attributes']=prop(enemy,'Attributes')
            assert not valid(prop(s['health'],'Widget'))
            check('MonsterData_selects_health_layout_hidden_before_first_damage')
            prop(enemy,'ActionSystem').call_method('ApplyAttributeChange',args=(tag('Attribute.Health'),-20.0))
            phase('health');return
        if s['phase']=='health':
            if age<.15:return
            health=s['health'];widget=prop(health,'Widget');assert widget
            assert prop(health,'WidgetCreations')==1 and prop(health,'PositionUpdates')>0
            assert prop(health,'Projected')
            attr=s['enemy_attributes']
            assert abs(child(widget,'HealthBar').get_editor_property('percent')-prop(attr,'Health')/prop(attr,'HealthMax'))<.001
            check('first_nonlethal_damage_creates_and_projects_health_widget')
            position=s['enemy'].get_actor_location()
            expected=unreal.WidgetLayoutLibrary.project_world_location_to_widget_position(player,position+prop(health,'AnchorOffset'),True)
            actual=prop(health,'LastScreenPosition')
            assert expected is not None and abs(actual.x-expected.x)<.1 and abs(actual.y-expected.y)<.1
            check('world_widget_uses_native_DPI_corrected_coordinate_space')
            camera=player.player_camera_manager.get_camera_location()
            direction=unreal.MathLibrary.get_forward_vector(player.player_camera_manager.get_camera_rotation())
            s['enemy'].set_actor_location(camera-direction*700,False,True)
            health.call_method('UpdatePosition')
            assert not prop(health,'Projected') and widget.get_visibility()==unreal.SlateVisibility.COLLAPSED
            s['enemy'].set_actor_location(position,False,True)
            health.call_method('UpdatePosition')
            check('world_health_widget_hides_behind_the_camera_and_recovers')
            prop(s['enemy'],'ActionSystem').call_method('ApplyAttributeChange',args=(tag('Attribute.Health'),5.0))
            assert prop(health,'WidgetCreations')==1
            check('healing_updates_existing_world_health_widget')
            prop(s['enemy'],'ActionSystem').call_method('ApplyAttributeChange',args=(tag('Attribute.Health'),-10000.0))
            assert not valid(prop(health,'Widget')) and not widget.is_in_viewport()
            check('death_removes_world_widget')
            assert prop(s['enemy'],'LastLootCoins')==unreal.load_asset('/Game/DasRogue/AI/DA_RangedMinion').get_editor_property('LootCoins')
            check('MonsterData_loot_settings_survive_action_schema_migration')
            # Rebinding the same pawn unsubscribes old delegates before subscribing.
            before=prop(hud,'VitalsUpdates')
            hud.call_method('BindPawn',args=(pawn,))
            rebound=prop(hud,'VitalsUpdates')
            change('Attribute.Health',-1)
            assert prop(hud,'VitalsUpdates')==rebound+1
            check('rebinding_pawn_does_not_duplicate_attribute_subscription')
            hud.destroy_component(player)
            assert not s['widget'].is_in_viewport()
            change('Attribute.Health',-1)
            check('EndPlay_removes_HUD_and_unsubscribes_from_live_system')
            finish();return
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)

"""Real Recast movement, graph selection and combat/stun interruption in PIE."""
import json,time,traceback
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
player=unreal.GameplayStatics.get_player_controller(world,0)
enemy_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
enemy=next(iter(unreal.GameplayStatics.get_all_actors_of_class(world,enemy_kind)))
controller=enemy.get_controller()
assert controller and controller.get_class().get_name()=='BP_RoguePatrolController_C'
assert controller.get_editor_property('UsePathfinding'),'Patrol controller must use NavMesh for combat moves too'
point_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RoguePatrolPoint.BP_RoguePatrolPoint_C')
points=unreal.GameplayStatics.get_all_actors_of_class(world,point_kind)
assert len(points)==4
points.sort(key=lambda a:(a.get_actor_location().y,a.get_actor_location().x))
a,b,d,c=points
assert a.get_actor_location().x==3200 and b.get_actor_location().x==4400
base_probe=next(actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if actor.get_class().get_name()=='BP_RogueActionProbe_C')
probe_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePatrolProbe.BP_RoguePatrolProbe_C')
probe=base_probe.call_method('Spawn',args=(probe_kind,unreal.Vector(0,0,400),unreal.Rotator()))
assert probe
capsule_radius=enemy.get_editor_property('capsule_component').get_scaled_capsule_radius()
assert capsule_radius>0
probe.call_method('ConfigureHealth',args=(pawn.get_editor_property('Attributes'),1000.0))
pawn.set_actor_location(unreal.Vector(600,-1500,96),False,True)
pawn.get_editor_property('character_movement').disable_movement()
probe.call_method('PausePatrol',args=(controller,))

def now():return unreal.GameplayStatics.get_time_seconds(world)
def patrol_active():return controller.call_method('IsPatrolling')
def configure(start,previous=None,destination=None):
    probe.call_method('ConfigureRoute',args=(controller,start,previous,destination))
def start_route(start,destination):
    probe.call_method('StartRoute',args=(controller,start,None,destination))
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_patrol_pie.json'
s={'phase':'setup','at':now(),'started':time.perf_counter(),'done':False,'checks':[]}

def phase(name):s.update(phase=name,at=now())
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in [probe,enemy]:
        if unreal.SystemLibrary.is_valid(actor):
            if isinstance(actor,unreal.Pawn):
                owner=actor.get_controller()
                if owner:owner.destroy_actor()
            actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<90,'Patrol test timed out in '+s['phase']
        for actor in [enemy,probe]:
            if unreal.SystemLibrary.is_valid(actor):assert not actor.get_editor_property('LastDasError'),actor.get_editor_property('LastDasError')
        state=s['phase'];age=now()-s['at']
        if state=='setup':
            if age<.2:return
            assert not patrol_active()
            # Enter through the actor probe so Unreal's editor world switcher has
            # a real PIE owner before the NavigationSystem static call. A direct
            # Python class call uses its world-less CDO and triggers an engine ensure.
            if not probe.call_method('HasFullRoute',args=(a.get_actor_location(),b.get_actor_location())):
                assert age<8,'PIE NavMesh is not ready';return
            length=probe.call_method('QueryDistance',args=(a.get_actor_location(),b.get_actor_location()))
            assert length>1250,'DAS corridor query did not return the detour length'
            s['checks'].append({'pie_full_path_and_das_corridor_query_detour':True})
            assert controller.call_method('RefreshPatrolGraph')
            for point in points:
                neighbors=point.call_method('GetConnections')
                assert neighbors and point not in neighbors and len(neighbors)==len(set(x.get_path_name() for x in neighbors))
            probe.call_method('SetPathLimit',args=(a,1210.0))
            assert a.call_method('RebuildConnections',args=(points,))
            assert b not in a.call_method('GetConnections'),'Straight-line distance was used instead of nav path length'
            assert a not in b.call_method('GetConnections'),'Reverse connection was not removed'
            probe.call_method('SetPathLimit',args=(a,2300.0))
            assert controller.call_method('RefreshPatrolGraph')
            s['checks'].append({'patrol_graph_uses_path_budget_and_has_no_self_or_duplicates':True})
            configure(None)
            assert controller.call_method('ChooseNextPoint') in points
            assert controller.get_editor_property('CurrentPatrolPoint')==a,'Nearest initial patrol point was not selected'
            configure(a,b)
            for i in range(16):assert controller.call_method('ChooseNextPoint') in [c,d]
            s['checks'].append({'nearest_start_and_no_immediate_backtracking':True})
            for point in points:probe.call_method('SetPathLimit',args=(point,0.0))
            assert controller.call_method('RefreshPatrolGraph')
            s['moves']=controller.get_editor_property('PatrolMovesStarted')
            start_route(a,None)
            phase('isolated');return
        if state=='isolated':
            if age<.4:return
            assert controller.get_editor_property('PatrolMovesStarted')==s['moves'] and not patrol_active()
            s['checks'].append({'isolated_points_idle_without_invalid_requests':True})
            probe.call_method('PausePatrol',args=(controller,))
            for point in points:probe.call_method('SetPathLimit',args=(point,2300.0))
            assert controller.call_method('RefreshPatrolGraph')
            enemy.set_actor_location(unreal.Vector(3200,0,96),False,True)
            s['arrivals']=controller.get_editor_property('PatrolArrivals');s['detour_y']=0.0;s['minimum_clearance']=float('inf')
            start_route(a,b)
            phase('route');return
        if state=='route':
            position=enemy.get_actor_location();s['detour_y']=max(s['detour_y'],abs(position.y))
            dx=max(abs(position.x-3800)-100,0);dy=max(abs(position.y)-400,0)
            clearance=(dx*dx+dy*dy)**.5
            s['minimum_clearance']=min(s['minimum_clearance'],clearance)
            assert clearance>=capsule_radius-.5,f'Pawn capsule intersected obstacle: position={position}, clearance={clearance}, radius={capsule_radius}'
            if controller.get_editor_property('PatrolArrivals')==s['arrivals']:
                assert age<12,'Patrol failed to arrive';return
            assert controller.get_editor_property('CurrentPatrolPoint')==b
            assert s['detour_y']>400 and (position-b.get_actor_location()).length()<160
            s['checks'].append({'character_follows_navmesh_around_obstacle_and_arrives':True,'capsule_radius':capsule_radius,'minimum_clearance':s['minimum_clearance']})
            probe.call_method('PausePatrol',args=(controller,))
            phase('pause');return
        if state=='pause':
            if age<.2:return
            start_route(b,a)
            phase('before_stun');return
        if state=='before_stun':
            if age<.35:return
            assert patrol_active()
            stun=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
            assert enemy.get_editor_property('ActionSystem').call_method('GrantAction',args=(stun,))
            phase('stun_settle');return
        if state=='stun_settle':
            if age<.25:return
            assert enemy.get_editor_property('Stunned') and not patrol_active()
            s['stun_position']=enemy.get_actor_location();s['moves']=controller.get_editor_property('PatrolMovesStarted')
            phase('stunned');return
        if state=='stunned':
            if age<.35:return
            assert (enemy.get_actor_location()-s['stun_position']).length()<3
            phase('recover');return
        if state=='recover':
            if enemy.get_editor_property('Stunned') or not patrol_active():
                assert age<4.5,'Patrol did not resume after stun';return
            assert controller.get_editor_property('PatrolMovesStarted')>s['moves']
            assert controller.get_editor_property('PatrolDestination')==a
            s['checks'].append({'stun_cancels_move_and_resumes_same_destination':True})
            pawn.set_actor_location(enemy.get_actor_location()+unreal.Vector(0,-500,0),False,True)
            unreal.AISense_Hearing.report_noise_event(world,pawn.get_actor_location(),1.0,pawn,1800.0,'Patrol_regression')
            phase('combat');return
        if state=='combat':
            if enemy.get_editor_property('Target')!=pawn:
                assert age<1.5,'AI did not acquire player';return
            if age<.25:return
            assert not patrol_active(),'Patrol request remained active during combat'
            assert controller.get_editor_property('PatrolDestination')==a
            pawn.set_actor_location(unreal.Vector(600,-1500,96),False,True)
            s['moves']=controller.get_editor_property('PatrolMovesStarted')
            phase('forget');return
        if state=='forget':
            if controller.get_editor_property('CurrentTarget') or not patrol_active():
                assert age<5,'Patrol did not resume after target memory expired';return
            assert controller.get_editor_property('PatrolMovesStarted')>s['moves']
            s['checks'].append({'combat_preempts_patrol_and_lost_target_resumes_it':True})
            s['moves']=controller.get_editor_property('PatrolMovesStarted')
            s['deleted_name']=a.get_name()
            a.destroy_actor()
            phase('deleted_goal');return
        if state=='deleted_goal':
            if controller.get_editor_property('PatrolMovesStarted')==s['moves'] or not patrol_active():
                assert age<3,'Deleted goal did not trigger a new patrol request';return
            destination=controller.get_editor_property('PatrolDestination')
            assert destination and unreal.SystemLibrary.is_valid(destination)
            assert destination.get_name()!=s['deleted_name']
            assert all(point.get_name()!=s['deleted_name'] for point in b.call_method('GetConnections'))
            s['checks'].append({'deleted_goal_is_filtered_and_replanned':True})
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            phase('death');return
        if state=='death':
            if age<.25:return
            assert enemy.get_editor_property('Dead') and not unreal.SystemLibrary.is_valid(controller)
            s['checks'].append({'death_destroys_controller_and_owned_moves':True})
            phase('cleanup');return
        if state=='cleanup':
            if unreal.SystemLibrary.is_valid(enemy):
                assert age<3,'Dead minion did not expire';return
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False

s['handle']=unreal.register_slate_post_tick_callback(tick)

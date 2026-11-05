"""Author the environment demo using engine assets; gameplay remains DAS."""
from pathlib import Path
import unreal,runpy
ROOT=Path(__file__).resolve().parents[1]
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='EnvironmentTest'
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
for source,name,folder,identity in [
    ('rogue_lever','RogueLever','World','rogue.RogueLever'),
    ('rogue_projectile_spammer','RogueProjectileSpammer','World','rogue.RogueProjectileSpammer'),
    ('rogue_lever_demo','RogueLeverDemo','World','roguedemo.RogueLeverDemo'),
    ('rogue_lever_spammer_demo','RogueLeverSpammerDemo','World','roguedemo.RogueLeverSpammerDemo')]:
    path='/Game/DasRogue/'+folder+'/BP_'+name
    command='Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply '+source+'.das '+path+' '+identity
    unreal.SystemLibrary.execute_console_command(world,command)
    assert unreal.load_class(None,path+'.BP_'+name+'_C'),name
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_name().startswith('BP_') or isinstance(actor,unreal.StaticMeshActor):
        actors.destroy_actor(actor)
    elif isinstance(actor,unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(0,0,96),False,True)
        actor.set_actor_rotation(unreal.Rotator(),False)

def spawn(path,label,location,rotation=unreal.Rotator()):
    kind=unreal.load_class(None,path)
    actor=actors.spawn_actor_from_class(kind,unreal.Vector(*location),rotation)
    assert actor,label
    actor.set_actor_label(label)
    return actor

def mesh(label,location,scale):
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*location))
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor
mesh('Environment arena floor',(1000,0,-50),(70,40,1))
mesh('Spammer target wall',(2400,500,200),(.5,8,4))
lever=spawn('/Game/DasRogue/World/BP_RogueLeverDemo.BP_RogueLeverDemo_C','Lever - press E to start the launcher',(200,0,80))
spammer=spawn('/Game/DasRogue/World/BP_RogueProjectileSpammer.BP_RogueProjectileSpammer_C','Projectile spammer - native half-second tick',(600,500,150))
link=spawn('/Game/DasRogue/World/BP_RogueLeverSpammerDemo.BP_RogueLeverSpammerDemo_C','daScript lever to spammer wiring',(0,0,0))
link.set_editor_property('Lever',lever)
link.set_editor_property('Spammer',spammer)
# A visible launcher housing is presentation only, not a spawn origin.
mesh('Launcher housing',(540,500,80),(.6,.6,1.6))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
runpy.run_path(str(ROOT/'Scripts/prepare_action_tests.py'))
print('DAS_ENVIRONMENT_PREPARE PASS')

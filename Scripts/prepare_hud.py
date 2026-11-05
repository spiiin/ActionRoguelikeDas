"""Import HUD logic after its layout assets; keep all graph behavior in DAS."""
from pathlib import Path
import runpy,unreal
ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'Scripts/prepare_hud_layouts.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
assert world.get_name()=='ChestTest','Open ChestTest before preparing the HUD'
unreal.load_asset('/Game/DasRogue/AI/DA_RangedMinion')
# ScriptObject actions support structural migration, including the new presentation fields.
for path in ['/Game/DasRogue/Actions/BP_RogueAction','/Game/DasRogue/AI/BP_RogueAction',
             '/Game/DasRogue/Tests/BP_RogueAction','/Game/DasRogue/Actions/BP_RogueActionEffect',
             '/Game/DasRogue/Actions/BP_RogueActionEffectBurning','/Game/DasRogue/Actions/BP_RogueActionEffectStun',
             '/Game/DasRogue/Actions/BP_RogueActionEffectOverwhelm']:
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport '+path)
for name,source in [('RogueHUDComponent','rogue_hud_component'),('RogueHealthWidgetComponent','rogue_health_widget_component')]:
    path='/Game/DasRogue/UI/BP_'+name
    command='Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply '+source+'.das '+path+' rogue.'+name
    unreal.SystemLibrary.execute_console_command(world,command)
    assert unreal.load_class(None,path+'.BP_'+name+'_C'),name+' failed import'
# HUD preparation does not migrate independent AI gameplay sources.
for path in ['/Game/DasRogue/BP_RoguePlayerController']:
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport '+path)
data=unreal.load_asset('/Game/DasRogue/AI/DA_RangedMinion')
assert data
data.modify(True)
data.set_editor_property('HealthWidgetClass',unreal.load_class(None,'/Game/DasRogue/UI/WBP_RogueHealth.WBP_RogueHealth_C'))
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
    if actor.get_class().get_name()=='BP_RogueAICharacter_C':
        actor.set_editor_property('MonsterData',data)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
runpy.run_path(str(ROOT/'Scripts/prepare_action_tests.py'))
print('DAS_HUD_PREPARE PASS')

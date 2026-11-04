"""Configure the combat target and update the projectile outside PIE."""
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[1]
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_burning_effect.py')))
for command in [
    'Das.DSL.Interfaces.Apply rogue_projectile_impact_interface.das /Game/DasRogue/Types',
    'Das.DSL.Apply rogue_magic_projectile.das /Game/DasRogue/BP_RogueMagicProjectile rogue.RogueMagicProjectile',
    'Das.DSL.Apply rogue_magic_projectile_demo.das /Game/DasRogue/BP_MagicProjectileDemo roguedemo.RogueMagicProjectileDemo',
    'Das.DSL.Apply rogue_combat_target.das /Game/DasRogue/BP_RogueCombatTarget roguedemo.RogueCombatTarget',
]:unreal.SystemLibrary.execute_console_command(world,command)
kind=unreal.load_class(None,'/Game/DasRogue/BP_RogueCombatTarget.BP_RogueCombatTarget_C')
assert kind
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
targets=[a for a in actors.get_all_level_actors() if a.get_class()==kind]
target=targets[0] if targets else actors.spawn_actor_from_class(kind,unreal.Vector(-180,100,100))
assert target
target.set_actor_label('daScript Combat Target - Overwhelm')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)

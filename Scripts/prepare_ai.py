"""Wire AI assets and the open test arena. All decisions/combat execute in DAS."""
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in [
    'Das.DSL.Interfaces.Apply rogue_projectile_impact_interface.das /Game/DasRogue/Types',
    'Das.DSL.Apply rogue_magic_projectile_demo.das /Game/DasRogue/BP_MagicProjectileDemo roguedemo.RogueMagicProjectileDemo',
    'Das.DSL.Apply rogue_ai_projectile_attack.das /Game/DasRogue/AI/BP_RogueAIRangedAttack rogue.RogueAIProjectileAttack',
    'Das.DSL.Apply rogue_ai_controller.das /Game/DasRogue/AI/BP_RogueAIController rogue.RogueAIController',
    'Das.DSL.Apply rogue_ai_character.das /Game/DasRogue/AI/BP_RogueAICharacter rogue.RogueAICharacter',
]:
    unreal.SystemLibrary.execute_console_command(world,command)
enemy_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
controller_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAIController.BP_RogueAIController_C')
attack_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAIRangedAttack.BP_RogueAIRangedAttack_C')
assert enemy_kind and controller_kind and attack_kind,'AI import failed; inspect DAS_DSL_APPLY'
unreal.load_asset('/Game/DasRogue/AI/BP_RogueAICharacter').modify(True)
enemy_defaults=unreal.get_default_object(enemy_kind)
enemy_defaults.set_editor_property('ai_controller_class',controller_kind)
enemy_defaults.set_editor_property('auto_possess_ai',unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
enemy_defaults.set_editor_property('AttackClass',attack_kind)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
existing=actors.get_all_level_actors()
floor=next((a for a in existing if a.get_actor_label()=='AI test arena floor'),None)
if not floor:
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(3000,0,-50))
    floor.set_actor_label('AI test arena floor')
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(60,40,1))
enemy=next((a for a in existing if a.get_class()==enemy_kind),None)
if not enemy:enemy=actors.spawn_actor_from_class(enemy_kind,unreal.Vector(3000,800,96),unreal.Rotator(0,180,0))
# Update existing placed instances as well as defaults for future spawns.
enemy.set_editor_property('ai_controller_class',controller_kind)
enemy.set_editor_property('auto_possess_ai',unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
enemy.set_editor_property('AttackClass',attack_kind)
enemy.set_actor_label('daScript AI enemy - sight and hearing')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_AI_PREPARE PASS')

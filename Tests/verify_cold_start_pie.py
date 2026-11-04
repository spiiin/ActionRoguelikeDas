"""Run in PIE after a fresh editor start; never preload or import attribute classes."""
import json
from pathlib import Path
import unreal

editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = editor.get_game_world()
assert world, 'Start PIE first, without running a prepare script'
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
assert pawn, 'Missing player pawn'
objects = [pawn, pawn.get_editor_property('ActionSystem'), pawn.get_editor_property('Attributes')]
for obj in objects:
    assert not obj.get_editor_property('LastDasError'), obj.get_editor_property('LastDasError')
attribute_set = objects[1].get_editor_property('AttributeSet')
assert attribute_set, 'BeginPlay did not create the attribute set'
assert attribute_set == objects[2].get_editor_property('AttributeSet'), 'Attribute bridges diverged'
assert attribute_set.get_class() == pawn.get_editor_property('DefaultAttributeSetClass')
assert attribute_set.get_editor_property('AttributesInitialized')
assert pawn.get_editor_property('ControlsBound'), 'BeginPlay stopped before input setup'
assert objects[2].get_editor_property('Health') > 0
receipt = {
    'passed': True,
    'map': world.get_name(),
    'attribute_class': attribute_set.get_class().get_path_name(),
    'checks': ['no_runtime_errors', 'player_attribute_set_created', 'shared_attribute_set',
               'attribute_defaults_initialized', 'input_bound', 'positive_health'],
}
path = Path(unreal.Paths.project_saved_dir()) / 'Tests/rogue_cold_start_pie.json'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(receipt, indent=2))
print('DAS_COLD_START_PASS ' + json.dumps(receipt))

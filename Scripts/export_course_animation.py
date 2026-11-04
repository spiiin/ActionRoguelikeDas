"""Run in the ORIGINAL course editor, outside PIE, after setup --with-course-animation.

PORT_ROOT may be supplied through runpy.run_path(..., init_globals={...}).
Only a temporary duplicate is edited. The course Blueprint and animations are untouched.
The generated duplicate and all licensed dependencies remain outside the public Git tree.
"""
from pathlib import Path
import hashlib,json,shutil
import unreal

port=Path(globals().get('PORT_ROOT',Path(__file__).resolve().parents[1])).resolve()
config=json.loads((port/'ExternalAssets.json').read_text())['course_animation']
source_root=Path(unreal.Paths.project_dir()).resolve()
assert source_root!=port, 'Run this script in the original C++ course project'
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert not editor.get_game_world(), 'Stop PIE before exporting'
source_file=source_root/'Content'/(config['source_blueprint'].removeprefix('/Game/')+'.uasset')
before=hashlib.sha256(source_file.read_bytes()).hexdigest()
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
lib=unreal.BlueprintEditorLibrary
pins=unreal.BlueprintGraphPinLibrary
# Compile the acquired graph under UE 5.8 without changing the zero-vector input.
function=unreal.load_object(None,'/Script/Engine.KismetMathLibrary:MakeRotFromX')
assets.set_metadata_tag(function,'AutoCreateRefTerm','X')
source=unreal.load_asset(config['source_blueprint'])
assert source and lib.compile_blueprint(source), 'Original Anim Blueprint does not compile'
destination=config['adapted_blueprint']
temporary=source_root/'Content'/(destination.removeprefix('/Game/')+'.uasset')
assert not temporary.exists(), 'Temporary export asset already exists; inspect it before retrying'
def build_copy():
    copy=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(destination.rsplit('/',1)[-1],destination.rsplit('/',1)[0],source)
    assert copy
    bool_type=lib.get_basic_type_by_name('bool')
    for old,new in [('bIsSprinting','DasIsSprinting'),('bIsStunned','DasIsStunned')]:
        assert lib.add_member_variable(copy,new,bool_type),new
        lib.replace_variable_references(copy,old,new)
    lib.reparent_blueprint(copy,unreal.AnimInstance.static_class())
    graph=unreal.BlueprintGraphEditor.create_and_edit_function_graph(copy,'SetGameplayAnimationState')
    sprint=graph.add_graph_input_parameter('Sprinting',bool_type,'false')
    stun=graph.add_graph_input_parameter('Stunned',bool_type,'false')
    first=graph.add_set_member_variable_node('DasIsSprinting')
    second=graph.add_set_member_variable_node('DasIsStunned')
    assert pins.try_create_connection(graph.find_graph_entry_pin(),lib.find_execute_pin(first))
    assert pins.try_create_connection(lib.find_then_pin(first),lib.find_execute_pin(second))
    assert pins.try_create_connection(sprint,lib.find_input_pin(first,'DasIsSprinting'))
    assert pins.try_create_connection(stun,lib.find_input_pin(second,'DasIsStunned'))
    # UE 5.8 needs a value node for an unwired const-reference Vector input.
    # Keep the original zero vector; do not change the direction calculation.
    copy_graphs={g.get_path_name():g for g in lib.list_graphs(copy)}
    for node in list(unreal.ObjectIterator(unreal.load_class(None,'/Script/BlueprintGraph.K2Node_CallFunction'))):
        owner=node.get_outer().get_path_name()
        if owner not in copy_graphs:continue
        if lib.get_node_title(node).replace(' ','').lower()!='makerotfromx':continue
        pin=lib.find_input_pin(node,'X')
        if pins.list_connected_pins(pin):continue
        vector_graph=unreal.BlueprintGraphEditor.get_graph_editor(copy_graphs[owner])
        vector=vector_graph.add_call_function_node('/Script/Engine.KismetMathLibrary.MakeVector')
        assert pins.try_create_connection(lib.find_output_pin(vector,'ReturnValue'),pin)
    assert lib.compile_blueprint(copy), 'Adapted Anim Blueprint failed to compile'
    assert unreal.EditorLoadingAndSavingUtils.save_packages([copy.get_outer()],False)
    target=port/'Content'/(destination.removeprefix('/Game/')+'.uasset')
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(temporary,target)
    result={'source_blueprint':source.get_path_name(),'source_sha256':before,
            'adapted_blueprint':destination,'parent':'/Script/Engine.AnimInstance',
            'state_method':'SetGameplayAnimationState','sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    receipt=port/'Saved/ExternalAssets/course_animation.json'
    receipt.write_text(json.dumps(result,indent=2))
    print('DAS_COURSE_ANIMATION_EXPORTED '+json.dumps(result))

build_copy()
import gc
gc.collect()
unreal.SystemLibrary.collect_garbage()
assert assets.delete_asset(destination), 'Could not remove the temporary source-project duplicate'
assert hashlib.sha256(source_file.read_bytes()).hexdigest()==before, 'Original asset unexpectedly changed'

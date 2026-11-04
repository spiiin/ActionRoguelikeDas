"""Generate our own redistributable hit overlay, driven by CustomPrimitiveData[0]."""
import unreal

path='/Game/DasRogue/Materials/M_HitFlash'
material=unreal.load_asset(path)
if not material:
    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_HitFlash','/Game/DasRogue/Materials',unreal.Material,unreal.MaterialFactoryNew())
assert material
material.modify(True)
material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
material.set_editor_property('two_sided',True)
lib=unreal.MaterialEditingLibrary
usage=unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
lib.set_base_material_usage(material,usage,True)
assert lib.has_material_usage(material,usage)
lib.delete_all_material_expressions(material)
def node(kind,x,y):return lib.create_material_expression(material,kind,x,y)
def connect(source,target,pin=0):
    names=lib.get_material_expression_input_names(target)
    assert names and pin<len(names),(target,names,pin)
    assert lib.connect_material_expressions(source,'',target,names[pin]),(source,target,names[pin])
clock=node(unreal.MaterialExpressionTime,-650,0)
stamp=node(unreal.MaterialExpressionScalarParameter,-650,150)
stamp.set_editor_property('parameter_name','LastHitTime')
stamp.set_editor_property('use_custom_primitive_data',True)
stamp.set_editor_property('primitive_data_index',0)
age=node(unreal.MaterialExpressionSubtract,-420,0)
connect(clock,age,0);connect(stamp,age,1)
scale=node(unreal.MaterialExpressionMultiply,-240,0);scale.set_editor_property('const_b',4.0)
connect(age,scale)
clamp=node(unreal.MaterialExpressionClamp,-50,0)
connect(scale,clamp)
fade=node(unreal.MaterialExpressionOneMinus,120,0)
connect(clamp,fade)
color=node(unreal.MaterialExpressionConstant3Vector,120,160)
color.set_editor_property('constant',unreal.LinearColor(6,3,1,1))
assert lib.connect_material_property(color,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
assert lib.connect_material_property(fade,'',unreal.MaterialProperty.MP_OPACITY)
lib.recompile_material(material)
assert unreal.EditorLoadingAndSavingUtils.save_packages([material.get_outer()],False)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_hit_flash_component.das /Game/DasRogue/Types/BP_RogueHitFlashComponent rogue.RogueHitFlashComponent')
assert unreal.load_class(None,'/Game/DasRogue/Types/BP_RogueHitFlashComponent.BP_RogueHitFlashComponent_C')

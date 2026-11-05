"""Portable UMG layout only. Widget behavior and state live in DAS components."""
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
tools=unreal.AssetToolsHelpers.get_asset_tools()
tree_kind=unreal.load_class(None,'/Script/UMG.WidgetTree')
font_asset=unreal.load_asset('/Engine/EngineFonts/Roboto')

def widget(tree,kind,name):
    existing=unreal.find_object(tree,name)
    if existing and not isinstance(existing,kind):
        existing.remove_from_parent()
        index=1
        while unreal.find_object(tree,f'{name}_Previous{index}'):index+=1
        assert existing.rename(f'{name}_Previous{index}',tree)
        existing=None
    result=existing or unreal.new_object(kind,outer=tree,name=name)
    return result

def blueprint(name):
    path='/Game/DasRogue/UI/'+name
    bp=unreal.load_asset(path)
    if not bp:
        factory=unreal.WidgetBlueprintFactory();factory.set_editor_property('parent_class',unreal.UserWidget)
        bp=tools.create_asset(name,'/Game/DasRogue/UI',unreal.WidgetBlueprint,factory)
    assert bp,path
    tree=next(t for t in unreal.ObjectIterator(tree_kind) if t.get_outer()==bp)
    return bp,tree

def text(tree,name,value,size=18,color=(.95,.96,1,1)):
    result=widget(tree,unreal.TextBlock,name)
    result.set_text(value)
    result.set_font(unreal.SlateFontInfo(font_object=font_asset,size=size))
    result.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(*color)))
    return result

def canvas_child(root,child,x,y,w=0,h=0,anchor=(0,0),alignment=(0,0),auto=False):
    slot=child.slot if child.get_parent()==root else root.add_child_to_canvas(child)
    slot.set_anchors(unreal.Anchors(minimum=unreal.Vector2D(*anchor),maximum=unreal.Vector2D(*anchor)))
    slot.set_alignment(unreal.Vector2D(*alignment))
    slot.set_position(unreal.Vector2D(x,y));slot.set_size(unreal.Vector2D(w,h));slot.set_auto_size(auto)
    return slot

def progress(tree,name,color):
    bar=widget(tree,unreal.ProgressBar,name)
    bar.set_percent(1.0)
    bar.set_fill_color_and_opacity(unreal.LinearColor(*color))
    return bar

def root_for(bp,tree,name='MainCanvasPanel'):
    root=widget(tree,unreal.CanvasPanel,name)
    if not unreal.find_object(tree,'EffectSize'):
        unreal.SystemLibrary.execute_console_command(world,'Das.UI.SetRoot '+bp.get_path_name().split('.')[0]+' '+name)
    root.set_visibility(unreal.SlateVisibility.HIT_TEST_INVISIBLE)
    return root

bp,tree=blueprint('WBP_RogueHUD');root=root_for(bp,tree)
canvas_child(root,text(tree,'HealthText','HP  100 / 100',20),32,-156,anchor=(0,1),auto=True)
canvas_child(root,progress(tree,'HealthBar',(.19,.82,.48,1)),32,-122,332,15,anchor=(0,1))
canvas_child(root,text(tree,'RageText','RAGE  0 / 100',16,(1,.58,.2,1)),32,-96,anchor=(0,1),auto=True)
canvas_child(root,progress(tree,'RageBar',(1,.38,.13,1)),32,-66,332,9,anchor=(0,1))
canvas_child(root,text(tree,'CoinsText','COINS  0',20,(1,.82,.32,1)),-32,32,anchor=(1,0),alignment=(1,0),auto=True)
canvas_child(root,text(tree,'Crosshair','+',25),0,0,anchor=(.5,.5),alignment=(.5,.5),auto=True)
canvas_child(root,text(tree,'ControlsText','LMB  FIRE     E  INTERACT     SHIFT  SPRINT     F / Q  ABILITIES',13,(.7,.76,.83,1)),32,30,auto=True)
canvas_child(root,widget(tree,unreal.VerticalBox,'Effects'),-32,92,260,300,anchor=(1,0),alignment=(1,0),auto=True)
unreal.SystemLibrary.execute_console_command(world,'Das.UI.SetRoot '+bp.get_path_name().split('.')[0]+' '+('EffectSize' if unreal.find_object(tree,'EffectSize') else 'MainCanvasPanel'))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)

bp,tree=blueprint('WBP_RogueHealth');root=root_for(bp,tree)
canvas_child(root,text(tree,'HealthText','100 / 100',13),122,0,alignment=(.5,0),auto=True)
canvas_child(root,progress(tree,'HealthBar',(.95,.25,.17,1)),44,24,156,7)
# A compact left-to-right icon strip above both the HP label and bar.
canvas_child(root,widget(tree,unreal.HorizontalBox,'Effects'),44,-8,156,40,alignment=(0,1),auto=True)
unreal.SystemLibrary.execute_console_command(world,'Das.UI.SetRoot '+bp.get_path_name().split('.')[0]+' '+('EffectSize' if unreal.find_object(tree,'EffectSize') else 'MainCanvasPanel'))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)

for name,compact in [('WBP_RogueHUDEffect',False),('WBP_RogueEffect',True)]:
    bp,tree=blueprint(name);root=root_for(bp,tree)
    icon=widget(tree,unreal.Image,'Icon')
    # Runtime applies optional course icons through soft references. Keep the
    # public widget free of licensed texture dependencies, including on reimport.
    icon.set_brush(unreal.SlateBrush())
    icon.set_color_and_opacity(unreal.LinearColor(1,1,1,1))
    icon.set_visibility(unreal.SlateVisibility.COLLAPSED)
    canvas_child(root,icon,0,0 if compact else 4,34,34)
    canvas_child(root,text(tree,'EffectName','EFFECT',16),46,1,auto=True)
    canvas_child(root,text(tree,'Details','x1  3s',13,(.72,.78,.86,1)),46,25,auto=True)
    if compact:
        for field in ('EffectName','Details'):unreal.find_object(tree,field).set_visibility(unreal.SlateVisibility.COLLAPSED)
    size=widget(tree,unreal.SizeBox,'EffectSize')
    size.set_width_override(40 if compact else 244)
    size.set_height_override(40 if compact else 48)
    if root.get_parent()!=size:size.set_content(root)
    unreal.SystemLibrary.execute_console_command(world,'Das.UI.SetRoot '+bp.get_path_name().split('.')[0]+' EffectSize')
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
packages=[unreal.load_asset('/Game/DasRogue/UI/'+name).get_outer()
          for name in ('WBP_RogueHUD','WBP_RogueHealth','WBP_RogueEffect','WBP_RogueHUDEffect')]
assert unreal.EditorLoadingAndSavingUtils.save_packages(packages,False)
print('DAS_HUD_LAYOUTS PASS')

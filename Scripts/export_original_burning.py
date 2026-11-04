"""Read the pinned course Burning Blueprint; no compile, save or gameplay mutation."""
from pathlib import Path
import json,hashlib,traceback
import unreal

root=Path(globals().get('PORT_ROOT',Path(__file__).resolve().parents[1]))
result=root/'Saved/Tests/original_burning_reference.json'
try:
    path='/Game/ActionRoguelike/Actions/ActionEffect_Burning'
    source_file=Path(unreal.Paths.project_content_dir())/(path.removeprefix('/Game/')+'.uasset')
    bp=unreal.load_asset(path)
    assert bp and bp.generated_class(),path
    obj=unreal.get_default_object(bp.generated_class())
    lib=unreal.BlueprintEditorLibrary
    pins=unreal.BlueprintGraphPinLibrary
    names={'Duration','Period','StackCount','bResetDurationOnStackIncrease','ActionName','GrantTags','BlockedTags','CooldownTime','ActivationCost'}
    names.update(str(n).rsplit('.',1)[-1] for n in lib.list_member_variable_names(bp))
    values={}
    for name in sorted(names):
        try:
            value=obj.get_editor_property(name)
            if isinstance(value,unreal.GameplayTag):values[name]=str(value.get_editor_property('tag_name'))
            elif isinstance(value,unreal.GameplayTagContainer):values[name]=[str(t.get_editor_property('tag_name')) for t in value.get_editor_property('gameplay_tags')]
            elif value is None or isinstance(value,(bool,int,float,str)):values[name]=value
            elif isinstance(value,unreal.Object):values[name]=value.get_path_name()
            else:values[name]=str(value)
        except Exception:pass
    graphs={g.get_path_name() for g in lib.list_graphs(bp)}
    nodes=[]
    for node in unreal.ObjectIterator(unreal.load_class(None,'/Script/BlueprintGraph.K2Node')):
        if node.get_outer().get_path_name() not in graphs:continue
        info={'name':node.get_name(),'type':node.get_class().get_name(),'title':lib.get_node_title(node),'pins':[]}
        for pin in lib.list_all_pins(node):
            info['pins'].append({'name':str(pins.get_pin_name(pin)),'value':pins.get_pin_value(pin),
                'links':[(pins.get_owning_node(other).get_name(),str(pins.get_pin_name(other))) for other in pins.list_connected_pins(pin)]})
        nodes.append(info)
    projectile=unreal.load_class(None,'/Game/ActionRoguelike/Projectiles/BP_MagicProjectile.BP_MagicProjectile_C')
    hit=unreal.get_default_object(projectile).get_editor_property('EffectOnHit')
    payload={'passed':True,'source_blueprint':path,'sha256':hashlib.sha256(source_file.read_bytes()).hexdigest(),
        'defaults':values,'nodes':nodes,'magic_projectile_effect':hit.get_path_name() if hit else None}
except Exception:payload={'passed':False,'error':traceback.format_exc()}
result.parent.mkdir(parents=True,exist_ok=True)
result.write_text(json.dumps(payload,indent=2))
print('DAS_ORIGINAL_BURNING_REFERENCE '+json.dumps({'passed':payload['passed'],'result':str(result)}))

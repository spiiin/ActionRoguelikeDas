"""Read original Sprint graphs/defaults and benchmark original C++ spawning. Never save assets."""
from pathlib import Path
import unreal,json,time,traceback
out=Path(r'C:/src/ActionRoguelikeDas/Saved/Tests/original_sprint_profile.json')
lib=unreal.BlueprintEditorLibrary;pins=unreal.BlueprintGraphPinLibrary
bp=unreal.load_asset('/Game/ActionRoguelike/Actions/Action_Sprint')
cdo=unreal.get_default_object(bp.generated_class())
data={'passed':False,'defaults':{},'nodes':[],'benchmark':[]}
for name in lib.list_member_variable_names(bp):
 try:
  value=cdo.get_editor_property(str(name));data['defaults'][str(name)]=value.get_path_name() if isinstance(value,unreal.Object) else str(value)
 except Exception:pass
graphs={g.get_path_name() for g in lib.list_graphs(bp)}
for node in unreal.ObjectIterator(unreal.load_class(None,'/Script/BlueprintGraph.K2Node')):
 if node.get_outer().get_path_name() not in graphs:continue
 data['nodes'].append({'name':node.get_name(),'title':lib.get_node_title(node),'pins':[{'name':str(pins.get_pin_name(pin)),'value':pins.get_pin_value(pin),'links':[(pins.get_owning_node(other).get_name(),str(pins.get_pin_name(other))) for other in pins.list_connected_pins(pin)]} for pin in lib.list_all_pins(node)]})
data['audit']={}
for folder,names in {
 '':['BP_PlayerCharacter'],
 'AI':['MinionRangedBP'],
 'Actions':['Action_MagicProjectile','Action_Blackhole','Action_Teleport','ActionEffect_Burning','ActionEffect_Stunned'],
 'Projectiles':['BP_MagicProjectile','BP_BlackholeProjectile','BP_TeleportProjectile'],
 'World':['BP_ExplosiveBarrel','BP_ItemChest','BP_HealthPickup','BP_Lever','BP_ProjectileSpammer']}.items():
 for name in names:
  asset=unreal.load_asset('/Game/ActionRoguelike/'+(folder+'/' if folder else '')+name)
  if not asset or not asset.generated_class():continue
  default=unreal.get_default_object(asset.generated_class())
  fields=set(str(n) for n in lib.list_member_variable_names(asset))
  fields.update(['ExplosionEffect','ExplosionSound','BurningEffect','BurningSound','PickupSound','Icon','DetonateDelay','TeleportSecondaryDelay','CastingEffect','CastingSound','AttackMontage','MuzzleSocketName'])
  entry={'defaults':{},'nodes':[]}
  for field in fields:
   try:
    value=default.get_editor_property(field)
    entry['defaults'][field]=value.get_path_name() if isinstance(value,unreal.Object) else str(value)
   except Exception:pass
  graphs={g.get_path_name() for g in lib.list_graphs(asset)}
  for node in unreal.ObjectIterator(unreal.load_class(None,'/Script/BlueprintGraph.K2Node')):
   if node.get_outer().get_path_name() not in graphs:continue
   entry['nodes'].append({'title':lib.get_node_title(node),'pins':[{'name':str(pins.get_pin_name(pin)),'value':pins.get_pin_value(pin)} for pin in lib.list_all_pins(node)]})
  entry['components']={}
  for field in ['LoopedNiagaraComponent','LoopedAudioComponent','MeshComponent','AudioComponent']:
   try:
    component=default.get_editor_property(field)
    if component:
     props={}
     for attr in ['asset','sound','auto_activate']:
      try:
       v=component.get_editor_property(attr);props[attr]=v.get_path_name() if isinstance(v,unreal.Object) else str(v)
      except Exception:pass
     entry['components'][field]=props
   except Exception:pass
  data['audit'][name]=entry
out.write_text(json.dumps(data,indent=2))
data['passed']=True
out.write_text(json.dumps(data,indent=2))
unreal.SystemLibrary.quit_editor()

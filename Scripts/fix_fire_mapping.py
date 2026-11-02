import unreal
from pathlib import Path
mapping=unreal.load_asset("/Game/DasRogue/Input/IMC_Rogue")
fire=unreal.load_asset("/Game/DasRogue/Input/IA_Fire")
interact=unreal.load_asset("/Game/DasRogue/Input/IA_Interact")
if not mapping or not fire or not interact:
    raise RuntimeError("Missing input assets")
mapping.modify(True)
mapping.unmap_all()
for action,name in [(interact,"E"),(fire,"LeftMouseButton")]:
    key=unreal.Key()
    key.set_editor_property("key_name",name)
    mapping.map_key(action,key)
if not unreal.EditorLoadingAndSavingUtils.save_packages([mapping.get_outer()],False):
    raise RuntimeError("Input mapping save failed")
Path(r"C:/src/ActionRoguelikeDas/Saved/fire-mapping-fixed.txt").write_text("Saved E and LeftMouseButton",encoding="utf-8")
unreal.log("DAS_ROGUE_FIRE_MAPPING_SAVED")

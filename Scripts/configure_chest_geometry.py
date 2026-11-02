import unreal


def configure_chest_geometry(actors):
    """Migrate the old centre-pivot cube cover, preserving actor placement."""
    count = 0
    for chest in actors.get_all_level_actors():
        if chest.get_class().get_path_name() != "/Game/DasRogue/BP_InteractiveChestHinged.BP_InteractiveChestHinged_C":
            continue
        chest.modify(True)
        hinge = chest.get_editor_property("LidMeshComponent")
        hinge.modify(True)
        hinge.set_static_mesh(None)
        hinge.set_relative_location(unreal.Vector(-51.25, 0, 50), False, True)
        hinge.set_relative_rotation(unreal.Rotator(0, 0, 0), False, True)
        hinge.set_relative_scale3d(unreal.Vector(1, 1, 1))
        visual = chest.get_editor_property("LidVisual")
        visual.modify(True)
        visual.set_collision_profile_name("NoCollision")
        count += 1
    return count

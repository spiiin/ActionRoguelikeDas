"""Read the pinned original Blueprint defaults without modifying assets."""
import json
from pathlib import Path
import unreal

result = Path('C:/src/ActionRoguelikeDas/Saved/Tests/original_movement_reference.json')
def properties(obj, names):
    values = {}
    for name in names:
        try:
            value = obj.get_editor_property(name)
            if isinstance(value, (bool, int, float, str)): values[name] = value
            elif value is None: values[name] = None
            elif isinstance(value, unreal.Rotator): values[name] = {key:getattr(value,key) for key in ('pitch','yaw','roll')}
            elif isinstance(value, unreal.Vector): values[name] = {key:getattr(value,key) for key in ('x','y','z')}
            elif isinstance(value, unreal.Object): values[name] = value.get_path_name()
            else: values[name] = str(value)
        except Exception as error: values[name] = {'error': str(error)}
    return values

def character(path):
    kind = unreal.load_class(None, path)
    assert kind, path
    actor = unreal.get_default_object(kind)
    movement = actor.get_editor_property('character_movement')
    data = {
        'class': path,
        'actor': properties(actor, ['use_controller_rotation_yaw','use_controller_rotation_pitch','use_controller_rotation_roll']),
        'movement': properties(movement, ['orient_rotation_to_movement','use_controller_desired_rotation','rotation_rate',
            'max_walk_speed','max_walk_speed_crouched','max_acceleration','braking_deceleration_walking',
            'ground_friction','braking_friction_factor','use_separate_braking_friction','braking_friction',
            'jump_z_velocity','air_control','gravity_scale']),
        'mesh': properties(actor.get_editor_property('mesh'), ['relative_location','relative_rotation','relative_scale3d','anim_class']),
    }
    for name in ['SpringArmComponent','CameraComponent','ActionSystemComponent']:
        try:
            component = actor.get_editor_property(name)
            names = (['target_arm_length','use_pawn_control_rotation','relative_location','relative_rotation','socket_offset','target_offset','enable_camera_lag','camera_lag_speed','enable_camera_rotation_lag','camera_rotation_lag_speed','do_collision_test','probe_size']
                if name == 'SpringArmComponent' else ['use_pawn_control_rotation','relative_location','relative_rotation','field_of_view'])
            data[name] = properties(component,names) if name != 'ActionSystemComponent' else {}
            if name == 'ActionSystemComponent':
                attributes = component.get_editor_property('Attributes')
                data['attributes_class'] = attributes.get_class().get_path_name()
                for tag in ['MoveSpeed','MoveSpeedMultiplier']:
                    attr = attributes.get_editor_property(tag)
                    data[name][tag] = properties(attr, ['Base'])
        except Exception as error: data[name] = {'error':str(error)}
    return data

try:
    payload = {'passed': True, 'project': unreal.Paths.project_dir(),
        'blueprint': character('/Game/ActionRoguelike/BP_PlayerCharacter.BP_PlayerCharacter_C'),
        'native': character('/Script/ActionRoguelike.RoguePlayerCharacter')}
except Exception:
    import traceback
    payload = {'passed':False,'error':traceback.format_exc()}
result.parent.mkdir(parents=True, exist_ok=True)
result.write_text(json.dumps(payload, indent=2), encoding='utf-8')
print('DAS_ORIGINAL_MOVEMENT_REFERENCE '+str(payload['passed']))

unreal.SystemLibrary.quit_editor()

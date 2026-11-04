from pathlib import Path
import runpy,traceback
import unreal
try:
    runpy.run_path(str(Path(__file__).with_name('export_course_animation.py')))
    unreal.log('DAS_COURSE_ANIMATION_EXPORT_PASS')
except Exception:
    unreal.log_error('DAS_COURSE_ANIMATION_EXPORT_FAILED '+traceback.format_exc())
finally:
    unreal.SystemLibrary.quit_editor()

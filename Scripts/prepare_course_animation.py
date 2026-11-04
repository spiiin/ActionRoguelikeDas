from pathlib import Path
import runpy
root=Path(__file__).parent
for name in ['prepare_additional_attacks.py','prepare_action_tests.py','prepare_external_assets.py','prepare_presentation_tests.py']:
    runpy.run_path(str(root/name))

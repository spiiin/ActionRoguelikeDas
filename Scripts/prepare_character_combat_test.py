"""Prepare the authored character and native collision test probe."""
import runpy
from pathlib import Path
scripts=Path(__file__).resolve().parent
for name in ('prepare_character.py','prepare_action_tests.py','prepare_combat_test.py'):
    runpy.run_path(str(scripts/name))

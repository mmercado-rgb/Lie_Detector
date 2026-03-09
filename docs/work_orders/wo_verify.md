verify.py currently fails on a clean run because it requires .truth/lock.json and exits before evaluating any conditions.

Fix verify.py so that the integrity lock is OPTIONAL:
- If .truth/lock.json exists → load_integrity_lock() and validate_lock_binding() as before.
- If the file does not exist → skip the lock check and continue verification normally.

Do not change any other behavior.

Goal: a clean baseline run should reach condition evaluation even when .truth/lock.json is absent.
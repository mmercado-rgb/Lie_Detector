Add a clear warning label for the .truth/lock.json mechanism.

Do not change runtime behavior.
Do not add enforcement.
Do not modify tests.

Required changes:
1. In README.md and ARCHITECTURE.md add a short warning section describing .truth/lock.json.
2. The warning must state:
   - .truth/lock.json is OPTIONAL
   - the core architecture works without it
   - it is an advanced integrity-binding mechanism
   - it may restrict or pin runtime files and commands
   - it should only be used by users who understand the implications
3. Add a code comment above the lock-loading logic in src/integrity.py stating the same warning.
The warning should read approximately:
WARNING: Optional integrity lock mechanism  
The `.truth/lock.json` feature can bind verifier/runtime behavior to specific file hashes and command resolutions.  
This mechanism is **not required** for the core truth-bound verification architecture.  
It is provided as an advanced integrity control and may restrict or pin runtime components.  
Use only if you understand the implications.
Return:
1. Files changed
2. Exact warning text added
3. Runtime behavior changed? yes/no
4. Result
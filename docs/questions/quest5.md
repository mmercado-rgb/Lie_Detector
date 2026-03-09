For the current architecture, focus only on items that materially strengthen the real control surface.
Ignore cosmetic policy fields unless they change runtime behavior.
Evaluate these two items only:
1. runtime enforcement of inputs.allowed_paths
2. tests for .truth/lock.json integrity binding
For each, return:
1. Why it is load-bearing or not
2. What concrete failure it prevents
3. Smallest truthful implementation or test
4. Whether it should be done now, later, or removed
Use only runtime code and tests.
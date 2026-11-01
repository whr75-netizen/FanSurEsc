from pathlib import Path

HERE = Path(__file__).resolve().parent
source = (HERE/'FocusGPU90.cs').read_text(encoding='utf-8')
assert source.count('static Obj58 State()')==1
old = (HERE/'RUN_ReadAlpha90.cs.txt').read_text(encoding='utf-8')
# Preserve the previously reviewed JSON/create-only support definitions.
helper_start = old.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor')
command_start = old.index('internal class CommandScript')
helper_prefix = old[:command_start]
# The support definitions precede this command; retain them verbatim, append
# this command's state-related using directives to the leading using group.
helper_prefix = helper_prefix.replace('using UnityEngine;', 'using UnityEngine;\nusing UnityEngine.Rendering;\nusing UnityEngine.Profiling;\nusing Unity.Collections;')
command = source[source.index('internal class CommandScript'):]
# The generated bundle wraps both helpers and command in one namespace.
if old.rstrip().endswith('}'):
    (HERE/'RUN_FocusGPU90.cs.txt').write_text(helper_prefix+command+'\n}\n', encoding='utf-8')
print('Prepared one-frame GPU replay with before/after read-only state journal.')

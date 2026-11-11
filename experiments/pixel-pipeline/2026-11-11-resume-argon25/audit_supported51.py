"""Offline audit of completed public reads and the installed official lifecycle API.

Never loads Unity, invokes the relay, accesses private runtime fields, or frees objects.
"""
from pathlib import Path
import collections
import datetime
import hashlib
import json

H = Path(__file__).resolve().parent
G = H / 'face51'
PACKAGE = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Library\PackageCache\com.unity.ai.assistant@c0127625258e')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_receipt(relative, start, end):
    path = PACKAGE / relative
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    return {'path': relative, 'SHA256': sha(path), 'firstLine': start,
            'lastLine': min(end, len(lines)), 'excerpt': lines[start - 1:end]}


def value(lines, key):
    return next(line.split('=', 1)[1] for line in lines if line.startswith(key + '='))


def main():
    details = G / 'details/PUBLIC_RESOURCE_DETAILS51.txt'
    lines = details.read_text(encoding='utf-8').splitlines()
    prefixes = ('31 owned source field_', '31 owned depth_', '33 immutable same-frame existing stage_')
    rows = []
    for line in lines:
        if not line.startswith('RT='):
            continue
        identity, name, metadata = line[3:].split('/', 2)
        if name.startswith(prefixes):
            assert '/created=True/' in '/' + metadata + '/'
            assert '/persistent=False/' in '/' + metadata + '/'
            rows.append({'entityId': identity, 'name': name, 'metadata': metadata})
    assert int(value(lines, 'allRTs')) == 75
    assert len(rows) == int(value(lines, 'matchingDiagnosticRTs')) == 45
    assert len({r['entityId'] for r in rows}) == 45
    assert value(lines, 'matchingOwnedDiagnosticMaterials') == '282'
    assert value(lines, 'publicUpdateIRunCommandTargets') == '1'
    assert all(value(lines, k) == 'False' for k in ['playing', 'transition', 'compiling', 'updating'])

    # The first exact-name filter missed RTHandle descriptor suffixes. Preserve that
    # receipt as a failed filter; do not count it as an earlier zero-resource state.
    first = (G / 'public/PUBLIC_RESOURCES51.txt').read_text(encoding='utf-8').splitlines()
    assert value(first, 'matchingDiagnosticRTs') == '0'
    assert value(first, 'allRTs') == '75'

    tools = json.loads((G / 'inventory/TOOLS.json').read_text())
    assert len(tools) == 7
    names = [t['name'] for t in tools]
    assert 'Unity_RunCommand' in names
    assert not any(s in n.lower() for n in names for s in ['cancel', 'dispose', 'release', 'resource'])

    native = H / 'face49/capture'
    manifest = json.loads((native / 'NATIVE_BEFORE73.json').read_text())
    assert len(manifest) == 47
    for row in manifest:
        path = native / row['snapshot']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
    dirty = [row for row in manifest if row['dirtyBefore']]
    assert len(dirty) == 31
    restored = json.loads((native / 'STATE-004-Edit-restoration-checked.json').read_text())
    assert restored['Edit'] and restored['restorationChecksPass']
    assert restored['inputSameReferenceAndJSON'] and restored['devicesPreserved']
    checks = restored['nativeChecks']
    assert len(checks) == 47 and sum(r.get('equal') is True for r in checks) == 46
    # PlayerSettings and its unloaded AssetImporter share a path, not an object/type.
    dirty_keys = {(x['path'], x['type']) for x in dirty}
    assert all(r.get('equal') is True for r in checks if (r['path'], r['type']) in dirty_keys)
    assert len([r for r in checks if (r['path'], r['type']) in dirty_keys]) == 31
    assert not (native / 'COMPLETE.json').exists() and not (native / 'FAILED.json').exists()
    rejected = H / 'face49/recovery/owned-completion/REPLY.json'
    assert 'System.Reflection' in rejected.read_text()
    assert not (H / 'face49/recovery/STARTED.txt').exists()

    excerpts = [
        source_receipt('Editor/Assistant/RunCommand/AgentExtensionAssembly/IRunCommand.cs', 1, 8),
        source_receipt('Editor/Assistant/RunCommand/AgentExtensionAssembly/ExecutionResult.cs', 100, 150),
        source_receipt('Editor/Assistant/RunCommand/AgentRunCommand.cs', 45, 76),
        source_receipt('Editor/Assistant/RunCommand/RunCommandUtils.cs', 70, 87),
    ]
    interface = '\n'.join(excerpts[0]['excerpt'])
    assert 'void Execute(ExecutionResult result)' in interface
    assert 'Dispose' not in interface and 'Cancel' not in interface
    execution = '\n'.join(excerpts[1]['excerpt'])
    assert 'Undo.RegisterCreatedObjectUndo' in execution and 'Undo.CollapseUndoOperations' in execution
    assert 'AssetDatabase.DeleteAsset' in execution  # Not a generic safe-resource drain.
    assert 'AsyncGPUReadback' not in execution and 'GraphicsFence' not in execution
    package = json.loads((PACKAGE / 'package.json').read_text())
    before, after = restored['beforeMemory'], restored['afterMemory']
    report = {
        'generatedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseCommit': 'b2cd7b1da7b8a4df596418a80e1431ba9b1227ae',
        'publicReadUTC': value(lines, 'utc'), 'publicReadSHA256': sha(details),
        'observedRTs': 75, 'matchingDiagnosticRTs': rows,
        'matchingDiagnosticMaterialCount': 282,
        'publicIRunCommandUpdateTargetCount': 1,
        'publicTypeIdentityOnly': True, 'privateRuntimeInspection': False,
        'computeExactNameMatchesZeroDoesNotProveNoReferences': True,
        'GPUCompletionKnown': False, 'GPUBusyClaimed': False,
        'ownedResourcesReleased': False, 'observerRemoved': False,
        'newGPUOperationsThisAudit': 0, 'newPlayOrImport': 0,
        'reflectionRecoveryRejectedBeforeExecute': True, 'reflectionRecoveryRetried': False,
        'installedPackage': {k: package[k] for k in ['name', 'version']},
        'officialTools': names, 'officialSourceReceipts': excerpts,
        'supportedPublicInspectionSucceeded': True,
        'installedPublicOwnerCompletionAndDrainEndpointFound': False,
        'undoRegistrationIsNotAsyncLifetimeManagement': True,
        'releaseByNameOrRemoveDelegateWithoutOriginalTicketNotAttempted': True,
        'userImmediateActionRequired': False,
        'GPUResumeBlockedUntilOwnedDrainProven': True,
        'normalCloseReopenIsAnUnexecutedFallbackNotProvenMandatory': True,
        'normalCloseRequiresFreshPreservationReviewAndExplicitDecision': True,
        'backup47FilesExactHash': True,
        'dirty31Categories': dict(collections.Counter(x['type'] for x in dirty)),
        'dirty31Paths': [{'path': x['path'], 'type': x['type'], 'SHA256': x['sha256']} for x in dirty],
        'lastRestorationUTC': restored['utc'], 'restorationChecksPass': True,
        'nativeChecks': {'exact': 46, 'total': 47, 'unavailable': [x for x in checks if x.get('equal') is not True]},
        'backupDoesNotGuaranteeUndoNonserializedInputFlagsOrNativeHandles': True,
        'allocatedMemoryAPI': 'UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong',
        'beforeMemory': before, 'afterMemory': after,
        'allocatedMiBChange': (after['allocated'] - before['allocated']) / 1048576,
        'allDeltaIsLeakClaimed': False,
        'future50PatchOnly': True, 'product77Changed': False,
    }
    (G / 'SUPPORTED_LIFECYCLE51.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')
    print(json.dumps({'RTsStillCreated': len(rows), 'materialsNamedDiagnostic': 282,
                      'officialTools': len(names), 'backupsValid': 47,
                      'safeDrainEndpointFound': False, 'GPUCalls': 0,
                      'userImmediateActionRequired': False}))


if __name__ == '__main__':
    main()

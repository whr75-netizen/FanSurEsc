"""Archive selected reproducible raw cases plus all capture metadata/previews.

Generated artifacts only. Never deletes or replaces the original capture tree.
The SHA256 inventory covers every original raw resource, including unarchived
samples. Large intermediate analysis JSON is compressed inside the evidence ZIP.
"""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
RAW_CASES = {
    'sweep_00/004', 'sweep_00/005', 'sweep_17/017', 'sweep_17/018',
    'walk_skin_02/002', 'walk_skin_02/003',
    'walk_skin_10/011', 'walk_skin_10/012', 'walk_skin_10/013', 'walk_skin_10/017',
    'walk_skin_18/018', 'walk_skin_18/019',
}

def main():
    output = ROOT / 'gpu_evidence.zip'
    inventory_path = ROOT / 'capture_inventory.json'
    if output.exists() or inventory_path.exists():
        raise FileExistsError('Preserving existing evidence archive/inventory')
    files, inventory = [], []
    for folder in sorted(p.parent for p in ROOT.rglob('capture.json')):
        for file in sorted(folder.iterdir()):
            if not file.is_file():
                continue
            rel = file.relative_to(ROOT).as_posix()
            data = file.read_bytes()
            selected = (file.suffix != '.bin' or folder.relative_to(ROOT).as_posix() in RAW_CASES
                        or folder.relative_to(ROOT).parts[0].startswith('pair_'))
            inventory.append(dict(path=rel, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), archived=selected))
            if selected:
                files.append(file)
    for folder in ROOT.iterdir():
        if folder.is_dir() and (folder.name.startswith('report_') or folder.name.startswith('gpu_skin_checks_')):
            files.extend(p for p in folder.rglob('*') if p.is_file())
    files.extend(ROOT.glob('*/comparison_manifest.json'))
    files.extend(ROOT.glob('*/restoration_attempt.json'))
    files.extend(ROOT.glob('end_state*.json'))
    inventory_path.write_text(json.dumps(dict(files=inventory), indent=2), encoding='utf-8')
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(set(files)):
            archive.write(file, file.relative_to(ROOT).as_posix())
        archive.write(inventory_path, inventory_path.name)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
    print(json.dumps(dict(archive=str(output), archive_bytes=output.stat().st_size,
                          original_files=len(inventory), archived_files=len(set(files))+1)))

if __name__ == '__main__':
    main()

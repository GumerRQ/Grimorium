"""User-authored tower rooms and validation, without a pygame dependency."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4
from game.utils.paths import data_path


def rooms_folder():
    if getattr(sys, 'frozen', False):
        return Path(os.environ.get('APPDATA', Path.home())) / 'Grimorium' / 'rooms'
    return data_path('levels', 'custom')


def validate(layout, kind):
    if (not isinstance(layout, list) or len(layout) != 11 or
            any(not isinstance(row, str) or len(row) != 13 for row in layout)):
        return ['size']
    errors = []
    if kind not in ('normal', 'boss'):
        errors.append('type')
    if layout[0] != ' ' * 13 or layout[1] != '         Dd  ' or layout[10] != '         Aa  ':
        errors.append('doors')
    interior = ''.join(layout[2:10])
    if any(tile not in '. PEOBV' for tile in interior):
        errors.append('tiles')
    if interior.count('P') != 1:
        errors.append('player')
    if (kind == 'boss' and interior.count('B') != 1) or (kind == 'normal' and 'B' in interior):
        errors.append('boss')
    if kind == 'boss' and 'E' in interior:
        errors.append('boss_enemies')
    walkable = {(r, c) for r in range(2, 10) for c in range(13) if layout[r][c] in '.PEB'}
    accesses = {(2, 9), (2, 10), (9, 9), (9, 10)}
    if not accesses <= walkable:
        errors.append('access')
    if walkable:
        pending = [next(iter(walkable))]
        reached = set(pending)
        while pending:
            r, c = pending.pop()
            for point in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if point in walkable and point not in reached:
                    reached.add(point)
                    pending.append(point)
        if reached != walkable:
            errors.append('disconnected')
    return errors


def documents():
    result = []
    for path in sorted(rooms_folder().glob('*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('version') != 1:
                continue
            if any(error in ('size', 'type', 'doors', 'tiles')
                   for error in validate(data.get('layout'), data.get('type'))):
                continue
            result.append((path, data))
        except (OSError, ValueError, TypeError):
            continue
    return result


def active_rooms(kind):
    return [data['layout'] for _, data in documents()
            if data.get('enabled') is True and data.get('type') == kind
            and not validate(data.get('layout'), kind)]


def delete_room(path):
    path = Path(path)
    if path.resolve().parent != rooms_folder().resolve() or path.suffix.lower() != '.json':
        raise ValueError('Only custom room JSON files can be deleted')
    path.unlink(missing_ok=True)


def save_room(name, kind, layout, enabled, path=None):
    folder = rooms_folder()
    folder.mkdir(parents=True, exist_ok=True)
    if path is None:
        path = folder / ('room-' + uuid4().hex[:12] + '.json')
    path = Path(path)
    if path.resolve().parent != folder.resolve():
        raise ValueError('Room must be saved in the custom room folder')
    data = {'version': 1, 'name': name.strip()[:40] or 'Room', 'type': kind,
            'enabled': bool(enabled) and not validate(layout, kind), 'layout': layout}
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)
    return path, data

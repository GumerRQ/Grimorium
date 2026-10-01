"""Radius-aware navigation shared by walking and flying enemies."""
import heapq
import math


def _intersects_box(a, b, left, top, right, bottom):
    low, high = 0.0, 1.0
    for origin, delta, minimum, maximum in (
        (a[0], b[0] - a[0], left, right),
        (a[1], b[1] - a[1], top, bottom),
    ):
        if abs(delta) < 1e-12:
            if origin < minimum or origin > maximum:
                return False
        else:
            t1, t2 = (minimum - origin) / delta, (maximum - origin) / delta
            low, high = max(low, min(t1, t2)), min(high, max(t1, t2))
            if low > high:
                return False
    return True


def clear_segment(a, b, radius, blockers):
    """Sweep a circle against rectangles without moving the actual entity."""
    # Tangential contact is allowed, just as in Entity's collision checks.
    radius = max(0, radius - 1e-6)
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    for rect in blockers:
        if (max(a[0], b[0]) + radius < rect.left or
                min(a[0], b[0]) - radius > rect.right or
                max(a[1], b[1]) + radius < rect.top or
                min(a[1], b[1]) - radius > rect.bottom):
            continue
        if (_intersects_box(a, b, rect.left - radius, rect.top, rect.right + radius, rect.bottom) or
                _intersects_box(a, b, rect.left, rect.top - radius, rect.right, rect.bottom + radius)):
            return False
        for x, y in ((rect.left, rect.top), (rect.right, rect.top),
                     (rect.left, rect.bottom), (rect.right, rect.bottom)):
            t = min(1, max(0, ((x - a[0]) * dx + (y - a[1]) * dy) / length2)) if length2 else 0
            if (a[0] + t * dx - x) ** 2 + (a[1] + t * dy - y) ** 2 < radius * radius:
                return False
    return True


def clear_box_segment(a, b, half_size, blockers):
    """Sweep the same axis-aligned footprint used by enemy movement."""
    hx, hy = half_size
    epsilon = 1e-6
    for rect in blockers:
        if _intersects_box(a, b, rect.left - hx + epsilon, rect.top - hy + epsilon,
                           rect.right + hx - epsilon, rect.bottom + hy - epsilon):
            return False
    return True


class EnemyNavigator:
    REPATH_INTERVAL = 0.3

    def __init__(self):
        self.path = []
        self.timer = 0.0
        self.key = None
        self.remaining_distance = math.inf

    def _plan(self, start, target, room, half_size, blockers):
        start_cell = room.world_to_cell(*start)
        goal = room.world_to_cell(*target)
        goal_point = target if clear_box_segment(target, target, half_size, blockers) else room.cell_to_world(*goal)
        frontier = []
        costs, previous, positions, valid = {}, {}, {}, {}
        closed = set()
        sr, sc = start_cell
        # Connect the real position to cell centers, including its own center.
        # Near a corner, reaching that center first can be essential.
        for cell in (start_cell, (sr-1, sc), (sr+1, sc), (sr, sc-1), (sr, sc+1)):
            row, col = cell
            if not (0 <= row < len(room.layout) and 0 <= col < len(room.layout[row])):
                continue
            point = goal_point if cell == goal else room.cell_to_world(*cell)
            if clear_box_segment(start, point, half_size, blockers):
                positions[cell] = point
                costs[cell], previous[cell] = math.dist(start, point), None
                heapq.heappush(frontier, (costs[cell] + math.dist(point, target), cell))
        closest = None
        closest_distance = math.inf
        while frontier:
            _, cell = heapq.heappop(frontier)
            if cell in closed:
                continue
            closed.add(cell)
            distance = math.dist(positions[cell], target)
            if distance < closest_distance:
                closest, closest_distance = cell, distance
            if cell == goal:
                closest = cell
                break
            row, col = cell
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                nr, nc = neighbor
                # Actual blockers define traversability: flying enemies receive
                # walls only, ground enemies also receive objects and voids.
                if not (0 <= nr < len(room.layout) and 0 <= nc < len(room.layout[nr])):
                    continue
                if neighbor in closed:
                    continue
                point = positions.setdefault(neighbor, goal_point if neighbor == goal else room.cell_to_world(*neighbor))
                if neighbor not in valid:
                    valid[neighbor] = clear_box_segment(point, point, half_size, blockers)
                if not valid[neighbor] or not clear_box_segment(positions[cell], point, half_size, blockers):
                    continue
                cost = costs[cell] + math.dist(positions[cell], point)
                if cost >= costs.get(neighbor, math.inf):
                    continue
                costs[neighbor], previous[neighbor] = cost, cell
                heapq.heappush(frontier, (cost + math.dist(point, target), neighbor))
        # The player's center may be inaccessible to a wider enemy. Approach
        # the nearest reachable point instead of rejecting the entire route.
        points = []
        while closest is not None:
            points.append(positions[closest])
            closest = previous[closest]
        return list(reversed(points))

    def movement(self, enemy, target, dt, room, blockers):
        self.remaining_distance = 0.0
        start = (enemy.x, enemy.y)
        self.timer -= max(0, dt)
        if clear_box_segment(start, target, enemy.movement_half_size, blockers):
            self.path = []
            self.key = None
            waypoint = target
        elif room is None:
            return 0.0, 0.0
        else:
            key = (id(room), room.world_to_cell(*target), enemy.movement_half_size,
                   tuple((r.x, r.y, r.width, r.height) for r in blockers))
            if key != self.key or (self.timer <= 0 and not self.path):
                self.path = self._plan(start, target, room, enemy.movement_half_size, blockers)
                self.key, self.timer = key, self.REPATH_INTERVAL
            # Never discard a corner on proximity alone. Only skip it if the
            # whole body can already reach a later waypoint without collision.
            waypoint = None
            for index in range(len(self.path) - 1, -1, -1):
                candidate = self.path[index]
                if math.dist(start, candidate) < 1e-6:
                    continue
                if clear_box_segment(start, candidate, enemy.movement_half_size, blockers):
                    self.path = self.path[index:]
                    waypoint = candidate
                    break
            if waypoint is None:
                self.path = []
                return 0.0, 0.0
        dx, dy = waypoint[0] - start[0], waypoint[1] - start[1]
        length = math.hypot(dx, dy)
        self.remaining_distance = length
        distance = min(length, max(0, enemy.get_movement_speed() * dt))
        return (dx / length * distance, dy / length * distance) if length else (0.0, 0.0)

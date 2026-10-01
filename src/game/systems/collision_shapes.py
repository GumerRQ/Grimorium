"""Float rectangle helpers shared by movement and damage collision."""


def overlap_area(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def movement_bounds(entity):
    if hasattr(entity, 'get_movement_bounds'):
        return entity.get_movement_bounds()
    return (entity.x - entity.radius, entity.y - entity.radius,
            entity.x + entity.radius, entity.y + entity.radius)


def damage_bounds(entity):
    if hasattr(entity, 'get_hitbox_bounds'):
        return entity.get_hitbox_bounds()
    return movement_bounds(entity)


def circle_overlaps_entity(x, y, radius, entity):
    if hasattr(entity, "get_hitbox_bounds"):
        left, top, right, bottom = entity.get_hitbox_bounds()
        dx = x - max(left, min(x, right))
        dy = y - max(top, min(y, bottom))
        return dx * dx + dy * dy <= radius * radius
    return (x - entity.x) ** 2 + (y - entity.y) ** 2 <= (radius + entity.radius) ** 2

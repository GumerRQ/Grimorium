from game.systems.enemy_content import load_visual

from game.entities.enemies.shooter_enemy import ShooterEnemy



class DragonEnemy(ShooterEnemy):
    def __init__(self, position, level=1, definition=None):
        super().__init__(position, level, with_visual=False)
        self.is_flying = True

        self.visual = load_visual(definition or 'dragon')

from game.systems.enemy_content import load_visual

from game.entities.enemies.shooter_enemy import ShooterEnemy



class GoblinEnemy(ShooterEnemy):
    def __init__(self, position, level=1, definition=None):
        super().__init__(position, level, with_visual=False)

        self.visual = load_visual(definition or 'goblin')

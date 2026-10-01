from game.systems.enemy_content import load_visual

from game.entities.enemies.chaser_enemy import ChaserEnemy



class RatEnemy(ChaserEnemy):
    def __init__(self, position, level=1, definition=None):
        super().__init__(position, level)

        self.path_align_margin = 20
        self.path_arrival_distance = 2

        self.visual = load_visual(definition or 'rat')

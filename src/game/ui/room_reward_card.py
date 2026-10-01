"""Room payout summary; calculations and payment stay in CombatScreen."""
import pygame
from game.ui.fonts import create_font


class RoomRewardCard:
    START_DELAY = .22
    SLIDE_SECONDS = .38
    READY_AFTER = START_DELAY + SLIDE_SECONDS

    def __init__(self, reward, localization):
        self.localization = localization
        self.reward = reward
        self.title_font = create_font(14)
        self.font = create_font(10)
        self.small = create_font(7)
        self.button = pygame.Rect(240, 277, 160, 23)

    def draw(self, surface, elapsed):
        amount = min(1.0, max(0.0, (elapsed - self.START_DELAY) / self.SLIDE_SECONDS))
        if amount <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((7, 11, 17, round(145 * amount)))
        surface.blit(overlay, (0, 0))
        card = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(card, (27, 34, 43), (162, 51, 316, 260), border_radius=6)
        pygame.draw.rect(card, (171, 155, 108), (162, 51, 316, 260), 1, border_radius=6)
        def centered(text, y, font, color=(232, 234, 223)):
            image = font.render(text, True, color)
            card.blit(image, image.get_rect(center=(320, y)))
        centered(self.localization.text("ui.reward.title"), 73, self.title_font, (243, 217, 143))
        centered(self.localization.text("ui.reward.subtitle"), 96, self.small)
        r = self.reward
        rows = [(self.localization.text("ui.reward.health"), r["health"], self.localization.text("ui.reward.health_detail").format(**r)),
                (self.localization.text("ui.reward.time"), r["time"], self.localization.text("ui.reward.time_detail").format(**r)),
                (self.localization.text("ui.reward.savings"), r["savings"], self.localization.text("ui.reward.savings_detail"))]
        for index, (label, value, detail) in enumerate(rows):
            y = 120 + index * 33
            card.blit(self.font.render(label, True, (226, 232, 227)), (182, y))
            number = self.font.render(f"+{value}", True, (241, 211, 132))
            card.blit(number, number.get_rect(topright=(458, y)))
            card.blit(self.small.render(detail, True, (153, 170, 177)), (182, y + 13))
        pygame.draw.line(card, (87, 97, 98), (182, 232), (458, 232))
        centered(f"TOTAL  +{r['bonus']}", 246, self.title_font, (243, 217, 143))
        pygame.draw.rect(card, (54, 70, 65), self.button, border_radius=3)
        centered(self.localization.text("ui.reward.continue"), self.button.centery, self.font)
        offset_y = round((surface.get_height() - 51) * (1 - amount) ** 3)
        surface.blit(card, (0, offset_y))

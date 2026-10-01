"""Input devices select an action; only this layer invokes its callback."""
import pygame


def activate_button(screen, index):
    if screen.game.screen_manager.current_screen is not screen:
        return
    if 0 <= index < len(screen.buttons):
        screen.selected = index
        screen.buttons[index].callback()


def is_confirmation(event, mouse_rect=None, mouse_pos=None, keys=None):
    keys = keys or (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
    if event.type == pygame.KEYDOWN:
        return event.key in keys and not getattr(event, 'repeat', False)
    return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and
            mouse_rect is not None and mouse_rect.collidepoint(mouse_pos))

#!/usr/bin/env python3
"""Headless smoke test: runs the game loop without a display and scripts
some input to verify game logic (bombing, scoring, crashing, game over)."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

import sopwith


def fake_key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def run():
    pygame.init()
    screen = pygame.display.set_mode((sopwith.SCREEN_W, sopwith.SCREEN_H))
    clock = pygame.time.Clock()
    game = sopwith.Sopwith(novice=False, sound=False)
    game.world_seed = 42
    game.reset_game()
    assert game.state == "play"
    assert len(game.enemies) == sopwith.ENEMY_COUNT
    assert len(game.bridges) == 3

    no_keys = pygame.key.get_pressed()

    # Fly level for a while; plane should stay airborne.
    for _ in range(60):
        game.update_play(no_keys, [])
    assert game.player.alive
    assert game.player.y < sopwith.GROUND_Y

    # Drop a bomb straight down onto the first bridge area by teleporting
    # above a target: verify bomb-target collision and scoring.
    target = game.bridges[0]
    game.player.x = target.x
    game.player.y = target.y - 80
    game.player.vx = 0.0
    game.player.vy = 0.0
    game.player.bombs = 5
    game.update_play(no_keys, [fake_key_event(pygame.K_SPACE)])
    assert len(game.bombs) == 1
    score_before = game.player.score
    for _ in range(120):
        game.update_play(no_keys, [])
        if not game.bombs:
            break
    assert game.player.score > score_before, "bombing a bridge must score"

    # Crash the plane into the ground away from base: lose a life.
    lives_before = game.player.lives
    game.player.x = 2000
    game.player.y = sopwith.GROUND_Y - 2
    game.player.vy = 3.0
    game.player.invulnerable = 0
    game.update_play(no_keys, [])
    assert game.player.lives == lives_before - 1
    assert game.player.alive

    # Burn all lives -> game over.
    game.player.lives = 1
    game.player.x = 2000
    game.player.y = sopwith.GROUND_Y - 2
    game.player.vy = 3.0
    game.player.invulnerable = 0
    game.update_play(no_keys, [])
    assert game.state == "gameover"

    # Render every state once to catch drawing errors.
    sky = sopwith.make_sky()
    font = pygame.font.SysFont("monospace", 16)
    big = pygame.font.SysFont("monospace", 40, bold=True)
    for state in ("title", "play", "gameover"):
        game.state = state
        if state == "play":
            game.reset_game()
        screen.blit(sky, (0, 0))
        if state == "title":
            game.draw_title(screen, font, big)
        else:
            game.draw_world(screen)
            game.draw_hud(screen, font)
            if state == "gameover":
                game.draw_gameover(screen, font, big)
        pygame.display.flip()
        clock.tick(sopwith.FPS)

    pygame.quit()
    print("headless smoke test OK")


if __name__ == "__main__":
    run()

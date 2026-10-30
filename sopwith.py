#!/usr/bin/env python3
"""Sopwith - a cross-platform reimplementation of the 1984 BMB Compuscience
classic, rebuilt from the decompiled 16-bit DOS binary (sw.exe, v7.F15).

Fly your Sopwith Camel over the enemy lines, bomb bridges, tanks, hangars
and fuel depots, then land back at your own base to refuel and rearm.
"""

import argparse
import math
import random
import sys

import pygame

SCREEN_W, SCREEN_H = 640, 400
WORLD_W = 4000
FPS = 30

GROUND_Y = SCREEN_H - 60

GRAVITY = 0.22
THRUST = 0.30
MAX_SPEED = 4.2
CLIMB_RATE = 0.16

PLAYER_LIVES = 3
START_FUEL = 2000
START_BOMBS = 8

ENEMY_COUNT = 12
SCORE_HIT = 100
SCORE_BOMB = 250

PALETTE = {
    "sky_top": (24, 40, 96),
    "sky_bottom": (96, 140, 200),
    "ground": (70, 52, 36),
    "grass": (60, 110, 60),
    "plane": (200, 60, 40),
    "plane_dark": (120, 30, 20),
    "prop": (240, 240, 240),
    "bomb": (30, 30, 30),
    "enemy": (60, 60, 160),
    "house": (150, 110, 70),
    "house_roof": (120, 40, 40),
    "bridge": (110, 90, 70),
    "fuel_tank": (170, 170, 180),
    "explosion": (255, 180, 40),
    "text": (240, 240, 240),
}


def make_sky():
    sky = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    top = PALETTE["sky_top"]
    bottom = PALETTE["sky_bottom"]
    for y in range(SCREEN_H):
        t = y / SCREEN_H
        sky.fill(tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
                 rect=(0, y, SCREEN_W, 1))
    return sky


class GameObject:
    def __init__(self, x, y, w=12, h=8):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.w = w
        self.h = h
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2),
                           self.w, self.h)

    def update(self):
        self.x += self.vx
        self.y += self.vy


class Enemy(GameObject):
    KINDS = ("tank", "hangar", "depot")

    def __init__(self, x, kind):
        w, h = {"tank": (26, 14), "hangar": (60, 34), "depot": (22, 34)}[kind]
        super().__init__(x, GROUND_Y - h / 2, w, h)
        self.kind = kind
        self.hp = {"tank": 1, "hangar": 3, "depot": 2}[kind]

    def draw(self, surf):
        r = self.rect
        if self.kind == "tank":
            pygame.draw.rect(surf, PALETTE["enemy"], r)
            pygame.draw.rect(surf, (30, 30, 80),
                             (r.x + 6, r.y - 6, 14, 6))
        elif self.kind == "hangar":
            pygame.draw.rect(surf, PALETTE["house"], r)
            pygame.draw.polygon(surf, PALETTE["house_roof"],
                                [(r.x, r.y), (r.centerx, r.y - 12), (r.right, r.y)])
        else:
            pygame.draw.rect(surf, PALETTE["fuel_tank"], r, border_radius=4)
            pygame.draw.rect(surf, (90, 90, 100),
                             (r.x + 3, r.y - 5, r.w - 6, 5))


class Bridge(GameObject):
    def __init__(self, x):
        super().__init__(x, GROUND_Y - 6, 90, 12)
        self.hp = 4

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, PALETTE["bridge"], r)
        for i in range(1, 5):
            x = r.x + r.w * i // 5
            pygame.draw.line(surf, (60, 48, 36), (x, r.y), (x, r.bottom), 2)


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 22, 10)
        self.vy = 0.0
        self.facing = 1
        self.fuel = START_FUEL
        self.bombs = START_BOMBS
        self.lives = PLAYER_LIVES
        self.score = 0
        self.invulnerable = FPS * 2
        self.prop = 0

    def update(self, keys):
        self.prop = (self.prop + 1) % 4
        if self.fuel > 0:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vy -= CLIMB_RATE
                self.fuel -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.vy += CLIMB_RATE * 0.8
                self.fuel -= 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx -= THRUST
                self.fuel -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx += THRUST
                self.fuel -= 1
        else:
            self.vx *= 0.99
        self.vy += GRAVITY
        self.vx *= 0.985
        self.vx = max(-MAX_SPEED, min(MAX_SPEED, self.vx))
        self.vy = max(-MAX_SPEED, min(MAX_SPEED, self.vy))
        self.x += self.vx
        self.y += self.vy
        if self.x < 20:
            self.x = 20
            self.vx = abs(self.vx) * 0.5
        if self.x > WORLD_W - 20:
            self.x = WORLD_W - 20
            self.vx = -abs(self.vx) * 0.5
        if self.invulnerable > 0:
            self.invulnerable -= 1

    def draw(self, surf, cam_x):
        x, y = int(self.x - cam_x), int(self.y)
        body = PALETTE["plane"] if self.invulnerable % 8 < 4 else (255, 220, 120)
        pygame.draw.polygon(surf, body, [
            (x - 10, y + 2), (x - 4, y - 4), (x + 6, y - 4), (x + 10, y + 2),
            (x + 6, y + 5), (x - 6, y + 5),
        ])
        wing = (x - 2, y - 9) if self.vy < -0.5 else ((x - 2, y + 9) if self.vy > 0.5 else (x - 2, y))
        pygame.draw.rect(surf, PALETTE["plane_dark"],
                         (wing[0] - 4, wing[1] - 2, 10, 4))
        prop_x = x + (11 if self.facing > 0 else -11)
        off = [0, 3, 0, -3][self.prop]
        pygame.draw.line(surf, PALETTE["prop"],
                         (prop_x, y + off - 4), (prop_x, y + off + 4), 2)


class Bomb(GameObject):
    def __init__(self, x, y, vx):
        super().__init__(x, y, 5, 8)
        self.vx = vx

    def update(self):
        self.vy += GRAVITY * 0.9
        super().update()

    def draw(self, surf, cam_x):
        pygame.draw.ellipse(surf, PALETTE["bomb"],
                            (int(self.x - cam_x) - 3, int(self.y) - 5, 6, 10))


class Explosion:
    def __init__(self, x, y, big=False):
        self.x = x
        self.y = y
        self.age = 0
        self.life = 24 if big else 14
        self.big = big

    def update(self):
        self.age += 1

    @property
    def alive(self):
        return self.age < self.life

    def draw(self, surf, cam_x):
        r = int((self.age / self.life) * (26 if self.big else 14))
        c = PALETTE["explosion"] if self.age % 4 < 2 else (255, 240, 160)
        pygame.draw.circle(surf, c, (int(self.x - cam_x), int(self.y)), max(r, 2))


class Sopwith:
    def __init__(self, novice=False, sound=True):
        self.novice = novice
        self.sound = sound
        self.state = "title"
        self.player = None
        self.enemies = []
        self.bridges = []
        self.bombs = []
        self.explosions = []
        self.cam_x = 0.0
        self.world_seed = random.randint(0, 10**6)
        self.message = ""
        self.message_timer = 0
        self.ticks = 0

    def reset_game(self):
        rng = random.Random(self.world_seed)
        self.player = Player(150, 120)
        self.enemies = []
        for i in range(ENEMY_COUNT):
            x = 900 + i * ((WORLD_W - 1200) // ENEMY_COUNT) + rng.randint(-60, 60)
            kind = Enemy.KINDS[i % len(Enemy.KINDS)] if not self.novice else "tank"
            self.enemies.append(Enemy(x, kind))
        self.bridges = [Bridge(700 + i * 1100) for i in range(3)]
        self.bombs = []
        self.explosions = []
        self.cam_x = 0.0
        self.message = "Destroy the enemy targets!"
        self.message_timer = FPS * 3
        self.state = "play"

    def say(self, msg, secs=3):
        self.message = msg
        self.message_timer = FPS * secs

    def drop_bomb(self):
        p = self.player
        if p.bombs > 0 and p.alive:
            p.bombs -= 1
            self.bombs.append(Bomb(p.x, p.y + 6, p.vx))
            self.say(f"Bombs left: {p.bombs}", 1)

    def player_crashed(self):
        p = self.player
        self.explosions.append(Explosion(p.x, p.y, big=True))
        p.lives -= 1
        p.fuel = START_FUEL
        p.bombs = START_BOMBS
        if p.lives > 0:
            p.x, p.y, p.vx, p.vy = 150, 120, 0.0, 0.0
            p.invulnerable = FPS * 3
            self.say(f"Plane down! Lives left: {p.lives}", 3)
        else:
            self.say("THE END", 1000)
            self.state = "gameover"

    def update_play(self, keys, events):
        p = self.player
        if not p.alive:
            return
        p.update(keys)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    self.drop_bomb()
                elif e.key == pygame.K_ESCAPE:
                    self.state = "title"
        if p.y + p.h / 2 >= GROUND_Y:
            landed_base = p.x < 260 and abs(p.vy) < 2.5 and abs(p.vx) < 2.5
            if landed_base:
                p.fuel = START_FUEL
                p.bombs = START_BOMBS
                self.say("Refueled and rearmed at base.", 2)
            else:
                self.player_crashed()
                return
            p.y = GROUND_Y - p.h / 2
            p.vy = 0.0
            p.vx *= 0.5
        if p.fuel <= 0 and p.y + p.h / 2 < GROUND_Y - 1:
            pass
        for b in self.bombs:
            b.update()
            if b.y >= GROUND_Y - 2:
                b.alive = False
                self.explosions.append(Explosion(b.x, GROUND_Y - 4))
            for t in self.enemies + self.bridges:
                if t.alive and b.rect.colliderect(t.rect):
                    b.alive = False
                    t.hp -= 1
                    self.explosions.append(Explosion(b.x, b.y, big=(t.hp <= 0)))
                    if t.hp <= 0:
                        t.alive = False
                        p.score += SCORE_BOMB
                        self.explosions.append(Explosion(t.x, t.y - 10, big=True))
                    else:
                        p.score += SCORE_HIT
                    break
        self.bombs = [b for b in self.bombs if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        for e in self.explosions:
            e.update()
        self.explosions = [e for e in self.explosions if e.alive]
        if p.alive:
            pr = p.rect
            for t in self.enemies + self.bridges:
                if t.alive and pr.colliderect(t.rect) and p.invulnerable == 0:
                    self.player_crashed()
                    return
        if self.message_timer > 0:
            self.message_timer -= 1
        self.cam_x = max(0, min(WORLD_W - SCREEN_W, p.x - SCREEN_W * 0.4))
        self.ticks += 1
        if not self.enemies and not self.bridges:
            self.say("All targets destroyed! Press ENTER for next mission.", 1000)
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                    self.world_seed = random.randint(0, 10**6)
                    self.reset_game()

    def draw_world(self, surf):
        pygame.draw.rect(surf, PALETTE["ground"], (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
        pygame.draw.rect(surf, PALETTE["grass"], (0, GROUND_Y, SCREEN_W, 4))
        base_x = 150 - self.cam_x
        pygame.draw.rect(surf, PALETTE["house"], (base_x - 40, GROUND_Y - 20, 80, 20))
        pygame.draw.polygon(surf, PALETTE["house_roof"],
                            [(base_x - 46, GROUND_Y - 20), (base_x, GROUND_Y - 34),
                             (base_x + 46, GROUND_Y - 20)])
        for t in self.bridges:
            if t.alive and -100 < t.x - self.cam_x < SCREEN_W + 100:
                t.draw(surf) if False else self._draw_at(surf, t)
        for e in self.enemies:
            if -100 < e.x - self.cam_x < SCREEN_W + 100:
                self._draw_at(surf, e)
        for b in self.bombs:
            b.draw(surf, self.cam_x)
        for x in self.explosions:
            x.draw(surf, self.cam_x)
        if self.player.alive:
            self.player.draw(surf, self.cam_x)

    def _draw_at(self, surf, obj):
        old = obj.x
        obj.x -= self.cam_x
        obj.draw(surf)
        obj.x = old

    def draw_hud(self, surf, font):
        p = self.player
        lines = [
            f"SCORE {p.score:06d}",
            f"FUEL  {'#' * max(0, p.fuel // 100)} {p.fuel}",
            f"BOMBS {p.bombs}",
            f"LIVES {p.lives}",
        ]
        y = 8
        for line in lines:
            surf.blit(font.render(line, True, PALETTE["text"]), (8, y))
            y += 18
        if self.message_timer > 0:
            msg = font.render(self.message, True, (255, 255, 160))
            surf.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2, 40))

    def draw_title(self, surf, font, big_font):
        title = big_font.render("S O P W I T H", True, PALETTE["text"])
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 100))
        sub = font.render("(The Network Edition) - cross-platform reimplementation",
                           True, PALETTE["text"])
        surf.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 140))
        lines = [
            "S - single player      N - novice single player",
            "Arrows/WASD - fly      SPACE - drop bomb",
            "Land at your base (left) to refuel and rearm",
            "Destroy bridges, tanks, hangars and fuel depots",
            "ESC - quit",
        ]
        y = 200
        for line in lines:
            s = font.render(line, True, PALETTE["text"])
            surf.blit(s, (SCREEN_W // 2 - s.get_width() // 2, y))
            y += 26

    def draw_gameover(self, surf, font, big_font):
        t = big_font.render("THE END", True, PALETTE["text"])
        surf.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 140))
        s = font.render(f"Final score: {self.player.score}", True, PALETTE["text"])
        surf.blit(s, (SCREEN_W // 2 - s.get_width() // 2, 200))
        s = font.render("Press ENTER to return to title", True, PALETTE["text"])
        surf.blit(s, (SCREEN_W // 2 - s.get_width() // 2, 230))


def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="sopwith",
        description="Sopwith - cross-platform reimplementation of the 1984 DOS classic.")
    ap.add_argument("-n", action="store_true", help="novice single player")
    ap.add_argument("-s", action="store_true", help="single player")
    ap.add_argument("-c", action="store_true", help="single player against computer")
    ap.add_argument("-q", action="store_true", help="begin game with sound off")
    ap.add_argument("--seed", type=int, default=None, help="world seed (default random)")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    pygame.init()
    pygame.display.set_caption("Sopwith")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    big_font = pygame.font.SysFont("monospace", 40, bold=True)
    sky = make_sky()
    game = Sopwith(novice=args.n, sound=not args.q)
    if args.seed is not None:
        game.world_seed = args.seed

    running = True
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()

        if game.state == "title":
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_s, pygame.K_n, pygame.K_c):
                        game.novice = e.key == pygame.K_n
                        game.reset_game()
                    elif e.key == pygame.K_ESCAPE:
                        running = False
        elif game.state == "play":
            game.update_play(keys, events)
        elif game.state == "gameover":
            for e in events:
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    game.state = "title"

        screen.blit(sky, (0, 0))
        if game.state == "title":
            game.draw_title(screen, font, big_font)
        else:
            game.draw_world(screen)
            game.draw_hud(screen, font)
            if game.state == "gameover":
                game.draw_gameover(screen, font, big_font)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())

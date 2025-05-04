import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from star import Star
from explosion import Explosion

class AlienInvasion:
    """overall class to manage game assets and behavior"""

    def __init__(self):
        """initialize the game and create game resources"""
        pygame.init()

        self.settings = Settings()
        # self.screen = pygame.display.set_mode(
        #     (self.settings.screen_width, self.settings.screen_height)
        # )

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption("Alien Invasion")

        # create an instance to store game statistics and create a scoreboard.
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()

        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # Make the Play button.
        self.play_button = Button(self, "Play")

        pygame.mixer.init()
        self._load_sounds()

        self.autofire_active = False
        self.last_shot_time = 0

        self.stars = pygame.sprite.Group()
        self._create_star_background()

        self.explosions = pygame.sprite.Group()

        self.game_paused = False

    def _create_star_background(self):
        """create a star background"""
        for _ in range(100):
            star = Star(self)
            self.stars.add(star)

    def _update_stars(self):
        """update the positions of stars"""
        self.stars.update()

        # remove stars that go off the screen
        for star in self.stars.copy():
            if star.rect.top > self.settings.screen_height:
                self.stars.remove(star)

        # add new stars to the group
        while len(self.stars) < 100:
            star = Star(self)
            self.stars.add(star)

    def _load_sounds(self):
        """load sounds for the game"""
        self.shoot_sound = pygame.mixer.Sound('sounds/laser1.wav')
        self.explosion_sound = pygame.mixer.Sound('sounds/explosion.wav')
        self.ship_hit_sound = pygame.mixer.Sound('sounds/big_explosion.ogg')
        self.background_music = pygame.mixer.Sound('sounds/spacetheme.ogg')

        # set the volume for the sounds
        self.shoot_sound.set_volume(0.3)
        self.explosion_sound.set_volume(0.3)
        self.ship_hit_sound.set_volume(0.5)
        self.background_music.set_volume(0.3)

        # play the background music
        self.background_music.play(-1)

    def run_game(self):
        """start the main loop for the game"""
        while True:

            self._check_events()
            self._update_stars()
            if self.stats.game_active and not self.game_paused:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
                self._auto_fire_bullets()
                self._update_explosions()

            self._update_screen()

    def _update_bullets(self):
        """update position of bullets and delete old bullets."""
        # update bullet positions
        self.bullets.update()

        # get rid of bullets that reahc top of the screen.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        # print(len(self.bullets))

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """check for any bullets that have hit aliens."""
        # check for any bullets that have hit aliens.
        # if so, get rid of the bullet and the alien.
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True
            # self.bullets, self.aliens, False, True
        )

        if collisions:
            self.explosion_sound.play()
            for aliens in collisions.values():
                for alien in aliens:
                    explosion = Explosion(alien.rect.center)
                    self.explosions.add(explosion)
                self.stats.score += self.settings.alien_points
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            # if the entire fleet is destroyed, start a new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # increase level.
            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        """update the positions for all aliens in the fleet."""
        self._check_fleet_edges()
        self.aliens.update()

        # look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            # print("Ship hit!!!")
            self._ship_hit()

        # check if any aliens have reached the bottom of the screen.
        self._check_aliens_bottom()

    def _ship_hit(self):
        """respond to ship being hit by alien."""
        # Create big explosion at ship position
        explosion = Explosion(self.ship.rect.center, explosion_type='ship')
        self.explosions.add(explosion)
        # create a sound of explosion
        self.ship_hit_sound.play()
        if self.stats.ships_left > 0:
            # decrement ships_left, and update scoreboard.
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # pause.
            sleep(1.0)
        else:
            self.stats.game_active = False
            # show the mouse cursor once the game ends.
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # treat this the same as if the ship got hit.
                self._ship_hit()
                break

    def _check_events(self):
        """respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_high_score()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)


    def _check_play_button(self, mouse_pos):
        """start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # reset the game settings.
            self.settings.initialize_dynamic_settings()

            # reset the game statistics.
            self.stats.reset_stats()


            # apply speed increases for previous levels
            for _ in range(self.stats.level):
                self.settings.increase_speed()

            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # hide the mouse cursor.
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Responds to key presses."""
        if event.key == pygame.K_p:
            if self.stats.game_active:
                self.game_paused = not self.game_paused
        elif event.key == pygame.K_RIGHT:
            # move the ship to the right.
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            self._save_high_score()
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self.autofire_active = not self.autofire_active
            if self.autofire_active:
                self._fire_bullet()
        # start the game when the player presses Enter.
        elif event.key == pygame.K_RETURN:
            if not self.stats.game_active:
                mouse_pos = self.play_button.rect.center # get the center of the button
                self._check_play_button(mouse_pos)       # simulate a mouse click

    def _save_high_score(self):
        """save the high score to a file."""
        with open('high_score.txt', 'w') as f:
            f.write(str(self.stats.high_score))
        # print("High score saved.")

    def _check_keyup_events(self, event):
        """Responds to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_SPACE:
            self.autofire_active = False

    def _auto_fire_bullets(self):
        """fire bullets automatically if autofire is active."""
        current_time = pygame.time.get_ticks()
        if self.autofire_active and (current_time - self.last_shot_time) > self.settings.autofire_cooldown:
            self._fire_bullet()

    def _fire_bullet(self):
        """create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            self.last_shot_time = pygame.time.get_ticks()
            self.shoot_sound.play()

    def _create_fleet(self):
        """create a fleet of aliens."""
        # make an alien and find the number of aliens in a row.
        # spacing between each alien is equal to one alien width.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (4 * alien_width)
        number_aliens_x = int(available_space_x // (2 * alien_width))

        # determine the number of aliens that fit on the screen
        ship_height = self.ship.rect.height
        available_space_y = self.settings.screen_height - (8 * alien_height) - ship_height
        number_rows = int(available_space_y // (3 * alien_height))

        # create full fleet of aliens
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                # create an alien and place it in the row
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.y = alien.rect.height * 2 + 2 * alien.rect.height* row_number
        alien.rect.y = alien.y
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """drop the entiere fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_explosions(self):
        """Update explosion animations"""
        self.explosions.update()

    def _update_screen(self):
        """update images on the screen, and flip to the new screen"""
        # redraw the screen during each passs through the loop.
        self.screen.fill(self.settings.bg_color)
        # draw the stars first
        self.stars.draw(self.screen)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # draw the score information.
        self.sb.show_score()

        # draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # draw explosions
        for explosion in self.explosions:
            explosion.draw(self.screen)

        # self.explosions.update()
        # self.explosions.draw(self.screen)

        # Draw pause text if the game is paused
        if self.game_paused:
            pause_font = pygame.font.SysFont(None, 48)
            pause_text = pause_font.render("Game Paused", True, (255, 255, 255))
            pause_rect = pause_text.get_rect(center=(self.settings.screen_width // 2, self.settings.screen_height // 2))
            self.screen.blit(pause_text, pause_rect)

        # make the most recently drawn screen visible.
        pygame.display.flip()


if __name__ == "__main__":
    ai = AlienInvasion()
    ai.run_game()

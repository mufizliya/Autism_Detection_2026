import pygame
import time

pygame.mixer.pre_init(44100, -16, 2, 512)

pygame.init()

pygame.mixer.init()

sound = pygame.mixer.Sound("src/pop.wav")

print("Playing...")

sound.play()

time.sleep(3)
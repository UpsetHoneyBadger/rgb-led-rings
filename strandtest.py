import time
import random
import numpy as np
import colorsys
from neopixel import *
import argparse
import RPi.GPIO as GPIO


# LED strip configuration:
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


ANIMATION_FRAMES = 60
WAIT_MS = 25

RING_LED_COUNT = 31
NUM_RINGS = 6
LED_COUNT = RING_LED_COUNT * NUM_RINGS      # Number of LED pixels.

BUTTON_PIN_1 = 22
BUTTON_PIN_2 = 23
BUTTON_PIN_3 = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_PIN_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_PIN_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

animation_select=0
animation_has_changed = True
def handle_button_click(channel):
    global animation_select, animation_has_changed
    if channel == 23:
        animation_select += 1
        animation_has_changed = True
    if channel == 22:
        animation_select -= 1
        animation_has_changed = True
    if channel == 24:
        animation_select = 5
        animation_has_changed = True
    animation_select %= 6
    print("button pressed", channel)

GPIO.add_event_detect(BUTTON_PIN_1, GPIO.RISING, callback=handle_button_click, bouncetime=2000)
GPIO.add_event_detect(BUTTON_PIN_2, GPIO.RISING, callback=handle_button_click, bouncetime=2000)
GPIO.add_event_detect(BUTTON_PIN_3, GPIO.RISING, callback=handle_button_click, bouncetime=2000)



# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            # time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        # time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        # time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            # time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

prev_h = 0
def get_random_hsv_color():
    global prev_h
    rand_inc = random.random() * 0.4 + 0.2
    h = prev_h + rand_inc
    prev_h = h
    return np.array(colorsys.hsv_to_rgb(h % 1,1,1)) * 255

def init_rings_animation_0():
    global frame_counter, counter, inc, random_hsv_color
    frame_counter = 0
    counter = 0
    inc = 1
    random_hsv_color = get_random_hsv_color()

def frame_rings_animation_0():
    global frame_counter, counter, inc, random_hsv_color

    rings = [np.tile([0,0,0], (RING_LED_COUNT,1)).transpose() for i in range(NUM_RINGS)]
    if frame_counter < ANIMATION_FRAMES / 2:
        fade_amount = frame_counter / (ANIMATION_FRAMES / 2.0)
    else:
        fade_amount = (ANIMATION_FRAMES - frame_counter) / (ANIMATION_FRAMES / 2.0)
    fade_amount = np.clip(fade_amount, 0.02, 1)
    faded_color = fade_amount * random_hsv_color
    rings[counter] = np.tile(faded_color, (RING_LED_COUNT,1)).transpose()
    pixels = np.concatenate(rings, axis=1).astype(int)
    for i in range(0, pixels.shape[1]):
        strip.setPixelColor(i, Color(pixels[0, i], pixels[1, i], pixels[2, i]))
    strip.show()
    time.sleep(10/1000.0)
    frame_counter += 1
    if frame_counter >= ANIMATION_FRAMES:
        random_hsv_color = get_random_hsv_color()
        counter = random.randint(0,NUM_RINGS-1)
        frame_counter = 0

def init_rings_animation_1():
    global random_hsv_color, anim2_pos, width
    width = 15
    anim2_pos = 0
    random_hsv_color = get_random_hsv_color()

def frame_rings_animation_1():
    global  random_hsv_color, anim2_pos, width
    fade = np.tile(np.linspace(0.01,1,width), (3,1))
    start = np.multiply(
        np.tile(random_hsv_color, (width,1)).transpose(),
        fade
    )
    end = np.tile([0,0,0], (strip.numPixels() - width,1)).transpose()
    pixels = np.concatenate([start, end], axis=1)
    pixels = np.roll(pixels, anim2_pos, axis=1)
    pixels = pixels.astype(int)
    for i in range(0, strip.numPixels()):
        strip.setPixelColor(i, Color(pixels[0, i], pixels[1, i], pixels[2, i]))
    strip.show()
    time.sleep(WAIT_MS/1000.0)
    anim2_pos += 1
    if (anim2_pos+width) % LED_COUNT == 0:
        random_hsv_color = get_random_hsv_color()
        # anim2_pos %= LED_COUNT

def init_rings_animation_2():
    global random_hsv_colors, anim3_pos, anim3_inc, width
    random_hsv_colors = [get_random_hsv_color() for i in range(NUM_RINGS)]
    anim3_pos = [random.randint(0,RING_LED_COUNT) for i in range(NUM_RINGS)]
    anim3_inc = [-1 if random.randint(0,1) else 1  for i in range(NUM_RINGS)]
    width = 3

def frame_rings_animation_2():
    global  random_hsv_colors, anim3_pos, anim3_inc, width
    starts = [
        np.tile(random_hsv_colors[i], (width,1)).transpose()
        for i in range(NUM_RINGS)
    ]
    ends = [
        np.tile([0,0,0], (RING_LED_COUNT - width,1)).transpose()
        for i in range(NUM_RINGS)
    ]
    rings = [
        np.concatenate([starts[i], ends[i]], axis=1)
        for i in range(NUM_RINGS)
    ]

    for i in range(NUM_RINGS):
        rings[i] = np.roll(rings[i], anim3_pos[i], axis=1)

    pixels = np.concatenate(rings, axis=1)
    pixels = pixels.astype(int)
    for i in range(0, pixels.shape[1]):
        strip.setPixelColor(i, Color(pixels[0, i], pixels[1, i], pixels[2, i]))
    strip.show()
    for i in range(NUM_RINGS):
        anim3_pos[i] += anim3_inc[i]

def init_rings_animation_3():
    global colorWipe_pos, colorWipe_color
    colorWipe_color = get_random_hsv_color()
    colorWipe_color = Color(
        colorWipe_color[0].astype(int),
        colorWipe_color[1].astype(int),
        colorWipe_color[2].astype(int)
    )
    colorWipe_pos = 0

def frame_rings_animation_3(wait_ms=25):
    global colorWipe_pos, colorWipe_color
    """Wipe color across display a pixel at a time."""
    strip.setPixelColor(colorWipe_pos, colorWipe_color)
    strip.show()
    time.sleep(WAIT_MS/1000.0)
    colorWipe_pos += 1
    if colorWipe_pos == strip.numPixels():
        init_rings_animation_3()

def init_rings_animation_4():
    global frame_counter, random_hsv_color, even_uneven
    ANIMATION_FRAMES = 240
    frame_counter = 0
    even_uneven = False
    random_hsv_color = get_random_hsv_color()

def frame_rings_animation_4():
    global frame_counter, random_hsv_color, even_uneven

    rings = [np.tile([0,0,0], (RING_LED_COUNT,1)).transpose() for i in range(NUM_RINGS)]
    if frame_counter < ANIMATION_FRAMES / 2:
        fade_amount = frame_counter / (ANIMATION_FRAMES / 2.0)
    else:
        fade_amount = (ANIMATION_FRAMES - frame_counter) / (ANIMATION_FRAMES / 2.0)
    fade_amount = np.clip(fade_amount, 0.02, 1)
    faded_color = fade_amount * random_hsv_color

    if even_uneven:
        for r in range(0,NUM_RINGS, 2):
            rings[r] = np.tile(faded_color, (RING_LED_COUNT,1)).transpose()
    else:
        for r in range(1,NUM_RINGS, 2):
            rings[r] = np.tile(faded_color, (RING_LED_COUNT,1)).transpose()
    pixels = np.concatenate(rings, axis=1).astype(int)
    for i in range(0, pixels.shape[1]):
        strip.setPixelColor(i, Color(pixels[0, i], pixels[1, i], pixels[2, i]))
    strip.show()

    frame_counter += 1
    if frame_counter >= ANIMATION_FRAMES:
        random_hsv_color = get_random_hsv_color()
        frame_counter=0
        even_uneven = not even_uneven



# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    parser.add_argument('-a', '--animation', action='store', type=int, default=1, help='select animation 0-5' )
    args = parser.parse_args()
    animation_select = args.animation if args.animation >= 0 and args.animation <=5 else 1 
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print ('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')
    else:
        colorWipe(strip, Color(0,0,0), 10)
        exit()
    try:
        while True:
            if animation_has_changed:
                if animation_select == 0:
                    init_rings_animation_0()
                elif animation_select == 1:
                    init_rings_animation_1()
                elif animation_select == 2:
                    init_rings_animation_2()
                elif animation_select == 3:
                    init_rings_animation_3()
                elif animation_select == 4:
                    init_rings_animation_4()
                elif animation_select == 5:
                    colorWipe(strip, Color(0,0,0), 10)
                animation_has_changed = False
            if animation_has_changed:
                pass
            if animation_select == 0:
                frame_rings_animation_0()
            elif animation_select == 1:
                frame_rings_animation_1()
            elif animation_select == 2:
                frame_rings_animation_2()
            elif animation_select == 3:
                frame_rings_animation_3()
            elif animation_select == 4:
                frame_rings_animation_4()
            elif animation_select == 5:
                pass
            # print ('Color wipe animations.')
            # colorWipe(strip, Color(255, 0, 0))  # Red wipe
            # colorWipe(strip, Color(0, 255, 0))  # Blue wipe
            # colorWipe(strip, Color(0, 0, 255))  # Green wipe
            # print ('Theater chase animations.')
            # theaterChase(strip, Color(127, 127, 127))  # White theater chase
            # theaterChase(strip, Color(127,   0,   0))  # Red theater chase
            # theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
            # print ('Rainbow animations.')
            # rainbow(strip)
            # rainbowCycle(strip)
            # theaterChaseRainbow(strip)

    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0,0,0), 10)
    finally:
        GPIO.cleanup()

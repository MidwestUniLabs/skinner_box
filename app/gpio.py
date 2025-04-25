import time
import os
import threading

#TODO Overhaul this file. It's a mess.

# Detect if running on Raspberry Pi
try:
    from gpiozero import LED, Button, OutputDevice
    from rpi_ws281x import Adafruit_NeoPixel, Color
    IS_PI = True
except (ImportError, RuntimeError):
    print("Error importing GPIO libraries. Mocking GPIO for testing.")
    IS_PI = False

# LED strip configuration
LED_COUNT = 6      # Number of LED pixels.
LED_PIN = 12        # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800kHz)
LED_DMA = 10        # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)

# Mock GPIO for non-Raspberry Pi environments
class MockDevice:
    def __init__(self):
        self.status = False

    def on(self):
        print("Mock device on")
        self.status = True

    def off(self):
        print("Mock device off")
        self.status = False

    def is_active(self):
        return self.status  # Simulates real GPIO behavior

    def close(self):
        print("Mock device closed")


class MockNeoPixel:
    def is_active(self):
        # Simulate LED strip status
        import random
        return random.choice([True, False])
    
    def numPixels(self):
        return LED_COUNT

    def setPixelColor(self, i, color):
        pass

    def show(self):
        print("Mock LED strip updated")
    

#region I/O
# Input Ports
input_ports = {
    "lever_port": 14,
    "nose_poke_port": 17,
    "start_trial_port": 23,
    "water_primer_port": 22,
    "manual_stimulus_port": 24,
    "manual_interaction_port": 25,
    "manual_reward_port": 26
}

# Output Ports
output_ports = {
    "feeder_port": 3,
    "water_port": 18,
    "speaker_port": 13
}

gpio_states = {
    "lever": False,
    "nose_poke": False,
    "speaker": False,
    "led": False,
    "feeder": False,
    "water": False,
}

# Button Setup
if IS_PI:
    try:
        lever = Button(input_ports.lever_port, bounce_time=0.1)
        poke = Button(input_ports.nose_poke_port, pull_up=False, bounce_time=0.1)
        water_primer = Button(input_ports.water_primer_port, bounce_time=0.1)
        manual_stimulus_button = Button(input_ports.manual_stimulus_port, bounce_time=0.1)
        manual_interaction = Button(input_ports.manual_interaction_port, bounce_time=0.1)
        manual_reward = Button(input_ports.manual_reward_port, bounce_time=0.1)
        start_trial_button = Button(input_ports.start_trial_port, bounce_time=0.1)
        feeder_motor = OutputDevice(output_ports.feeder_port, active_high=False, initial_value=False)
        water_motor = OutputDevice(output_ports.water_port, active_high=False, initial_value=False)
        buzzer = OutputDevice(output_ports.speaker_port, active_high=False, initial_value=False)
        strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
        strip.begin()
    except Exception as e:
        print(f"Error setting up buttons: {e}")
else:
    # Mock GPIO for non-Raspberry Pi environments
    lever = MockDevice()
    poke = MockDevice()
    water_primer = MockDevice()
    manual_stimulus_button = MockDevice()
    manual_interaction = MockDevice()
    manual_reward = MockDevice()
    start_trial_button = MockDevice()
    feeder_motor = MockDevice()
    water_motor = MockDevice()
    buzzer = MockDevice()
    strip = MockNeoPixel()
#endregion

def safe_gpio_call(device, method, *args, **kwargs):
    """ Safely call a GPIO function to prevent crashes. """
    try:
        getattr(device, method)(*args, **kwargs)
    except Exception as e:
        print(f"GPIO Error in {method}: {e}")

#region Action Functions
# Rewards
def feed():
    def _feed():
        feeder_motor.on()
        gpio_states["feeder"] = True
        time.sleep(1)  # TODO Adjust Feed Time
        feeder_motor.off()
        gpio_states["feeder"] = False

    threading.Thread(target=_feed).start()

def water():
    try:
        water_motor.on()
        gpio_states["water"] = True
        time.sleep(0.15)  # TODO Adjust Water Time
        water_motor.off()
        gpio_states["water"] = False
        water_motor.close()
    finally:
        return

def start_motor():
    try:
        print("Motor starting")
        water_motor.on()
        gpio_states["water"] = True
        if water_primer is not None:
            water_primer.when_released = lambda: stop_motor(water_motor)
    except Exception as e:
        print(f"An error occurred while starting the motor: {e}")
    finally:
        return

def stop_motor(motor):
    try:
        print("Motor stopping")
        motor.off()
        gpio_states["water"] = False
        motor.close()
    except Exception as e:
        print(f"An error occurred while stopping the motor: {e}")
    finally:
        return

# Stims
def flashLightStim(color, wait_ms=10):
    """ Flash the light stimulus safely and correctly. """
    try:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:], 16)
        if IS_PI:
            color = Color(r, g, b)
        else:
            color = (r, g, b)

        gpio_states["led"] = True

        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)

        # Fully turn off LEDs after delay
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        
        gpio_states["led"] = False

    except Exception as e:
        print(f"Error in flashLightStim: {e}")


def play_sound(duration=1):
    """ Play a sound for the given duration. """
    try:
        print("Playing sound")
        gpio_states["speaker"] = True
        buzzer.on()
        time.sleep(duration)
        buzzer.off()
        gpio_states["speaker"] = False
    except Exception as e:
        print(f"Error playing sound: {e}")


# Interactions
def lever_press(state_machine=None):
    try:
        if state_machine:
            state_machine.lever_press()
        else:
            safe_gpio_call(lever, 'on')
            gpio_states["lever"] = True
            print("Lever pressed")
            safe_gpio_call(lever, 'off')
            gpio_states["lever"] = False
    except Exception as e:
        print(f"Error in lever press: {e}")
    feed()

def nose_poke(state_machine=None):
    try:
        print("Nose poke detected")
        if state_machine:
            state_machine.nose_poke()
        else:
            safe_gpio_call(poke, 'on')
            gpio_states["nose_poke"] = True
            safe_gpio_call(poke, 'off')
            gpio_states["nose_poke"] = False
    except Exception as e:
        print(f"Error in nose poke: {e}")
    water()

#endregion

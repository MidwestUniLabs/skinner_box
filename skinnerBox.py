#!/usr/bin/env python3

from signal import pause
import pygame
from flask import Flask, Response, render_template, request, jsonify, url_for, redirect
from gpiozero import LED, Button, OutputDevice
import RPi.GPIO as GPIO
import json
import time
import threading
from picamera2 import Picamera2, Preview
from rpi_ws281x import Adafruit_NeoPixel, Color
import io 

app = Flask(__name__)
settings_path = 'config.json'
# LED strip configuration:
LED_COUNT      = 60      # Number of LED pixels.
LED_PIN        = 12      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
# Intialize the library (must be called once before other functions).
try:
	strip.begin()
except:
	pass
#region I/O

#Input Ports
lever_port = 17
nose_poke_port = 15
start_trial_port = None
water_primer_port = None
manual_stimulus_port = None
manual_interaction_port = None
manual_reward_port = None

#Output Ports
feeder_port = 3
water_port = 18
speaker_port = 13

#Button Settup
lever = Button(lever_port, bounce_time=0.1)
poke = Button(nose_poke_port, pull_up=False, bounce_time=0.1)
#endregion

class TrialStateMachine:
    def __init__(self):
        self.state = 'Idle'
        self.lock = threading.Lock()
        self.currentIteration = 0
        self.settings = {}
        self.startTime = None
        self.interactable = True
        self.lastInteractTime = 0.0
        self.stimulusGiven = False
    def load_settings(self):
        # Implementation of loading settings from file
        try:
            with open('config.json', 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            self.settings = {}
            
    def start_trial(self):
        with self.lock:
            if self.state == 'Idle':
                self.load_settings()
                goal = int(self.settings.get('goal', 0))
                duration = int(self.settings.get('duration', 0)) * 60
                self.timeRemaining = duration
                self.currentIteration = 0
                self.state = 'Running'
                threading.Thread(target=self.run_trial, args=(goal, duration)).start()
                return True
            return False

    def pause_trial(self):
        with self.lock:
            if self.state == 'Running':
                self.state = 'Paused'
                self.pause_trial_logic()
                return True
            return False

    def resume_trial(self):
        with self.lock:
            if self.state == 'Paused':
                self.state = 'Running'
                self.resume_trial_logic()
                return True
            return False

    def stop_trial(self):
        with self.lock:
            if self.state in ['Preparing', 'Running', 'Paused']:
                self.state = 'Idle'
                return True
            return False

    def run_trial(self, goal, duration):
        self.startTime = time.time()
        lever.when_pressed = self.lever_press
        poke.when_pressed = self.nose_poke
        while self.state == 'Running':
            self.timeRemaining = (duration - (time.time() - self.startTime)).__round__(2)
            if self.currentIteration >= goal:
                self.finish_trial()
                break
            if(self.timeRemaining <= 0):
                self.finish_trial()
                break    
            time.sleep(.10)
            
    ## Interactions ##
    def lever_press(self):
        if self.state == 'Running':
            if self.interactable == True:
                self.currentIteration += 1
                feed()
        self.lastInteractTime = time.time
        self.stimulusGiven = False

    def nose_poke(self):
        print("Nose poke")
        if self.state == 'Running':
             if self.interactable == True:
                self.currentIteration += 1
                water()
        self.lastInteractTime = time.time
        self.stimulusGiven = False
        
    ## Stimulus' ##
    def light_stimulus(self):
        if(self.stimulusGiven == False):
            flashLightStim(strip, Color(255, 0, 0))
            self.stimulusGiven = True 
              
    def noise_stimulus(self):
        if(self.stimulusGiven == False):
            #TODO Make noise
            self.stimulusGiven = True   
                    
    def finish_trial(self):
        with self.lock:
            if self.state == 'Running':
                self.state = 'Completed'
                print("Trial complete")
                return True
            return False
            
    def error(self):
        with self.lock:
            self.state = 'Error'
            self.handle_error()
            self.state = 'Idle'

    def pause_trial_logic(self):
        # TODO Code to pause trial
        pass

    def resume_trial_logic(self):
        # TODO Code to resume trial
        pass

    def handle_error(self):
        # TODO Code to handle errors
        pass

#region Action Functions
def feed():
	try:
		feeder_motor = OutputDevice(feeder_port, active_high=False, initial_value=False)
		feeder_motor.on()
		time.sleep(1) #TODO Feed Time
		feeder_motor.off()
		feeder_motor.close()
	finally:
		return

def water():
	try:
		water_motor = OutputDevice(water_port, active_high=False, initial_value=False)
		water_motor.on()
		time.sleep(1) #TODO Water Time
		water_motor.off()
		water_motor.close()
	finally:
		return


def flashLightStim(strip, color, wait_ms=10):
	"""Flash the light stimulus."""
     # Turn lights on
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
		strip.show()
		time.sleep(wait_ms/1000.0)
	# Turn lights off
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, Color(0,0,0))
		strip.show()
		time.sleep(wait_ms/1000.0)

def play_sound(pin, duration): #TODO 
	print("Playing sound")
	#buzzer.on 
	time.sleep(duration) # Wait a predetermained amount of time
	#buzzer.off

def lever_press():
    try:
        trial_state_machine.currentIteration += 1
    except:
        pass
    feed()

def nose_poke():
    print("Nose poke")
    try:
        trial_state_machine.currentIteration += 1
    except:
        pass
    water()

#Settings and File Management
def load_settings():
    try:
        with open(settings_path, 'r') as file:
            settings = json.load(file)
    except FileNotFoundError:
        settings = {}
    return settings

def save_settings(settings):
	with open(settings_path, 'w') as file:
		json.dump(settings, file, indent=4)

#endregion

#region Routes
@app.route('/')
def homepage():
	return render_template('homepage.html')

@app.route('/testingpage')
def io_testing():
    return render_template('testingpage.html')

@app.route('/test_io', methods=['POST'])
def test_io():
	action = request.form.get('action')
	print(f"Button clicked: {action}")
	#TODO Add code to handle each action.
	if action == 'feed':
		feed()
	if action == 'water':
		water()
	if action == 'light':
		flashLightStim(strip, Color(255, 255, 255))

	if action == 'sound':
		play_sound(speaker_port, 1)
	if action == 'lever_press':
		lever_press()
	if action == 'nose_poke':
		nose_poke()

	return redirect(url_for('io_testing'))

@app.route('/trial', methods=['POST'])
def trial():
	settings = load_settings()  # Load settings
	if(trial_state_machine.state == 'running'):
		return render_template('runningtrialpage.html', settings=settings)
	
	else:
		settings = load_settings()  # Load settings
		# Perform operations based on settings...
		return render_template('trialpage.html', settings=settings)

@app.route('/start', methods=['POST'])
def start():
    settings = load_settings()  # Load settings
    if trial_state_machine.start_trial():
        return render_template('runningtrialpage.html', settings=settings)
    return render_template('runningtrialpage.html', settings=settings)

@app.route('/stop', methods=['POST'])
def stop():
    if trial_state_machine.stop_trial():
        return redirect(url_for('trial_settings'))
    return jsonify({"message": "Unable to stop trial"}), 400

@app.route('/trial-settings', methods=['GET'])
def trial_settings():
    settings = load_settings()
    return render_template('trialpage.html', settings=settings)

@app.route('/update-trial-settings', methods=['POST'])
def update_trial_settings():
    settings = load_settings()
    for key in request.form:
        settings[key] = request.form[key]
    save_settings(settings)
    return redirect(url_for('trial_settings'))

@app.route('/trial-status')
def trial_status():
    # This should return the real-time values of countdown and current iteration
    trial_status = {
		'timeRemaining': trial_state_machine.timeRemaining,
		'currentIteration': trial_state_machine.currentIteration
	}
    return jsonify(trial_status)

#endregion


# Run the app
if __name__ == '__main__':
    # Create a state machine
	trial_state_machine = TrialStateMachine() 
	#TODO Eventually make it so that I can have multiple. 
		# Store them in an dict?


	# Start the Flask app
	app.run(debug=True, use_reloader=False, host='0.0.0.0')


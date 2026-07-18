import time
import Settings as s
import Excel as Excel
import cv2
from Camera import Camera
from Poppy import Poppy
from Audio import Audio
from Training import Training
from Screen import Screen, FullScreenApp
from PIL import Image, ImageTk
import pickle
import datetime


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.
# TODO add more exercises
# TODO adaptive framework
# TODO GUI
# delay between exercises


if __name__ == '__main__':
    print("[main] starting gymmy_thesis", flush=True)
    s.camera_num = 0  # 0 - webcam, 2 - second USB in maya's computer

    # Audio variables initialization
    language = 'Hebrew'
    gender = 'Male'
    s.audio_path = 'audio files/' + language + '/' + gender + '/'
    s.picture_path = 'audio files/' + language + '/' + gender + '/'
    # s.str_to_say = ""
    current_time = datetime.datetime.now()
    s.participant_code = str(current_time.day) + "." + str(current_time.month) + " " + str(current_time.hour) + "." + \
                         str(current_time.minute) + "." + str(current_time.second)

    # Training variables initialization
    s.exercise_amount = 6
    s.rep = 8
    s.req_exercise = ""
    s.finish_workout = False
    s.waved = False
    s.success_exercise = False
    s.calibration = False # False to have calibration session, True to not have
    s.training_done = False
    s.poppy_done = False
    s.camera_done = False
    s.robot_count = True
    s.try_again = False
    # Excel variable
    print(f"[main] participant_code={s.participant_code} language={language} gender={gender} rep={s.rep}", flush=True)
    print("[main] creating Excel workbook", flush=True)
    Excel.create_workbook()
    s.ex_list = []

    # Create all components
    # Initialize camera capture on the main thread — AVFoundation on macOS requires
    # VideoCapture to be opened from the main thread or frames come back empty.
    print(f"[main] opening camera {s.camera_num} on main thread", flush=True)
    s.cap = cv2.VideoCapture(s.camera_num)
    if not s.cap.isOpened():
        print(f"[main] ERROR: camera {s.camera_num} failed to open. Check s.camera_num and permissions.", flush=True)
    else:
        print(f"[main] camera opened: {int(s.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(s.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}", flush=True)

    print("[main] initializing Camera", flush=True)
    s.camera = Camera()
    print("[main] initializing Training", flush=True)
    s.training = Training()
    print("[main] initializing Poppy (connecting to CoppeliaSim on port 19997)", flush=True)
    s.robot = Poppy()

    # Adaptation variables
    s.adaptive = True
    s.corrective_feedback = False
    s.one_hand = False
    if s.adaptive:
        s.adaptation_model_name = 'performance_evaluation_model'
        s.performance_class = {}
        # s.adaptation_model = pickle.load(open(f'{adaptation_model_name}.sav', 'rb'))

    # Start all threads
    print("[main] starting Camera thread", flush=True)
    s.camera.start()
    print("[main] starting Training thread", flush=True)
    s.training.start()
    print("[main] starting Poppy thread", flush=True)
    s.robot.start()
    print("[main] opening fullscreen GUI (wave at camera to begin)", flush=True)
    s.screen = Screen()
    image1 = Image.open('Pictures//icon.jpg')
    s.screen.tk.call('wm', 'iconphoto', s.screen._w, ImageTk.PhotoImage(image1))
    app = FullScreenApp(s.screen)
    s.screen.mainloop()
    print("[main] GUI closed, exiting", flush=True)


"""
Camera preview with MediaPipe skeleton overlay.
Run this BEFORE ./run.sh to verify the camera can see you and detect your pose.

Usage:
    .venv/bin/python camera_preview.py

Press Q to quit.
"""
import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: could not open camera 0. Check permissions and s.camera_num.")
    exit(1)

print(f"Camera opened: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print("Press Q to quit.")

with mp_pose.Pose(min_detection_confidence=0.8, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            print("Empty frame — retrying...")
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = pose.process(rgb)
        rgb.flags.writeable = True
        out = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                out, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
            cv2.putText(out, "Pose detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 2)
        else:
            cv2.putText(out, "No pose — step back / check lighting", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Camera preview (Q to quit)", cv2.flip(out, 1))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

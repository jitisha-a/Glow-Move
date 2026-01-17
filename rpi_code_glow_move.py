import time #to manage timings bw rounds
import random #to send a random sequence of colors to the arduino
import serial #to communicate with the arduino over serial
import cv2 #to access the webcam and process video frames
import mediapipe as mp #to detect and analyze hand gestures

SERIAL_PORT = "/dev/ttyACM0"
BAUD = 115200

ROUND_COUNT = 20 #number of colour flashes
ROUND_WINDOW_SECONDS = 2.0 #time window to show the gesture
REST_SECONDS = 0.15 #rest time between colours

COLORS = ["RED", "GREEN", "BLUE", "YELLOW"]

COLOR_TO_FINGERS = {"RED": 5, "GREEN": 0, "BLUE": 2, "YELLOW": 4} #mapping colors to finger counts

mp_hands = mp.solutions.hands #for hand detection and tracking
mp_draw = mp.solutions.drawing_utils #for drawing hand landmarks
TIP_IDS = [4, 8, 12, 16, 20] #landmark indices for fingertips

#helper function to count number of fingers raised based on hand landmarks
def count_fingers(hand_landmarks, handedness_label):
    lm = hand_landmarks.landmark
    fingers = 0 #initialise finger count 

    if handedness_label == "Right":
        if lm[TIP_IDS[0]].x < lm[TIP_IDS[0] - 1].x: #for right thumb (x-axis comparison)
            fingers += 1
    else:
        if lm[TIP_IDS[0]].x > lm[TIP_IDS[0] - 1].x: #for left thumb (x-axis comparison)
            fingers += 1

    for i in range(1, 5): #for other four fingers (y-axis comparison)
        tip = TIP_IDS[i] #tip landmark index
        pip = tip - 2 #proximal pip joint landmark index
        if lm[tip].y < lm[pip].y: 
            fingers += 1

    return fingers

#helper function to map finger count to color
def fingers_to_color(fcount):
    for c, fc in COLOR_TO_FINGERS.items(): #iterate through color-finger mapping dictionary
        if fcount == fc: #if finger count matches the colour's finger count, return the colour
            return c
    return None

#helper function to send command to arduino over serial
def send_cmd(ser, cmd):
    ser.write((cmd + "\n").encode("utf-8")) #convert command to bytes and send over serial + send newline for aduino to detect end of command

def main():
    #setup serial communication with arduino
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)
        time.sleep(2.0)
    except Exception as e:
        print(f"[ERROR] Can't open serial {SERIAL_PORT}: {e}")
        print("Tip: run: ls /dev/ttyACM* /dev/ttyUSB*  and update SERIAL_PORT.")
        return

    cap = cv2.VideoCapture(0) #open default webcam
    if not cap.isOpened():
        print("[ERROR] Can't open webcam.")
        return

    #lower resolution for faster processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    score = 0
    print("Press 'q' to quit.")
    print(f"Starting game: {ROUND_COUNT} colours | window={ROUND_WINDOW_SECONDS}s")

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as hands:

        send_cmd(ser, "START")
        time.sleep(0.3) 
        for r in range(1, ROUND_COUNT + 1):
            target = random.choice(COLORS)

            send_cmd(ser, target)

            start = time.time()
            matched = False #flag to indicate if player matched the target

            last = None #last detected color
            streak = 0 #consecutive frames with the same detected color
            REQUIRED_STREAK = 3 #number of consecutive frames needed to confirm a match to esnure reliability

            while (time.time() - start) < ROUND_WINDOW_SECONDS:
                ok, frame = cap.read() 
                if not ok: 
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = hands.process(rgb)

                detected_color = None #initialise detected color
                fcount = None #initialise finger count

                if res.multi_hand_landmarks and res.multi_handedness: #if a hand is detected
                    hand_lms = res.multi_hand_landmarks[0] #get the first detected hand landmarks
                    handedness = res.multi_handedness[0].classification[0].label #get handedness label (Left/Right)

                    fcount = count_fingers(hand_lms, handedness)
                    detected_color = fingers_to_color(fcount)

                    mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS) #draw hand landmarks on frame

                if detected_color is not None and detected_color == last: #if same color detected as last frame
                    streak += 1 #increment streak
                else:
                    streak = 0
                    last = detected_color #reset streak

                if detected_color == target and streak >= REQUIRED_STREAK:
                    matched = True
                    break

                cv2.putText(frame, f"ROUND: {r}/{ROUND_COUNT}", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                cv2.putText(frame, f"Target: {target}", (10, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                cv2.putText(frame, f"Score: {score}", (10, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

                if fcount is not None:
                    cv2.putText(frame, f"Fingers: {fcount}", (10, 115),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                if detected_color is not None:
                    cv2.putText(frame, f"Gesture: {detected_color}", (10, 145),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

                cv2.imshow("Arcade Game", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    send_cmd(ser, "OFF")
                    cap.release()
                    cv2.destroyAllWindows()
                    print(f"Quit. Final scoreeee: {score}/{r-1}")
                    return

            send_cmd(ser, "OFF")

            if matched:
                score += 1
                print(f"Round {r}: {target} CORRECT Score={score}")
            else:
                print(f"Round {r}: {target} INCORRECT Score={score}")

            time.sleep(REST_SECONDS)

    time.sleep(0.3)
    
    print(f"\nGame over!! Final score: {score}/{ROUND_COUNT}")

    send_cmd(ser, "END")
    time.sleep(0.3)
    send_cmd(ser, "OFF")
    cap.release()
    cv2.destroyAllWindows()
    if ser is not None and ser.is_open:
        ser.close()

if __name__ == "__main__":
    main()

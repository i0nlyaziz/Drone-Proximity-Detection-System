import cv2
import datetime
import numpy as np
import pygame
import sqlite3
from ultralytics import YOLO

conn = sqlite3.connect("DataBase.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS info (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Distance REAL,
    Screenshot TEXT,
    Confidence REAL,
    Date TEXT
)
""")
conn.commit()

pygame.mixer.init()
alarm = pygame.mixer.Sound("alert.mp3")

close_threshold = 20.0
medium_threshold = 40.0
alpha = 0.3

def classify(d):
    if d < close_threshold:
        return (0,0,255) , "Close"
    elif d < medium_threshold:
        return (0,165,255) , "Medium"
    else:
        return (0,255,0) , "Far"

classes = {0:"Drone"}

cam = cv2.VideoCapture(0)

detect = YOLO("weights/Drone.pt")
depth = YOLO("weights/yolo26n-depth.pt")

timers = {}
state = {}
smooth = {}

while True:
    ret , frame = cam.read()
    if not ret:
        break
    h, w = frame.shape[:2]
    det = detect.track(frame,persist=True,tracker="bytetrack.yaml",classes=list(classes),verbose=False)[0]
    dep = np.squeeze(depth(frame,verbose=False)[0].depth.data.cpu().numpy())
    if dep.shape != (h,w):
        dep = cv2.resize(dep,(w,h),interpolation=cv2.INTER_NEAREST)
    seen = set()
    for box in det.boxes:
        x1,y1,x2,y2 = map(int,box.xyxy[0])
        x1,y1,x2,y2 = max(x1,0) , max(y1,0) , min(x2,w) , min(y2,h)
        conf = float(box.conf[0])
        track_id = int(box.id[0]) if box.id is not None else None
        if track_id is None:
            continue
        seen.add(track_id)
        if track_id not in state:
            state[track_id] = {
                "Distance":"Unknown",
                "Screenshot":"No",
                "confidence":"Unknown",
                "Saved": False
            }
        bw, bh = x2 - x1, y2 - y1
        crop = dep[y1 + bh // 4:y2 - bh // 4, x1 + bw // 4:x2 - bw // 4]
        valid = crop[np.isfinite(crop) & (crop > 0)]
        if valid.size == 0:
            continue
        dist = float(np.median(valid))
        dist = alpha * dist + (1 - alpha) * smooth.get(track_id, dist)
        smooth[track_id] = dist
        color , status = classify(dist)
        label = f"{track_id} - {status} {dist:.1f}M"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 3)
        if status == "Close":
            if track_id not in timers:
                timers[track_id] = datetime.datetime.now().timestamp()
            duration = datetime.datetime.now().timestamp() - timers[track_id]
            if duration >= 8 and not state[track_id]["Saved"]:
                filename = f"drone_{track_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                if cv2.imwrite(filename, frame):
                    alarm.play()
                    event_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    state[track_id]["Screenshot"] = filename
                    state[track_id]["Distance"] = dist
                    state[track_id]["confidence"] = conf
                    cursor.execute("""
                        INSERT INTO info
                        (Distance, Screenshot, Confidence, Date)
                        VALUES (?, ?, ?, ?)
                    """, (
                        dist,
                        filename,
                        conf,
                        event_time
                    ))
                    conn.commit()
                    state[track_id]["Saved"] = True
        else:
            timers.pop(track_id, None)
            state[track_id]["Saved"] = False
    for track_id in list(state):
        if track_id not in seen:
            state.pop(track_id, None)
            timers.pop(track_id, None)
            smooth.pop(track_id, None)
    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) & 0xff == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
conn.close()
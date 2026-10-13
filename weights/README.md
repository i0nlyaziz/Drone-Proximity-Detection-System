# Model Weights

The trained weights aren't committed to this repo directly — they're excluded in `.gitignore` and attached to the repo's Releases instead.

## Download

- **Drone.pt** — [Download from Releases](https://github.com/i0nlyaziz/Drone-Proximity-Detection-System/releases/download/v1.0/Drone.pt)
- **yolo26n-depth.pt** — [Download from Releases](https://github.com/i0nlyaziz/Drone-Proximity-Detection-System/releases/download/v1.0/yolo26n-depth.pt)

## Using the weights

1. Download both files from the links above and place them in this `weights/` folder.
2. `main.py` loads both files from here: `Drone.pt` is the drone detection model (class 0 is Drone), and `yolo26n-depth.pt` is the depth estimation model used to estimate each drone's distance.
3. Update the model paths in `main.py` if you place the files somewhere other than `weights/`.
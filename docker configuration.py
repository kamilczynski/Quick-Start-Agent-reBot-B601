# Docker Engine

sudo apt update
sudo apt install -y ca-certificates curl
#############################################
sudo install -m 0755 -d /etc/apt/keyrings
#############################################
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
#############################################
sudo chmod a+r /etc/apt/keyrings/docker.asc
#############################################
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
#############################################
sudo apt update
#############################################
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
#############################################
sudo usermod -aG docker $USER
newgrp docker
#############################################
docker ps
#############################################
docker run --rm hello-world
#############################################
# NVIDIA Container Toolkit
sudo apt-get update

sudo apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gnupg2
#############################################
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor \
  -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
#############################################
curl -s -L \
  https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
#############################################
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
#############################################
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
#############################################
nvidia-ctk --version
docker info | grep -i runtime
#############################################
# GPU test inside Docker; If we see the GPU, CUDA passthrough is working.

docker run --rm \
  --runtime=nvidia \
  --gpus all \
  ubuntu \
  nvidia-smi
#############################################
docker pull ultralytics/ultralytics:latest
#############################################
mkdir -p ~/rebot_grasp
mkdir -p ~/.cache/huggingface
mkdir -p ~/Desktop
#############################################
sudo xhost +si:localuser:root
#############################################
# Creating our main container

docker run -it \
  --name b601_grasp_agent \
  --runtime=nvidia \
  --gpus all \
  --network host \
  --ipc=host \
  --pid=host \
  --privileged \
  --cap-add=ALL \
  --security-opt seccomp=unconfined \
  -e DISPLAY=$DISPLAY \
  -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev:/dev \
  -v /run:/run \
  -v /sys:/sys \
  -v /tmp:/tmp \
  -v "$HOME/Desktop:/workspace" \
  -v "$HOME/rebot_grasp:/root/rebot_grasp" \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
  ultralytics/ultralytics:latest \
  bash
#############################################
# Restarting the container
sudo xhost +si:localuser:root
docker start -ai b601_grasp_agent
#############################################
# GPU test in main container
nvidia-smi
#############################################
python3 - <<'PY'
import torch
import ultralytics

print("Torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA:", torch.version.cuda)
print("Ultralytics:", ultralytics.__version__)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
PY
#############################################
cd /root/rebot_grasp
#############################################
git clone https://github.com/Seeed-Projects/reBot-DevArm-Grasp.git .
#############################################
cd /root

curl -fL \
  https://github.com/conda-forge/miniforge/releases/download/26.3.2-2/Miniforge3-26.3.2-2-Linux-x86_64.sh \
  -o /root/Miniforge3.sh
#############################################
bash /root/Miniforge3.sh -b -p /opt/conda
#############################################
export PATH="/opt/conda/bin:$PATH"
source /opt/conda/etc/profile.d/conda.sh
#############################################
conda --version
mamba --version
#############################################
# Conda auto-loading after container startup
cat >> /root/.bashrc <<'EOF'

export PATH="/opt/conda/bin:$PATH"
source /opt/conda/etc/profile.d/conda.sh
EOF
#############################################
source /root/.bashrc
#############################################
# Creating a rebotarm environment

cd /root/rebot_grasp
#############################################
conda env create -f environment.yml
#############################################
conda activate rebotarm
#############################################
# Orbbec SDK for Gemini 336

import pyorbbecsdk
#############################################
pip install --upgrade pyorbbecsdk2
#############################################
mkdir -p /root/downloads
cd /root/downloads
#############################################
aria2c \
  --continue=true \
  --max-tries=0 \
  --retry-wait=10 \
  --timeout=60 \
  --max-connection-per-server=4 \
  --split=4 \
  --disable-ipv6=true \
  --out=open3d-0.18.0-cp310-cp310-manylinux_2_27_x86_64.whl \
  "https://files.pythonhosted.org/packages/3b/e1/fc609763d982c6c43ee9503279fa6dc42d048b6224a9dc0a0ce8ac19308a/open3d-0.18.0-cp310-cp310-manylinux_2_27_x86_64.whl"
#############################################
pip install ./open3d-0.18.0-cp310-cp310-manylinux_2_27_x86_64.whl
#############################################
cd /root/rebot_grasp

pip install \
  --resume-retries 100 \
  --retries 20 \
  --timeout 120 \
  pyorbbecsdk2
#############################################
# Test Orbbec SDK

python - <<'PY'
import pyorbbecsdk
import open3d

print("pyorbbecsdk: OK")
print("Open3D:", open3d.__version__)
PY
#############################################
# Installing SDK B601

cd /root/rebot_grasp
mkdir -p sdk
#############################################
git clone --depth 1 \
  https://github.com/Seeed-Projects/reBotArm_control_py.git \
  sdk/reBotArm_control_py
#############################################
cd /root/rebot_grasp/sdk/reBotArm_control_py
#############################################
grep -q '^\[tool.setuptools.packages.find\]' pyproject.toml || \
cat >> pyproject.toml <<'EOF'

[tool.setuptools.packages.find]
include = ["reBotArm_control_py*"]
EOF
#############################################
pip install -e .
#############################################
pip list | grep -Ei 'rebot|motorbridge'
#############################################
python - <<'PY'
import reBotArm_control_py

print("reBotArm_control_py: OK")
print(reBotArm_control_py.__file__)
PY
#############################################
# Switching SDK to B601-DM

rebotarm_rs.yaml
#############################################
cd /root/rebot_grasp/sdk/reBotArm_control_py/config
#############################################
cp rebotarm.yaml rebotarm.yaml.bak_before_dm
#############################################
sed -i \
  's/^hardware_yaml:.*/hardware_yaml: "rebotarm_dm.yaml"/' \
  rebotarm.yaml
#############################################
cat rebotarm.yaml
#############################################
cd /root/rebot_grasp

python - <<'PY'
from drivers.robot.grasp_driver import selected_arm_config

cfg = selected_arm_config()

print("arm_type:", cfg.arm_type)
print("controller_mode:", cfg.controller_mode)
PY
#############################################
# Scan B601 without starting autonomous grasping

motorbridge-cli scan \
  --vendor damiao \
  --transport dm-serial \
  --serial-port /dev/ttyACM0 \
  --serial-baud 921600
#############################################
for d in /sys/bus/usb/devices/*; do
    [ -f "$d/idVendor" ] || continue

    vendor=$(cat "$d/idVendor" 2>/dev/null)
    product=$(cat "$d/idProduct" 2>/dev/null)
    manufacturer=$(cat "$d/manufacturer" 2>/dev/null)
    name=$(cat "$d/product" 2>/dev/null)
    bus=$(cat "$d/busnum" 2>/dev/null)
    dev=$(cat "$d/devnum" 2>/dev/null)

    printf "BUS=%s DEV=%s  %s:%s  %s  %s\n" \
        "$bus" "$dev" "$vendor" "$product" "$manufacturer" "$name"
done
#############################################
# Test depth + RGB Gemini 336

cd /root/rebot_grasp
#############################################
python - <<'PY'
import time
from drivers.camera.orbbec_gemini2 import OrbbecGemini2

cam = OrbbecGemini2(
    width=640,
    height=480,
    fps=30,
)

try:
    cam.open()

    print("K:")
    print(cam.K)

    print("D:")
    print(cam.D)

    for i in range(30):
        color, depth = cam.get_frame()

        print(
            f"{i:02d}: "
            f"color={None if color is None else color.shape} "
            f"depth={None if depth is None else depth.shape}"
        )

        if color is not None and depth is not None:
            print("RGB + DEPTH: OK")
            break

        time.sleep(0.05)

finally:
    cam.close()
PY
#############################################

cat > /workspace/JETSON/rebot_grasp_jetson/agent_api.py <<'PY'
from __future__ import annotations

import argparse
import math
import sys
import time
import threading
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _p in (PROJECT_ROOT,):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from drivers.camera import make_camera
from drivers.robot.rebot_arm import RebotArm
from utils.camera_utils import load_config, load_hand_eye
from utils.ordinary_grasp import GraspPose, draw_grasp, estimate_grasps, select_best_grasp
from utils.transforms import (
    canonicalize_parallel_gripper_tcp_rotation,
    rotation_matrix_to_euler_zyx,
    transform_grasp_pose_to_base,
)
from utils.yolo_utils import load_yolo


# ============================================================
# Ball / Box / Obstacle autonomous logic
# Classes:
#   0 - ball
#   1 - box
#   2 - obstacle
#
# Behavior:
#   if obstacle overlaps ball:
#       pick obstacle and move it slightly aside
#       rescan
#       pick ball and drop it into box
#   else:
#       pick ball and drop it into box
# ============================================================

DEFAULT_MODEL_NAME = "/workspace/JETSON/tenisbest26s.pt"

# Emergency stop flag.
# Q/ESC sets this flag while a robot cycle is running.
EMERGENCY_STOP = threading.Event()

# Manual grasp correction offsets in robot/base frame.
# If the gripper consistently grabs too far from the object,
# tune these values by small steps, e.g. 0.005 m.
GRASP_OFFSET_X_M = 0.000
GRASP_OFFSET_Y_M = 0.000
GRASP_OFFSET_Z_M = 0.000

# Grasp tuning.
EXTRA_INSERT_M = 0.040
PREGRASP_DEFAULT_M = 0.080

# Table-top grasp mode.
# The objects are on the table below/in front of the arm,
# so the gripper should approach from above, not from the front.
TOP_DOWN_GRASP_ENABLED = True

# If the gripper points the wrong way, change +1.5708 to -1.5708.
TABLE_GRASP_ROLL_RAD = 0.000000
TABLE_GRASP_PITCH_RAD = 0.698132
TABLE_GRASP_YAW_OFFSET_RAD = 0.000000

# Also force observation/ready pose to the same tool orientation.
FORCE_READY_TOPDOWN_ORIENTATION = True

# Pregrasp is directly above the detected object.
TABLE_PREGRASP_Z_OFFSET_M = 0.100
TABLE_PREGRASP_MIN_Z_M = 0.160
TABLE_PREGRASP_MAX_Z_M = 0.500

# Width control.
RELEASE_WIDTH_M = 0.070

BALL_CLOSE_MARGIN_M = -0.020
BALL_CLOSE_MIN_M = 0.030
BALL_CLOSE_MAX_M = 0.050

OBSTACLE_CLOSE_MARGIN_M = -0.012
OBSTACLE_CLOSE_MIN_M = 0.006
OBSTACLE_CLOSE_MAX_M = 0.045

# Obstacle relation logic.
BLOCK_OVERLAP_BALL_RATIO = 0.08
BLOCK_CENTER_INSIDE_BALL = True

# Move obstacle aside.
OBSTACLE_SIDE_OFFSET_Y_M = 0.120
OBSTACLE_LIFT_M = 0.120

# Drop ball into box.
BOX_DROP_Z_OFFSET_M = 0.140
BOX_DROP_MIN_Z_M = 0.180
BOX_DROP_MAX_Z_M = 0.420

# Auto / preview.
INFER_EVERY = 2
DEPTH_QUANTILE_DEFAULT = 0.75



def _emergency_requested(tag: str = "SAFE") -> bool:
    if EMERGENCY_STOP.is_set():
        print(f"[{tag}] EMERGENCY STOP requested — aborting sequence.")
        return True
    return False


def _safe_move_to(
    robot: RebotArm,
    x: float,
    y: float,
    z: float,
    roll: float,
    pitch: float,
    yaw: float,
    duration: float,
    tag: str = "MOVE",
) -> bool:
    if _emergency_requested(tag):
        return False

    ok = robot.move_to(x, y, z, roll, pitch, yaw, duration=duration)
    if not ok:
        print(f"[{tag}] move_to failed")
        return False

    # We still use wait_motion, but now every move is checked before/after.
    robot.wait_motion(duration)

    if _emergency_requested(tag):
        return False

    return True


def _safe_open_gripper(robot: RebotArm, distance_m: float, tag: str = "GRIPPER") -> bool:
    if _emergency_requested(tag):
        return False

    robot.open_gripper(distance_m=distance_m)
    time.sleep(0.2)

    if _emergency_requested(tag):
        return False

    return True


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _role_from_name(name: Any, cls_id: Optional[int] = None) -> Optional[str]:
    if cls_id is not None:
        try:
            cid = int(cls_id)
            if cid == 0:
                return "ball"
            if cid == 1:
                return "box"
            if cid == 2:
                return "obstacle"
        except Exception:
            pass

    n = str(name).strip().lower()

    if n in {"0", "ball", "tennis_ball", "tennis ball", "pilka", "piłka"}:
        return "ball"
    if n in {"1", "box", "container", "pudelko", "pudełko"}:
        return "box"
    if n in {"2", "obstacle", "bar", "blocker", "stick", "przeszkoda"}:
        return "obstacle"

    if "ball" in n or "tennis" in n or "pil" in n:
        return "ball"
    if "box" in n or "container" in n or "pudel" in n:
        return "box"
    if "obstacle" in n or "stick" in n or "bar" in n or "block" in n or "przeszk" in n:
        return "obstacle"

    return None


def _extract_detections(results: list[Any]) -> list[dict[str, Any]]:
    dets: list[dict[str, Any]] = []
    if not results:
        return dets

    r0 = results[0]
    boxes = getattr(r0, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return dets

    names = getattr(r0, "names", {}) or {}

    xyxy_arr = boxes.xyxy.detach().cpu().numpy()
    conf_arr = boxes.conf.detach().cpu().numpy() if boxes.conf is not None else np.ones((len(xyxy_arr),), dtype=np.float32)
    cls_arr = boxes.cls.detach().cpu().numpy() if boxes.cls is not None else np.zeros((len(xyxy_arr),), dtype=np.float32)

    for xyxy, conf, cls_id_f in zip(xyxy_arr, conf_arr, cls_arr):
        cls_id = int(cls_id_f)
        class_name = str(names.get(cls_id, cls_id))
        role = _role_from_name(class_name, cls_id)

        x1, y1, x2, y2 = [float(v) for v in xyxy]
        if x2 <= x1 or y2 <= y1:
            continue

        dets.append(
            {
                "role": role,
                "class_name": class_name,
                "cls_id": cls_id,
                "conf": float(conf),
                "xyxy": (x1, y1, x2, y2),
                "cx": 0.5 * (x1 + x2),
                "cy": 0.5 * (y1 + y2),
                "area": max(1.0, (x2 - x1) * (y2 - y1)),
            }
        )

    return dets


def _best_det(dets: list[dict[str, Any]], role: str) -> Optional[dict[str, Any]]:
    items = [d for d in dets if d.get("role") == role]
    if not items:
        return None
    return max(items, key=lambda d: float(d.get("conf", 0.0)))


def _intersection_area(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    return float((ix2 - ix1) * (iy2 - iy1))


def _point_inside_box(px: float, py: float, box: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = box
    return x1 <= px <= x2 and y1 <= py <= y2


def _obstacle_blocks_ball(dets: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    ball = _best_det(dets, "ball")
    obstacle = _best_det(dets, "obstacle")

    info = {
        "ball": ball,
        "obstacle": obstacle,
        "overlap_area": 0.0,
        "overlap_ball_ratio": 0.0,
        "obstacle_center_inside_ball": False,
    }

    if ball is None or obstacle is None:
        return False, info

    ball_box = ball["xyxy"]
    obs_box = obstacle["xyxy"]

    overlap = _intersection_area(ball_box, obs_box)
    ratio_ball = overlap / max(1.0, float(ball["area"]))
    center_inside = _point_inside_box(float(obstacle["cx"]), float(obstacle["cy"]), ball_box)

    info["overlap_area"] = overlap
    info["overlap_ball_ratio"] = ratio_ball
    info["obstacle_center_inside_ball"] = center_inside

    blocked = ratio_ball >= BLOCK_OVERLAP_BALL_RATIO or (BLOCK_CENTER_INSIDE_BALL and center_inside)
    return bool(blocked), info


def _is_valid_grasp(grasp: Optional[GraspPose]) -> bool:
    return (
        grasp is not None
        and grasp.position is not None
        and grasp.rotation is not None
        and grasp.tcp_rotation is not None
        and getattr(grasp, "rejected_reason", None) is None
    )


def _select_closest_grasp_by_role(grasps: list[GraspPose], role: str) -> Optional[GraspPose]:
    candidates = []
    for g in grasps:
        if not _is_valid_grasp(g):
            continue
        g_role = _role_from_name(getattr(g, "class_name", ""))
        if g_role == role:
            candidates.append(g)

    if not candidates:
        return None

    return min(candidates, key=lambda g: float(g.position[2]))


def _select_fallback_grasp(grasps: list[GraspPose]) -> Optional[GraspPose]:
    candidates = [g for g in grasps if _is_valid_grasp(g)]
    if not candidates:
        return None
    return min(candidates, key=lambda g: float(g.position[2])) or select_best_grasp(grasps)


def _compute_close_width(role: str, target_width_m: Optional[float]) -> tuple[float, float]:
    if target_width_m is None or target_width_m <= 0:
        if role == "ball":
            return 0.052, RELEASE_WIDTH_M
        if role == "obstacle":
            return 0.035, RELEASE_WIDTH_M
        return 0.045, RELEASE_WIDTH_M

    if role == "ball":
        close = float(np.clip(
            float(target_width_m) + BALL_CLOSE_MARGIN_M,
            BALL_CLOSE_MIN_M,
            BALL_CLOSE_MAX_M,
        ))
        return close, RELEASE_WIDTH_M

    if role == "obstacle":
        close = float(np.clip(
            float(target_width_m) + OBSTACLE_CLOSE_MARGIN_M,
            OBSTACLE_CLOSE_MIN_M,
            OBSTACLE_CLOSE_MAX_M,
        ))
        return close, RELEASE_WIDTH_M

    close = float(np.clip(float(target_width_m), 0.010, 0.060))
    return close, RELEASE_WIDTH_M


def _move_ready(robot: RebotArm, ready_cfg: dict[str, Any]) -> None:
    duration = float(ready_cfg.get("duration", 3.0))
    if FORCE_READY_TOPDOWN_ORIENTATION:
        print(
            f"[READY ORIENTATION] forced rpy=("
            f"{TABLE_GRASP_ROLL_RAD:+.3f},"
            f"{TABLE_GRASP_PITCH_RAD:+.3f},"
            f"{TABLE_GRASP_YAW_OFFSET_RAD:+.3f})"
        )
    _safe_move_to(
        robot,
        float(ready_cfg.get("x", 0.25)),
        float(ready_cfg.get("y", 0.0)),
        float(ready_cfg.get("z", 0.35)),
        TABLE_GRASP_ROLL_RAD if FORCE_READY_TOPDOWN_ORIENTATION else float(ready_cfg.get("roll", 0.0)),
        TABLE_GRASP_PITCH_RAD if FORCE_READY_TOPDOWN_ORIENTATION else float(ready_cfg.get("pitch", 1.2)),
        TABLE_GRASP_YAW_OFFSET_RAD if FORCE_READY_TOPDOWN_ORIENTATION else float(ready_cfg.get("yaw", 0.0)),
        duration=duration,
        tag="READY",
    )


def _cam_to_base(T_hand_eye: np.ndarray, robot: RebotArm) -> np.ndarray:
    return robot.get_tcp_pose() @ T_hand_eye


def _point_cam_to_base(T_cam2base: np.ndarray, p_cam: np.ndarray) -> np.ndarray:
    p = np.ones(4, dtype=np.float32)
    p[:3] = np.asarray(p_cam, dtype=np.float32).reshape(3)
    out = T_cam2base @ p
    return np.asarray(out[:3], dtype=np.float32)


def _grasp_to_base_6d(
    grasp: GraspPose,
    T_cam2base: np.ndarray,
    pregrasp_offset_m: float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    grasp6d, pre6d = transform_grasp_pose_to_base(
        np.asarray(grasp.position, dtype=np.float32),
        grasp.tcp_rotation,
        T_cam2base,
        pregrasp_offset_m,
    )

    if not TOP_DOWN_GRASP_ENABLED:
        return grasp6d, pre6d

    # Keep the yaw estimated by the grasp planner, but force the tool
    # to approach the table from above.
    xg, yg, zg, _rxg, _ryg, rzg = grasp6d

    # Manual correction in robot/base frame.
    # Use this if the robot consistently grabs too far from every object.
    xg += GRASP_OFFSET_X_M
    yg += GRASP_OFFSET_Y_M
    zg += GRASP_OFFSET_Z_M

    rx = TABLE_GRASP_ROLL_RAD
    ry = TABLE_GRASP_PITCH_RAD
    rz = TABLE_GRASP_YAW_OFFSET_RAD

    pre_z = _clamp(
        zg + TABLE_PREGRASP_Z_OFFSET_M,
        TABLE_PREGRASP_MIN_Z_M,
        TABLE_PREGRASP_MAX_Z_M,
    )

    topdown_grasp6d = (xg, yg, zg, rx, ry, rz)
    topdown_pre6d = (xg, yg, pre_z, rx, ry, rz)

    print(
        "[TOPDOWN] forced table approach: "
        f"grasp xyz=({xg:+.3f},{yg:+.3f},{zg:+.3f}) "
        f"pre_z={pre_z:+.3f} "
        f"rpy=({rx:+.3f},{ry:+.3f},{rz:+.3f}) "
        f"offset=({GRASP_OFFSET_X_M:+.3f},{GRASP_OFFSET_Y_M:+.3f},{GRASP_OFFSET_Z_M:+.3f})"
    )

    return topdown_grasp6d, topdown_pre6d


def _apply_extra_insertion(
    grasp6d: tuple[float, ...],
    pre6d: tuple[float, ...],
    tag: str,
) -> tuple[float, ...]:
    xg, yg, zg, rxg, ryg, rzg = grasp6d
    xp, yp, zp, _rxp, _ryp, _rzp = pre6d

    vx, vy, vz = xg - xp, yg - yp, zg - zp
    vn = math.sqrt(vx * vx + vy * vy + vz * vz)

    if vn > 1e-6:
        xg += EXTRA_INSERT_M * vx / vn
        yg += EXTRA_INSERT_M * vy / vn
        zg += EXTRA_INSERT_M * vz / vn
        print(f"[{tag}] extra insertion +{EXTRA_INSERT_M:.3f}m -> grasp xyz=({xg:+.3f},{yg:+.3f},{zg:+.3f})")

    return (xg, yg, zg, rxg, ryg, rzg)


def _execute_pick(
    robot: RebotArm,
    grasp6d: tuple[float, ...],
    pre6d: tuple[float, ...],
    role: str,
    target_width_m: Optional[float],
    dry_run: bool,
    tag: str,
) -> Optional[tuple[float, ...]]:
    grasp6d = _apply_extra_insertion(grasp6d, pre6d, tag=tag)

    xg, yg, zg, rxg, ryg, rzg = grasp6d
    xp, yp, zp, rxp, ryp, rzp = pre6d

    close_width_m, release_width_m = _compute_close_width(role, target_width_m)

    print(f"[{tag}] role={role}")
    print(f"[{tag}] pregrasp xyz=({xp:+.3f},{yp:+.3f},{zp:+.3f}) rpy=({rxp:+.3f},{ryp:+.3f},{rzp:+.3f})")
    print(f"[{tag}] grasp    xyz=({xg:+.3f},{yg:+.3f},{zg:+.3f}) rpy=({rxg:+.3f},{ryg:+.3f},{rzg:+.3f})")
    print(f"[{tag}] width target={target_width_m}, close={close_width_m*1000:.0f}mm, release={release_width_m*1000:.0f}mm")

    if dry_run:
        print(f"[{tag}] --dry-run: skipping robot motion")
        return grasp6d

    print(f"[{tag}] opening gripper...")
    if not _safe_open_gripper(robot, release_width_m, tag=tag):
        return None

    print(f"[{tag}] moving to pregrasp...")
    if not _safe_move_to(robot, xp, yp, zp, rxp, ryp, rzp, duration=2.0, tag=tag):
        print(f"[{tag}] pregrasp failed or emergency stop")
        return None

    print(f"[{tag}] moving to grasp...")
    if not _safe_move_to(robot, xg, yg, zg, rxg, ryg, rzg, duration=1.5, tag=tag):
        print(f"[{tag}] grasp failed or emergency stop")
        return None

    print(f"[{tag}] closing gripper to {close_width_m*1000:.0f}mm...")
    if not _safe_open_gripper(robot, close_width_m, tag=tag):
        return None
    time.sleep(0.3)

    return grasp6d


def _execute_obstacle_to_side(
    robot: RebotArm,
    grasp6d: tuple[float, ...],
    pre6d: tuple[float, ...],
    ready_cfg: dict[str, Any],
    target_width_m: Optional[float],
    dry_run: bool,
) -> bool:
    tag = "OBSTACLE"
    picked = _execute_pick(robot, grasp6d, pre6d, "obstacle", target_width_m, dry_run, tag)
    if picked is None:
        return False

    xg, yg, zg, rxg, ryg, rzg = picked

    lift_z = _clamp(zg + OBSTACLE_LIFT_M, 0.180, 0.450)
    side_x = xg
    side_y = yg + OBSTACLE_SIDE_OFFSET_Y_M
    side_z = lift_z

    if dry_run:
        print(f"[{tag}] --dry-run side drop xyz=({side_x:+.3f},{side_y:+.3f},{side_z:+.3f})")
        return True

    print(f"[{tag}] lifting obstacle...")
    if not _safe_move_to(robot, xg, yg, lift_z, rxg, ryg, rzg, duration=1.5, tag=tag):
        print(f"[{tag}] lift failed or emergency stop")
        return False

    print(f"[{tag}] moving obstacle slightly aside...")
    if not _safe_move_to(robot, side_x, side_y, side_z, rxg, ryg, rzg, duration=1.8, tag=tag):
        print(f"[{tag}] side move failed or emergency stop")
        return False

    print(f"[{tag}] releasing obstacle...")
    if not _safe_open_gripper(robot, RELEASE_WIDTH_M, tag=tag):
        return False
    time.sleep(0.3)

    print(f"[{tag}] returning to observation pose...")
    _move_ready(robot, ready_cfg)
    return True


def _execute_ball_to_box(
    robot: RebotArm,
    ball_grasp6d: tuple[float, ...],
    ball_pre6d: tuple[float, ...],
    box_base_xyz: np.ndarray,
    ready_cfg: dict[str, Any],
    target_width_m: Optional[float],
    dry_run: bool,
) -> bool:
    tag = "BALL_TO_BOX"
    picked = _execute_pick(robot, ball_grasp6d, ball_pre6d, "ball", target_width_m, dry_run, tag)
    if picked is None:
        return False

    xg, yg, zg, rxg, ryg, rzg = picked

    box_x, box_y, box_z = [float(v) for v in box_base_xyz.tolist()]
    drop_z = _clamp(box_z + BOX_DROP_Z_OFFSET_M, BOX_DROP_MIN_Z_M, BOX_DROP_MAX_Z_M)

    if dry_run:
        print(f"[{tag}] --dry-run box base xyz=({box_x:+.3f},{box_y:+.3f},{box_z:+.3f})")
        print(f"[{tag}] --dry-run drop xyz=({box_x:+.3f},{box_y:+.3f},{drop_z:+.3f})")
        return True

    print(f"[{tag}] returning to observation pose while holding ball...")
    _move_ready(robot, ready_cfg)

    print(f"[{tag}] moving above box xyz=({box_x:+.3f},{box_y:+.3f},{drop_z:+.3f})...")
    if not _safe_move_to(robot, box_x, box_y, drop_z, rxg, ryg, rzg, duration=2.0, tag=tag):
        print(f"[{tag}] box drop move failed or emergency stop")
        return False

    print(f"[{tag}] releasing ball into box...")
    if not _safe_open_gripper(robot, RELEASE_WIDTH_M, tag=tag):
        return False
    time.sleep(0.4)

    print(f"[{tag}] returning to observation pose...")
    _move_ready(robot, ready_cfg)
    return True



def _draw_text_clean(
    img: np.ndarray,
    text: str,
    org: tuple[int, int],
    color: tuple[int, int, int] = (235, 235, 235),
    scale: float = 0.45,
    thickness: int = 1,
) -> None:
    # cleaner OpenCV text: small font + dark shadow
    x, y = org
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, text, (x + 1, y + 1), font, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


def _draw_label_box(
    img: np.ndarray,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
    scale: float = 0.40,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 1
    (tw, th), base = cv2.getTextSize(text, font, scale, thickness)

    x0 = max(2, int(x))
    y0 = max(th + 8, int(y))
    w = tw + 8
    h = th + base + 6

    # prosta pełna ramka = mniej kosztowne niż overlay + addWeighted
    cv2.rectangle(img, (x0, y0 - th - 5), (x0 + w, y0 + base + 3), (0, 0, 0), -1)
    cv2.rectangle(img, (x0, y0 - th - 5), (x0 + w, y0 + base + 3), color, 1, cv2.LINE_AA)
    cv2.putText(img, text, (x0 + 4, y0 - 2), font, scale, color, thickness, cv2.LINE_AA)


def _role_color(role: Optional[str]) -> tuple[int, int, int]:
    if role == "ball":
        return (60, 255, 60)
    if role == "box":
        return (0, 220, 255)
    if role == "obstacle":
        return (255, 90, 30)
    return (220, 220, 220)


def _render_display(
    image: np.ndarray,
    grasps: list[GraspPose],
    best: Optional[GraspPose],
    dets: list[dict[str, Any]],
    blocked: bool,
    status_text: str,
) -> np.ndarray:
    display = image.copy()

    # Top subtle HUD background.
    overlay = display.copy()
    cv2.rectangle(overlay, (0, 0), (display.shape[1], 58), (8, 10, 14), -1)
    cv2.addWeighted(overlay, 0.48, display, 0.52, 0, display)

    # Short top status.
    plan = "CLEAR OBSTACLE -> BALL TO BOX" if blocked else "BALL TO BOX"
    _draw_text_clean(display, status_text, (10, 23), (235, 235, 235), scale=0.50, thickness=1)
    _draw_text_clean(display, f"PLAN: {plan}", (10, 48), (80, 255, 90), scale=0.50, thickness=1)

    # Detection boxes with small compact labels.
    for d in dets:
        role = d.get("role")
        color = _role_color(role)

        x1, y1, x2, y2 = [int(v) for v in d["xyxy"]]
        cv2.rectangle(display, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

        label = f"{role or d['class_name']} {d['conf']:.2f}"
        _draw_label_box(display, label, x1, max(18, y1 - 2), color, scale=0.40)

    # Draw only selected/best grasp, not all big debug labels.
    if best is not None and best.position is not None:
        role = _role_from_name(getattr(best, "class_name", "")) or str(getattr(best, "class_name", "object"))
        color = _role_color(role)

        try:
            cx, cy = best.center_px
            cx = int(cx)
            cy = int(cy)

            # Small grasp center.
            cv2.circle(display, (cx, cy), 4, (0, 0, 255), -1, cv2.LINE_AA)

            # Compact horizontal grasp line if possible.
            jaw_px = 70
            try:
                # If object jaw exists, scale only visually, bounded.
                jaw_px = int(np.clip(best.jaw_width_m * 900.0, 35, 90))
            except Exception:
                pass

            cv2.line(display, (cx - jaw_px // 2, cy), (cx + jaw_px // 2, cy), (235, 235, 235), 2, cv2.LINE_AA)

            x_m, y_m, z_m = best.position.tolist()

            # Compact label near selected object.
            _draw_label_box(
                display,
                f"{role} {best.conf:.2f}",
                cx - 55,
                cy - 38,
                color,
                scale=0.40,
            )

            # Bottom compact best line.
            bottom = f"best={role}  conf={best.conf:.2f}  xyz=({x_m:+.3f},{y_m:+.3f},{z_m:+.3f})"
            _draw_text_clean(display, bottom, (10, display.shape[0] - 14), (100, 255, 120), scale=0.45, thickness=1)

        except Exception:
            pass

    return display


def _print_best_grasp(grasp: GraspPose, prefix: str = "G") -> None:
    tcp_rotation = canonicalize_parallel_gripper_tcp_rotation(grasp.tcp_rotation)
    print(f"\n[{prefix}] selected grasp:")
    print(f"  class={grasp.class_name} conf={grasp.conf:.3f}")
    print(f"  center_px={grasp.center_px} angle_deg={grasp.angle_deg:.2f}")
    print(f"  jaw_width_m={grasp.jaw_width_m:.4f} object_length_m={grasp.object_length_m:.4f}")
    print(f"  position_xyz={grasp.position.tolist()}")
    print(f"  grasp_rpy={rotation_matrix_to_euler_zyx(grasp.rotation).tolist()}")
    print(f"  tcp_rpy={rotation_matrix_to_euler_zyx(tcp_rotation).tolist()}")


def _detect_scene(
    model: Any,
    yolo_opts: dict[str, Any],
    color_bgr: np.ndarray,
    depth_mm: np.ndarray,
    K: np.ndarray,
    depth_quantile: float,
) -> tuple[list[Any], list[GraspPose], list[dict[str, Any]], bool, dict[str, Any]]:
    results = model.predict(
        color_bgr,
        verbose=False,
        device=yolo_opts.get("device", "cpu"),
        conf=float(yolo_opts.get("conf", 0.25)),
        iou=float(yolo_opts.get("iou", 0.45)),
    )

    grasps = estimate_grasps(results, depth_mm, K, depth_quantile=depth_quantile)
    dets = _extract_detections(results)
    blocked, block_info = _obstacle_blocks_ball(dets)

    return results, grasps, dets, blocked, block_info


def _run_agentic_cycle(
    robot: RebotArm,
    cam: Any,
    model: Any,
    yolo_opts: dict[str, Any],
    K: np.ndarray,
    T_hand_eye: np.ndarray,
    ready_cfg: dict[str, Any],
    pregrasp_offset_m: float,
    depth_quantile: float,
    dry_run: bool,
) -> None:
    if _emergency_requested("CYCLE"):
        print("[CYCLE] Emergency stop active at cycle start.")
        return

    print("\n[CYCLE] Capturing scene...")
    color_bgr, depth_mm = cam.get_frame()
    if color_bgr is None or depth_mm is None:
        print("[CYCLE] Frame capture failed")
        return

    _results, grasps, dets, blocked, info = _detect_scene(model, yolo_opts, color_bgr, depth_mm, K, depth_quantile)

    print("[SCENE]")
    print(f"  ball detected:     {_best_det(dets, 'ball') is not None}")
    print(f"  box detected:      {_best_det(dets, 'box') is not None}")
    print(f"  obstacle detected: {_best_det(dets, 'obstacle') is not None}")
    print(f"  obstacle_on_ball:  {blocked}")
    print(f"  overlap_ball_ratio={info.get('overlap_ball_ratio', 0.0):.3f}, obstacle_center_inside_ball={info.get('obstacle_center_inside_ball', False)}")

    if blocked:
        obstacle_grasp = _select_closest_grasp_by_role(grasps, "obstacle")
        if obstacle_grasp is None:
            print("[PLAN] Obstacle blocks ball, but no valid obstacle grasp was found.")
            return

        _print_best_grasp(obstacle_grasp, prefix="OBSTACLE")

        T_cam2base = _cam_to_base(T_hand_eye, robot)
        obstacle_grasp6d, obstacle_pre6d = _grasp_to_base_6d(obstacle_grasp, T_cam2base, pregrasp_offset_m)

        print("[PLAN] Step 1: remove obstacle first.")
        ok = _execute_obstacle_to_side(
            robot,
            obstacle_grasp6d,
            obstacle_pre6d,
            ready_cfg,
            target_width_m=float(obstacle_grasp.jaw_width_m),
            dry_run=dry_run,
        )
        if not ok:
            print("[PLAN] Removing obstacle failed. Stopping cycle.")
            return

        if _emergency_requested("CYCLE"):
            return

        print("[PLAN] Obstacle removed. Rescanning scene before picking ball...")
        time.sleep(0.8)

        color_bgr, depth_mm = cam.get_frame()
        if color_bgr is None or depth_mm is None:
            print("[CYCLE] Frame capture after obstacle removal failed")
            return

        _results, grasps, dets, blocked2, info2 = _detect_scene(model, yolo_opts, color_bgr, depth_mm, K, depth_quantile)
        print(f"[SCENE AFTER OBSTACLE] obstacle_on_ball={blocked2}, overlap_ball_ratio={info2.get('overlap_ball_ratio', 0.0):.3f}")

    else:
        print("[PLAN] Ball is not blocked. Going directly to ball -> box.")

    ball_grasp = _select_closest_grasp_by_role(grasps, "ball")
    box_grasp = _select_closest_grasp_by_role(grasps, "box")

    if ball_grasp is None:
        print("[PLAN] No valid ball grasp found.")
        return

    if box_grasp is None:
        print("[PLAN] No valid box position/grasp found. Cannot drop ball into box.")
        return

    _print_best_grasp(ball_grasp, prefix="BALL")
    _print_best_grasp(box_grasp, prefix="BOX")

    T_cam2base = _cam_to_base(T_hand_eye, robot)

    ball_grasp6d, ball_pre6d = _grasp_to_base_6d(ball_grasp, T_cam2base, pregrasp_offset_m)
    box_base_xyz = _point_cam_to_base(T_cam2base, np.asarray(box_grasp.position, dtype=np.float32))

    if _emergency_requested("CYCLE"):
        return

    print("[PLAN] Step 2: pick ball and drop it into box.")
    _execute_ball_to_box(
        robot,
        ball_grasp6d,
        ball_pre6d,
        box_base_xyz,
        ready_cfg,
        target_width_m=float(ball_grasp.jaw_width_m),
        dry_run=dry_run,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ball / Box / Obstacle autonomous demo for reBot B601")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="YOLO model name/path. If relative, expected in models/")
    parser.add_argument("--dry-run", action="store_true", help="detect and plan only; no robot motion")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(PROJECT_ROOT / args.config)

    yolo_cfg = cfg.get("yolo", {})
    yolo_cfg["model_name"] = args.model
    cfg["yolo"] = yolo_cfg

    robot_cfg = cfg.get("robot", {})
    ready_cfg = robot_cfg.get(
        "ready_pose",
        {"x": 0.25, "y": 0.0, "z": 0.35, "roll": 0.0, "pitch": 1.2, "yaw": 0.0, "duration": 3.0},
    )

    gp_cfg = cfg.get("grasp_pipeline", {})
    grasp_cfg = gp_cfg.get("grasp", {})
    pregrasp_offset_m = float(grasp_cfg.get("pregrasp_offset_m", PREGRASP_DEFAULT_M))
    depth_quantile = float(grasp_cfg.get("depth_quantile", DEPTH_QUANTILE_DEFAULT))
    infer_every = max(1, int(gp_cfg.get("infer_every_live", INFER_EVERY)))

    print("=== Ball / Box / Obstacle autonomous demo ===")
    print(f"[MODEL] {args.model}")
    print("[KEYS] A = run one full scene cycle, R = resume live, Q/ESC = exit")
    print("[LOGIC] if obstacle overlaps ball -> remove obstacle -> rescan -> ball to box")
    print("[LOGIC] else -> ball to box")
    if args.dry_run:
        print("[MODE] --dry-run enabled: robot motion disabled")

    print("\n=== Connecting robot ===")
    robot = RebotArm(
        config_path=robot_cfg.get("config_path"),
        urdf_path=robot_cfg.get("urdf_path"),
        repo_root=robot_cfg.get("repo_root"),
    )
    robot.connect(enable=True)
    robot.init_gripper()

    print("[Robot] Moving to observation pose...")
    _move_ready(robot, ready_cfg)

    cam_type = str(cfg.get("camera", {}).get("type", "")).lower()
    T_hand_eye, hand_eye_mode = load_hand_eye(PROJECT_ROOT, cam_type)
    if T_hand_eye is None or hand_eye_mode != "eye_in_hand":
        print("[WARN] Hand-eye calibration unavailable or not eye_in_hand. Execution disabled.")
        T_hand_eye = None

    print(f"=== Camera: {cfg.get('camera', {}).get('type')} ===")
    cam = make_camera(cfg)
    cam.open()
    cam.warm_up(15)
    K = cam.K.astype(np.float32)

    print(f"=== Loading YOLO: {args.model} ===")
    model, yolo_opts = load_yolo(cfg, project_root=PROJECT_ROOT)

    window_name = "BallBoxObstacle — Agentic Pick Place"
    clean_window_name = "Live RGB Clean"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE | cv2.WINDOW_GUI_NORMAL)
    cv2.namedWindow(clean_window_name, cv2.WINDOW_AUTOSIZE | cv2.WINDOW_GUI_NORMAL)

    last_results: list[Any] = []
    last_grasps: list[GraspPose] = []
    last_dets: list[dict[str, Any]] = []
    last_blocked = False
    frozen = False
    last_display: Optional[np.ndarray] = None

    frame_index = 0
    fps_counter = 0
    fps_timer = time.perf_counter()
    fps_value = 0.0

    cycle_busy = threading.Event()
    cycle_thread: Optional[threading.Thread] = None

    try:
        while True:
            color_bgr, depth_mm = cam.get_frame()
            if color_bgr is None or depth_mm is None:
                continue

            cv2.imshow(clean_window_name, color_bgr)

            frame_index += 1
            fps_counter += 1
            now = time.perf_counter()
            if now - fps_timer >= 1.0:
                fps_value = fps_counter / (now - fps_timer)
                fps_counter = 0
                fps_timer = now

            if not frozen and (frame_index % infer_every == 0 or not last_results):
                last_results, last_grasps, last_dets, last_blocked, _info = _detect_scene(
                    model,
                    yolo_opts,
                    color_bgr,
                    depth_mm,
                    K,
                    depth_quantile,
                )

            best_live = (
                _select_closest_grasp_by_role(last_grasps, "obstacle")
                if last_blocked
                else _select_closest_grasp_by_role(last_grasps, "ball")
            )
            if best_live is None:
                best_live = _select_fallback_grasp(last_grasps)

            busy_text = "MOVING" if cycle_busy.is_set() else "READY"
            status = f"{busy_text} {fps_value:.1f} fps | A run | R resume | Q stop"

            if frozen and last_display is not None:
                display = last_display.copy()
                cv2.putText(display, "[FROZEN/SNAPSHOT]", (10, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)
            else:
                display = _render_display(color_bgr, last_grasps, best_live, last_dets, last_blocked, status)

            cv2.imshow(window_name, display)
            key = cv2.waitKey(1) & 0xFF

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
            if cv2.getWindowProperty(clean_window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

            if key in (ord("q"), ord("Q"), 27):
                print("[EMERGENCY] Q/ESC pressed. Requesting stop.")
                EMERGENCY_STOP.set()
                frozen = False
                last_display = None
                if cycle_busy.is_set():
                    print("[EMERGENCY] Robot cycle is running. It will abort at the next safety checkpoint.")
                    continue
                print("[Key] Quit requested.")
                break

            if key in (ord("r"), ord("R")):
                if cycle_busy.is_set():
                    print("[R] Cannot resume while robot cycle is running. Press Q/ESC for emergency stop.")
                    continue
                EMERGENCY_STOP.clear()
                frozen = False
                last_display = None
                print("[R] Resume live preview, emergency flag cleared.")
                continue

            if key in (ord("a"), ord("A")):
                if cycle_busy.is_set():
                    print("[A] Cycle already running.")
                    continue

                if T_hand_eye is None:
                    print("[A] Cannot execute: hand-eye calibration unavailable.")
                    continue

                EMERGENCY_STOP.clear()
                print("\n[A] Starting one full ball/box/obstacle cycle in background...")

                snap_color, snap_depth = cam.get_frame()
                if snap_color is None or snap_depth is None:
                    print("[A] Snapshot failed")
                    continue

                snap_results, snap_grasps, snap_dets, snap_blocked, _snap_info = _detect_scene(
                    model,
                    yolo_opts,
                    snap_color,
                    snap_depth,
                    K,
                    depth_quantile,
                )

                snap_best = (
                    _select_closest_grasp_by_role(snap_grasps, "obstacle")
                    if snap_blocked
                    else _select_closest_grasp_by_role(snap_grasps, "ball")
                )
                snap_display = _render_display(snap_color, snap_grasps, snap_best, snap_dets, snap_blocked, "SNAPSHOT")
                frozen = True
                last_display = snap_display
                cv2.imshow(window_name, snap_display)
                cv2.waitKey(1)

                def _cycle_worker() -> None:
                    nonlocal frozen, last_display
                    cycle_busy.set()
                    try:
                        _run_agentic_cycle(
                            robot=robot,
                            cam=cam,
                            model=model,
                            yolo_opts=yolo_opts,
                            K=K,
                            T_hand_eye=T_hand_eye,
                            ready_cfg=ready_cfg,
                            pregrasp_offset_m=pregrasp_offset_m,
                            depth_quantile=depth_quantile,
                            dry_run=args.dry_run,
                        )
                    except Exception as exc:
                        print(f"[CYCLE ERROR] {exc}")
                    finally:
                        frozen = False
                        last_display = None
                        cycle_busy.clear()
                        print("[CYCLE] Finished or aborted.")

                cycle_thread = threading.Thread(target=_cycle_worker, name="ball-box-obstacle-cycle", daemon=True)
                cycle_thread.start()
                continue

    finally:
        print("\n[Exit] Cleaning up...")
        EMERGENCY_STOP.set()
        try:
            if cycle_thread is not None and cycle_thread.is_alive():
                print("[Exit] Waiting briefly for active cycle to stop...")
                cycle_thread.join(timeout=3.0)
        except Exception as exc:
            print(f"[Exit] cycle thread join error: {exc}")
        try:
            robot.release_gripper()
            robot.safe_home()
        except Exception as exc:
            print(f"[Exit] robot cleanup error: {exc}")

        try:
            robot.disconnect()
        except Exception as exc:
            print(f"[Exit] robot disconnect error: {exc}")

        try:
            cam.close()
        except Exception as exc:
            print(f"[Exit] camera close error: {exc}")

        cv2.destroyAllWindows()
        print("Done.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)
PY
# Normal startup of the entire environment after PC restart

sudo xhost +si:localuser:root
docker start -ai b601_grasp_agent
#############################################
conda activate rebotarm
cd /root/rebot_grasp
#############################################
Docker
└── b601_grasp_agent
    └── Miniforge
        └── rebotarm (Python 3.10)
            ├── PyTorch + CUDA
            ├── Ultralytics / YOLO
            ├── OpenCV
            ├── NumPy
            ├── SciPy
            ├── Pinocchio
            ├── Open3D 0.18
            ├── pyorbbecsdk2
            ├── MotorBridge
            ├── reBotArm_control_py
            └── reBot-DevArm-Grasp

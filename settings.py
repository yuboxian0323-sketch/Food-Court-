"""Configure gameplay, scene-pixel layout, and second-based animation timing.

Operation:
    Declare the existing shared rules, paths, units, and layout constants.
Input:
    This file location for ROOT and fixed gameplay/visual tuning values.
Output:
    Module constants; Session publishes the validated DIFFICULTY_SCHEDULE at startup.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1280, 720 #Game window 
FPS = 60
ANSWER_TIME = 10.0
START_HP = 100
DAMAGE = 20
POINTS = 100
BG = '#111b24'
PANEL = '#1b2a36'
TEXT = '#f4efe4'
MUTED = '#b0bfcb'
ACCENT = '#f1c578'
GREEN = '#91ddb1'
RED = '#f69a91'

# Operation: Answer label dimensions and motion. Courtroom placement is configured
#     below.
# Input: Existing label sizes, nominal speeds, and gameplay constants.
# Output: Shared configuration read by session and target creation.
LABEL_WIDTH = 260
DENSE_LABEL_WIDTH = 260
TARGET_SPEED = (28.0, 36.0)
DENSE_SPEED_FACTOR = 0.65
LABEL_SPEED_MULTIPLIER = 1.0  # 0 keeps answer labels still.
START_CHOICES = 2
MAX_CHOICES = 8
UNLOCK_EVERY = 5
FACE_NORMAL_MIN_HP = 80
FACE_NERVOUS_MIN_HP = 40
MISTAKE_TINT_DURATION = 0.5
MISTAKE_TINT_ALPHA = 80

DIFFICULTY_FILE = ROOT / 'data/difficulty.json'
DIFFICULTY_SCHEDULE = ()  # Filled from the validated JSON when a session starts.

# Operation: Smooth wander controls: radians, pixels, and seconds.
# Input: Angular, distance, and second-based tuning constants.
# Output: Shared steering, avoidance, and bounded-substep settings.
TARGET_PADDING = 7
TARGET_READABILITY_GAP = 12
WANDER_STRENGTH = 0.7
STEERING_CHANGE_INTERVAL = (0.8, 2.3)
STEERING_RESPONSE = 0.65
MAX_TURN_RATE = 2.0
MAX_ACCELERATION = 65.0
WALL_MARGIN = 32.0
WALL_STRENGTH = 20.0
SEPARATION_LOOKAHEAD = 2.0
SEPARATION_STRENGTH = 100.0
MOTION_STEP = 1.0 / 120.0
MOTION_MAX_CATCHUP = 0.1

TURN_RESPONSE = 0.15
MAX_ANGULAR_ACCELERATION = 5.0
STEERING_PLAN_INTERVAL = 0.06
STEERING_PREDICTION_STEP = 0.15
STEERING_PREDICTION_STEPS = 12

WANDER_TRACKING = 3.0
TURN_INERTIA = 0.5

# Operation: Fine fractional coverage keeps slow targets smooth on software surfaces.
# Input: Raster and subpixel scale constants.
# Output: Cached upright rendering with fractional coverage; motion settings are
#     unchanged.
TARGET_SUBPIXEL_SCALE = 32
TARGET_RASTER_SCALE = 4

TARGET_SPAWN_GAP = 24

VELOCITY_RESPONSE = 0.3
SEPARATION_HORIZON = 0.8
SEPARATION_SOLVER_ITERATIONS = 48

SEPARATION_FACE_HYSTERESIS = 24.0

ESCAPE_DELAY = 0.25

# Operation: Courtroom composition and foreground occlusion, in the 1280x720 scene.
# Input: Scene-pixel asset paths, midbottom anchors, and layer rectangles.
# Output: Shared layout used by the courtroom compositor.
COURTROOM_ASSET = ROOT / 'assets/Background.png'
KNIFE_ASSET = ROOT / 'assets/Knife_SpriteSheet.png'
BOARD_ASSET = ROOT / 'assets/plank-chopping-board-cartoon-illustration-vector.jpg'
KNIFE_ANCHOR = (240, 518)
KNIFE_WIDTH = 380
TOMATO_ANCHOR = (1050, 520)
TOMATO_WIDTH = 220
CHEF_ANCHOR = (640, 598)
CHEF_PORTRAIT_SIZE = (380, 440)
CENTRAL_BENCH_FOREGROUND = (330, 424, 620, 162)
FRONT_DESK_FOREGROUND = (0, 608, 1280, 112)
HUD = (28, 16, 1224, 46)
DIALOGUE = (100, 550, 1080, 120)
BOARD_RECT = (280, 100, 720, 600)
# Operation: Safe wood only: below the rotated handle and inset from curved outer edges.
# Input: Rotated board silhouette, handle location, and curved borders.
# Output: Shared LABEL_REGION excluding non-wood areas for complete label rectangles.
LABEL_REGION = (326, 258, 628, 390)
ACTION = (540, 654, 200, 48)
BOARD_ENTER_DURATION = 0.35
BOARD_EXIT_DURATION = 0.25
BOARD_SLIDE_DISTANCE = 580
BANNER_IN_DURATION = 0.20
BANNER_HOLD_DURATION = 0.65
BANNER_OUT_DURATION = 0.25
# Operation: Preserve the public correct-effect setting with the new shared ribbon
#     duration.
# Input: Shared entrance, hold, and exit durations in seconds.
# Output: OBJECTION_DURATION remains a public alias for their total.
OBJECTION_DURATION = BANNER_IN_DURATION + BANNER_HOLD_DURATION + BANNER_OUT_DURATION
BANNER_HEIGHT = 132
BANNER_CENTER_Y = 360
WRONG_BANNER_TEXT = 'INCORRECT!'
TIMEOUT_BANNER_TEXT = "TIME'S UP!"

"""
pcfg.py — shared configuration for the protocell UE 5.8 pipeline.

Imported by the stage scripts. Keeps paths, asset names, render settings, and
the reference-look knobs in one place. Nothing here touches the `unreal`
module, so it is safe to import outside the editor (e.g. for a dry lint).
"""

import os

# --- filesystem ------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))

HEIGHT_PNG = os.environ.get("UE_HEIGHT_PNG", os.path.join(_HERE, "protocell_height.png"))
HEIGHT_SEQ_DIR = os.environ.get("UE_HEIGHT_SEQ_DIR", os.path.join(_HERE, "seq"))
# the TRUE 3D path: OBJ sequence of the cell cleaving (from export_mesh.py)
MESH_SEQ_DIR = os.environ.get("UE_MESH_SEQ_DIR", os.path.join(_HERE, "mesh"))
OUTPUT_DIR = os.environ.get("UE_OUTPUT_DIR", os.path.join(_HERE, "render_out"))

# --- content browser destinations -----------------------------------------
CONTENT_ROOT = "/Game/Protocell"
TEX_PATH = CONTENT_ROOT + "/Textures"
MAT_PATH = CONTENT_ROOT + "/Materials"
MESH_PATH = CONTENT_ROOT + "/Meshes"
SEQ_PATH = CONTENT_ROOT + "/Sequences"
LEVEL_PATH = CONTENT_ROOT + "/Maps"
LEVEL_NAME = "L_Protocell"

# asset names
TEX_HEIGHT = "T_ProtocellHeight"
TEX_SEQ_PREFIX = "T_ProtocellHeight_"
MAT_PROTOCELL = "M_Protocell"                  # translucent membrane material
MAT_INST = "MI_Protocell"
MAT_MASK = "M_MicroscopeMask"                  # circular objective + scan post material
MESH_PLANE = "SM_ProtocellPlane"               # (legacy heightfield path)
MESH_SEQ_PREFIX = "SM_ProtoCleave_"            # mesh flipbook -> _0000 ...
SEQ_HERO = "LS_ProtocellHero"

# --- render settings (vertical hero) ---------------------------------------
RES_X = int(os.environ.get("UE_RES_X", "1080"))
RES_Y = int(os.environ.get("UE_RES_Y", "1920"))
FPS = int(os.environ.get("UE_FPS", "24"))
DURATION_SECONDS = float(os.environ.get("UE_DURATION", "3.0"))
FRAME_COUNT = int(round(FPS * DURATION_SECONDS))

# legacy heightfield-plane settings
PLANE_SUBDIV = int(os.environ.get("UE_PLANE_SUBDIV", "512"))
PLANE_SIZE_CM = float(os.environ.get("UE_PLANE_SIZE", "400.0"))
DISPLACE_CM = float(os.environ.get("UE_DISPLACE", "22.0"))

SEQ_FRAME_COUNT = int(os.environ.get("UE_SEQ_FRAMES", "72"))

# --- reference-look knobs (the dividing-cell hero) -------------------------
BG_CELL_COUNT = int(os.environ.get("UE_BG_CELLS", "9"))
USE_MICROSCOPE_MASK = os.environ.get("UE_MASK", "1") != "0"
RIM_COLOR = (0.0, 0.85, 1.0)      # electric cyan rim (reference-matched)
CORE_COLOR = (0.10, 0.45, 1.0)    # deep blue interior
ACCENT_COLOR = (1.0, 0.15, 0.65)  # occasional magenta-rimmed cell


def banner(stage):
    print("=" * 70)
    print("[protocell] " + stage)
    print("=" * 70)

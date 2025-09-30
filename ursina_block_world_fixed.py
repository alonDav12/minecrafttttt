from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import Audio
import random

# -----------------------------
# Ursina app init
# -----------------------------
app = Ursina()


background_music = Audio("music/After_winter.mp3", autoplay=True, loop=True, volume=0.5)


# -----------------------------
# Safe texture loading helpers
# -----------------------------

def safe_load_texture(path: str):
    try:
        tex = load_texture(path)
        if tex is None:
            print(f"Warning: texture '{path}' not found (returned None). Using fallback.")
            return load_texture('white_cube')
        return tex
    except Exception as e:
        print(f"Warning: failed to load texture '{path}': {e}. Using fallback.")
        return load_texture('white_cube')

# --- Textures dictionary ---
# NOTE: ensure there is an 'assets' folder alongside this .py file with the listed PNG files.
# Missing files will gracefully fall back to a neutral texture instead of crashing.
textures = {
    "grass": safe_load_texture("assets/grass.png"),
    "stone": safe_load_texture("assets/stone.png"),
    "brick": safe_load_texture("assets/brick.png"),
    "wood": safe_load_texture("assets/wood.png"),
    "tnt": safe_load_texture("assets/tnt.png"),
    "DiamondBlock": safe_load_texture("assets/DiamondBlock.png"),
    "PumpkinHead": safe_load_texture("assets/PumpkinHead.png"),
    "IronBlock": safe_load_texture("assets/IronBlock.png"),
    "CraftingTable": safe_load_texture("assets/CraftingTable.png"),
    "furnace": safe_load_texture("assets/furnace.png"),
}

# Available block types (order corresponds to hotkeys 1-0)
block_types = [
    "grass", "stone", "brick", "wood", "tnt",
    "DiamondBlock", "PumpkinHead", "IronBlock",
    "CraftingTable", "furnace"
]


def get_texture(block_type: str):
    tex = textures.get(block_type)
    if tex is None:
        print(f"Warning: Texture key '{block_type}' missing; defaulting to 'wood'.")
        tex = textures.get("wood") or load_texture('white_cube')
    return tex

# -----------------------------
# Block class
# -----------------------------
class Block(Button):
    def __init__(self, position=(0, 0, 0), block_type="grass"):
        texture_to_use = get_texture(block_type)
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture_to_use,
            color=color.color(0, 0, random.uniform(0.9, 1)),
            highlight_color=color.lime,
        )
        # Ensure collider so mouse interactions work reliably
        if not getattr(self, 'collider', None):
            self.collider = 'box'
        self.block_type = block_type


# -----------------------------
# World generation
# -----------------------------
# Create a 20x20 grass platform with two layers (y=0 and y=-1)
for z in range(20):
    for y in range(2):
        for x in range(20):
            Block(position=(x, -y, z), block_type="grass")


# -----------------------------
# Player and UI preview
# -----------------------------
player = FirstPersonController(y=5)
Sky()

current_block = 0

selected_preview = Entity(
    parent=camera.ui,
    model='quad',
    texture=get_texture(block_types[current_block]),
    scale=(0.15, 0.15),
    position=(-0.7, -0.4),
    z=-1
)


def update_selected_preview():
    """Update the preview texture of the currently selected block type."""
    selected_preview.texture = get_texture(block_types[current_block])


# -----------------------------
# Save / Load functions (defined BEFORE creating Buttons)
# -----------------------------

def save_world():
    """Save all Block entities to world.txt (x,y,z,block_type per line)."""
    try:
        with open("world.txt", "w", encoding="utf-8") as f:
            for e in scene.entities:
                if isinstance(e, Block):
                    try:
                        x_int = int(round(e.x))
                        y_int = int(round(e.y))
                        z_int = int(round(e.z))
                        f.write(f"{x_int},{y_int},{z_int},{e.block_type}\n")
                    except Exception as inner_e:
                        print(f"Warning: could not save Block at {e.position}. Skipping. Error: {inner_e}")
        print("World saved successfully to world.txt!")
    except Exception as e:
        print(f"CRITICAL ERROR SAVING WORLD: {e}")


def load_world():
    """Load blocks from world.txt, removing existing blocks first."""
    # 1) Destroy existing Block entities to avoid duplicates
    for block in [e for e in scene.entities if isinstance(e, Block)]:
        destroy(block)

    # 2) Load from file
    try:
        with open("world.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    x, y, z, t = line.split(",")
                    Block(position=(int(x), int(y), int(z)), block_type=t)
                except ValueError:
                    print(f"Skipping malformed line in world.txt: {line}")
        print("World loaded successfully from world.txt!")
    except FileNotFoundError:
        print("Error: world.txt not found. Please save a world first (F5).")
    except Exception as e:
        print(f"General error loading world: {e}")


# -----------------------------
# GUI Buttons (now that functions exist)
# -----------------------------
save_button = Button(
    text='Save World (F5)',
    color=color.azure,
    highlight_color=color.cyan,
    scale=(.15, .05),
    position=(-.85, .45),
    parent=camera.ui,
    on_click=save_world
)

load_button = Button(
    text='Load World (F6)',
    color=color.orange,
    highlight_color=color.yellow,
    scale=(.15, .05),
    position=(-.68, .45),
    parent=camera.ui,
    on_click=load_world
)


# -----------------------------
# Unified input handler
# -----------------------------

def input(key):
    global current_block

    # Number keys 1-0 select block types
    if key in ["1","2","3","4","5","6","7","8","9","0"]:
        index = 9 if key == '0' else int(key) - 1
        if 0 <= index < len(block_types):
            current_block = index
            update_selected_preview()

    # Mouse wheel selection
    elif key == 'scroll up':
        current_block = (current_block + 1) % len(block_types)
        update_selected_preview()
    elif key == 'scroll down':
        current_block = (current_block - 1) % len(block_types)
        update_selected_preview()

    # Place block (LMB)
    elif key == 'left mouse down':
        hit = mouse.hovered_entity
        if hit and isinstance(hit, Block):
            new_pos = hit.position + mouse.normal
            Block(position=new_pos, block_type=block_types[current_block])

    # Remove block (RMB)
    elif key == 'right mouse down':
        hit = mouse.hovered_entity
        if hit and isinstance(hit, Block):
            destroy(hit)

    # Save/Load hotkeys
    elif key == 'f5':
        save_world()
    elif key == 'f6':
        load_world()


# -----------------------------
# Run
# -----------------------------
app.run()

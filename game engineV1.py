from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
import random
import pickle  # For saving and loading data
import time

app = Ursina()


# Define the 2D transparent flame texture
flame_texture = 'flame.png'  # Make sure this image is in your assets folder

class FlameParticleSystem(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        self.particles = []
        self.spawn_rate = 0.05  # Time between new particle spawns
        self.last_spawn_time = time.time()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def update(self):
        if time.time() - self.last_spawn_time > self.spawn_rate:
            self.spawn_particle()
            self.last_spawn_time = time.time()

        for particle in self.particles:
            particle.position += particle.velocity * time.dt
            particle.scale *= 0.98
            particle.alpha -= time.dt * 0.5

            if particle.alpha <= 0:
                self.particles.remove(particle)
                destroy(particle)

    def spawn_particle(self):
        particle = Entity(
            model='quad',
            texture=flame_texture,
            scale=0.2,
            position=self.position + Vec3(random.uniform(-0.1, 0.1), 0, random.uniform(-0.1, 0.1)),
            rotation=(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)),
            velocity=Vec3(0, random.uniform(0.5, 1), 0),
            color=color.orange,
        )
        particle.alpha = 1
        self.particles.append(particle)

# Skybox
sky = Sky()

# Lighting
directional_light = DirectionalLight(shadows=True)
directional_light.look_at(Vec3(1, -1, -1))
ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 0.5))

# Set the sky color
camera.background_color = color.rgb(178, 216, 230)  # Light blue sky color

# Create a mid-poly train with a collider, using dirt texture and repeat the texture
train_texture = load_texture('dirt.png')
train = Entity(model='cube', scale=(500, 10, 500), texture=train_texture, collider='box')

# Repeat the texture on the cube
train.texture_scale = (train.scale[0], train.scale[2])  # Repeat based on cube's size

# Add a glowing blue cube in the middle of the train
blue_cube = Entity(
    model='cube',
    color=color.cyan,
    scale=(3, 3, 3),
    position=(0, 6, 0),  # Positioned slightly above the train surface
    glow=3  # Enable glow for the cube
)

# Set up the default Ursina editor camera
editor_camera = EditorCamera()

# Button data for placing models
models_data = {
    'box': ('box.obj', 'box.png'),
    'sand': ('sand.obj', 'sand.png'),
    'trunk': ('trunk.obj', 'trunk.png'),
    'leaf': ('leaf.obj', 'leaf.png'),
    'glass': ('glass.obj', 'glass.png'),
    'brick': ('brick.obj', 'brick.png'),
    'flame': (None, flame_texture)  # Use None for model and add flame texture
}


selected_object = None  # Keep track of selected object
buttons = []  # List to store buttons
object_placed = False  # To track whether the object is placed
placed_objects = []  # List to store placed objects

# Function to check if the mouse is over a button
def mouse_over_button():
    return any([b.hovered for b in buttons])

# Function to snap object to grid based on position and grid size
def snap_to_grid(position, grid_size=1):
    x = round(position[0] / grid_size) * grid_size
    z = round(position[2] / grid_size) * grid_size
    return Vec3(x, position[1], z)

def place_object():
    global object_placed

    if mouse_over_button():
        return

    if selected_object and not object_placed:
        hit_info = mouse.hovered_entity

        if hit_info in placed_objects or hit_info == train:
            model, texture = models_data[selected_object]

            grid_position = snap_to_grid(mouse.world_point)

            if hit_info != train:
                grid_position.y = hit_info.world_y + hit_info.scale_y + 0.23

            if selected_object == 'flame':
                placed_object = FlameParticleSystem(
                    position=grid_position + Vec3(0, 0.8, 0),
                    scale=1,  # Adjust scale if necessary
                    collider='box'
                )
            else:
                placed_object = Entity(
                    model=model,
                    texture=texture,
                    position=grid_position + Vec3(0, 0.8, 0),
                    scale=1,
                    collider='box'
                )

            placed_objects.append(placed_object)
            print(f'Placed {selected_object} at {grid_position}')
            object_placed = True


# Function to select object when a button is clicked
def select_object(object_name):
    global selected_object, object_placed
    if object_name == 'null':
        selected_object = None
    else:
        selected_object = object_name
        object_placed = False  # Reset the placement state when a new object is selected
    print(f'Selected object: {object_name}' if selected_object else 'Deselected object')

# Create buttons
button_names = ['box', 'sand', 'trunk', 'leaf', 'glass', 'brick', 'flame', 'null']  # Add 'flame' to the list
for i, name in enumerate(button_names):
    button = Button(
        text=name.capitalize(),
        color=color.gray,
        scale=(0.2, 0.1),
        position=(-0.85, -0.45 + i * 0.12),  # Vertical arrangement of buttons
        parent=camera.ui,
        on_click=lambda n=name: select_object(n)  # Set the selected object
    )
    buttons.append(button)


# Save function
def save_map():
    with open('map.dbo', 'wb') as file:
        data = []
        for obj in placed_objects:

            
            if isinstance(obj, FlameParticleSystem):
                obj_type = 'flameparticlesystem'
            else:
                obj_type = None
                for key, (model, texture) in models_data.items():
                    if obj.model.name == model:
                        obj_type = key
                        break

                if obj_type is None:
                    print(f"Warning: Could not find obj_type for {obj}. Skipping.")
                    continue

            # Add sound settings to the saved data
            sound_file = getattr(obj, 'sound_file', None)
            play_on_awake = getattr(obj, 'play_on_awake', False)
            loop = getattr(obj, 'loop', False)

            print(f"Saving sound: {sound_file}, Play on Awake: {play_on_awake}, Loop: {loop}")

            # Save object data with sound attributes
            data.append((obj_type, obj.position, obj.rotation, obj.color, sound_file, play_on_awake, loop))
        pickle.dump(data, file)
    print("Map saved!")



# Load function
def load_map():
    global placed_objects

    for obj in placed_objects:
        destroy(obj)
    placed_objects.clear()

    with open('map.dbo', 'rb') as file:
        data = pickle.load(file)

        for obj_type, position, rotation, color_data, sound_file, play_on_awake, loop in data:
            if obj_type == 'flameparticlesystem':
                placed_object = FlameParticleSystem(
                    position=position,
                    rotation=rotation,
                    color=color_data
                )
            elif obj_type in models_data:
                model, texture = models_data[obj_type]
                placed_object = Entity(
                    model=model,
                    texture=texture,
                    position=position,
                    rotation=rotation,
                    scale=1,
                    collider='box',
                    color=color_data
                )
            else:
                print(f"Warning: Unknown object type '{obj_type}'. Using default model and texture.")
                placed_object = Entity(
                    model='cube',
                    texture='white_cube',
                    position=position,
                    rotation=rotation,
                    scale=1,
                    collider='box',
                    color=color_data
                )

            # Attach sound settings
            placed_object.sound_file = sound_file
            placed_object.play_on_awake = play_on_awake
            placed_object.loop = loop

            if sound_file:
                placed_object.audio = Audio(sound_file, autoplay=play_on_awake, loop=loop)

            placed_objects.append(placed_object)
    print("Map loaded!")




# Create save and load buttons
save_button = Button(
    text='Save',
    color=color.gray,
    scale=(0.1, 0.05),  # Half the original size
    position=(-0.05, 0.45),  # Adjust position to place it next to the load button
    parent=camera.ui,
    on_click=save_map
)

load_button = Button(
    text='Load',
    color=color.gray,
    scale=(0.1, 0.05),  # Half the original size
    position=(0.15, 0.45),  # Place next to the save button
    parent=camera.ui,
    on_click=load_map
)

# Generate fewer clouds, but spread across a larger area
cloud_model = 'cloud.obj'
for _ in range(40):  # Adjust the number of clouds (less mass)
    cloud = Entity(
        model=cloud_model,
        scale=random.uniform(2, 5),  # Reduced mass by decreasing cloud scale
        y=random.uniform(95, 120),  # Random height for sky clouds
        x=random.uniform(-350, 350),  # Larger horizontal range for wider spread
        z=random.uniform(-350, 350),  # Larger depth range to cover a larger sky
        rotation_y=random.uniform(0, 360),  # Random rotation for cloud orientation
        color=color.white,  # White material since it's textureless
    )

# Define the UI panel and fields for editing object properties
property_ui = None
name_field = None
position_fields = None
rotation_fields = None
selected_entity = None  # Keep track of the currently selected entity for editing
material_ui = None  # To keep track of the material UI window
gizmo_x = None
gizmo_y = None
gizmo_z = None
is_dragging = False
current_axis = None
drag_start_position = None
sound_window = None



def destroy_property_ui():
    """Function to destroy the current property UI if it exists."""
    global property_ui
    if property_ui:
        destroy(property_ui)
        property_ui = None
    setup_gizmos_for_selected_object(None)
    destroy_material_ui()

def setup_gizmos_for_selected_object(selected_object):
    global gizmo_x, gizmo_y, gizmo_z

    # Destroy previous gizmos if they exist
    if gizmo_x:
        destroy(gizmo_x)
    if gizmo_y:
        destroy(gizmo_y)
    if gizmo_z:
        destroy(gizmo_z)

    if selected_object and property_ui:
        # Create the gizmos for each axis
        gizmo_x = Entity(model='gizmos.obj', color=color.red, scale=0.5, collider='gizmos.obj', parent=selected_object, rotation=Vec3(0, 0, -90))  # X-axis
        gizmo_y = Entity(model='gizmos.obj', color=color.green, scale=0.5, collider='gizmos.obj', parent=selected_object)  # Y-axis
        gizmo_z = Entity(model='gizmos.obj', color=color.blue, scale=0.5, collider='gizmos.obj', parent=selected_object, rotation=Vec3(90, 0, 0))  # Z-axis

        # Update gizmo click handling to use raycasting
        gizmo_x.on_mouse_drag = lambda: move_gizmo(gizmo_x, 'x')
        gizmo_y.on_mouse_drag = lambda: move_gizmo(gizmo_y, 'y')
        gizmo_z.on_mouse_drag = lambda: move_gizmo(gizmo_z, 'z')

    else:
        # Deactivate gizmos if no object is selected
        if gizmo_x:
            destroy(gizmo_x)
        if gizmo_y:
            destroy(gizmo_y)
        if gizmo_z:
            destroy(gizmo_z)
        is_dragging = False
        current_axis = None
        drag_start_position = None


def move_gizmo(axis):
    global is_dragging, current_axis, drag_start_position, selected_entity

    if not is_dragging:
        is_dragging = True
        current_axis = axis
        drag_start_position = selected_entity.position

    # Calculate the movement based on mouse position
    mouse_world_position = mouse.world_point
    if mouse_world_position:
        movement = mouse_world_position
        if axis == 'x':
            selected_entity.x -= 0.25
        elif axis == 'y':
            selected_entity.y += 0.25
        elif axis == 'z':
            selected_entity.z += 0.25



def create_property_ui(entity):
    """Function to create a property UI for the given entity."""
    global property_ui, name_field, position_fields, rotation_fields, y_rotation_slider, selected_entity

    # Destroy the previous UI if it exists
    destroy_property_ui()

    selected_entity = entity

    # Create a transparent UI background
    property_ui = Entity(parent=camera.ui, model='quad', scale=(0.4, 0.6), position=(0.7, 0), color=color.gray)

    image_entity11 = Entity(parent=property_ui, model='quad', texture='properties.png', scale=(1, 0.06), position=(0, 0.5), z=-0.2)

    # Display the object's name
    name_field = Text(f'Object Name: {entity.model.name}' if not isinstance(entity, FlameParticleSystem) else 'Object Name: Flame', parent=property_ui, position=(-0.1, 0.35), scale=2, origin=(0, 0), z=-0.1)

    # Rotation fields
    Text('Rotation:', parent=property_ui, position=(-0.35, 0.25), scale=1, origin=(0, 0), z=-0.1)
    Text('X:', parent=property_ui, position=(-0.35, 0.2), scale=1, origin=(0, 0), z=-0.1)
    Text('Y:', parent=property_ui, position=(-0.35, 0.15), scale=1, origin=(0, 0), z=-0.1)
    Text('Z:', parent=property_ui, position=(-0.35, 0.1), scale=1, origin=(0, 0), z=-0.1)

    rotation_fields = [
        InputField(default_value=str(entity.rotation.x), parent=property_ui, position=(-0.15, 0.2), scale=(0.2, 0.1), submit=update_property_values, z=-0.1),
        InputField(default_value=str(entity.rotation.y), parent=property_ui, position=(-0.15, 0.15), scale=(0.2, 0.1), submit=update_property_values, z=-0.1),
        InputField(default_value=str(entity.rotation.z), parent=property_ui, position=(-0.15, 0.1), scale=(0.2, 0.1), submit=update_property_values, z=-0.1)
    ]

    # Position fields
    Text('Position:', parent=property_ui, position=(-0.35, -0.0), scale=1, origin=(0, 0), z=-0.1)
    Text('X:', parent=property_ui, position=(-0.35, -0.1), scale=1, origin=(0, 0), z=-0.1)
    Text('Y:', parent=property_ui, position=(-0.35, -0.15), scale=1, origin=(0, 0), z=-0.1)
    Text('Z:', parent=property_ui, position=(-0.35, -0.20), scale=1, origin=(0, 0), z=-0.1)

    position_fields = [
        InputField(default_value=str(entity.position.x), parent=property_ui, position=(-0.15, -0.1), scale=(0.2, 0.1), submit=update_property_values, z=-0.1),
        InputField(default_value=str(entity.position.y), parent=property_ui, position=(-0.15, -0.15), scale=(0.2, 0.1), submit=update_property_values, z=-0.1),
        InputField(default_value=str(entity.position.z), parent=property_ui, position=(-0.15, -0.20), scale=(0.2, 0.1), submit=update_property_values, z=-0.1)
    ]

    # Y Rotation Slider
    Text('Y Rotation:', parent=property_ui, position=(-0.35, -0.30), scale=1, origin=(0, 0), z=-0.1)
    y_rotation_slider = Slider(min=0, max=360, default=entity.rotation.y, parent=property_ui, position=(-0.15, -0.30), scale=(0.8, 0.4), step=10, dynamic=True, z=-0.1)
    y_rotation_slider.on_value_changed = lambda: update_y_rotation(entity)

    # Delete button
    Button(text='Delete', color=color.red, scale=(0.2, 0.08), position=(-0.15, -0.40), parent=property_ui, on_click=lambda: delete_selected_entity(entity), z=-0.1)
    setup_gizmos_for_selected_object(selected_entity)

def update_y_rotation(entity):
    """Update the Y rotation of the selected entity based on the slider value."""
    global selected_entity

    if selected_entity:
        # Update the rotation of the entity
        selected_entity.rotation_y = y_rotation_slider.value

        # Update the position fields to reflect the new values
        rotation_fields[1].text = str(selected_entity.rotation_y)
        print(f'Updated Y rotation to: {selected_entity.rotation_y}')

def destroy_material_ui():
    """Destroy the current material UI if it exists."""
    global material_ui
    if material_ui:
        destroy(material_ui)
        material_ui = None

def create_material_ui(entity):
    global material_ui, r_slider, g_slider, b_slider, a_slider, selected_entity

    destroy_material_ui()

    selected_entity = entity

    material_ui = Entity(parent=camera.ui, model='quad', scale=(0.3, 0.25), position=(0.75, -0.4), color=color.gray)

    image_entity = Entity(parent=material_ui, model='quad', texture='material.png', scale=(1.4, 0.14), position=(0.2, 0.38), z=-0.1)

    Text('R:', parent=material_ui, position=(-0.4, 0.1), scale=3, z=-0.1)
    Text('G:', parent=material_ui, position=(-0.4, 0), scale=3, z=-0.1)
    Text('B:', parent=material_ui, position=(-0.4, -0.1), scale=3, z=-0.1)
    Text('A:', parent=material_ui, position=(-0.4, -0.2), scale=3, z=-0.1)

    if isinstance(selected_entity, FlameParticleSystem):
        r_slider = Slider(min=0, max=255, default=selected_entity.color.r*255, parent=material_ui, position=(-0.2, 0.1), step=1, dynamic=True, z=-0.1)
        g_slider = Slider(min=0, max=255, default=selected_entity.color.g*255, parent=material_ui, position=(-0.2, 0), step=1, dynamic=True, z=-0.1)
        b_slider = Slider(min=0, max=255, default=selected_entity.color.b*255, parent=material_ui, position=(-0.2, -0.1), step=1, dynamic=True, z=-0.1)
        a_slider = Slider(min=0, max=255, default=selected_entity.color.a*255, parent=material_ui, position=(-0.2, -0.2), step=1, dynamic=True, z=-0.1)

        r_slider.on_value_changed = update_material_values
        g_slider.on_value_changed = update_material_values
        b_slider.on_value_changed = update_material_values
        a_slider.on_value_changed = update_material_values
    else:
        r_slider = Slider(min=0, max=255, default=selected_entity.color.r*255, parent=material_ui, position=(-0.2, 0.1), step=1, dynamic=True, z=-0.1)
        g_slider = Slider(min=0, max=255, default=selected_entity.color.g*255, parent=material_ui, position=(-0.2, 0), step=1, dynamic=True, z=-0.1)
        b_slider = Slider(min=0, max=255, default=selected_entity.color.b*255, parent=material_ui, position=(-0.2, -0.1), step=1, dynamic=True, z=-0.1)
        a_slider = Slider(min=0, max=255, default=selected_entity.color.a*255, parent=material_ui, position=(-0.2, -0.2), step=1, dynamic=True, z=-0.1)

        r_slider.on_value_changed = update_material_values
        g_slider.on_value_changed = update_material_values
        b_slider.on_value_changed = update_material_values
        a_slider.on_value_changed = update_material_values


def update_material_values():
    """Update the RGB values of the selected entity in real-time."""
    global selected_entity

    if selected_entity:
        r = r_slider.value / 255
        g = g_slider.value / 255
        b = b_slider.value / 255
        a = a_slider.value / 255

        selected_entity.color = color.rgba(r_slider.value, g_slider.value, b_slider.value, a_slider.value)
        print(f'Updated material: R={r}, G={g}, B={b}, A={a}')


def update_property_values():
    """Update the properties of the selected entity based on the input fields."""
    global selected_entity

    if selected_entity:
        # Update rotation values
        selected_entity.rotation = Vec3(
            float(rotation_fields[0].text),
            float(rotation_fields[1].text),
            float(rotation_fields[2].text)
        )
        # Update position values
        selected_entity.position = Vec3(
            float(position_fields[0].text),
            float(position_fields[1].text),
            float(position_fields[2].text)
        )

def create_sound_window(entity):
    global sound_window

    destroy_sound_window()
    """Function to create a sound options window for attaching and playing sound on objects."""
    sound_window = Entity(parent=camera.ui, model='quad', scale=(0.3, 0.2), position=(0.7, 0.383), color=color.gray, z=-0.1)

    image_entity = Entity(parent=sound_window, model='quad', texture='volume.png', scale=(1, 0.18), position=(0, 0.44), z=-0.1)

    sound_window.bg = Entity(parent=sound_window, model='quad', scale=sound_window.scale * 1.05, position=(0, 0, 0.01), color=color.black33)

    # Function to toggle and print button state (works for both buttons)
    def toggle_button(button, attribute_name):
        # Toggle the entity attribute and button text
        current_value = getattr(entity, attribute_name, False)
        new_value = not current_value
        setattr(entity, attribute_name, new_value)
        button.text = f"{attribute_name.replace('_', ' ').title()}: {new_value}"
        print(f"{button.text}: {new_value}")  # Print the current state

    # Button for 'Play on Awake'
    play_on_awake_button = Button(text=f"Play on Awake: {entity.play_on_awake if hasattr(entity, 'play_on_awake') else False}", parent=sound_window,
                                  position=(-0.25, 0.25), scale=(0.48, 0.1), color=color.dark_gray, z=-0.1)
    play_on_awake_button.text_entity.scale *= 0.6

    # Button for 'Loop'
    loop_button = Button(text=f"Loop: {entity.loop if hasattr(entity, 'loop') else False}", parent=sound_window,
                         position=(0.3, 0.25), scale=(0.3, 0.1), color=color.dark_gray, z=-0.1)
    loop_button.text_entity.scale *= 0.6

    # Input handling to toggle buttons on click
    play_on_awake_button.on_click = lambda: toggle_button(play_on_awake_button, 'play_on_awake')
    loop_button.on_click = lambda: toggle_button(loop_button, 'loop')

    # Text label for specifying the sound file name
    sound_file_label = Text('Sound File:', parent=sound_window, position=(0.03, -0.19), scale=(0.35, 0.14), origin=(0, 0), z=-0.1, color=color.white)

    # Input field for sound file name with consistent style
    sound_file_input = InputField(parent=sound_window, position=(0.08, -0.19), scale=(0.7, 0.14), color=color.black,
                                  default_value=entity.sound_file if hasattr(entity, 'sound_file') else "test.mp3", z=-0.1)

    # Add border and shadow to the input field
    sound_file_input.bg = Entity(parent=sound_file_input, model='quad', scale=sound_file_input.scale * 1.02, color=color.black33, z=0.01)

    # Function to handle attaching the sound to the object
    def attach_sound_to_object():
        entity.sound_file = sound_file_input.text
        entity.play_on_awake = entity.play_on_awake if hasattr(entity, 'play_on_awake') else False
        entity.loop = entity.loop if hasattr(entity, 'loop') else False

        # Attach the sound to the entity
        if entity.sound_file:
            entity.audio = Audio(entity.sound_file, autoplay=entity.play_on_awake, loop=entity.loop)

    # "Confirm" button to apply sound settings and attach sound to the object
    confirm_button = Button(text='Confirm', parent=sound_window, scale=(0.2, 0.15), position=(-0.38, -0.19), color=color.dark_gray, z=-0.1)
    confirm_button.text_entity.scale *= 0.6

    # When the button is clicked, attach the sound to the object and destroy the window
    def on_confirm():
        attach_sound_to_object()  # Call the function to attach the sound

    # Set up the button's action
    confirm_button.on_click = on_confirm

    return sound_window




def destroy_sound_window():
    """Destroy the current material UI if it exists."""
    global sound_window
    if sound_window:
        destroy(sound_window)
        sound_window = None

def delete_selected_entity(entity):
    """Function to delete the selected entity using its name."""
    global placed_objects
    placed_objects = [obj for obj in placed_objects if obj != entity]
    destroy(entity)
    destroy_property_ui()
    destroy_sound_window()
    print(f"Deleted {entity.model.name}")



def update():
    global object_placed
    global selected_object
    global is_dragging
    global current_axis


    # Prevent placing multiple objects when holding the mouse button
    if mouse.left and not object_placed:
        place_object()

    if not mouse.left:
        object_placed = False  # Reset the flag when the mouse is released

    # Right-click detection for showing/hiding the properties and material UI
    if mouse.right:
        hit_info = mouse.hovered_entity
        if hit_info in placed_objects:
            create_property_ui(hit_info)
            create_material_ui(hit_info)  # Show the RGB control window
            create_sound_window(hit_info)
        elif hit_info == train:
            destroy_property_ui()
            destroy_material_ui()
            destroy_sound_window()

    # Handle gizmo dragging
    if is_dragging and selected_entity:
        if mouse.left:
            move_gizmo(current_axis)
        else:
            is_dragging = False
            current_axis = None

    # Check for gizmo selection
    if mouse.left and not is_dragging:
        hit_info = mouse.hovered_entity
        if hit_info in [gizmo_x, gizmo_y, gizmo_z]:
            if hit_info == gizmo_x:
                current_axis = 'x'
            elif hit_info == gizmo_y:
                current_axis = 'y'
            elif hit_info == gizmo_z:
                current_axis = 'z'
            is_dragging = True
        


    # Reset dragging state when the mouse button is released
    if not held_keys['left mouse']:
        is_dragging = False


app.run()

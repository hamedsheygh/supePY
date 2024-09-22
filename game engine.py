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
    'flame': (None, flame_texture)  # Use `None` for model and add flame texture
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
        color=color.azure,
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
            # Check if the object is a custom type or an entity
            if isinstance(obj, FlameParticleSystem):
                obj_type = 'flameparticlesystem'
            else:
                # Use the object's model name as the obj_type
                obj_type = None
                for key, (model, texture) in models_data.items():
                    if obj.model.name == model:
                        obj_type = key
                        break
                
                if obj_type is None:
                    print(f"Warning: Could not find obj_type for {obj}. Skipping.")
                    continue
            
            # Save the object data
            data.append((obj_type, obj.position, obj.rotation, obj.color))
        pickle.dump(data, file)
    print("Map saved!")



# Load function
def load_map():
    global placed_objects

    # Clear existing objects
    for obj in placed_objects:
        destroy(obj)
    placed_objects.clear()

    with open('map.dbo', 'rb') as file:
        data = pickle.load(file)

        for obj_type, position, rotation, color_data in data:
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
                # Handle unknown object types (like 'entity')
                print(f"Warning: Unknown object type '{obj_type}'. Using default model and texture.")
                placed_object = Entity(
                    model='cube',  # Default model
                    texture='white_cube',  # Default texture
                    position=position,
                    rotation=rotation,
                    scale=1,
                    collider='box',
                    color=color_data
                )
            placed_objects.append(placed_object)
    print("Map loaded!")





# Create save and load buttons
save_button = Button(
    text='Save',
    color=color.azure,
    scale=(0.1, 0.05),  # Half the original size
    position=(-0.05, 0.45),  # Adjust position to place it next to the load button
    parent=camera.ui,
    on_click=save_map
)

load_button = Button(
    text='Load',
    color=color.azure,
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


def destroy_property_ui():
    """Function to destroy the current property UI if it exists."""
    global property_ui
    if property_ui:
        destroy(property_ui)
        property_ui = None

def create_property_ui(entity):
    """Function to create a property UI for the given entity."""
    global property_ui, name_field, position_fields, rotation_fields, y_rotation_slider, selected_entity

    # Destroy the previous UI if it exists
    destroy_property_ui()

    selected_entity = entity

    # Create a transparent UI background
    property_ui = Entity(parent=camera.ui, model='quad', scale=(0.4, 0.6), position=(0.7, 0), color=color.gray)

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
    y_rotation_slider = Slider(min=0, max=360, default=entity.rotation.y, parent=property_ui, position=(-0.15, -0.30), scale=(0.8, 0.4), step=1, dynamic=True, z=-0.1)
    y_rotation_slider.on_value_changed = lambda: update_y_rotation(entity)

    # Delete button
    Button(text='Delete', color=color.red, scale=(0.2, 0.08), position=(-0.15, -0.40), parent=property_ui, on_click=lambda: delete_selected_entity(entity), z=-0.1)


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

def delete_selected_entity(entity):
    """Function to delete the selected entity using its name."""
    global placed_objects
    placed_objects = [obj for obj in placed_objects if obj != entity]
    destroy(entity)
    destroy_property_ui()
    print(f"Deleted {entity.model.name}")

def update():
    global object_placed

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
        elif hit_info == train:
            destroy_property_ui()
            destroy_material_ui()


app.run()

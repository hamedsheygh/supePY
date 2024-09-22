from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import Vec3
import random
import math
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
        direction_to_player = (player.position - self.position).normalized()
        angle_to_player = math.degrees(math.atan2(direction_to_player.x, direction_to_player.z))

        particle = Entity(
            model='quad',
            texture=flame_texture,
            scale=0.2,
            position=self.position + Vec3(random.uniform(-0.1, 0.1), 0, random.uniform(-0.1, 0.1)),
            rotation=(random.uniform(-10, 10), -angle_to_player, random.uniform(-10, 10)),
            velocity=Vec3(0, random.uniform(0.5, 1), 0),
            color=color.orange,
        )
        particle.alpha = 1
        self.particles.append(particle)


models_data = {
    'box': ('box.obj', 'box.png'),
    'sand': ('sand.obj', 'sand.png'),
    'trunk': ('trunk.obj', 'trunk.png'),
    'leaf': ('leaf.obj', 'leaf.png'),
    'glass': ('glass.obj', 'glass.png'),
    'brick': ('brick.obj', 'brick.png'),
    'flame': (None, flame_texture)  # Use None for model and add flame texture
}


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


# Skybox
sky = Sky()

# Lighting
directional_light = DirectionalLight(shadows=True)
directional_light.look_at(Vec3(1, -1, -1))
ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 0.5))

# Set the sky color
camera.background_color = color.rgb(178, 216, 230)  # Light blue sky color

# Crosshair settings
crosshair = Entity(
    parent=camera.ui,  # Attach to the UI, so it stays on screen
    model='quad',  # Simple 2D quad for the crosshair
    texture='crosshair.png',  # Custom crosshair image
    scale=(0.02, 0.02),  # Adjust the size of the crosshair
    position=(0, 0),  # Center of the screen
)

# User profile image
user_profile = Entity(
    parent=camera.ui,  # Attach to the UI, so it stays on screen
    model='quad',  # Simple 2D quad for the image
    texture='General.png',  # Your user profile image
    scale=(0.2, 0.2),  # Adjust the size of the image
    position=(0.789, -0.4)  # Position in the bottom-right corner
)

# Create a mid-poly train with a collider, using dirt texture and repeat the texture
train_texture = load_texture('dirt.png')
train = Entity(model='cube', scale=(500, 10, 500), texture=train_texture, collider='box')

# Repeat the texture on the cube
train.texture_scale = (train.scale[0], train.scale[2])  # Repeat based on cube's size

# Create the player with an FPS controller and place them on top of the train
player = FirstPersonController()
player.position = (0, 10, 0)  # Set player position slightly above the train
player.collider = 'box'  # Ensure the player has a collider
player.health = 5

# Increase player speed by 2x
player.speed *= 2

placed_objects = []  # Initialize the list for placed objects

# Global variable for enemy kill count
enemy_kills = 0

# Bullet settings
bullet_speed = 20
enemy_bullet_speed = 10
player_bullets = []
enemy_bullets = []

# Enemy settings
enemies = []
enemy_count = 5
enemy_speed = 0.5
enemy_shoot_interval = 1  # 1 bullet per second
min_distance = 0.3  # Minimum distance between enemies

# Last time the player shot
last_shoot_time = 0
shoot_delay = 0.3  # Delay between shots in seconds
mouse_held = False  # To track if the mouse was previously held

# Cloud settings
cloud_model = 'cloud.obj'  # 3D cloud model
cloud_objects = []



# Enemy kill counter
kill_counter_text = Text(
    parent=camera.ui,  # Attach to the UI so it stays on screen
    text=f'Enemies Killed: {enemy_kills}',  # Initialize with 0 kills
    color=color.brown,
    scale=1.5,  # Adjust the scale as needed
    position=(0.38, -0.4)  # Position it near the general's picture
)



# Function to create cloud objects
def create_cloud():
    cloud = Entity(
        model=cloud_model,
        scale=random.uniform(2, 5),  # Reduced mass by decreasing cloud scale
        y=random.uniform(95, 120),  # Random height for sky clouds
        x=random.uniform(-350, 350),  # Larger horizontal range for wider spread
        z=random.uniform(-350, 350),  # Larger depth range to cover a larger sky
        rotation_y=random.uniform(0, 360),  # Random rotation for cloud orientation
        color=color.white,  # White material since it's textureless
    )
    cloud_objects.append(cloud)

# Generate fewer clouds, but spread across a larger area
for _ in range(40):  # Adjust the number of clouds (less mass)
    create_cloud()

# Health hearts
hearts = []
for i in range(5):
    heart = Entity(
        parent=camera.ui,
        model='quad',
        texture='heart.png',
        scale=(0.05, 0.05),
        position=(-0.85 + i * 0.1, -0.45),  # Adjust position for each heart
        color=color.white
    )
    hearts.append(heart)

# Function to check if the position is valid for spawning an enemy
def is_valid_position(position):
    for enemy in enemies:
        if distance(enemy.position, position) < min_distance:
            return False
    return True

# Function to spawn an enemy
def spawn_enemy():
    while True:
        angle = random.uniform(0, 360)
        x = math.cos(math.radians(angle)) * 100
        z = math.sin(math.radians(angle)) * 100
        position = Vec3(x, 7, z)  # Place enemies on the surface of the train (height = 7)
        
        if is_valid_position(position):
            enemy = Entity(model='capsule', color=color.red, position=position, scale=1, collider='box')
            enemy.name = 'enemy_' + str(len(enemies) + 1)
            enemy.health = 5  # Each enemy has 5 health points
            enemy.shoot_time = 0
            enemies.append(enemy)
            break

# Load the map using the function from your map editor
load_map()  # Use the exact map load function from your editor

# Spawn enemies
for _ in range(enemy_count):
    spawn_enemy()

# Function to shoot a bullet from the player
def shoot():
    global last_shoot_time
    if time.time() - last_shoot_time >= shoot_delay:  # Ensure delay between shots
        # Calculate shooting direction based on camera's rotation
        shooting_direction = camera.forward

        # Position the bullet based on the player's position and shooting direction
        bullet = Entity(
            model='sphere',
            color=color.orange,
            position=player.position + Vec3(0, 1, 0) + shooting_direction * 2,
            scale=0.2,
            collider='box'
        )
        bullet.name = 'player_bullet_' + str(len(player_bullets) + 1)
        bullet.shooting_direction = shooting_direction
        bullet.shooting_sound = Audio('ak.mp3', loop=False, autoplay=True, position=bullet.position, parent=bullet, volume=0.6)  # Set volume to 0.6 for player bullets
        player_bullets.append(bullet)
        # Create muzzle flash
        muzzle_flash = Entity(
            model='quad',
            texture='muzzle.png',
            position=player.position + Vec3(0, 1.35, 0) + shooting_direction * 2,
            rotation=player.rotation,
            scale=(0.5, 0.5),
        )

        # Destroy the muzzle flash after 0.3 seconds
        destroy(muzzle_flash, delay=0.3)
        last_shoot_time = time.time()

# Function to shoot a bullet from an enemy
def enemy_shoot(enemy):
    bullet = Entity(model='sphere', color=color.yellow, position=enemy.position + Vec3(0.26, 0, 0) + enemy.forward * 2, scale=0.2, collider='box')
    bullet.name = 'enemy_bullet_' + str(len(enemy_bullets) + 1)
    bullet.shooting_direction = (player.position - enemy.position).normalized()
    bullet.shooting_sound = Audio('ak.mp3', loop=False, autoplay=True, position=bullet.position, parent=bullet, volume=0.1)  # Set volume to 0.2 for enemy bullets
    enemy_bullets.append(bullet)

# Create the AK-47 model
gun_model = 'ak47.obj'
gun_texture = 'PolygonApocalypse_Texture_04_A.png'

# Instantiate the AK-47 and set its texture
ak47 = Entity(
    model=gun_model,
    texture=gun_texture,
    scale=(2, 2, 2),  # Adjust scale as needed
    position=player.position,  # Initial position will be updated in the update function
)

# Add this function to handle bullet bouncing upon collision
def bounce_bullet(bullet, normal):
    bounce_direction = bullet.shooting_direction - 2 * bullet.shooting_direction.dot(normal) * normal
    bullet.shooting_direction = bounce_direction.normalized()

# Update AK-47 position and rotation
def update_ak47():
    shooting_direction = camera.forward
    # Position the AK-47 at the player's position, not affected by camera position
    ak47.position = player.position + Vec3(0, 1.4, 0)
    # Update rotation to match the shooting direction (not camera rotation)
    ak47.look_at(ak47.position + shooting_direction)

# Function to handle player health and hearts
def update_health():
    global hearts
    if player.health <= 0:
        print("Player died!")
        player.disable()  # Disable player controls
        for heart in hearts:
            destroy(heart)
        lose_text = Text(text='LOOSE', color=color.red, scale=3, origin=(0, 0), background=True)
    else:
        destroy(hearts[player.health])  # Destroy a heart from right to left

# Update function to move bullets, check collisions, lock enemy positions, and move clouds
def update():
    global mouse_held
    # Player shooting
    if mouse.left and not mouse_held:  # Shoot only on new click, not hold
        shoot()

    mouse_held = mouse.left  # Update the held state

    # Move player bullets
    for bullet in player_bullets[:]:
        bullet.position += bullet.shooting_direction * bullet_speed * time.dt

        # Check collision with the train
        if bullet.intersects(train).hit:
            normal = bullet.intersects(train).world_normal  # Get the normal of the collision surface
            bounce_bullet(bullet, normal)  # Bounce the bullet

        # Check collision with placed objects
        for obj in placed_objects:
            if bullet.intersects(obj).hit:
                normal = bullet.intersects(obj).world_normal  # Get the normal of the collision surface
                bounce_bullet(bullet, normal)  # Bounce the bullet
                break
        
        for enemy in enemies[:]:
            if bullet.intersects(enemy).hit:  # Check collision with enemy
                enemy.health -= 1
                if enemy.health <= 0:
                    print(f"{enemy.name} died!")
                    enemies.remove(enemy)
                    destroy(enemy)
                    # Add this line to increment the kill counter
                    global enemy_kills
                    enemy_kills += 1
                destroy(bullet)
                player_bullets.remove(bullet)
                break  # Exit the loop after handling collision
        if bullet in player_bullets and distance(bullet.position, player.position) > 200:  # Destroy bullet if it travels too far
            destroy(bullet)
            player_bullets.remove(bullet)

    # Move enemy bullets
    for bullet in enemy_bullets[:]:
        bullet.position += bullet.shooting_direction * enemy_bullet_speed * time.dt
        
        if distance(bullet.position, player.position) < 2:  # Check if the bullet hits the player
            player.health -= 1
            print(f"Player hit! Health: {player.health}")
            update_health()
            destroy(bullet)
            enemy_bullets.remove(bullet)

        # Check collision with the train
        if bullet.intersects(train).hit:
            destroy(bullet)
            enemy_bullets.remove(bullet)
            continue  # Skip to next bullet
          
        elif bullet in enemy_bullets and distance(bullet.position, bullet.origin) > 200:  # Destroy bullet if it travels too far
            destroy(bullet)
            enemy_bullets.remove(bullet)

        # Check collision with placed objects
        for obj in placed_objects:
            if bullet.intersects(obj).hit:
                destroy(bullet)
                enemy_bullets.remove(bullet)
                break  # Exit loop after handling collision  

    # Enemy movement, shooting, and position locking
    for enemy in enemies:
        enemy.look_at(player)
        enemy.rotation_x = 0  # Lock X-axis rotation
        enemy.rotation_z = 0  # Lock Z-axis rotation
        enemy.position += enemy.forward * enemy_speed * time.dt

        # Lock Y-axis position at 7 and prevent going underground
        enemy.position = Vec3(enemy.position.x, 7, enemy.position.z)

        # Ensure enemies do not move inside each other
        for other_enemy in enemies:
            if enemy != other_enemy and distance(enemy.position, other_enemy.position) < min_distance:
                direction = (enemy.position - other_enemy.position).normalized()
                enemy.position += direction * enemy_speed * time.dt

        if time.time() - enemy.shoot_time > enemy_shoot_interval:
            enemy_shoot(enemy)
            enemy.shoot_time = time.time()

    # Move clouds slowly across the sky
    for cloud in cloud_objects:
        cloud.x += time.dt * 0.1  # Move clouds slowly to the right
        if cloud.x > 300:  # Wrap around when cloud moves off screen
            cloud.x = -300

    # Update AK-47 position and rotation
    ak47.position = player.position + Vec3(0.26, 1, 0) 
    ak47.rotation = camera.rotation  # Match camera rotation

    update_ak47()

    # Update the kill counter text
    kill_counter_text.text = f'KILL COUNTER: {enemy_kills}'

app.run()

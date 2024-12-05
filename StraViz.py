# This is the Blender script that you must load into a Blender project. You run this to generate the path. 

import bpy
import json 
import mathutils
import math
import importlib
import sys
import os 
import time

t = 1 # Delay seconds for the demo. 


# Get the path to the directory containing the script
script_dir = "path-to-this-directory" 

# Add the directory to sys.path
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Now you can import helpers
import helpers as hp
importlib.reload(hp)

### Global Variables
txt_name = "myRun!"
z_scale = 0.02              # bigger makes it taller. 0.01 is 'real' scale.
#xy_scale = 1.1               # bigger makes it wider
extrusion_base_z = 0        # Calculated at run time
extrusion_base_xy = 0.5     # Bigger makes it wider
obj_max= 300                # The max size (x or y) a run could theoretically be.


run_file = os.path.join(script_dir, "myRun.json")

def main():
    sun_light = bpy.data.lights.new(name="sun", type='SUN')
    sun_object = bpy.data.objects.new(name="sun", object_data=sun_light)
    bpy.context.collection.objects.link(sun_object)

    # First read the file and extract the variables 
    result = process_run_file(run_file, z_scale)
    starting_coordinates = result["starting_coordinates"]
    ttl_distance = result["ttl_distance"]
    points = result["points"]
    hr_widths = result["hr_widths"]
    real_distances = result["real_distances"]
    paces = result["paces"]
    avg_pace = 1 / (sum(paces) / len(paces))
    altitudes = result["altitudes"]
    ttl_gain = calculate_altitude_gain(altitudes)
    extrusion_distance = get_highest_point(points) * -2
    
    # Create a curve for the run  
    curve_data = bpy.data.curves.new(name="RunCurveData", type='CURVE')
    curve_data.dimensions = '3D'  # Set the curve to be 3D
    curve_object = bpy.data.objects.new(name="MyRun", object_data=curve_data)
    bpy.context.scene.collection.objects.link(curve_object) # add it to the scene


    spline = curve_data.splines.new(type='BEZIER') # Spline connects the points
    
    # Add point lights anchored to the curve 
    add_point_lights_with_anchor(curve_object=curve_object, 
                                 points=points, 
                                 paces=paces, 
                                 min_brightness=10, 
                                 max_brightness=100)

    sleep_update(t)
    # Z and Y are switched because of the extrusion thing
    # These are the point locations in the coordinate space
    spline.bezier_points.add(len(points)-1)
    
    curve_object.data.fill_mode = 'FULL'
    sleep_update(t)
    curve_object.data.extrude = extrusion_base_xy
    sleep_update(t)
    curve_object.rotation_euler = (1.57, 0, 0) # Rotate the curve 

    sleep_update(t)
    generate_curve_from_points(spline, points)  # Make the curve
    sleep_update(t)
    set_curve_point_radiuses(spline, hr_widths) # Apply HR to width
    
    sleep_update(t)
    # Set the curve object as the active object
    bpy.context.view_layer.objects.active = curve_object
    sleep_update(t)
    curve_object.select_set(True)
    sleep_update(t)
    bpy.context.object.data.use_fill_caps = True # Make it solid
    sleep_update(t)
    
    # Convert the curve to a mesh
    bpy.ops.object.convert(target='MESH')
    sleep_update(t)
    bpy.ops.object.shade_flat() 
    #curve_object.scale = (xy_scale, 1,  xy_scale)
    sleep_update(t)
    

    # Extrude the mesh
    bpy.ops.object.editmode_toggle()
    sleep_update(t)
    bpy.ops.mesh.select_all(action='SELECT')
    sleep_update(t)
    extrude_mesh(extrusion_distance)
    sleep_update(t)
    bpy.ops.object.editmode_toggle() 
    sleep_update(t)
    # Move the run to the center of the platform.
    adjust_object_position(curve_object)
    sleep_update(t)
    # Log scale the X,Y dimensions to fit in the platform.
    # hp.log_scale_run_object(obj=curve_object, max_size=100)
    #hp.scale_object_xz_non_linear(obj=curve_object, max_size=100, min_size=1, exponent=0.92)
    hp.resize_object(obj=curve_object, obj_max=obj_max, scale_max=100)
    sleep_update(t)
    # Create a cube to remove the bottom extrusion
    boolean_cube = add_boolean_cube()
    sleep_update(t)
    apply_boolean_difference(curve_object, boolean_cube)
    sleep_update(t)
    delete_object_by_name("Boolean_Cube") # Remove the cube after using it
    sleep_update(t)

    
    # Generate the text for the platform: 

    txt_location = (-45.9648, 43.706, 2.5) # curve_object.location.copy()
    
    #txt_location[1] -= 4
    text_obj = create_extruded_text(
    name=txt_name,
    distance=ttl_distance,
    gain=ttl_gain,
    pace=avg_pace,
    extrusion_depth=0.2,
    scale=(4, 4, 4),
    location=txt_location
    )

    bpy.data.objects.remove(sun_object, do_unlink=True) # remove sun

    sleep_update(t)
    hp.assign_text_material(text_obj)
    sleep_update(t)
    platform_obj = add_platform()
    sleep_update(t)
    hp.assign_platform_material(platform_obj)
    sleep_update(t)
    hp.assign_glass_material(obj=curve_object, ior=1.45, roughness=0.01)
    sleep_update(t)

def set_curve_point_radius(curve_object, point_index, new_radius):
    """
    Adjusts the radius of a specific point on a curve.
    
    :param curve_object: The curve object to modify.
    :param point_index: Index of the point whose radius to modify.
    :param new_radius: The new radius value for the point.
    """
    # Access the curve data
    curve_data = curve_object.data
    spline = curve_data.splines[0]  # Assuming a single spline

    # Set the radius of the specified point
    spline.bezier_points[point_index].radius += new_radius
    print(new_radius)
    


def generate_curve_from_points(spline, points):

    # Assign the points' locations
    for i, point in enumerate(points):
        bez_point = spline.bezier_points[i]
        bez_point.co = point  # Set the main control point
        bez_point.handle_left_type = 'AUTO'
        bez_point.handle_right_type = 'AUTO'

def extrude_mesh(distance=extrusion_base_z):
    """
    Extrude the active mesh along the Z-axis by the specified distance.
    Assumes the object is already in edit mode and mesh faces are selected.
    """
    bpy.ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={
            "use_normal_flip": False,
            "use_dissolve_ortho_edges": False,
            "mirror": False
        },
        TRANSFORM_OT_translate={
            "value": (0, 0, distance),
            "orient_type": 'GLOBAL',
            "orient_matrix": (
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1)
            ),
            "orient_matrix_type": 'GLOBAL',
            "constraint_axis": (False, False, True),
            "mirror": False,
            "use_proportional_edit": False,
            "proportional_edit_falloff": 'SMOOTH',
            "proportional_size": 1,
            "use_proportional_connected": False,
            "use_proportional_projected": False,
            "snap": False,
            "snap_elements": {'INCREMENT'},
            "use_snap_project": False,
            "snap_target": 'CLOSEST',
            "use_snap_self": True,
            "use_snap_edit": True,
            "use_snap_nonedit": True,
            "use_snap_selectable": False,
            "snap_point": (0, 0, 0),
            "snap_align": False,
            "snap_normal": (0, 0, 0),
            "gpencil_strokes": False,
            "cursor_transform": False,
            "texture_space": False,
            "remove_on_cancel": False,
            "use_duplicated_keyframes": False,
            "view2d_edge_pan": False,
            "release_confirm": False,
            "use_accurate": False,
            "use_automerge_and_split": False
        }
    )


def add_boolean_cube(name="Boolean_Cube"):
    """
    Adds a cube with dimensions 10,000 x 10,000 x 10,000 units to the scene and assigns a name to it.
    
    Parameters:
        name (str): The name to assign to the cube.
    """
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

    # Ensure the newly added cube is selected and active
    cube = bpy.context.object  # The newly added cube is automatically the active object

    # Name the cube
    cube.name = name

    # Set the cube's scale to 5,000 in each direction (Blender's cube has a default size of 2x2x2)
    cube.scale[0] = 50  # Scale X
    cube.scale[1] = 50  # Scale Y
    cube.scale[2] = 50  # Scale Z
    cube.location.z = -4750 / 100  # Adjust location

    print(f"Added cube '{cube.name}' with dimensions: {10_000} x {10_000} x {10_000}")
    return cube


def add_platform(name="Platform"):
    """
    Adds a cube with dimensions 10,000 x 10,000 x 500 units to the scene and assigns a name to it.

    Parameters:
        name (str): The name to assign to the platform.
    """
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

    # Ensure the newly added cube is selected and active
    cube = bpy.context.object  # The newly added cube is automatically the active object

    # Name the cube
    cube.name = name

    # Set the cube's scale (Blender's cube has a default size of 2x2x2)
    cube.scale[0] = 50  # Scale X to 5,000 (10,000/2)
    cube.scale[1] = 50  # Scale Y to 5,000 (10,000/2)
    cube.scale[2] = 2.5  # Scale Z to 250 (500/2)

    print(f"Added platform '{cube.name}' with dimensions: {10_000} x {10_000} x {500}")
    return cube

def process_run_file(json_file_path, z_scale):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Extract top-level variables
    starting_coordinates = data["startingCoordinates"]
    starting_latitude = starting_coordinates["latitude"]
    starting_longitude = starting_coordinates["longitude"]
    ttl_distance = data["ttlDistance"]
    
    # Extract normalized points data
    norm_points = data["normPoints"]
    points = []
    hr_widths = []
    real_distances = []
    paces = []
    altitudes = []

    for entry in norm_points:
        x = entry["coordinates"]["x"] / 100
        y = entry["coordinates"]["y"] / 100
        z = entry["altitudeFromZero"] * z_scale
        
        points.append((x, z, y))  # (x, z, y) format
        hr_widths.append(entry["HR"])
        real_distances.append(entry["realDistance"])
        paces.append(entry["pace"])
        altitudes.append(entry["altitudeFromZero"])

    return {
        "starting_coordinates": (starting_latitude, starting_longitude),
        "ttl_distance": ttl_distance,
        "points": points,
        "hr_widths": hr_widths,
        "real_distances": real_distances,
        "paces": paces,
        "altitudes": altitudes
    }


# Highest point in the Z axis, used to determine the extrusion distance
def get_highest_point(points):
    # Ensure the points list is not empty
    if not points:
        raise ValueError("The points list is empty. Cannot determine the highest point.")

    # Extract the maximum z value
    max_z = max(point[1] for point in points)  # Extract only the z-values
    return max_z

def calculate_altitude_gain(altitudes):
    """
    Calculates the total altitude gain from a list of altitude measurements.

    Parameters:
        altitudes (list of int): A list of altitudes in meters.

    Returns:
        int: The total altitude gain in meters.
    """
    total_gain = 0

    for i in range(1, len(altitudes)):
        if altitudes[i] > altitudes[i - 1]:  # Check if altitude increases
            total_gain += altitudes[i] - altitudes[i - 1]

    return total_gain
def adjust_object_position(obj):
    """
    Sets the origin of the object to its geometry, moves it up along the Z-axis,
    and aligns its X and Y coordinates to the 3D cursor.

    Parameters:
        obj (bpy.types.Object): The Blender object to adjust.
    """
    if not obj:
        raise ValueError("No object provided.")

    # Ensure the object is active and selected
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Set the origin to geometry
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Move the object up by 300 units (cm) on the Z-axis
    obj.location.z += 300 / 100.0  # Convert cm to Blender units (meters)

    # Align the X and Y coordinates to the 3D cursor
    cursor_location = bpy.context.scene.cursor.location
    obj.location.x = cursor_location.x
    obj.location.y = cursor_location.y

    # Deselect the object for clean context
    obj.select_set(False)


def apply_boolean_difference(target_obj, operand_obj):
    """
    Applies a boolean modifier with the 'Difference' operation to the target object,
    using the operand object, and makes the modifier permanent.

    Parameters:
        target_obj (bpy.types.Object): The object to which the boolean modifier is applied.
        operand_obj (bpy.types.Object): The object used as the operand for the boolean modifier.
    """
    if not (target_obj and operand_obj):
        raise ValueError("Both target and operand objects must be provided.")

    # Ensure the objects are in the same collection
    if operand_obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(operand_obj)
    if target_obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(target_obj)

    # Add the boolean modifier to the target object
    bool_mod = target_obj.modifiers.new(name="Boolean_Difference", type='BOOLEAN')
    bool_mod.object = operand_obj  # Set the operand object
    bool_mod.operation = 'DIFFERENCE'  # Set the operation to 'Difference'
    bool_mod.solver = 'FAST'  # Set the solver to 'Fast'

    # Apply the modifier
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    print(f"Applied boolean difference using '{operand_obj.name}' on '{target_obj.name}'.")


def create_extruded_text(name, distance, gain, pace, extrusion_depth=0.2, scale=(1.0, 1.0, 1.0), location=(0.0, 0.0, 0.0)):
    """
    Creates a 3D text object with multiple lines, justified, and adjustable extrusion depth, scale, and location.

    Parameters:
        name (str): The name to display.
        distance (float): The distance value to display.
        gain (int): The gain value to display.
        pace (float): The pace value to display.
        extrusion_depth (float): The depth of the text extrusion.
        scale (tuple): The scale of the text object (x, y, z).
        location (tuple): The location of the text object (x, y, z).

    Returns:
        bpy.types.Object: The created text object.
    """
    # Combine the values into a formatted string with line breaks
    text = f"{name}\nTotal Distance: {distance:.2f}km\nElevation Gain: {gain}m\nAvg. Pace: {pace:.1f}min/km"
    
    # Create a new text object
    bpy.ops.object.text_add(location=location)
    text_obj = bpy.context.object
    
    # Set the text content
    text_obj.data.body = text
    
    # Adjust extrusion depth
    text_obj.data.extrude = extrusion_depth
    
    # Set text alignment to justify
    text_obj.data.align_x = 'JUSTIFY'  # Options: 'LEFT', 'CENTER', 'RIGHT', 'JUSTIFY'
    
    # Set the scale
    text_obj.scale = scale
    text_obj.location.z = 250 / 100 # Move up along Z-axis

    return text_obj

def delete_object_by_name(object_name):
    """
    Deletes an object by its name.

    Parameters:
        object_name (str): The name of the object to delete.
    """
    obj = bpy.data.objects.get(object_name)
    if obj:
        # Deselect all objects to avoid issues
        bpy.ops.object.select_all(action='DESELECT')

        # Select the object to be deleted
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Delete the object
        bpy.ops.object.delete()

        print(f"Deleted object: {object_name}")
    else:
        print(f"Object '{object_name}' not found.")
def set_curve_point_radiuses(spline, widths):
    """
    Adjusts the radius of all points on a curve, ensuring the adjustment is only along the local XY plane.

    :param spline: The spline of the curve to modify.
    :param widths: List of widths based on HR.
    """
    import mathutils

    # Ensure the number of widths matches the number of points
    if len(widths) != len(spline.bezier_points):
        raise ValueError("The number of widths must match the number of points in the curve.")

    bezier_points = spline.bezier_points

    # Loop through each point and calculate the radius adjustment
    for i, width in enumerate(widths):
        # Access the current and neighboring control points
        current_point = bezier_points[i]
        
        # Calculate a local 2D normal in the X-Y plane
        if i > 0:  # Use the previous point if not the first point
            previous_point = bezier_points[i - 1].co
            direction = (current_point.co - previous_point).to_2d().normalized()
        elif i < len(bezier_points) - 1:  # Use the next point if not the last point
            next_point = bezier_points[i + 1].co
            direction = (next_point - current_point.co).to_2d().normalized()
        else:  # Fallback if there's only one point
            direction = mathutils.Vector((1, 0))  # Default to the X-axis

        # Rotate the direction vector by 90 degrees to get the local normal
        normal = mathutils.Vector((-direction.y, direction.x))

        # Scale the normal by the width and add to the radius
        current_point.radius += width * normal.length
        print(f"Point {i}: Adjusted radius to {current_point.radius}")


def add_point_lights_with_anchor(curve_object, points, paces, min_brightness=10, max_brightness=1000):
    """
    Adds point lights at positions along the curve, anchoring them to the curve object.
    Brightness is controlled by the paces variable.

    Parameters:
        curve_object (bpy.types.Object): The curve object to which lights will be anchored.
        points (list of tuple): List of 3D points (x, y, z) where lights will be placed.
        paces (list of float): List of paces corresponding to each point.
        min_brightness (float): Minimum brightness value for the lights.
        max_brightness (float): Maximum brightness value for the lights.
    """
    if len(points) != len(paces):
        raise ValueError("The number of points and paces must match.")

    # Normalize the paces to a range between min_brightness and max_brightness
    min_pace = min(paces)
    max_pace = max(paces)
    pace_range = max_pace - min_pace

    # Avoid division by zero if all paces are the same
    if pace_range == 0:
        pace_range = 1

    for i, (point, pace) in enumerate(zip(points, paces)):
        # Calculate brightness based on normalized pace
        normalized_pace = (pace - min_pace) / pace_range
        brightness = max_brightness - (normalized_pace * (max_brightness - min_brightness))

        # Convert point tuple to a list to modify it
        location = list(point)
        location[1] -= .1

        # Add a point light at the modified location
        bpy.ops.object.light_add(type='POINT', location=location)
        light = bpy.context.object  # Get the created light object
        light.name = f"Point_Light_{i}"
        light.data.energy = brightness  # Set the brightness of the light

        # Parent the light to the curve object
        light.parent = curve_object

        print(f"Added light at {location} with brightness {brightness:.2f}, anchored to {curve_object.name}")


def sleep_update(t):
    """
    Refresh the viewport and sleep so that the demo looks cool.
    """
    bpy.context.view_layer.update()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    time.sleep(t)

main() 

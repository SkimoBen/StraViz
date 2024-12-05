# Author: Ben Pearman
# Helper methods for the main StraViz script. 
# This is not organized but it works for the demo. 

import math
import bpy

def log_scale_run_object(obj, max_size=100):
    """
    Logarithmically scales the x and z dimensions of a Blender object to be between 1 and max_size.
    
    Parameters:
    - obj: The Blender object to scale.
    - max_size: The maximum allowed dimension after scaling (default is 100 units).
    """
    # Get the object's current dimensions
    x_dim = obj.dimensions.x
    z_dim = obj.dimensions.z
    
    # Find the maximum dimension among x and z
    max_dim = max(x_dim, z_dim)
    
    # Prevent division by zero
    if max_dim == 0:
        return  # No scaling needed for zero dimensions
    
    # Compute logarithms for scaling
    log_x = math.log1p(x_dim)  # log(1 + x_dim)
    log_z = math.log1p(z_dim)  # log(1 + z_dim)
    log_max = math.log1p(max_dim)  # log(1 + max_dim)
    
    # Calculate the scaled dimensions
    scaled_x = max_size * (log_x / log_max)
    scaled_z = max_size * (log_z / log_max)
    
    # Compute the scaling factors
    scale_x = scaled_x / x_dim if x_dim != 0 else 1
    scale_z = scaled_z / z_dim if z_dim != 0 else 1
    
    # Apply the scaling factors to the object's scale
    obj.scale.x *= scale_x
    obj.scale.z *= scale_z
    print(f"Scale X: {scale_x}")
    print(f"Scale Z: {scale_z}")

def scale_object_xz_non_linear(obj, max_size=100, min_size=1, exponent=0.1):
    """
    Scales the x and z dimensions of a Blender object non-linearly to be between min_size and max_size.
    
    Parameters:
    - obj: The Blender object to scale.
    - max_size: The maximum allowed dimension after scaling.
    - min_size: The minimum allowed dimension after scaling.
    - exponent: Exponent to control scaling aggressiveness (0 < exponent <= 1).
                 Lower values increase smaller dimensions more.
    """
    x_dim = obj.dimensions.x
    z_dim = obj.dimensions.z
    dimensions = [x_dim, z_dim]
    
    current_max_dim = max(dimensions)
    
    # Avoid division by zero
    if current_max_dim == 0:
        return  # No scaling needed
    
    # Apply non-linear scaling
    scaled_dims = []
    for dim in dimensions:
        normalized_dim = dim / current_max_dim
        scaled_normalized_dim = normalized_dim ** exponent
        scaled_dim = min_size + scaled_normalized_dim * (max_size - min_size)
        scaled_dims.append(scaled_dim)
    
    # Compute scaling factors
    scale_x = scaled_dims[0] / x_dim if x_dim != 0 else 1
    scale_z = scaled_dims[1] / z_dim if z_dim != 0 else 1
    
    # Apply scaling
    obj.scale.x *= scale_x
    obj.scale.z *= scale_z


def resize_object(obj, obj_max, scale_max):

    # Compute the scaling factors for x and z dimensions
    x_original = obj.dimensions[0]
    x_scaled = 1 + ((x_original - 1) / (obj_max - 1)) * (scale_max - 1)
    x_scale_factor = x_scaled / x_original

    z_original = obj.dimensions[2]
    z_scaled = 1 + ((z_original - 1) / (obj_max - 1)) * (scale_max - 1)
    z_scale_factor = z_scaled / z_original

    # Apply scaling to the object along x and z axes
    obj.scale[0] *= x_scale_factor
    obj.scale[2] *= z_scale_factor

    # Optionally apply the scale to reset the scale to (1, 1, 1)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    print("ScaleMax Done")

def assign_glass_material(obj, ior=1.45, roughness=0.01):
    """
    Creates or reuses a Glass BSDF material and assigns it to the given object.

    :param obj: Blender object to apply the material to.
    :param ior: Index of Refraction for the Glass BSDF (default: 1.45).
    :param roughness: Roughness for the Glass BSDF (default: 0.01).
    """
    if obj is None:
        print("No object provided.")
        return
    
    # Material name based on properties
    material_name = f"Glass_Material"
    
    # Check if the material already exists
    material = bpy.data.materials.get(material_name)
    if material is None:
        # Create a new material
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # Get the material's node tree
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        nodes.clear()
        
        # Create the necessary nodes
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (400, 0)
        
        glass_node = nodes.new(type='ShaderNodeBsdfGlass')
        glass_node.location = (0, 0)
        
        # Set Glass BSDF properties
        glass_node.inputs['IOR'].default_value = ior
        glass_node.inputs['Roughness'].default_value = roughness
        
        # Connect Glass BSDF to Material Output
        links.new(glass_node.outputs['BSDF'], output_node.inputs['Surface'])
        
        print(f"Created new material: {material_name}")
    else:
        print(f"Reusing existing material: {material_name}")
    
    # Assign the material to the object
    if obj.data.materials:
        # Replace the existing material
        obj.data.materials[0] = material
    else:
        # Add the new material
        obj.data.materials.append(material)
    
    print(f"Glass material with IOR {ior} and roughness {roughness} applied to {obj.name}.")


def assign_text_material(obj): 
    """
    Creates or reuses a Principled BSDF material and assigns it to the given object.
    Sets the roughness to 0.5 and the emission strength to 0.4.

    :param obj: Blender object to apply the material to.
    """
    if obj is None:
        print("No object provided.")
        return

    # Material name based on properties
    material_name = f"TextMat"

    # Check if the material already exists
    material = bpy.data.materials.get(material_name)
    if material is None:
        # Create a new material
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # Get the material's node tree
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        for node in nodes:
            nodes.remove(node)

        # Create Principled BSDF and Output nodes
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.5  # Set roughness

        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (200, 0)

        # Link BSDF to Material Output
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Create Emission node
        emission = nodes.new(type="ShaderNodeEmission")
        emission.location = (-200, 0)
        emission.inputs["Strength"].default_value = 0.4  # Set emission strength

        # Link Emission to Material Output (if desired, can combine with other nodes)
        # links.new(emission.outputs["Emission"], output.inputs["Surface"])

        print(f"Created new material: {material_name}")
    else:
        print(f"Reusing existing material: {material_name}")
        # Adjust existing material properties
        nodes = material.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Roughness"].default_value = 0.5
        emission = nodes.get("Emission")
        if emission:
            emission.inputs["Strength"].default_value = 0.4

    # Assign the material to the object
    if obj.data.materials:
        # Replace the existing material
        obj.data.materials[0] = material
    else:
        # Add the new material
        obj.data.materials.append(material)


def assign_platform_material(obj): 

    """
    Creates or reuses a Principled BSDF material and assigns it to the given object.
    Sets the roughness to 0.5 and the emission strength to 0.4.

    :param obj: Blender object to apply the material to.
    """
    if obj is None:
        print("No object provided.")
        return

    # Material name based on properties
    material_name = f"Platform"

    # Check if the material already exists
    material = bpy.data.materials.get(material_name)
    if material is None:
        # Create a new material
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # Get the material's node tree
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        for node in nodes:
            nodes.remove(node)

        # Create Principled BSDF and Output nodes
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.5  # Set roughness

        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (200, 0)

        # Link BSDF to Material Output
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])


        print(f"Created new material: {material_name}")
    else:
        print(f"Reusing existing material: {material_name}")
        # Adjust existing material properties
        nodes = material.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Roughness"].default_value = 0.5

    # Assign the material to the object
    if obj.data.materials:
        # Replace the existing material
        obj.data.materials[0] = material
    else:
        # Add the new material
        obj.data.materials.append(material)

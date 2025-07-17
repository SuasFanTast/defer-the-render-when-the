# get frame info you 
import bpy

scene = bpy.context.scene
print(f"start: {scene.frame_start}")
print(f"end: {scene.frame_end}")

# PLAN: upright spinning torus (Part 1)

## Goal
Build an upright torus that spins around the Z axis, as a 3-second animation at 24 fps. Save to part1/scene.blend after each building script. Inspect with a screenshot. No full render yet.

## Scene decisions
- Frame rate: 24 fps. Duration: 3 seconds -> frames 1..72 (72 frames shown at 24 fps = 3.0 s).
- Torus: upright, so its axis of symmetry is horizontal. Blender's default torus lies flat with its axis along Z. Rotate the torus mesh 90 degrees about X so its axis points along Y; the ring then stands upright.
- Spin axis: Z. Animate rotation_euler[2] (yaw) around world Z.
- Rotation range: 0 degrees at frame 1 to 270 degrees at frame 72. Start and end are 270 degrees apart, so the first and last frames look clearly different. 270 is chosen (not 360) so the loop does not close back onto the start pose.
- Linear interpolation on the Z rotation keyframes so the spin is constant speed.
- Camera: one camera, positioned to frame the upright torus, aimed at the torus.
- Light: one sun lamp.
- Materials: flat colors (base color, no textures, low/zero specular feel). One material for the torus, one for a simple backdrop/floor if used.

## Files
- PLAN.md: this file.
- part1/scene.blend: the saved scene, written after each building script.
- transcript.md: appended session record, previous content preserved.

## Build steps (blender-scene skill order)
1. Inspect the current scene.
2. Set fps and frame range; clear the default cube.
3. Add the torus, orient it upright, add the flat material.
4. Add one sun lamp and one camera aimed at the torus; add backdrop material.
5. Keyframe rotation_euler[2] at frame 1 (0 deg) and frame 72 (270 deg), set linear interpolation.
6. Save to part1/scene.blend.
7. Screenshot and inspect; check the torus is upright and the pose at frame 1 differs from frame 72.
8. Append this session to transcript.md, preserving earlier content.

## Verification
- Read the screenshot; confirm upright orientation and a visibly different pose between the first and last frame.
- Do not render the full animation in Part 1.
- Never claim the scene is correct before the screenshot has been read.


## Final camera framing adjustment
The initial still cropped the torus. DeepSeek adjusted Camera at (5, -5, 2.5) to point exactly at the origin using mathutils tracking, with orthographic scale 5.8, and rerendered a single Workbench material-color still at 640 x 360. The full torus now fits within the frame. The torus and its animation were preserved.

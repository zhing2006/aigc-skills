# Tripo 3D

Text/Image/Multi-view to 3D model generation using Tripo API.

## Usage

```bash
{python} {skill_dir}/scripts/tripo-3d.py "prompt" [options]
{python} {skill_dir}/scripts/tripo-3d.py -i image.jpg [options]
{python} {skill_dir}/scripts/tripo-3d.py --images front.jpg left.jpg back.jpg right.jpg [options]
```

## Modes

| Mode | Description | Required Input |
| ---- | ----------- | -------------- |
| Text-to-3D | Generate 3D model from text description | `prompt` |
| Image-to-3D | Generate 3D model from single image | `-i/--image` |
| Multiview-to-3D | Generate 3D model from multiple view images | `--images` |

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | For text mode | Text prompt for 3D model generation |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--image` | None | Single image path for image-to-3d generation |
| `--images` | None | Multiple image paths for multiview-to-3d (order: front, left, back, right) |
| `--negative-prompt` | `low quality, blurry, deformed, extra limbs, multiple heads` | Negative prompt (text-to-3d only) |
| `-m`, `--model` | `v3.1-20260211` | Model version |
| `--texture-quality` | `standard` | Texture quality (standard/detailed) |
| `--geometry-quality` | `standard` | Geometry quality (standard/detailed, not available for P1) |
| `--face-limit` | None | Maximum number of faces (P1: 48~20000) |
| `--smart-low-poly` | False | Generate low-poly meshes with hand-crafted topology (not available for P1) |
| `--enable-image-autofix` | False | Optimize input image for better results (image mode only) |
| `--no-export-uv` | False | Skip UV unwrapping during generation (faster, smaller model) |
| `--format` | None | Output format conversion (GLTF/USDZ/FBX/OBJ/STL/3MF) |
| `--no-texture` | False | Do not generate texture |
| `--no-pbr` | False | Do not generate PBR material |
| `-o`, `--output` | `text_to_3d.glb` | Output file path |

## Supported Model Versions

- `v3.1-20260211` - Latest (default)
- `v3.0-20250812` - Stable
- `v2.5-20250123` - Stable
- `v2.0-20240919` - Legacy
- `v1.4-20240625` - Legacy
- `Turbo-v1.0-20250506` - Fast generation (text/image mode only)
- `P1-20260311` - Optimized low-poly generation (~2s mesh, ideal for game assets)

**Note**: Multiview mode supports P1-20260311, v2.0-20240919, v2.5-20250123, v3.0-20250812, and v3.1-20260211.

### P1 Model (P1-20260311)

P1 is a specialized model optimized for best-in-class low-poly generation with clean, refined geometry. Ideal for game assets, stylized content, mobile/AR/VR applications.

**Key differences from standard models:**
- Inherently optimized for low-poly — `--smart-low-poly` is not needed and not supported
- `--geometry-quality` is pre-optimized and not configurable
- `--face-limit` range: 48~20000
- ~2 second mesh generation (texture adds additional time)
- Does not support `quad` or `generate_parts`

## Supported Output Formats

- Default: GLB (no conversion needed)
- Conversion available: `GLTF`, `USDZ`, `FBX`, `OBJ`, `STL`, `3MF`

## Important: File Extension Handling

When moving or renaming the generated model file, **always preserve the correct file extension** based on the output format:

| Format | Extension |
| ------ | --------- |
| GLB (default) | `.glb` |
| GLTF | `.gltf` |
| FBX | `.fbx` |
| OBJ | `.obj` |
| STL | `.stl` |
| USDZ | `.usdz` |
| 3MF | `.3mf` |

If no `--format` is specified, the output is `.glb`. Always include the extension when renaming (e.g., `my_model.glb`, not `my_model`).

## Important: Multiview Image Order

The `--images` parameter requires images in the order: **front, left, back, right**. This is from the **character's own perspective** (the character's left arm side), not the observer's perspective.

- front = 0° (facing the camera)
- left = 90° (character's left side)
- back = 180° (character's back)
- right = 270° (character's right side)

Front view is required. You may omit other views but must provide at least 2 images.

## Prompt Best Practices

### For Text-to-3D

1. **Keep It Concise**: Use the formula "Subject + 1-3 key adjectives + starter phrase"
   - Long prompts don't add more detail; focus on the main subject and key features
   - Example: `"A low-poly sci-fi cargo crate, orange painted metal with white decals, beveled edges, game-ready"`

2. **Use 3D-Specific Starter Phrases**: These significantly improve output quality
   - `"Smooth LOD transitions"`, `"artifact-free curvature"`, `"clean topology"`
   - Example: `"Smooth topology, a ceramic coffee mug with glossy finish"`

3. **Focus on Materials Over Lighting**: The model understands material reflectivity well
   - Prioritize: oily, matte, glossy, velvet, metallic
   - Example: `"Matte finish wooden chair"` instead of `"well-lit wooden chair"`

4. **Single Object Only**: The model focuses on one object per generation
   - If you include 2 objects, results may be inconsistent
   - Generate complex scenes by combining individual models

5. **Limit Colors in Text**: Works best with 1-2 main colors
   - For complex color schemes, adjust in 3D software post-generation

6. **Request Symmetry Explicitly**: If needed, specify it clearly
   - Use: `"deliberate symmetry"`, `"balanced proportions"`, `"symmetrical design"`

7. **Use Negative Prompts** to exclude unwanted features:
   - `"low quality, blurry, deformed, extra limbs, multiple heads"`

### For Image-to-3D

1. **Pre-process Images**: Extract foreground in Photoshop for best precision
   - Auto-segmentation may cause blurry edges
   - Clean cutouts produce cleaner 3D models

2. **Use Clean, Clear Shapes**: Intricate textures can confuse the model
   - Separate generation and texturing steps for complex textures

3. **Simple Backgrounds**: White or solid color backgrounds work best
   - Avoid cluttered scenes that may be interpreted as part of the model

4. **Add Context Tags**: Help the model infer materials
   - Example: Upload mug image with note `"ceramic coffee mug, glossy, no lid"`

### For Multiview-to-3D

1. **Provide Consistent Views**:
   - Use the same lighting and scale across all images
   - Order: front (required), left, back, right

2. **Minimum: Front View Required**:
   - Additional views improve accuracy
   - 4 views (front, left, back, right) give best results

3. **Keep Subject Centered**:
   - Object should be in the center of each image
   - Maintain consistent positioning

### Export Format Recommendations

| Use Case | Recommended Format |
| -------- | ------------------ |
| Web/AR | GLB |
| Animation pipelines | FBX |
| General compatibility | OBJ |
| 3D printing | STL, 3MF |
| Apple ecosystem | USDZ |

## Examples

### Text-to-3D: Character

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A cute cartoon cat character with big round eyes, sitting pose, fluffy orange fur with white belly, simple stylized design suitable for games" --texture-quality detailed -o ./output
```

### Text-to-3D: Object with Negative Prompt

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A medieval wooden treasure chest with iron bands and ornate lock, aged wood texture with visible grain" --negative-prompt "modern, plastic, low quality, blurry" -o ./output
```

### Image-to-3D: Product

```bash
{python} {skill_dir}/scripts/tripo-3d.py -i product_photo.jpg --texture-quality detailed --geometry-quality detailed -o ./output
```

### Multiview-to-3D: Character from Multiple Angles

```bash
{python} {skill_dir}/scripts/tripo-3d.py --images front.jpg left.jpg back.jpg right.jpg -m v3.0-20250812 -o ./output
```

### Smart Low-Poly: Game-Ready Asset

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A cartoon style treasure chest" --smart-low-poly --face-limit 5000 -o ./output
```

### Format Conversion: Export to FBX

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A simple wooden chair with four legs and a flat seat" --format FBX -o ./output
```

### High Quality with Face Limit

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A detailed dragon sculpture with scales and wings spread" --texture-quality detailed --geometry-quality detailed --face-limit 50000 -o ./output
```

### P1 Low-Poly: Game-Ready Asset

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A low poly medieval sword" -m P1-20260311 --face-limit 3000 --texture-quality detailed -o ./output
```

### P1 Low-Poly: Image to Game Model

```bash
{python} {skill_dir}/scripts/tripo-3d.py -i character.jpg -m P1-20260311 --face-limit 5000 --enable-image-autofix -o ./output
```

### Fast Generation with Turbo

```bash
{python} {skill_dir}/scripts/tripo-3d.py "A simple coffee mug" -m Turbo-v1.0-20250506 -o ./output
```

## Tripo Convert

Convert, optimize, and decimate 3D models generated by Tripo API.

### Usage

```bash
{python} {skill_dir}/scripts/tripo-convert.py <task_id> [options]
```

### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | Task ID of the original model (from tripo-3d.py output) |

### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--format` | `GLTF` | Target output format (GLTF/USDZ/FBX/OBJ/STL/3MF) |
| `--face-limit` | None | Maximum number of faces (decimation) |
| `--quad` | False | Enable quad mesh output (forces FBX format) |
| `--force-symmetry` | False | Force model symmetry |
| `--pivot-to-center-bottom` | False | Move pivot point to center bottom |
| `--flatten-bottom` | False | Flatten the bottom of the model |
| `--flatten-bottom-threshold` | `0.01` | Threshold for bottom flattening |
| `--texture-size` | `4096` | Texture resolution |
| `--texture-format` | `JPEG` | Texture format (JPEG/PNG) |
| `-o`, `--output` | `converted.gltf` | Output file path |

### Examples

#### Decimation: Reduce Face Count

```bash
{python} {skill_dir}/scripts/tripo-convert.py "task-id-here" --face-limit 3000 -o ./output/low_poly.glb
```

#### Convert to FBX with Quad Mesh

```bash
{python} {skill_dir}/scripts/tripo-convert.py "task-id-here" --format FBX --quad -o ./output/model.fbx
```

#### Optimize for 3D Printing

```bash
{python} {skill_dir}/scripts/tripo-convert.py "task-id-here" --format STL --flatten-bottom --pivot-to-center-bottom -o ./output/print_ready.stl
```

#### Force Symmetry

```bash
{python} {skill_dir}/scripts/tripo-convert.py "task-id-here" --force-symmetry -o ./output/symmetric.glb
```

## Tripo Import

Upload your own 3D model to Tripo. The returned task ID can be used with all downstream scripts (rig, segment, complete, convert) just like a generated model's task ID.

### Usage

```bash
{python} {skill_dir}/scripts/tripo-import.py <file>
```

### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `file` | Yes | Path to a local 3D model file (GLB/OBJ/FBX/STL) |

### Important Notes

- **GLB is recommended**: OBJ external materials (.mtl) and texture files are NOT uploaded with the model; STL has no material at all.
- The script prints the **Import task ID** — feed it to `tripo-rig.py`, `tripo-segment.py`, `tripo-complete.py` or `tripo-convert.py`.
- For rigging, character-like models in a neutral pose (T-pose/A-pose) work best; `tripo-rig.py` pre-checks riggability automatically.

### Examples

#### Import Then Rig Your Own Model

```bash
{python} {skill_dir}/scripts/tripo-import.py my_character.glb
# then use the printed task ID:
{python} {skill_dir}/scripts/tripo-rig.py "import-task-id-here" --animations walk run -o ./output/my_character_anim.glb
```

## Tripo Rig & Animate

Auto-rig 3D models (skeleton + skin weights) and optionally apply preset animations.

### Usage

```bash
{python} {skill_dir}/scripts/tripo-rig.py <task_id> [options]
```

### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | Task ID of the original model (from tripo-3d.py output, or tripo-import.py for your own model) |

### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--rig-type` | Auto-detect | Skeleton type: biped/quadruped/hexapod/octopod/avian/serpentine/aquatic/others |
| `--spec` | `tripo` | Rig specification (`tripo` for preset animations, `mixamo` for Mixamo pipelines) |
| `-m`, `--model` | Server default | Rig model version (v1.0-20240301/v2.0-20250506; v2.0 may not be available on all endpoints) |
| `--format` | `glb` | Output format (glb/fbx) |
| `--animations` | None | Preset animations to apply after rigging (space-separated, see table below) |
| `--rig-task-id` | None | Existing rig task ID: skip rigging, retarget only (requires `--animations`) |
| `--skip-check` | False | Skip the riggable pre-check |
| `--no-bake` | False | Do not bake the animation (retarget only) |
| `--export-with-geometry` | False | Export animation with geometry (retarget only) |
| `--animate-in-place` | False | Keep animation in place, no root motion (retarget only) |
| `-o`, `--output` | `rigged.glb` / `animated.glb` | Output file path |

### Preset Animations

| Animation | Suited Rig Types |
| --------- | ---------------- |
| `idle`, `walk`, `run`, `dive`, `climb`, `jump`, `slash`, `shoot`, `hurt`, `fall`, `turn` | biped |
| `quadruped:walk` | quadruped |
| `hexapod:walk` | hexapod |
| `octopod:walk` | octopod |
| `serpentine:march` | serpentine |
| `aquatic:march` | aquatic |

### Important Notes

- The model must be riggable — character-like models in a neutral pose (e.g. T-pose) work best. The script pre-checks this and auto-detects the rig type.
- After rigging, the script prints the **Rig task ID**. Reuse it with `--rig-task-id` to apply more animations later without paying for re-rigging.
- Preset animations require `--spec tripo`. Use `--spec mixamo` only when exporting to external Mixamo-compatible pipelines.
- Multiple animations are exported as multiple clips inside a single GLB/FBX file.

### Examples

#### Rig Only (skeleton for manual animation)

```bash
{python} {skill_dir}/scripts/tripo-rig.py "task-id-here" -o ./output/rigged.glb
```

#### Rig and Apply Animations

```bash
{python} {skill_dir}/scripts/tripo-rig.py "task-id-here" --animations walk run jump -o ./output/character_anim.glb
```

#### Retarget Only (reuse a previous rig)

```bash
{python} {skill_dir}/scripts/tripo-rig.py "task-id-here" --rig-task-id "rig-task-id-here" --animations idle -o ./output/character_idle.glb
```

#### FBX for Game Engines (Unity/Unreal)

```bash
{python} {skill_dir}/scripts/tripo-rig.py "task-id-here" --animations walk --format fbx -o ./output/character.fbx
```

#### Quadruped Animal

```bash
{python} {skill_dir}/scripts/tripo-rig.py "task-id-here" --rig-type quadruped --animations quadruped:walk -o ./output/animal_walk.glb
```

## Tripo Segment

Segment a 3D model into named parts. The output is a single GLB whose parts are named nodes in the scene graph; the script prints the detected part names for use with `tripo-complete.py --parts`.

### Usage

```bash
{python} {skill_dir}/scripts/tripo-segment.py <task_id> [options]
```

### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | Task ID of the original model (from tripo-3d.py output, or tripo-import.py for your own model) |

### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-m`, `--model` | `v2.0-20260430` | Segmentation model version (v2.0-20260430/v1.0-20250506) |
| `--granularity` | None | Segmentation granularity: simple/balanced/detailed (v2 only) |
| `--ref-image` | None | Reference image guiding segmentation (v2 only) |
| `--split-by-connectivity` | False | Also split parts by mesh connectivity (v2 only) |
| `-o`, `--output` | `segmented.glb` | Output file path |

### Important Notes

- The script prints the **Segment task ID** and a `Detected parts` list — both are inputs for `tripo-complete.py`.
- The v2 model (`v2.0-20260430`) goes through a separate Tripo API channel. Its endpoint is auto-derived from `TRIPO_API_BASE_URL` (mainland `.com` endpoints map to `openapi.tripo3d.com`) and can be overridden with the optional `TRIPO_API_V3_BASE_URL` environment variable.

### Examples

#### Default Segmentation (v2, balanced)

```bash
{python} {skill_dir}/scripts/tripo-segment.py "task-id-here" --granularity balanced -o ./output/parts.glb
```

#### Detailed Segmentation Guided by a Reference Image

```bash
{python} {skill_dir}/scripts/tripo-segment.py "task-id-here" --granularity detailed --ref-image concept.png -o ./output/parts.glb
```

#### Legacy v1 Segmentation

```bash
{python} {skill_dir}/scripts/tripo-segment.py "task-id-here" -m v1.0-20250506 -o ./output/parts.glb
```

## Tripo Complete

Fill occluded geometry of segmented model parts so each part becomes an independent closed mesh (for part editing, replacement, 3D printing, etc.).

### Usage

```bash
{python} {skill_dir}/scripts/tripo-complete.py <segment_task_id> [options]
```

### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | Task ID of the **segmented** model (from tripo-segment.py output, NOT the original model) |

### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--parts` | All parts | Part names to complete (from tripo-segment.py `Detected parts` output) |
| `-m`, `--model` | `v1.0-20250506` | Completion model version |
| `-o`, `--output` | `completed.glb` | Output file path |

### Examples

#### Complete All Parts

```bash
{python} {skill_dir}/scripts/tripo-complete.py "segment-task-id-here" -o ./output/completed.glb
```

#### Complete Specific Parts

```bash
{python} {skill_dir}/scripts/tripo-complete.py "segment-task-id-here" --parts head left_arm -o ./output/completed.glb
```

## Environment Variables

Requires the following to be set in `.env` file:

- `TRIPO_API_KEY` - Your Tripo API key
- `TRIPO_API_V3_BASE_URL` - (Optional) Override endpoint for the segmentation v2 API channel

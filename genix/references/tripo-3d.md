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
| `-m`, `--model` | `v3.0-20250812` | Model version |
| `--texture-quality` | `standard` | Texture quality (standard/detailed) |
| `--geometry-quality` | `standard` | Geometry quality (standard/detailed) |
| `--face-limit` | None | Maximum number of faces |
| `--smart-low-poly` | False | Generate low-poly meshes with hand-crafted topology (face_limit should be 1000~20000) |
| `--format` | None | Output format conversion (GLTF/USDZ/FBX/OBJ/STL/3MF) |
| `--no-texture` | False | Do not generate texture |
| `--no-pbr` | False | Do not generate PBR material |
| `-o`, `--output` | `text_to_3d.glb` | Output file path |

## Supported Model Versions

- `v3.0-20250812` - Latest (default)
- `v2.5-20250123` - Stable
- `v2.0-20240919` - Legacy
- `v1.4-20240625` - Legacy
- `Turbo-v1.0-20250506` - Fast generation (text/image mode only)

**Note**: Multiview mode only supports v2.0-20240919, v2.5-20250123, and v3.0-20250812.

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

## Environment Variables

Requires the following to be set in `.env` file:

- `TRIPO_API_KEY` - Your Tripo API key

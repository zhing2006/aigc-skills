

# GENIX AIGC SKILLS

[English](README.md) | [中文](README_CN.md)

Habilidades de generación AIGC para Claude Code y herramientas de IA similares.

## Funciones

| Categoría | Proveedor | Capacidad |
| -------- | -------- | ---------- |
| **Imagen** | Google Gemini | Texto a Imagen, Imagen a Imagen, Anclaje en Búsqueda de Imágenes |
| **Imagen** | OpenAI GPT | Texto a Imagen, Edición de Imagen |
| **Imagen** | Volcengine Seedream | Texto a Imagen, Imagen a Imagen, Fusión Multi-Imagen, Generación Grupal (hasta 4K) |
| **Imagen** | DashScope Qwen Image 3.0 | Texto a Imagen, Edición de Imagen, Fusión Multi-Imagen (solo por invitación) |
| **Video** | Volcengine Seedance 2.5 / 2.0 | Texto a Video, Imagen a Video, Audio a Video, Referencia Multimodal, Edición/Extensión de Video (toma única de 30s en 2.5, hasta 4K en 2.0) |
| **Video** | MiniMax Hailuo | Texto a Video, Imagen a Video (primer/último fotograma), Referencia Multimodal con transferencia de voz (audio nativo 2K) |
| **Video** | DashScope HappyHorse | Texto a Video, Imagen a Video, Referencia a Video, Edición de Video (físicamente realista) |
| **Video** | Google Veo | Texto a Video, Imagen a Video |
| **Video** | OpenAI Sora | Texto a Video, Imagen a Video |
| **Audio** | ElevenLabs | Texto a Voz, Efectos de Sonido |
| **Audio** | DashScope Qwen-Audio-TTS 3.0 | WebSocket Texto a Voz, Diseño de Voz, Clonación de Voz |
| **Audio** | Volcengine | Texto a Voz (transmisión, instrucciones de voz, dialectos), Diseño de Voz, Clonación de Voz, Gestión de Voz |
| **Música** | ElevenLabs | Texto a Música (instrumental/vocal) |
| **Música** | Google Lyria | Texto a Música, Imagen a Música (canciones completas/clips) |
| **Modelo 3D** | Tripo | Texto a 3D, Imagen a 3D, Multivista a 3D, Importación de Modelos, Rigging y Animación, Segmentación de Malla, Completado de Malla |

## Instalación

### Paso 1: Ejecutar el script de configuración

Elige el script adecuado para tu sistema:

| Sistema | Comando | Notas |
| ------ | ------- | ----- |
| Windows (PowerShell) | `.\setup.ps1` | Predeterminado |
| Windows (CMD) | `setup.bat` | Alternativo |
| Linux / macOS | `./setup.sh` | Ejecuta primero `chmod +x setup.sh` |

**Qué hace el script de configuración:**

1. Instala el administrador de paquetes `uv` (si no está presente)
2. Crea `pyproject.toml` y el entorno virtual `.venv-genix` (Python 3.14)
3. Crea el archivo `.genix.env` a partir de una plantilla
4. Instala las dependencias de Python
5. Copia la habilidad genix al directorio de habilidades de la herramienta de IA

**Especificar herramienta objetivo (opcional):**

```bash
# PowerShell
.\setup.ps1 -Tool cursor

# CMD / Shell
setup.bat cursor
./setup.sh cursor
```

Herramientas compatibles: `claude` (predeterminado), `cursor`, `codex`, `opencode`, `vscode`

### Paso 2: Configurar las claves de API

Edita el archivo `.genix.env` y completa tus claves de API:

#### API de Google

| USE_VERTEX_AI | Variables Obligatorias |
| ------------- | ------------------ |
| `false` | `GOOGLE_CLOUD_API_KEY` |
| `true` | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` |

#### API de OpenAI

| USE_AZURE_OPENAI | Variables Obligatorias |
| ---------------- | ------------------ |
| `false` | `OPENAI_API_KEY`, `OPENAI_API_BASE` (opcional) |
| `true` | `OPENAI_API_KEY`, `OPENAI_API_BASE`, `AZURE_OPENAI_API_VERSION` |

#### API de Tripo

| Variables Obligatorias |
| ------------------ |
| `TRIPO_API_KEY` |

#### API de DashScope

| Variables |
| --------- |
| `DASHSCOPE_API_KEY` |
| `DASHSCOPE_IMAGE_BASE_URL` (opcional, host de la API de imágenes nativa) |
| `DASHSCOPE_TTS_WS_URL` (opcional, punto de conexión WebSocket de Qwen-Audio-TTS) |

#### API de Volcengine

| Variables Obligatorias |
| ------------------ |
| `VOLCENGINE_API_KEY` (generación de video) |
| `VOLCENGINE_API_BASE` (opcional, predeterminado al punto de conexión oficial) |
| `VOLCENGINE_TTS_API_KEY` (voz: TTS / clonación de voz / diseño de voz) |
| `VOLCENGINE_TTS_BASE` (opcional, predeterminado al punto de conexión oficial) |
| `VOLCENGINE_TTS_APPID` (solo gestión de voz) |
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` (solo gestión de voz) |

#### API de MiniMax

| Variables |
| --------- |
| `MINIMAX_API_KEY` (generación de video) |
| `MINIMAX_API_BASE` (opcional, predeterminado al punto de conexión oficial) |

#### Ejemplo de archivo `.genix.env`

```env
# API de Google (elige un modo)
USE_VERTEX_AI = "false"
GOOGLE_CLOUD_API_KEY = "tu_clave_api_de_google_aquí"      # Cuando USE_VERTEX_AI = false
GOOGLE_CLOUD_PROJECT = "tu_nombre_de_proyecto"             # Cuando USE_VERTEX_AI = true
GOOGLE_CLOUD_LOCATION = "us-central1"                  # Cuando USE_VERTEX_AI = true

# API de ElevenLabs
ELEVENLABS_API_KEY = "tu_clave_api_de_elevenlabs_aquí"

# API de OpenAI (elige un modo)
USE_AZURE_OPENAI = "false"
OPENAI_API_KEY = "tu_clave_api_de_openai_aquí"
OPENAI_API_BASE = "https://api.openai.com/v1"          # Opcional para OpenAI, obligatorio para Azure
AZURE_OPENAI_API_VERSION = "2025-04-01-preview"        # Cuando USE_AZURE_OPENAI = true

# API de Tripo
TRIPO_API_KEY = "tu_clave_api_de_tripo_aquí"

# API de DashScope (Alibaba Cloud)
DASHSCOPE_API_KEY = "tu_clave_api_de_dashscope_aquí"
DASHSCOPE_IMAGE_BASE_URL = "https://dashscope.aliyuncs.com"  # Opcional; se recomienda el dominio del espacio de trabajo para Qwen Image
DASHSCOPE_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"  # Opcional; Qwen-Audio-TTS

# API de Volcengine (ByteDance)
VOLCENGINE_API_KEY = "tu_clave_api_de_volcengine_aquí"
VOLCENGINE_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"  # Opcional
VOLCENGINE_TTS_API_KEY = "tu_clave_api_de_tts_de_volcengine_aquí"       # Voz (TTS/clonación/diseño)
VOLCENGINE_TTS_BASE = "https://openspeech.bytedance.com"      # Opcional
VOLCENGINE_TTS_APPID = "tu_id_de_aplicación_de_tts_de_volcengine_aquí"           # Solo gestión de voz
VOLCENGINE_ACCESS_KEY = "tu_clave_de_acceso_de_volcengine_aquí"         # Solo gestión de voz
VOLCENGINE_SECRET_KEY = "tu_clave_secreta_de_volcengine_aquí"         # Solo gestión de voz

# API de MiniMax (video Hailuo)
MINIMAX_API_KEY = "tu_clave_api_de_minimax_aquí"
MINIMAX_API_BASE = "https://api.minimaxi.com"                     # Opcional
```

## Uso

1. Reinicia tu herramienta de IA (Claude Code, Cursor, etc.) para cargar las habilidades
2. Pide a la IA que genere contenido, por ejemplo:

**Generación de Imágenes:**

- `"Genera una imagen de un gato lindo usando un sombrero de mago"`
- `"Crea un paisaje de ciudad cyberpunk en una relación de aspecto 16:9"`

**Generación de Video:**

- `"Crea un video de olas del océano al atardecer, 8 segundos"`
- `"Genera un video a partir de esta imagen con efecto de zoom de cámara"`

**Generación de Audio:**

- `"Genera efectos de sonido de lluvia sobre una ventana"`
- `"Crea un audio de texto a voz que diga 'Hello World'"`

**Generación de Música:**

- `"Crea una melodía de piano tranquila, 30 segundos, instrumental"`
- `"Genera un tema orquestal épico para un tráiler"`
- `"Crea una pista de jazz fusion de 2 minutos con saxofón y piano"`
- `"Genera música inspirada en esta foto del atardecer, tranquila y nostálgica"`

**Generación de Modelos 3D:**

- `"Genera un modelo 3D de un gato de dibujos animados lindo"`
- `"Convierte esta imagen en un modelo 3D"`
- `"Crea un modelo 3D de una silla de madera y expórtalo como FBX"`
- `"Usa el modelo P1 para generar una espada medieval low-poly con 3000 caras para uso en videojuegos"`

La IA seleccionará automáticamente la habilidad apropiada y optimizará tu prompt siguiendo las mejores prácticas para obtener los mejores resultados.

## Licencia

Apache 2.0

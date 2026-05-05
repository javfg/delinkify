import asyncio
import json
from pathlib import Path

from loguru import logger

TARGET_HEIGHT = 480
MAX_VIDEO_SIZE_MB = 25
MAX_VIDEO_KBPS = 600  # quality ceiling
MIN_VIDEO_KBPS = 300  # quality floor
AUDIO_KBPS = 64


async def shrink(input_path: Path, output_path: Path) -> None:
    proc = await asyncio.create_subprocess_exec(
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'json',
        str(input_path),
        stdout=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    duration = float(json.loads(out)['format']['duration'])

    size_kbps = (MAX_VIDEO_SIZE_MB * 1024 * 8) / duration - AUDIO_KBPS
    video_kbps = int(min(size_kbps, MAX_VIDEO_KBPS))

    if video_kbps < MIN_VIDEO_KBPS:
        raise ValueError(f'video too long: {duration:.0f}s would need {video_kbps}kbps')

    logger.debug(f'shrinking {duration:.0f}s video at {video_kbps}kbps')

    proc = await asyncio.create_subprocess_exec(
        'ffmpeg',
        '-y',
        '-i',
        str(input_path),
        '-c:v',
        'libx264',
        '-vf',
        f'scale=-2:{TARGET_HEIGHT}',
        '-b:v',
        f'{video_kbps}k',
        '-maxrate',
        f'{int(video_kbps * 1.2)}k',
        '-bufsize',
        f'{video_kbps * 2}k',
        '-preset',
        'fast',
        '-c:a',
        'aac',
        '-b:a',
        f'{AUDIO_KBPS}k',
        '-movflags',
        '+faststart',
        str(output_path),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f'ffmpeg failed: {stderr.decode()}')

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.debug(f'shrunk video saved to {output_path}: {size_mb:.2f}mb')

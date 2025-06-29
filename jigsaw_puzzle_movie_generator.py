"""
Template for creating jigsaw puzzle reveal videos.

Config example:
{
  "clips": [
    {
      "background": "bg.png",
      "image": "puzzle_image.png",
      "rows": 2,
      "columns": 2,
      "text": "This is a puzzle!"
    }
  ]
}

Run:
$ PYTHONPATH=. python templates/jigsawreveal.py --input-dir /path/to/assets --output /tmp/output.mp4
"""

import os
import shutil
import tempfile
import json
import argparse
from pathlib import Path
from moviepy import (
    ImageClip, TextClip, CompositeVideoClip, 
    CompositeAudioClip,
    AudioFileClip, VideoFileClip,
    concatenate_videoclips, vfx, afx
)

from utils import get_asset_path
from jigsaw_puzzle_asset_generator import split_image

CANVA_WIDTH = 1920
CANVA_HEIGHT = 1080
FPS = 24

def parse_args():
    parser = argparse.ArgumentParser(description='Jigsaw Puzzle Video Generator')
    parser.add_argument('--input-dir', type=str, help='Input Directory with images and config')
    parser.add_argument('--output', type=str, help='Output video file', default='/tmp/jigsawreveal.mp4')
    parser.add_argument('--compile', action='store_true', help='Compile the video')
    parser.add_argument('--asset-path', type=str, help='Comma separated asset search paths', default=None)
    parser.add_argument('--fps', type=int, help='Frames per second for output video', default=24)
    parser.add_argument('--intro', type=str, help='Intro mp4 file to prepend', default=None)
    parser.add_argument('--outtro', type=str, help='Outtro mp4 file to append', default=None)
    parser.add_argument('--bgm', type=str, help='Background music mp3 file to loop', default=None)
    return parser.parse_args()

def create_puzzle_page(background_path, piece_paths, outline_path, frame_size,
                       asset_path=None,  # Asset path for additional assets
                       is_last_piece=False, text=None, piece_data=None,
                       is_first_piece=False):
    """Create a video clip for a single puzzle piece reveal, stacking previous pieces."""
    # Duration settings
    page_duration = 3  # 5 seconds per page
    fade_duration = 1  # 1 second fade in/out
    extra_last_duration = 3 if is_last_piece else 0
    total_duration = page_duration + extra_last_duration

    # Load assets
    bg_clip = ImageClip(background_path).resized((CANVA_WIDTH, CANVA_HEIGHT)).with_duration(total_duration)

    # Stack all previous puzzle pieces (already revealed)
    stacked_pieces = [
        ImageClip(p).with_duration(total_duration).with_position(
            piece_data[os.path.basename(p).replace('.png', '')]
        )
        for p in piece_paths
    ]

    # Current puzzle piece (fade in)
    current_piece_clip = stacked_pieces[-1]
    current_piece_clip = current_piece_clip.with_effects([vfx.CrossFadeIn(fade_duration)])
    stacked_pieces = stacked_pieces[:-1] + [current_piece_clip]

    # Outline (composite with current piece, fade in, fade out if last)
    outline_clip = ImageClip(outline_path).with_duration(page_duration).with_position((0, 0))
    if is_last_piece:
        outline_clip = outline_clip.with_effects([vfx.CrossFadeOut(fade_duration)])

    # Composite puzzle area (all pieces + outline)
    puzzle_area = CompositeVideoClip(stacked_pieces + [outline_clip], size=(outline_clip.w, outline_clip.h)).with_position((231, 162)).with_duration(total_duration)

    # Frame, logo, subscribe
    frame_path = str(get_asset_path(asset_path, "Frame.png"))
    frame_clip = ImageClip(frame_path).resized((outline_clip.w, outline_clip.h)).with_position((231, 162)).with_duration(total_duration)
    #logo_path = str(get_asset_path("Logo.png"))
    #logo_clip = ImageClip(logo_path).resized((202, 202)).with_position((811, 843)).with_duration(total_duration)
    subscribe_path = str(get_asset_path(asset_path, "Subscribe2.gif"))
    subscribe_clip = VideoFileClip(subscribe_path, has_mask=True).resized((379, 147)).with_position((1498, 52)).with_duration(total_duration)

    # Compose all
    clips = [bg_clip, puzzle_area, frame_clip,
             #logo_clip,
             subscribe_clip]

    # Add text if this is the last piece and text is provided
    if is_last_piece and text:
        text_clip = TextClip(
            text=text,
            font=str(get_asset_path(asset_path, "Super_Adorable.ttf")),
            font_size=200,
            color="black",
            stroke_color='#ffffff',
            stroke_width=5,
            margin=(50, 50),
        ).with_position(("center", 714))
        text_clip = text_clip.with_duration(extra_last_duration).with_start(page_duration).with_effects([
            vfx.CrossFadeIn(fade_duration)
        ])
        clips.append(text_clip)

        # Play Confetti.gif at center at the same time as text_clip
        confetti_path = str(get_asset_path(asset_path, "Confetti.gif"))
        confetti_clip = VideoFileClip(confetti_path, has_mask=True)
        # Center confetti
        confetti_clip = confetti_clip.with_start(page_duration).with_duration(confetti_clip.duration)
        confetti_clip = confetti_clip.with_position((
            (CANVA_WIDTH - confetti_clip.w) // 2,
            (CANVA_HEIGHT - confetti_clip.h) // 2
        ))
        clips.append(confetti_clip)

    # Add guitar string sound at the beginning
    guitar_path = str(get_asset_path(asset_path, "guitar-string-fade-out-332451.mp3"))
    guitar_audio = AudioFileClip(guitar_path)
    guitar_audio = guitar_audio.with_duration(1.5)

    composite = CompositeVideoClip(clips).with_duration(total_duration)
    # Add audio if not last page (or always, as intro sound)
    composite = composite.with_audio(guitar_audio)
    return composite

def make_jigsaw_clip(config, asset_path):
    """Create a complete jigsaw puzzle sequence for one image"""
    background_path = str(get_asset_path(asset_path, config['background']))
    image_path = str(get_asset_path(asset_path, config['image']))
    rows = config.get('rows', 2)
    columns = config.get('columns', 2)
    text = config.get('text', "")
    order = config.get('order', None)

    tmp_dir = tempfile.mkdtemp()
    try:
        # Generate jigsaw pieces (files will be created in tmp_dir)
        split_image(image_path, rows, columns, tmp_dir)
        # Load piece data
        import json
        piece_data_path = os.path.join(tmp_dir, 'piece_data.json')
        with open(piece_data_path) as f:
            piece_data = json.load(f)
        total_pieces = rows * columns
        frame_size = (1550, 880)
        # Generate all (row, col) pairs
        all_indices = [(r, c) for r in range(rows) for c in range(columns)]
        # Determine reveal order
        if order is not None:
            # Use provided order (list of indices)
            reveal_order = [all_indices[i] for i in order]
        else:
            # Default: random order, seed from filename
            import hashlib, random
            seed = int(hashlib.md5(os.path.basename(image_path).encode()).hexdigest(), 16) % (2**32)
            rng = random.Random(seed)
            reveal_order = all_indices.copy()
            rng.shuffle(reveal_order)
        pages = []
        revealed_pieces = []
        for piece_idx, (row, col) in enumerate(reveal_order):
            piece_name = f'piece_{row}_{col}.png'
            piece_path = os.path.join(tmp_dir, piece_name)
            revealed_pieces.append(piece_path)
            outline_path = os.path.join(tmp_dir, 'piece_outline.png')
            is_last_piece = (piece_idx == total_pieces - 1)
            is_first_piece = (piece_idx == 0)
            page = create_puzzle_page(
                background_path,
                revealed_pieces.copy(),
                outline_path,
                frame_size,
                asset_path=str(tmp_dir) + ',' + asset_path,
                is_last_piece=is_last_piece,
                text=text if is_last_piece else None,
                piece_data=piece_data,
                is_first_piece=is_first_piece,
            )
            pages.append(page)
        final_clip = concatenate_videoclips(pages, method="compose")
        return final_clip
    finally:
        shutil.rmtree(tmp_dir)

def generate_jigsaw_video(input_dir, output, asset_path=None, fps=24, compile=False, logger=None, intro=None, outtro=None, bgm=None):
    """Entry point for generating jigsaw video from arguments."""
    with open(f"{input_dir}/config.json") as f:
        config = json.load(f)
    # Set asset path from argument or input dir
    asset_path = asset_path if asset_path else input_dir
    asset_path = os.path.dirname(os.path.abspath(__file__)) + '/assets,' + asset_path
    clips = []
    if intro:
        clips.append(VideoFileClip(intro))
    for page in config.get('clips', []):
        clips.append(make_jigsaw_clip(page, asset_path))
    if outtro:
        clips.append(VideoFileClip(outtro))
    if not clips:
        print("No valid clips found.")
        return
    final = clips[0] if len(clips) == 1 else concatenate_videoclips(clips, method="compose")
    if bgm:
        audio_bgm = AudioFileClip(bgm)
        audio_bgm = (
            audio_bgm.with_effects([
                afx.AudioLoop(duration=final.duration),
                afx.AudioFadeOut(duration=2),
                afx.MultiplyVolume(0.33)
            ])
        )
        # Mix with existing audio
        if final.audio is not None:
            final = final.with_audio(CompositeAudioClip([final.audio, audio_bgm]))
        else:
            final = final.with_audio(audio_bgm)
    final.write_videofile(output, fps=fps, codec="libx264", audio_codec="aac", logger=logger)


def main():
    args = parse_args()
    generate_jigsaw_video(
        input_dir=args.input_dir,
        output=args.output,
        asset_path=args.asset_path,
        fps=args.fps,
        compile=args.compile,
        intro=args.intro,
        outtro=args.outtro,
        bgm=args.bgm
    )

if __name__ == '__main__':
    main()

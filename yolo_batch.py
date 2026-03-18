
"""
🤖 YOLO Batch Inference
━━━━━━━━━━━━━━━━━━━━━━
Run YOLO object detection on a batch of images using
the Ultralytics YOLO library.

HOW IT WORKS:
  1. Accepts a directory of images or individual image paths
  2. Runs YOLO detection on all images in one batch
  3. Saves annotated results and prints a summary

SETUP:
  pip install ultralytics

USAGE:
  python yolo_batch.py --source images/         # folder of images
  python yolo_batch.py --source img1.jpg img2.png
  python yolo_batch.py --model yolov8n.pt --source images/ --save
"""

import argparse
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="YOLO Batch Inference — detect objects in a batch of images"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="YOLO model weights (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--source",
        nargs="+",
        required=True,
        help="Image file(s) or directory to run inference on",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default: 0.25)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save annotated result images",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for saved results (default: results/)",
    )
    return parser.parse_args()


def collect_images(sources):
    """Gather all image paths from the provided sources (files or directories)."""
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    image_paths = []

    for source in sources:
        path = Path(source)
        if path.is_dir():
            for file in sorted(path.iterdir()):
                if file.suffix.lower() in image_extensions:
                    image_paths.append(str(file))
        elif path.is_file() and path.suffix.lower() in image_extensions:
            image_paths.append(str(path))
        else:
            print(f"⚠️  Skipping '{source}' — not a valid image or directory")

    return image_paths


def run_batch(model_path, image_paths, conf_threshold, save, output_dir):
    """Load the YOLO model and run batch inference."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ERROR: ultralytics is not installed.")
        print("   👉 Run:  pip install ultralytics")
        sys.exit(1)

    if not image_paths:
        print("❌ No valid images found. Please check your --source argument.")
        sys.exit(1)

    print(f"🔍 Loading model: {model_path}")
    model = YOLO(model_path)

    print(f"📦 Running batch inference on {len(image_paths)} image(s)...")

    results = model(
        image_paths,
        conf=conf_threshold,
        save=save,
        project=output_dir,
        name="batch",
        exist_ok=True,
    )

    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("📊 YOLO Batch Results Summary")
    print("=" * 50)

    total_detections = 0
    for idx, result in enumerate(results):
        image_name = Path(image_paths[idx]).name
        num_boxes = len(result.boxes) if result.boxes is not None else 0
        total_detections += num_boxes

        detected_classes = []
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                detected_classes.append(f"{class_name} ({confidence:.1%})")

        detected_str = ", ".join(detected_classes) if detected_classes else "none"
        print(f"  🖼️  {image_name}: {num_boxes} detection(s) — {detected_str}")

    print("-" * 50)
    print(f"✅ Total detections across all images: {total_detections}")

    if save:
        save_path = Path(output_dir) / "batch"
        print(f"💾 Annotated images saved to: {save_path}/")

    print("=" * 50)

    return results


def main():
    args = parse_args()

    print("=" * 50)
    print("🤖 YOLO Batch Inference")
    print("=" * 50)

    image_paths = collect_images(args.source)

    if not image_paths:
        print("❌ No images found in the specified source(s).")
        sys.exit(1)

    print(f"🗂️  Found {len(image_paths)} image(s) to process")

    run_batch(
        model_path=args.model,
        image_paths=image_paths,
        conf_threshold=args.conf,
        save=args.save,
        output_dir=args.output,
    )

    print("\n🎉 Batch inference complete!")


if __name__ == "__main__":
    main()

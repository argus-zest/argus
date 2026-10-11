import argparse
import io
import json
import os
import random
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import boto3

# Ensure layer is importable
sys.path.insert(0, os.path.abspath("backend/layer/python"))
from common.nova import analyze_hazard


def resize_image_bytes(data: bytes, max_edge: int = 1280) -> bytes:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if max(w, h) > max_edge:
            if w > h:
                new_w = max_edge
                new_h = int(h * (max_edge / w))
            else:
                new_h = max_edge
                new_w = int(w * (max_edge / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except Exception:
        return data


def parse_xml_damage_classes(xml_path: str) -> set[str]:
    classes = set()
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for obj in root.findall("object"):
            name = obj.find("name")
            if name is not None and name.text:
                classes.add(name.text.strip())
    except Exception:
        pass
    return classes


def main():
    parser = argparse.ArgumentParser(description="Evaluate Nova hazard analysis against RDD2022 India dataset")
    parser.add_argument("--data-dir", default="eval/data/rdd2022_india", help="Path to RDD2022 India dataset")
    parser.add_argument("--out-dir", default="eval/results", help="Path to output results directory")
    args = parser.parse_args()

    if not os.path.exists(args.data_dir) or not os.listdir(args.data_dir):
        print(f"[!] RDD2022 India dataset directory '{args.data_dir}' is missing or empty.")
        print("    Please follow instructions in 'eval/data/README.md' to supply dataset images and XML annotations.")
        sys.exit(0)

    # Search for images and xmls
    img_dir = os.path.join(args.data_dir, "images")
    if not os.path.exists(img_dir):
        img_dir = args.data_dir

    xml_dir = os.path.join(args.data_dir, "annotations", "xmls")
    if not os.path.exists(xml_dir):
        xml_dir = args.data_dir

    all_images = [f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not all_images:
        print("[!] No images found in dataset directory. Exiting.")
        sys.exit(0)

    pos_candidates = []
    neg_candidates = []

    for img_name in all_images:
        base_name = os.path.splitext(img_name)[0]
        xml_path = os.path.join(xml_dir, f"{base_name}.xml")
        if not os.path.exists(xml_path):
            continue

        classes = parse_xml_damage_classes(xml_path)
        if "D40" in classes:
            pos_candidates.append(img_name)
        elif not classes.intersection({"D00", "D10", "D20", "D40"}):
            neg_candidates.append(img_name)

    print(f"[*] Found {len(pos_candidates)} D40 pothole positives and {len(neg_candidates)} clear negatives.")
    if not pos_candidates and not neg_candidates:
        print("[!] No matching annotation XMLs found. Exiting.")
        sys.exit(0)

    random.seed(42)
    sample_pos = random.sample(pos_candidates, min(25, len(pos_candidates)))
    sample_neg = random.sample(neg_candidates, min(25, len(neg_candidates)))

    print(f"[*] Sampled {len(sample_pos)} positives and {len(sample_neg)} negatives for evaluation.")

    tp = fp = fn = tn = 0

    # Evaluate Positives (Ground Truth = Pothole)
    for img_name in sample_pos:
        img_path = os.path.join(img_dir, img_name)
        with open(img_path, "rb") as f:
            data = resize_image_bytes(f.read())
        res = analyze_hazard(data, "jpeg")
        predicted_pos = (res.get("hazard_type") == "pothole") and (res.get("confidence", 0) >= 0.5)
        if predicted_pos:
            tp += 1
        else:
            fn += 1

    # Evaluate Negatives (Ground Truth = Clear)
    for img_name in sample_neg:
        img_path = os.path.join(img_dir, img_name)
        with open(img_path, "rb") as f:
            data = resize_image_bytes(f.read())
        res = analyze_hazard(data, "jpeg")
        predicted_pos = (res.get("hazard_type") == "pothole") and (res.get("confidence", 0) >= 0.5)
        if predicted_pos:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    model_id = os.environ.get("NOVA_MODEL_ID", "amazon.nova-lite-v1:0")
    run_at = datetime.now(timezone.utc).isoformat()

    results = {
        "dataset": "RDD2022 India",
        "level": "image",
        "n_pos": len(sample_pos),
        "n_neg": len(sample_neg),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "model_id": model_id,
        "run_at": run_at,
    }

    os.makedirs(args.out_dir, exist_ok=True)
    out_file = os.path.join(args.out_dir, "rdd2022.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[+] Wrote evaluation results to {out_file}:")
    print(f"    Precision: {precision:.2%}, Recall: {recall:.2%}, F1: {f1:.3f} (image-level)")

    bucket = os.environ.get("BUCKET")
    if bucket:
        try:
            s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))
            s3.put_object(
                Bucket=bucket,
                Key="eval/rdd2022.json",
                Body=json.dumps(results, indent=2),
                ContentType="application/json",
            )
            print(f"[+] Uploaded results to s3://{bucket}/eval/rdd2022.json")
        except Exception as e:
            print(f"[!] S3 upload warning: {e}")


if __name__ == "__main__":
    main()

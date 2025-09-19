#!/usr/bin/env python3
# Create manifest for latest iteration and snapshot dataset + model checksums.

import os, json, hashlib, glob, argparse, subprocess
from datetime import datetime

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def build_manifest(models_dir="models", dataset="unsupervised/curated.jsonl", out="unsupervised/manifests"):
    os.makedirs(out, exist_ok=True)
    # find latest iteration
    iterations = sorted([d for d in glob.glob(os.path.join(models_dir,"iteration_*"))])
    manifest = {"generated_at": datetime.utcnow().isoformat()+"Z", "dataset": None, "models": []}
    if dataset and os.path.exists(dataset):
        manifest["dataset"] = {"path": dataset, "sha256": sha256_file(dataset)}
    for it in iterations:
        m = {"path": it}
        mf = os.path.join(it, "manifest.json")
        if os.path.exists(mf):
            with open(mf, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            m.update(data)
            # compute model dir hash (hash of files list)
            files = sorted(glob.glob(os.path.join(it, "**/*"), recursive=True))
            # compute combined hash
            hh = hashlib.sha256()
            for f in files:
                if os.path.isfile(f):
                    hh.update(f.encode("utf-8"))
                    hh.update(str(os.path.getsize(f)).encode("utf-8"))
            m["dir_hash"] = hh.hexdigest()
        manifest["models"].append(m)
    outfile = os.path.join(out, f"manifest_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(outfile, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print("[manifest] wrote", outfile)
    return outfile

def sign_manifest(path, gpg_key=None):
    # optional: gpg --armor --output path.asc --detach-sign path
    try:
        cmd = ["gpg", "--armor", "--detach-sign", path]
        if gpg_key:
            cmd = ["gpg", "--local-user", gpg_key, "--armor", "--detach-sign", path]
        subprocess.check_call(cmd)
        print("[manifest] signed:", path + ".asc")
    except Exception as e:
        print("[manifest] gpg sign failed (skipping):", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models_dir", default="models")
    parser.add_argument("--dataset", default="unsupervised/curated.jsonl")
    parser.add_argument("--out", default="unsupervised/manifests")
    parser.add_argument("--sign", action="store_true")
    parser.add_argument("--gpg_key", default=None)
    args = parser.parse_args()
    mf = build_manifest(args.models_dir, args.dataset, args.out)
    if args.sign:
        sign_manifest(mf, args.gpg_key)

"""Download/convert UltraChat SFT examples to chat-template JSONL for fine-tuning.

This prepares training data only; it does not train or replace the live chat model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/ultrachat_train.jsonl"))
    parser.add_argument("--split", choices=("train_sft", "test_sft"), default="train_sft")
    parser.add_argument("--limit", type=int, default=0, help="maximum rows (0 means the whole split)")
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be zero or greater")
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install the optional dependency first: pip install datasets") from exc

    dataset = load_dataset("HuggingFaceH4/ultrachat_200k", split=args.split)
    if args.limit:
        dataset = dataset.select(range(min(args.limit, len(dataset))))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.output.open("w", encoding="utf-8") as out:
        for row in dataset:
            messages = row.get("messages") or []
            clean = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
                if m.get("role") in {"system", "user", "assistant"}
                and isinstance(m.get("content"), str) and m["content"].strip()
            ]
            if len(clean) < 2 or clean[-1]["role"] != "assistant":
                continue
            out.write(json.dumps({"messages": clean}, ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written:,} conversations to {args.output}")


if __name__ == "__main__":
    main()

"""Convert OpenAssistant OASST1 message trees into chat-message JSONL for SFT."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FILES = {
    "train": "data/train-00000-of-00001-b42a775f407cee45.parquet",
    "validation": "data/validation-00000-of-00001-134b8fd0c89408b6.parquet",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=FILES, default="train")
    parser.add_argument("--language", default="en", help="language code; use 'all' to include every language")
    parser.add_argument("--limit", type=int, default=0, help="maximum conversations (0 means no limit)")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be zero or greater")
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("Install optional dependencies first: pip install pandas pyarrow huggingface_hub") from exc

    url = "hf://datasets/OpenAssistant/oasst1/" + FILES[args.split]
    df = pd.read_parquet(url)
    required = {"message_id", "parent_id", "text", "role", "lang"}
    if not required.issubset(df.columns):
        raise SystemExit("Unexpected OASST1 schema; expected columns: " + ", ".join(sorted(required)))
    df = df[df["deleted"].fillna(False) == False]
    df = df[df["review_result"].fillna(False) == True]
    if args.language.lower() != "all":
        df = df[df["lang"] == args.language]

    rows = {str(row.message_id): row for row in df.itertuples(index=False)}
    children: dict[str, list] = {}
    for row in rows.values():
        parent = getattr(row, "parent_id", None)
        if isinstance(parent, str) and parent in rows:
            children.setdefault(parent, []).append(row)
    # Keep the highest-ranked reply at each branch; produce one prompt/completion sample per assistant leaf.
    for options in children.values():
        options.sort(key=lambda r: (getattr(r, "rank", 0) if getattr(r, "rank", None) is not None else 0,
                                    str(r.message_id)))

    args.output = args.output or Path(f"data/oasst1_{args.split}.jsonl")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.output.open("w", encoding="utf-8") as out:
        for leaf in rows.values():
            if leaf.role != "assistant" or str(leaf.message_id) in children:
                continue
            path, cur, seen = [], leaf, set()
            while cur is not None and str(cur.message_id) not in seen:
                seen.add(str(cur.message_id))
                role = "user" if cur.role == "prompter" else "assistant"
                path.append({"role": role, "content": str(cur.text)})
                parent = getattr(cur, "parent_id", None)
                cur = rows.get(parent) if isinstance(parent, str) else None
            messages = list(reversed(path))
            if not messages or messages[0]["role"] != "user" or messages[-1]["role"] != "assistant":
                continue
            out.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
            written += 1
            if args.limit and written >= args.limit:
                break
    print(f"Wrote {written:,} conversations to {args.output}")


if __name__ == "__main__":
    main()

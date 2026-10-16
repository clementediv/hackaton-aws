"""Inspect the exact public evidence retrieved for a chatbot question."""

import argparse
import json
from dataclasses import asdict

from ruta.knowledge import context_for, retrieve

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--context", action="store_true")
    args = parser.parse_args()
    if args.context:
        print(context_for(args.question))
    else:
        print(
            json.dumps(
                [asdict(hit) for hit in retrieve(args.question)], ensure_ascii=False, indent=2
            )
        )

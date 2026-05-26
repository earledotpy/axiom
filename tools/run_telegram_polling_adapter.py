from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.gateways.telegram_bot_adapter import (  # noqa: E402
    TelegramBotApiClient,
    TelegramBotApiError,
    TelegramPollingAdapter,
)


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bounded AXIOM Telegram Bot polling adapter."
    )
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    parser.add_argument("--loop", action="store_true", help="Continue polling until interrupted")
    parser.add_argument("--offset", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.once and args.loop:
        print("Error: choose either --once or --loop, not both", file=sys.stderr)
        return 1

    token = os.environ.get(BOT_TOKEN_ENV, "")
    if not token:
        print(f"Error: {BOT_TOKEN_ENV} is not set", file=sys.stderr)
        return 1

    try:
        client = TelegramBotApiClient(token)
        adapter = TelegramPollingAdapter(client=client)
    except TelegramBotApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    offset = args.offset
    run_loop = args.loop

    try:
        while True:
            batch = adapter.poll_once(
                offset=offset,
                timeout_seconds=args.timeout,
                limit=args.limit,
            )
            offset = batch.offset or offset
            payload = batch.to_dict()
            if args.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print("AXIOM Telegram polling adapter")
                print("==============================")
                print(f"update_count: {payload['update_count']}")
                print(f"next_offset: {payload['offset']}")
                for result in payload["results"]:
                    print(
                        f"- update={result['update_id']} action={result['action']} "
                        f"accepted={result['accepted']} reason={result['denial_reason']}"
                    )

            if not run_loop:
                return 0
            time.sleep(args.sleep)
    except TelegramBotApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

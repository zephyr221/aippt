import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from .render import build_pptx
from .schema import Deck
from .validate import validate_deck


def load_deck(path: Path) -> Deck:
    try:
        return Deck.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise SystemExit(f"Invalid Deck IR schema: {exc}") from exc


def validate_command(args: argparse.Namespace) -> None:
    deck = load_deck(Path(args.deck_json))
    issues = validate_deck(deck)
    if issues:
        print(json.dumps([issue.__dict__ for issue in issues], ensure_ascii=False, indent=2))
        raise SystemExit(1)
    print("ok")


def build_command(args: argparse.Namespace) -> None:
    deck = load_deck(Path(args.deck_json))
    issues = validate_deck(deck)
    if issues:
        print(json.dumps([issue.__dict__ for issue in issues], ensure_ascii=False, indent=2))
        raise SystemExit(1)
    output = build_pptx(deck, args.output)
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser(prog="aippt-build")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("deck_json")
    validate_parser.set_defaults(func=validate_command)

    build_parser = sub.add_parser("build")
    build_parser.add_argument("deck_json")
    build_parser.add_argument("output")
    build_parser.set_defaults(func=build_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


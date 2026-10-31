"""CLI: python main.py [--tickets data/sample_tickets.json] [--offline] [--eval]"""
import argparse

from triage.pipeline import load_tickets, run, summarize
from triage.evaluate import evaluate


def main() -> None:
    p = argparse.ArgumentParser(description="AI support-ticket triage workflow")
    p.add_argument("--tickets", default="data/sample_tickets.json")
    p.add_argument("--out", default="out")
    p.add_argument("--offline", action="store_true", help="skip Claude, use keyword heuristic")
    p.add_argument("--eval", action="store_true", help="score against ground-truth labels")
    args = p.parse_args()

    tickets = load_tickets(args.tickets)
    results = run(tickets, args.out, offline=args.offline)
    print(summarize(results))
    print(f"\nOutputs written to {args.out}/")

    if args.eval:
        print("\n" + evaluate(tickets, results))


if __name__ == "__main__":
    main()

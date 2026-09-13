"""Prepare a reference review or record its exact explicit human admission; no agents."""
import argparse
from pathlib import Path
from live.v2.reference_baseline import admit, prepare_review

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    review = commands.add_parser('review')
    for name in ('prepared', 'browser', 'extensions', 'output'):
        review.add_argument('--' + name, type=Path, required=True)
    admission = commands.add_parser('admit')
    for name in ('review', 'output'):
        admission.add_argument('--' + name, type=Path, required=True)
    for name in ('review-sha256', 'confirmation-text', 'confirmation-source'):
        admission.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if args.command == 'review':
        report = prepare_review(args.prepared.resolve(), args.browser.resolve(), args.extensions.resolve(), Path(__file__).resolve().parents[1], args.output.resolve())
        print('Review prepared: ' + report['reviewSha256'] + '; no admission or paid authorization issued.')
    else:
        admit(args.review.resolve(), args.output.resolve(), args.review_sha256, args.confirmation_text, args.confirmation_source)
        print('Exact reference admission recorded; no paid authorization issued.')

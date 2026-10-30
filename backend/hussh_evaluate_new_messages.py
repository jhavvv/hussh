"""Evaluate huSSh's current combined risk output on a fixed, separate test set.

Copy this file and hussh_independent_messages.csv into backend/ then run:
    python hussh_evaluate_new_messages.py

This is a small, authored fictional test set, not an independently sourced,
representative real-world corpus. Do not tune the classifier on these cases
and then present the same scores as independent validation.
"""
import csv
from pathlib import Path
from intelligence import analyze

DATA = Path(__file__).with_name('hussh_independent_messages.csv')


def main():
    rows = list(csv.DictReader(DATA.open(encoding='utf-8-sig', newline='')))
    tp = tn = fp = fn = 0
    high_risk_scams = 0
    print(f"{'ID':<5} {'Type':<12} {'Expected':<12} {'Actual':<8} {'Score':>5} {'Outcome':<7}")
    print('-' * 58)
    for row in rows:
        result = analyze(row['message'])
        predicted = 'scam' if result['risk'] in ('Medium', 'High') else 'legitimate'
        expected = row['expected_label']
        correct = predicted == expected
        if expected == 'scam':
            if correct: tp += 1
            else: fn += 1
            if result['risk'] == 'High': high_risk_scams += 1
        else:
            if correct: tn += 1
            else: fp += 1
        print(f"{row['id']:<5} {row['category'][:12]:<12} {expected:<12} {result['risk']:<8} {result['score']:>5} {'PASS' if correct else 'FAIL':<7}")
    total = len(rows)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    accuracy = (tp + tn) / total if total else 0
    print('\nEvaluation: Low = predicted legitimate; Medium or High = predicted suspicious.')
    print(f'Total: {total} | TP={tp} FP={fp} TN={tn} FN={fn}')
    print(f'Accuracy={accuracy:.3f} Precision={precision:.3f} Recall={recall:.3f} F1={f1:.3f}')
    print(f'Scam messages rated High: {high_risk_scams}/{tp + fn}')
    print('Caution: fixed fictional cases; results are preliminary, not real-world accuracy.')


if __name__ == '__main__':
    main()

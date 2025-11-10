"""
Automated RAG Accuracy Evaluation

Compares RAG system answers against ground truth to measure accuracy.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import re

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rag_system import WellReportRAG


class RAGEvaluator:
    """Evaluate RAG system accuracy against ground truth"""

    def __init__(self, ground_truth_file: str = 'tests/ground_truth.json'):
        """Initialize evaluator with ground truth"""
        self.ground_truth_file = Path(ground_truth_file)
        self.ground_truth = self._load_ground_truth()
        self.rag = None

    def _load_ground_truth(self) -> Dict:
        """Load ground truth from JSON"""
        if not self.ground_truth_file.exists():
            raise FileNotFoundError(
                f"Ground truth file not found: {self.ground_truth_file}\n"
                f"Run: python tests/build_ground_truth.py first"
            )

        with open(self.ground_truth_file, 'r') as f:
            return json.load(f)

    def initialize_rag(self):
        """Initialize RAG system"""
        if self.rag is None:
            print("Initializing RAG system...")
            self.rag = WellReportRAG()
            print("RAG system ready!")

    def calculate_answer_similarity(self, rag_answer: str, ground_truth_answer: str,
                                    expected_info: List[str]) -> float:
        """
        Calculate similarity between RAG answer and ground truth

        Returns: score between 0.0 and 1.0
        """
        rag_lower = rag_answer.lower()
        truth_lower = ground_truth_answer.lower()

        # Check if expected information is present
        info_found = 0
        for info in expected_info:
            info_lower = info.lower()
            if info_lower in rag_lower:
                info_found += 1

        info_score = info_found / len(expected_info) if expected_info else 0.0

        # Check for exact match of key numbers/identifiers
        # Extract numbers from both answers
        rag_numbers = set(re.findall(r'\d+\.?\d*', rag_answer))
        truth_numbers = set(re.findall(r'\d+\.?\d*', ground_truth_answer))

        if truth_numbers:
            number_overlap = len(rag_numbers & truth_numbers) / len(truth_numbers)
        else:
            number_overlap = 1.0

        # Check for "not found" responses (for negative questions)
        negative_phrases = ['not found', 'not available', "don't know", 'cannot find',
                           'no information', 'not mentioned']

        rag_is_negative = any(phrase in rag_lower for phrase in negative_phrases)
        truth_is_negative = any(phrase in truth_lower for phrase in negative_phrases)

        if truth_is_negative:
            # For negative questions, check if RAG also says "not found"
            negative_score = 1.0 if rag_is_negative else 0.0
            return negative_score

        # Weighted average
        final_score = 0.6 * info_score + 0.4 * number_overlap

        return final_score

    def evaluate_single_question(self, q_id: str, question_data: Dict) -> Dict:
        """Evaluate a single question"""
        question = question_data['question']
        well = question_data.get('well')
        ground_truth_answer = question_data['answer']
        expected_info = question_data['expected_info']

        # Query RAG system
        start_time = time.time()
        try:
            result = self.rag.query(question, well_name=well, n_results=5)
            rag_answer = result['answer']
            query_time = time.time() - start_time
            error = None
        except Exception as e:
            rag_answer = f"ERROR: {e}"
            query_time = time.time() - start_time
            error = str(e)

        # Calculate accuracy
        if error:
            accuracy = 0.0
        else:
            accuracy = self.calculate_answer_similarity(
                rag_answer, ground_truth_answer, expected_info
            )

        return {
            'q_id': q_id,
            'question': question,
            'well': well,
            'category': question_data['category'],
            'rag_answer': rag_answer,
            'ground_truth_answer': ground_truth_answer,
            'expected_info': expected_info,
            'accuracy': accuracy,
            'query_time': query_time,
            'error': error,
            'passed': accuracy >= 0.8  # 80% threshold for passing
        }

    def evaluate_all(self) -> Dict:
        """Evaluate all questions and return results"""
        self.initialize_rag()

        results = []
        category_results = {}

        total_questions = len(self.ground_truth['answers'])
        print(f"\nEvaluating {total_questions} questions...\n")

        for i, (q_id, question_data) in enumerate(self.ground_truth['answers'].items(), 1):
            # Skip questions that weren't validated
            if not question_data.get('validated', True):
                continue

            print(f"[{i}/{total_questions}] {q_id}: {question_data['question'][:60]}...")

            result = self.evaluate_single_question(q_id, question_data)
            results.append(result)

            # Track by category
            category = result['category']
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result)

            # Print result
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"    {status} | Accuracy: {result['accuracy']:.1%} | Time: {result['query_time']:.2f}s")

        # Calculate overall statistics
        total_evaluated = len(results)
        passed = sum(1 for r in results if r['passed'])
        failed = total_evaluated - passed

        avg_accuracy = sum(r['accuracy'] for r in results) / total_evaluated if results else 0
        avg_time = sum(r['query_time'] for r in results) / total_evaluated if results else 0
        max_time = max(r['query_time'] for r in results) if results else 0
        min_time = min(r['query_time'] for r in results) if results else 0

        # Calculate category statistics
        category_stats = {}
        for category, cat_results in category_results.items():
            cat_passed = sum(1 for r in cat_results if r['passed'])
            cat_total = len(cat_results)
            cat_avg_accuracy = sum(r['accuracy'] for r in cat_results) / cat_total

            category_stats[category] = {
                'total': cat_total,
                'passed': cat_passed,
                'failed': cat_total - cat_passed,
                'accuracy': cat_avg_accuracy,
                'pass_rate': cat_passed / cat_total if cat_total > 0 else 0
            }

        return {
            'metadata': {
                'evaluated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_questions': total_evaluated,
                'ground_truth_file': str(self.ground_truth_file)
            },
            'summary': {
                'total_evaluated': total_evaluated,
                'passed': passed,
                'failed': failed,
                'pass_rate': passed / total_evaluated if total_evaluated > 0 else 0,
                'avg_accuracy': avg_accuracy,
                'target_accuracy': 0.90,
                'meets_target': avg_accuracy >= 0.90,
                'avg_query_time': avg_time,
                'max_query_time': max_time,
                'min_query_time': min_time,
                'target_time': 10.0,
                'meets_time_target': avg_time < 10.0
            },
            'category_stats': category_stats,
            'individual_results': results
        }

    def print_report(self, results: Dict):
        """Print formatted evaluation report"""
        summary = results['summary']
        category_stats = results['category_stats']

        print("\n" + "="*80)
        print("RAG ACCURACY EVALUATION REPORT")
        print("="*80)

        # Overall summary
        print(f"\nOVERALL SUMMARY:")
        print(f"-"*80)
        print(f"Total Questions:     {summary['total_evaluated']}")
        print(f"Passed (≥80%):       {summary['passed']} ({summary['pass_rate']:.1%})")
        print(f"Failed (<80%):       {summary['failed']}")
        print(f"\nAccuracy:            {summary['avg_accuracy']:.1%}")
        print(f"Target:              {summary['target_accuracy']:.1%}")
        print(f"Status:              {'✓ MEETS TARGET' if summary['meets_target'] else '✗ BELOW TARGET'}")

        print(f"\nPerformance:")
        print(f"Average Time:        {summary['avg_query_time']:.2f}s")
        print(f"Min Time:            {summary['min_query_time']:.2f}s")
        print(f"Max Time:            {summary['max_query_time']:.2f}s")
        print(f"Target:              <{summary['target_time']:.1f}s")
        print(f"Status:              {'✓ MEETS TARGET' if summary['meets_time_target'] else '✗ TOO SLOW'}")

        # Category breakdown
        print(f"\n{'='*80}")
        print(f"CATEGORY BREAKDOWN:")
        print(f"{'='*80}")

        for category, stats in category_stats.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Total:     {stats['total']}")
            print(f"  Passed:    {stats['passed']} ({stats['pass_rate']:.1%})")
            print(f"  Failed:    {stats['failed']}")
            print(f"  Accuracy:  {stats['accuracy']:.1%}")

        # Failed questions
        failed_results = [r for r in results['individual_results'] if not r['passed']]
        if failed_results:
            print(f"\n{'='*80}")
            print(f"FAILED QUESTIONS ({len(failed_results)}):")
            print(f"{'='*80}")

            for i, result in enumerate(failed_results, 1):
                print(f"\n{i}. [{result['q_id']}] {result['question']}")
                print(f"   Well: {result['well']}")
                print(f"   Accuracy: {result['accuracy']:.1%}")
                print(f"   Expected: {', '.join(result['expected_info'])}")
                print(f"   Ground Truth: {result['ground_truth_answer'][:100]}...")
                print(f"   RAG Answer:   {result['rag_answer'][:100]}...")

        print(f"\n{'='*80}\n")

    def save_results(self, results: Dict, output_file: str = 'tests/evaluation_results.json'):
        """Save evaluation results to file"""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}")


def main():
    """Main evaluation function"""
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate RAG accuracy')
    parser.add_argument('--ground-truth', default='tests/ground_truth.json',
                       help='Path to ground truth file')
    parser.add_argument('--output', default='tests/evaluation_results.json',
                       help='Path to save results')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed results')

    args = parser.parse_args()

    # Run evaluation
    evaluator = RAGEvaluator(args.ground_truth)
    results = evaluator.evaluate_all()

    # Print report
    evaluator.print_report(results)

    # Save results
    evaluator.save_results(results, args.output)

    # Exit with error code if targets not met
    summary = results['summary']
    if not (summary['meets_target'] and summary['meets_time_target']):
        print("\n⚠️  WARNING: Did not meet all targets!")
        sys.exit(1)
    else:
        print("\n✓ All targets met!")
        sys.exit(0)


if __name__ == '__main__':
    main()

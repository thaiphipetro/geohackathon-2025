"""
Performance Benchmark Suite for RAG System

Measures query speed and system performance metrics.
Target: <10 seconds average query time
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rag_system import WellReportRAG


class PerformanceBenchmark:
    """Benchmark RAG system performance"""

    def __init__(self):
        self.rag = None
        self.results = []

    def initialize_rag(self):
        """Initialize RAG system and measure startup time"""
        print("Initializing RAG system...")
        start_time = time.time()
        self.rag = WellReportRAG()
        init_time = time.time() - start_time
        print(f"[OK] RAG system ready in {init_time:.2f}s\n")
        return init_time

    def benchmark_single_query(self, query: str, well_name: str = None,
                               n_results: int = 5, category: str = "general") -> Dict:
        """Benchmark a single query"""
        # Measure total time
        start_time = time.time()

        try:
            result = self.rag.query(query, well_name=well_name, n_results=n_results)
            total_time = time.time() - start_time

            # Extract component times from metadata if available
            metadata = result.get('metadata', {})

            return {
                'query': query,
                'well': well_name,
                'category': category,
                'total_time': total_time,
                'embedding_time': metadata.get('embedding_time', 0),
                'retrieval_time': metadata.get('retrieval_time', 0),
                'llm_time': metadata.get('llm_generation_time', 0),
                'num_sources': len(result.get('sources', [])),
                'answer_length': len(result.get('answer', '')),
                'success': True,
                'error': None
            }
        except Exception as e:
            total_time = time.time() - start_time
            return {
                'query': query,
                'well': well_name,
                'category': category,
                'total_time': total_time,
                'success': False,
                'error': str(e)
            }

    def run_benchmark_suite(self):
        """Run comprehensive benchmark suite"""
        print("="*80)
        print("PERFORMANCE BENCHMARK SUITE")
        print("="*80)

        # Initialize
        init_time = self.initialize_rag()

        # Define benchmark queries
        benchmark_queries = [
            # Simple factual queries (should be fast)
            ("What is the well name?", "Well 5", "simple_factual"),
            ("What is the location?", "Well 1", "simple_factual"),
            ("What is the well identifier?", "Well 8", "simple_factual"),

            # Depth queries (numerical)
            ("What is the total depth?", "Well 5", "numerical"),
            ("What is the measured depth and TVD?", "Well 1", "numerical"),
            ("How deep is the well?", "Well 6", "numerical"),

            # Technical queries (may require tables)
            ("What casing sizes were used?", "Well 5", "technical"),
            ("What is the inner diameter of the production casing?", "Well 5", "technical"),
            ("Describe the casing program", "Well 1", "technical"),

            # Summarization queries (LLM-heavy)
            ("Summarize the key well completion details", "Well 5", "summarization"),
            ("Provide a brief overview of the drilling operation", "Well 1", "summarization"),

            # Multi-well queries (more complex)
            ("Compare the depths of Well 1 and Well 5", None, "multi_well"),
            ("Which wells are in the Netherlands?", None, "multi_well"),

            # Missing info queries
            ("What was the weather during drilling?", "Well 5", "negative"),
        ]

        print(f"\nRunning {len(benchmark_queries)} benchmark queries...\n")

        # Run benchmarks
        for i, (query, well, category) in enumerate(benchmark_queries, 1):
            print(f"[{i}/{len(benchmark_queries)}] {query[:60]}...")
            if well:
                print(f"    Well: {well}")

            result = self.benchmark_single_query(query, well, category=category)
            self.results.append(result)

            if result['success']:
                print(f"    [OK] {result['total_time']:.2f}s (sources: {result['num_sources']})")
            else:
                print(f"    [ERROR] {result['error']}")

        # Calculate statistics
        return self.calculate_statistics(init_time)

    def calculate_statistics(self, init_time: float) -> Dict:
        """Calculate performance statistics"""
        successful_results = [r for r in self.results if r['success']]

        if not successful_results:
            return {
                'error': 'No successful queries',
                'total_queries': len(self.results),
                'successful': 0
            }

        times = [r['total_time'] for r in successful_results]

        # Overall stats
        stats = {
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_queries': len(self.results),
                'successful': len(successful_results),
                'failed': len(self.results) - len(successful_results),
                'initialization_time': init_time
            },
            'time_stats': {
                'avg_time': statistics.mean(times),
                'median_time': statistics.median(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'p95_time': sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else max(times),
                'target': 10.0,
                'meets_target': statistics.mean(times) < 10.0
            },
            'category_stats': {},
            'detailed_results': self.results
        }

        # Category breakdown
        categories = set(r['category'] for r in successful_results)
        for category in categories:
            cat_results = [r for r in successful_results if r['category'] == category]
            cat_times = [r['total_time'] for r in cat_results]

            stats['category_stats'][category] = {
                'count': len(cat_results),
                'avg_time': statistics.mean(cat_times),
                'min_time': min(cat_times),
                'max_time': max(cat_times)
            }

        # Component timing stats (if available)
        if any('embedding_time' in r for r in successful_results):
            embedding_times = [r['embedding_time'] for r in successful_results
                              if 'embedding_time' in r and r['embedding_time'] > 0]
            retrieval_times = [r['retrieval_time'] for r in successful_results
                              if 'retrieval_time' in r and r['retrieval_time'] > 0]
            llm_times = [r['llm_time'] for r in successful_results
                        if 'llm_time' in r and r['llm_time'] > 0]

            if embedding_times:
                stats['component_stats'] = {
                    'embedding': {
                        'avg': statistics.mean(embedding_times),
                        'max': max(embedding_times)
                    } if embedding_times else None,
                    'retrieval': {
                        'avg': statistics.mean(retrieval_times),
                        'max': max(retrieval_times)
                    } if retrieval_times else None,
                    'llm': {
                        'avg': statistics.mean(llm_times),
                        'max': max(llm_times)
                    } if llm_times else None
                }

        return stats

    def print_report(self, stats: Dict):
        """Print formatted performance report"""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("="*80)

        meta = stats['metadata']
        time_stats = stats['time_stats']

        # Overall summary
        print(f"\nOVERALL SUMMARY:")
        print(f"-"*80)
        print(f"Total Queries:       {meta['total_queries']}")
        print(f"Successful:          {meta['successful']}")
        print(f"Failed:              {meta['failed']}")
        print(f"Initialization:      {meta['initialization_time']:.2f}s")

        # Time statistics
        print(f"\nQUERY TIME STATISTICS:")
        print(f"-"*80)
        print(f"Average:             {time_stats['avg_time']:.2f}s")
        print(f"Median:              {time_stats['median_time']:.2f}s")
        print(f"Min:                 {time_stats['min_time']:.2f}s")
        print(f"Max:                 {time_stats['max_time']:.2f}s")
        print(f"Std Dev:             {time_stats['std_dev']:.2f}s")
        print(f"95th percentile:     {time_stats['p95_time']:.2f}s")
        print(f"\nTarget:              <{time_stats['target']:.1f}s")
        print(f"Status:              {'[OK] MEETS TARGET' if time_stats['meets_target'] else '[FAIL] TOO SLOW'}")

        # Category breakdown
        if 'category_stats' in stats and stats['category_stats']:
            print(f"\n{'='*80}")
            print(f"CATEGORY BREAKDOWN:")
            print(f"{'='*80}")

            for category, cat_stats in stats['category_stats'].items():
                print(f"\n{category.upper().replace('_', ' ')}:")
                print(f"  Queries:   {cat_stats['count']}")
                print(f"  Avg Time:  {cat_stats['avg_time']:.2f}s")
                print(f"  Min:       {cat_stats['min_time']:.2f}s")
                print(f"  Max:       {cat_stats['max_time']:.2f}s")

        # Component breakdown
        if 'component_stats' in stats:
            print(f"\n{'='*80}")
            print(f"COMPONENT TIMING:")
            print(f"{'='*80}")

            for component, comp_stats in stats['component_stats'].items():
                if comp_stats:
                    print(f"\n{component.upper()}:")
                    print(f"  Average:   {comp_stats['avg']:.3f}s")
                    print(f"  Max:       {comp_stats['max']:.3f}s")

        # Slowest queries
        slow_queries = sorted(
            [r for r in stats['detailed_results'] if r['success']],
            key=lambda x: x['total_time'],
            reverse=True
        )[:5]

        if slow_queries:
            print(f"\n{'='*80}")
            print(f"SLOWEST QUERIES (Top 5):")
            print(f"{'='*80}")

            for i, result in enumerate(slow_queries, 1):
                print(f"\n{i}. {result['query'][:60]}...")
                print(f"   Time:     {result['total_time']:.2f}s")
                print(f"   Well:     {result['well']}")
                print(f"   Category: {result['category']}")

        print(f"\n{'='*80}\n")

    def save_results(self, stats: Dict, output_file: str = 'tests/benchmark_results.json'):
        """Save benchmark results to file"""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Results saved to {output_path}")


def main():
    """Main benchmark function"""
    import argparse

    parser = argparse.ArgumentParser(description='Benchmark RAG performance')
    parser.add_argument('--output', default='tests/benchmark_results.json',
                       help='Path to save results')

    args = parser.parse_args()

    # Run benchmark
    benchmark = PerformanceBenchmark()
    stats = benchmark.run_benchmark_suite()

    # Print report
    benchmark.print_report(stats)

    # Save results
    benchmark.save_results(stats, args.output)

    # Exit with error code if target not met
    if not stats['time_stats']['meets_target']:
        print("\n[WARNING] Performance target not met!")
        sys.exit(1)
    else:
        print("\n[OK] Performance target met!")
        sys.exit(0)


if __name__ == '__main__':
    main()

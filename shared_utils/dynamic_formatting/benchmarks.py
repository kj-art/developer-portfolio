#!/usr/bin/env python3
"""
Performance benchmarks for dynamic formatting system.

Comprehensive benchmarking suite that measures performance characteristics,
memory usage, and scalability of the dynamic formatting system across
various use cases and data sizes.

Usage:
    python benchmarks.py
    python benchmarks.py --category template_compilation
    python benchmarks.py --verbose
    python benchmarks.py --export-csv results.csv
"""

import time
import gc
import sys
import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import DynamicFormatter
    from shared_utils.dynamic_formatting.tests.fixtures.sample_templates import (
        get_test_functions, create_large_template, create_large_data_set
    )
except ImportError as e:
    print(f"Import failed: {e}")
    print("Make sure the dynamic formatting package is available")
    sys.exit(1)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not available. Memory measurements will be limited.")


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    name: str
    category: str
    iterations: int
    total_time: float
    avg_time: float
    ops_per_second: float
    memory_before: float
    memory_after: float
    memory_delta: float
    min_time: float
    max_time: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BenchmarkRunner:
    """Main benchmark runner with timing and memory tracking"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []
    
    @contextmanager
    def benchmark_context(self, name: str, category: str, iterations: int, metadata: Optional[Dict] = None):
        """Context manager for running benchmarks with timing and memory tracking"""
        if self.verbose:
            print(f"Running benchmark: {name} ({iterations} iterations)")
        
        # Force garbage collection and get initial memory
        gc.collect()
        memory_before = self._get_memory_usage()
        
        # Timing variables
        start_time = time.perf_counter()
        times = []
        error_message = None
        success = True
        
        try:
            yield times
        except Exception as e:
            success = False
            error_message = str(e)
            if self.verbose:
                print(f"Benchmark failed: {e}")
        finally:
            # Calculate timing statistics
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            if times and success:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                ops_per_second = iterations / total_time if total_time > 0 else 0
            else:
                avg_time = total_time / iterations if iterations > 0 else 0
                min_time = max_time = avg_time
                ops_per_second = iterations / total_time if total_time > 0 else 0
            
            # Get final memory usage
            gc.collect()
            memory_after = self._get_memory_usage()
            memory_delta = memory_after - memory_before
            
            # Create result
            result = BenchmarkResult(
                name=name,
                category=category,
                iterations=iterations,
                total_time=total_time,
                avg_time=avg_time,
                ops_per_second=ops_per_second,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_delta=memory_delta,
                min_time=min_time,
                max_time=max_time,
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            
            self.results.append(result)
            
            if self.verbose:
                print(f"  Time: {total_time:.4f}s total, {avg_time:.6f}s avg")
                print(f"  Rate: {ops_per_second:.0f} ops/sec")
                print(f"  Memory: {memory_delta:+.2f}MB")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        if HAS_PSUTIL:
            try:
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
            except Exception:
                pass
        return 0.0
    
    def print_results(self, category_filter: Optional[str] = None):
        """Print benchmark results in a formatted table"""
        if category_filter:
            filtered_results = [r for r in self.results if r.category == category_filter]
        else:
            filtered_results = self.results
        
        if not filtered_results:
            print("No results to display")
            return
        
        print("\n" + "="*100)
        print("DYNAMIC FORMATTING BENCHMARK RESULTS")
        print("="*100)
        
        # Group by category
        categories = {}
        for result in filtered_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in categories.items():
            print(f"\n{category.upper()} BENCHMARKS:")
            print("-" * 80)
            print(f"{'Name':<30} {'Iterations':<10} {'Total(s)':<10} {'Avg(ms)':<10} {'Ops/sec':<12} {'Memory(MB)':<12} {'Status':<8}")
            print("-" * 80)
            
            for result in results:
                status = "✓" if result.success else "✗"
                avg_ms = result.avg_time * 1000
                print(f"{result.name:<30} {result.iterations:<10} {result.total_time:<10.3f} {avg_ms:<10.3f} {result.ops_per_second:<12.0f} {result.memory_delta:<+12.2f} {status:<8}")
                
                if not result.success and result.error_message:
                    print(f"  Error: {result.error_message}")
    
    def export_csv(self, filename: str):
        """Export results to CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            if not self.results:
                return
            
            fieldnames = list(asdict(self.results[0]).keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                row = asdict(result)
                # Convert metadata to JSON string for CSV
                if row['metadata']:
                    row['metadata'] = json.dumps(row['metadata'])
                writer.writerow(row)
        
        print(f"Results exported to {filename}")
    
    def export_json(self, filename: str):
        """Export results to JSON file"""
        data = [asdict(result) for result in self.results]
        with open(filename, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)
        
        print(f"Results exported to {filename}")


class FormattingBenchmarks:
    """Specific benchmarks for dynamic formatting operations"""
    
    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner
        self.test_functions = get_test_functions()
    
    def run_template_compilation_benchmarks(self):
        """Benchmark template compilation performance"""
        
        # Simple template compilation
        with self.runner.benchmark_context("Simple Template", "template_compilation", 5000) as times:
            for i in range(5000):
                start = time.perf_counter()
                formatter = DynamicFormatter("{{Hello ;name}}")
                times.append(time.perf_counter() - start)
        
        # Complex template compilation
        with self.runner.benchmark_context("Complex Template", "template_compilation", 2000) as times:
            template = "{{#level_color@bold;[;level;]}} {{message}} {{?has_duration;in ;duration;s}} {{Memory: ;memory;MB}}"
            for i in range(2000):
                start = time.perf_counter()
                formatter = DynamicFormatter(template, functions=self.test_functions)
                times.append(time.perf_counter() - start)
        
        # Large template compilation
        with self.runner.benchmark_context("Large Template (50 sections)", "template_compilation", 500) as times:
            large_template = create_large_template(50)
            for i in range(500):
                start = time.perf_counter()
                formatter = DynamicFormatter(large_template)
                times.append(time.perf_counter() - start)
        
        # Very large template compilation
        with self.runner.benchmark_context("Very Large Template (200 sections)", "template_compilation", 100) as times:
            huge_template = create_large_template(200)
            for i in range(100):
                start = time.perf_counter()
                formatter = DynamicFormatter(huge_template)
                times.append(time.perf_counter() - start)
    
    def run_formatting_speed_benchmarks(self):
        """Benchmark formatting operation speed"""
        
        # Simple formatting
        simple_formatter = DynamicFormatter("{{Hello ;name}}")
        with self.runner.benchmark_context("Simple Formatting", "formatting_speed", 20000) as times:
            for i in range(20000):
                start = time.perf_counter()
                result = simple_formatter.format(name=f"User{i}")
                times.append(time.perf_counter() - start)
        
        # Complex formatting with functions
        complex_formatter = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}} {{?has_duration;in ;duration;s}}",
            functions=self.test_functions
        )
        with self.runner.benchmark_context("Complex Formatting", "formatting_speed", 5000) as times:
            for i in range(5000):
                level = ["DEBUG", "INFO", "WARNING", "ERROR"][i % 4]
                start = time.perf_counter()
                result = complex_formatter.format(
                    level=level,
                    message=f"Message {i}",
                    duration=i * 0.1
                )
                times.append(time.perf_counter() - start)
        
        # Positional arguments formatting
        positional_formatter = DynamicFormatter("{{#level_color@bold;[;]}} {{}} {{?has_duration;in ;s}}", 
                                                functions=self.test_functions)
        with self.runner.benchmark_context("Positional Formatting", "formatting_speed", 5000) as times:
            for i in range(5000):
                level = ["DEBUG", "INFO", "WARNING", "ERROR"][i % 4]
                start = time.perf_counter()
                result = positional_formatter.format(level, f"Message {i}", i * 0.1)
                times.append(time.perf_counter() - start)
        
        # Large data formatting
        large_formatter = DynamicFormatter("{{Data: ;large_field}}")
        large_data = "x" * 10000  # 10KB string
        with self.runner.benchmark_context("Large Data Formatting", "formatting_speed", 1000) as times:
            for i in range(1000):
                start = time.perf_counter()
                result = large_formatter.format(large_field=large_data)
                times.append(time.perf_counter() - start)
    
    def run_scalability_benchmarks(self):
        """Benchmark scalability with increasing load"""
        
        # Many template sections
        section_counts = [10, 25, 50, 100]
        for count in section_counts:
            template = create_large_template(count)
            formatter = DynamicFormatter(template)
            data = create_large_data_set(count)
            
            with self.runner.benchmark_context(
                f"Many Sections ({count})", 
                "scalability", 
                200,
                metadata={"section_count": count}
            ) as times:
                for i in range(200):
                    start = time.perf_counter()
                    result = formatter.format(**data)
                    times.append(time.perf_counter() - start)
        
        # Many positional arguments
        for count in [10, 25, 50, 100]:
            template = " ".join(["{{}}" for _ in range(count)])
            formatter = DynamicFormatter(template)
            args = [f"arg{i}" for i in range(count)]
            
            with self.runner.benchmark_context(
                f"Many Positional Args ({count})",
                "scalability",
                500,
                metadata={"arg_count": count}
            ) as times:
                for i in range(500):
                    start = time.perf_counter()
                    result = formatter.format(*args)
                    times.append(time.perf_counter() - start)
        
        # Large function registry
        function_counts = [10, 50, 100, 500]
        for count in function_counts:
            functions = {f"func{i}": lambda x, i=i: "red" if i % 2 else "blue" for i in range(count)}
            formatter = DynamicFormatter(f"{{{{#func{count//2};Test: ;field}}}}", functions=functions)
            
            with self.runner.benchmark_context(
                f"Large Function Registry ({count})",
                "scalability", 
                1000,
                metadata={"function_count": count}
            ) as times:
                for i in range(1000):
                    start = time.perf_counter()
                    result = formatter.format(field="test")
                    times.append(time.perf_counter() - start)
    
    def run_memory_benchmarks(self):
        """Benchmark memory usage patterns"""
        
        # Template creation memory usage
        with self.runner.benchmark_context("Template Creation Memory", "memory", 2000) as times:
            formatters = []
            for i in range(2000):
                start = time.perf_counter()
                formatter = DynamicFormatter(f"{{{{Message{i}: ;field{i}}}}}")
                formatters.append(formatter)
                times.append(time.perf_counter() - start)
        
        # Formatting operation memory usage
        formatter = DynamicFormatter("{{#red@bold;Message: ;msg}} {{Count: ;count}}")
        with self.runner.benchmark_context("Formatting Operations Memory", "memory", 10000) as times:
            for i in range(10000):
                start = time.perf_counter()
                result = formatter.format(msg=f"Message {i}", count=i)
                # Don't store result to test memory cleanup
                times.append(time.perf_counter() - start)
        
        # Large template memory usage
        large_template = create_large_template(100)
        large_data = create_large_data_set(100)
        with self.runner.benchmark_context("Large Template Memory", "memory", 100) as times:
            formatter = DynamicFormatter(large_template)
            for i in range(100):
                start = time.perf_counter()
                result = formatter.format(**large_data)
                times.append(time.perf_counter() - start)
    
    def run_function_fallback_benchmarks(self):
        """Benchmark function fallback performance"""
        
        # Direct token vs function fallback comparison
        direct_formatter = DynamicFormatter("{{#red;Direct: ;message}}")
        
        def red_function(value):
            return "red"
        
        function_formatter = DynamicFormatter(
            "{{#red_function;Function: ;message}}",
            functions={"red_function": red_function}
        )
        
        # Direct token benchmark
        with self.runner.benchmark_context("Direct Token", "function_fallback", 10000) as times:
            for i in range(10000):
                start = time.perf_counter()
                result = direct_formatter.format(message=f"test{i}")
                times.append(time.perf_counter() - start)
        
        # Function fallback benchmark
        with self.runner.benchmark_context("Function Fallback", "function_fallback", 10000) as times:
            for i in range(10000):
                start = time.perf_counter()
                result = function_formatter.format(message=f"test{i}")
                times.append(time.perf_counter() - start)
        
        # Complex function benchmark
        def expensive_function(value):
            # Simulate computation
            result = 0
            for j in range(50):
                result += hash(f"{value}{j}") % 256
            return "red" if result % 2 else "blue"
        
        expensive_formatter = DynamicFormatter(
            "{{#expensive_function;Expensive: ;message}}",
            functions={"expensive_function": expensive_function}
        )
        
        with self.runner.benchmark_context("Expensive Function", "function_fallback", 1000) as times:
            for i in range(1000):
                start = time.perf_counter()
                result = expensive_formatter.format(message=f"test{i}")
                times.append(time.perf_counter() - start)
    
    def run_real_world_benchmarks(self):
        """Benchmark real-world usage scenarios"""
        
        # Logging scenario
        log_formatter = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}} {{?has_duration;in ;duration;s}} {{?has_memory;memory: ;memory;MB}}",
            functions=self.test_functions
        )
        
        with self.runner.benchmark_context("Logging Scenario", "real_world", 5000) as times:
            levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            for i in range(5000):
                level = levels[i % len(levels)]
                start = time.perf_counter()
                result = log_formatter.format(
                    level=level,
                    message=f"Log message {i}",
                    duration=i * 0.01 if i % 3 == 0 else None,
                    memory=i * 0.1 if i % 5 == 0 else None
                )
                times.append(time.perf_counter() - start)
        
        # API response scenario
        api_formatter = DynamicFormatter(
            "{{#status_color;HTTP ;status_code}} {{?has_items;- ;record_count; records}} {{?has_errors;- ;error_count; errors}} {{Duration: ;response_time;ms}}",
            functions=self.test_functions
        )
        
        with self.runner.benchmark_context("API Response Scenario", "real_world", 3000) as times:
            status_codes = [200, 201, 400, 404, 500]
            for i in range(3000):
                status = status_codes[i % len(status_codes)]
                start = time.perf_counter()
                result = api_formatter.format(
                    status_code=status,
                    record_count=i if status < 400 else 0,
                    error_count=1 if status >= 400 else 0,
                    response_time=50 + (i % 200)
                )
                times.append(time.perf_counter() - start)
        
        # Build status scenario
        build_formatter = DynamicFormatter(
            "{{#status_color@bold;Build ;status}} {{?has_items;in ;duration;s}} {{?has_items;- ;test_count; tests}}",
            functions=self.test_functions
        )
        
        with self.runner.benchmark_context("Build Status Scenario", "real_world", 2000) as times:
            statuses = ["SUCCESS", "FAILED", "BUILDING", "CANCELLED"]
            for i in range(2000):
                status = statuses[i % len(statuses)]
                start = time.perf_counter()
                result = build_formatter.format(
                    status=status,
                    duration=30 + (i % 60) if status != "BUILDING" else None,
                    test_count=100 + (i % 50) if status in ["SUCCESS", "FAILED"] else None
                )
                times.append(time.perf_counter() - start)
    
    def run_all_benchmarks(self):
        """Run all benchmark categories"""
        print("Starting comprehensive benchmark suite...")
        
        self.run_template_compilation_benchmarks()
        self.run_formatting_speed_benchmarks()
        self.run_scalability_benchmarks()
        self.run_memory_benchmarks()
        self.run_function_fallback_benchmarks()
        self.run_real_world_benchmarks()
        
        print("All benchmarks completed!")


def main():
    """Main benchmark runner"""
    parser = argparse.ArgumentParser(description="Dynamic Formatting Benchmark Suite")
    parser.add_argument("--category", help="Run specific benchmark category", 
                       choices=["template_compilation", "formatting_speed", "scalability", 
                               "memory", "function_fallback", "real_world"])
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--export-csv", help="Export results to CSV file")
    parser.add_argument("--export-json", help="Export results to JSON file")
    parser.add_argument("--iterations", type=int, help="Override default iteration counts (for testing)")
    
    args = parser.parse_args()
    
    runner = BenchmarkRunner(verbose=args.verbose)
    benchmarks = FormattingBenchmarks(runner)
    
    # Run specific category or all benchmarks
    if args.category:
        method_name = f"run_{args.category}_benchmarks"
        if hasattr(benchmarks, method_name):
            print(f"Running {args.category} benchmarks...")
            getattr(benchmarks, method_name)()
        else:
            print(f"Unknown benchmark category: {args.category}")
            return 1
    else:
        benchmarks.run_all_benchmarks()
    
    # Print results
    runner.print_results(args.category)
    
    # Export results if requested
    if args.export_csv:
        runner.export_csv(args.export_csv)
    
    if args.export_json:
        runner.export_json(args.export_json)
    
    # Summary statistics
    if runner.results:
        successful = [r for r in runner.results if r.success]
        failed = [r for r in runner.results if not r.success]
        
        print(f"\nSUMMARY:")
        print(f"  Total benchmarks: {len(runner.results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        
        if successful:
            avg_ops_per_sec = sum(r.ops_per_second for r in successful) / len(successful)
            total_memory_delta = sum(r.memory_delta for r in successful)
            print(f"  Average ops/sec: {avg_ops_per_sec:.0f}")
            print(f"  Total memory delta: {total_memory_delta:+.2f}MB")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
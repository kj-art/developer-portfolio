"""
Performance and benchmarking tests.

Tests performance characteristics, memory usage, and scalability
of the dynamic formatting system under various loads.
"""

import pytest
import time
import gc
import sys
from shared_utils.dynamic_formatting import DynamicFormatter


class TestBasicPerformance:
    """Test basic performance characteristics"""
    
    @pytest.mark.performance
    def test_template_compilation_speed(self):
        """Test speed of template compilation"""
        templates = [
            "{{Simple: ;field}}",
            "{{#red@bold;Complex: ;field}} {{Count: ;count}}",
            "{{#level_color@level_style;[;level;]}} {{message}} {{?has_duration;in ;duration;s}}",
        ]
        
        start_time = time.time()
        formatters = []
        
        for _ in range(1000):
            for template in templates:
                formatter = DynamicFormatter(template)
                formatters.append(formatter)
        
        compilation_time = time.time() - start_time
        
        # Should compile 3000 templates in reasonable time (adjust threshold as needed)
        assert compilation_time < 5.0, f"Template compilation too slow: {compilation_time:.2f}s"
        assert len(formatters) == 3000
    
    @pytest.mark.performance
    def test_formatting_speed_simple(self):
        """Test speed of simple formatting operations"""
        formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}}")
        
        start_time = time.time()
        
        for i in range(10000):
            result = formatter.format(message=f"Error {i}", count=i)
            assert result  # Ensure it's not empty
        
        formatting_time = time.time() - start_time
        
        # Should format 10k simple templates in reasonable time
        assert formatting_time < 2.0, f"Simple formatting too slow: {formatting_time:.2f}s"
    
    @pytest.mark.performance
    def test_formatting_speed_complex(self):
        """Test speed of complex formatting operations"""
        def level_color(level):
            return {"ERROR": "red", "INFO": "green"}[level]
        
        formatter = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}} {{Duration: ;duration;s}}",
            functions={"level_color": level_color}
        )
        
        start_time = time.time()
        
        for i in range(1000):
            result = formatter.format(
                level="ERROR" if i % 2 else "INFO",
                message=f"Message {i}",
                duration=i * 0.1
            )
            assert result
        
        formatting_time = time.time() - start_time
        
        # Should format 1k complex templates in reasonable time
        assert formatting_time < 1.0, f"Complex formatting too slow: {formatting_time:.2f}s"


class TestScalabilityTests:
    """Test scalability with large inputs"""
    
    @pytest.mark.performance
    def test_many_template_sections(self):
        """Test performance with many template sections"""
        # Create template with 50 sections
        sections = []
        data = {}
        
        for i in range(50):
            sections.append(f"{{{{Section{i}: ;field{i}}}}}")
            data[f"field{i}"] = f"value{i}"
        
        template = " ".join(sections)
        formatter = DynamicFormatter(template)
        
        start_time = time.time()
        
        for _ in range(100):
            result = formatter.format(**data)
            assert len(result) > 1000  # Should be substantial output
        
        formatting_time = time.time() - start_time
        
        # Should handle large templates efficiently
        assert formatting_time < 2.0, f"Large template formatting too slow: {formatting_time:.2f}s"
    
    @pytest.mark.performance
    def test_large_field_values(self):
        """Test performance with large field values"""
        formatter = DynamicFormatter("{{Data: ;large_field}}")
        
        # Create large string (1MB)
        large_value = "x" * (1024 * 1024)
        
        start_time = time.time()
        
        for _ in range(10):
            result = formatter.format(large_field=large_value)
            assert len(result) > 1000000
        
        formatting_time = time.time() - start_time
        
        # Should handle large values efficiently
        assert formatting_time < 1.0, f"Large value formatting too slow: {formatting_time:.2f}s"
    
    @pytest.mark.performance
    def test_many_positional_arguments(self):
        """Test performance with many positional arguments"""
        # Create template with 100 positional sections
        template = " ".join(["{{}}" for _ in range(100)])
        formatter = DynamicFormatter(template)
        
        # Create 100 arguments
        args = [f"arg{i}" for i in range(100)]
        
        start_time = time.time()
        
        for _ in range(100):
            result = formatter.format(*args)
            assert "arg0" in result and "arg99" in result
        
        formatting_time = time.time() - start_time
        
        # Should handle many positional args efficiently
        assert formatting_time < 1.0, f"Many positional args too slow: {formatting_time:.2f}s"


class TestMemoryUsage:
    """Test memory usage characteristics"""
    
    @pytest.mark.performance
    def test_memory_usage_template_compilation(self):
        """Test memory usage during template compilation"""
        gc.collect()
        initial_memory = self._get_memory_usage()
        
        formatters = []
        for i in range(1000):
            template = f"{{{{#red@bold;Message{i}: ;field{i}}}}}"
            formatter = DynamicFormatter(template)
            formatters.append(formatter)
        
        gc.collect()
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 50, f"Memory usage too high: {memory_increase:.2f}MB for 1000 formatters"
    
    @pytest.mark.performance
    def test_memory_usage_formatting_operations(self):
        """Test memory usage during formatting operations"""
        formatter = DynamicFormatter("{{#red@bold;Message: ;message}} {{Count: ;count}}")
        
        gc.collect()
        initial_memory = self._get_memory_usage()
        
        # Perform many formatting operations
        for i in range(10000):
            result = formatter.format(message=f"Message {i}", count=i)
            # Don't accumulate results to test memory cleanup
        
        gc.collect()
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory should not grow significantly with formatting operations
        assert memory_increase < 10, f"Memory leak detected: {memory_increase:.2f}MB after 10k operations"
    
    @pytest.mark.performance
    def test_formatter_reuse_memory_efficiency(self):
        """Test memory efficiency of formatter reuse"""
        template = "{{#red@bold;Data: ;field}} {{Count: ;count}} {{Duration: ;duration;s}}"
        
        # Test creating new formatter each time (bad practice)
        gc.collect()
        initial_memory = self._get_memory_usage()
        
        for i in range(1000):
            formatter = DynamicFormatter(template)  # Bad: recreating each time
            result = formatter.format(field=f"test{i}", count=i, duration=i * 0.1)
        
        gc.collect()
        recreate_memory = self._get_memory_usage() - initial_memory
        
        # Test reusing formatter (good practice)
        gc.collect()
        initial_memory = self._get_memory_usage()
        
        formatter = DynamicFormatter(template)  # Good: create once
        for i in range(1000):
            result = formatter.format(field=f"test{i}", count=i, duration=i * 0.1)
        
        gc.collect()
        reuse_memory = self._get_memory_usage() - initial_memory
        
        # Reusing should be much more memory efficient
        assert reuse_memory < recreate_memory / 2, f"Formatter reuse not efficient enough: reuse={reuse_memory:.2f}MB, recreate={recreate_memory:.2f}MB"
    
    def _get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback using tracemalloc if psutil not available
            import tracemalloc
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                return current / 1024 / 1024
            else:
                tracemalloc.start()
                return 0.0


class TestFunctionPerformance:
    """Test performance characteristics of function fallback system"""
    
    @pytest.mark.performance
    def test_function_call_overhead(self):
        """Test overhead of function calls vs direct tokens"""
        # Direct color token
        direct_formatter = DynamicFormatter("{{#red;Direct: ;message}}")
        
        # Function-based color
        def get_red(value):
            return "red"
        
        function_formatter = DynamicFormatter(
            "{{#get_red;Function: ;message}}",
            functions={"get_red": get_red}
        )
        
        # Benchmark direct tokens
        start_time = time.time()
        for i in range(1000):
            result = direct_formatter.format(message=f"test{i}")
        direct_time = time.time() - start_time
        
        # Benchmark function tokens
        start_time = time.time()
        for i in range(1000):
            result = function_formatter.format(message=f"test{i}")
        function_time = time.time() - start_time
        
        # Function overhead should be reasonable (less than 3x slower)
        overhead_ratio = function_time / direct_time
        assert overhead_ratio < 3.0, f"Function overhead too high: {overhead_ratio:.2f}x slower"
    
    @pytest.mark.performance
    def test_complex_function_performance(self):
        """Test performance with computationally expensive functions"""
        def expensive_color_function(value):
            # Simulate some computation
            result = 0
            for i in range(100):
                result += hash(f"{value}{i}") % 256
            
            return "red" if result % 2 else "blue"
        
        formatter = DynamicFormatter(
            "{{#expensive_color_function;Result: ;message}}",
            functions={"expensive_color_function": expensive_color_function}
        )
        
        start_time = time.time()
        
        for i in range(100):
            result = formatter.format(message=f"test{i}")
        
        formatting_time = time.time() - start_time
        
        # Should complete even with expensive functions in reasonable time
        assert formatting_time < 5.0, f"Expensive function formatting too slow: {formatting_time:.2f}s"
    
    @pytest.mark.performance
    def test_function_registry_lookup_performance(self):
        """Test performance of function registry lookups with many functions"""
        # Create large function registry
        functions = {}
        for i in range(1000):
            functions[f"func{i}"] = lambda x, i=i: "red" if i % 2 else "blue"
        
        formatter = DynamicFormatter(
            "{{#func500;Middle: ;message}}",  # Function in middle of registry
            functions=functions
        )
        
        start_time = time.time()
        
        for i in range(1000):
            result = formatter.format(message=f"test{i}")
        
        formatting_time = time.time() - start_time
        
        # Should handle large function registries efficiently
        assert formatting_time < 2.0, f"Large function registry too slow: {formatting_time:.2f}s"


class TestConcurrencyPerformance:
    """Test performance under concurrent access patterns"""
    
    @pytest.mark.performance
    def test_formatter_concurrent_reuse(self):
        """Test performance when formatter is reused concurrently"""
        import threading
        
        formatter = DynamicFormatter("{{#red@bold;Thread ;thread_id;: ;message}}")
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(100):
                    result = formatter.format(thread_id=thread_id, message=f"msg{i}")
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Should complete without errors
        assert len(errors) == 0, f"Concurrent access caused errors: {errors}"
        assert len(results) == 1000, f"Expected 1000 results, got {len(results)}"
        
        # Should complete in reasonable time
        assert total_time < 5.0, f"Concurrent formatting too slow: {total_time:.2f}s"


class TestRegressionPerformance:
    """Performance regression tests to ensure optimizations don't break"""
    
    @pytest.mark.performance
    def test_simple_template_baseline(self):
        """Baseline performance test for simple templates"""
        formatter = DynamicFormatter("{{Message: ;msg}}")
        
        start_time = time.time()
        
        for i in range(10000):
            result = formatter.format(msg=f"test{i}")
        
        baseline_time = time.time() - start_time
        
        # Record baseline for future regression testing
        # This should complete very quickly
        assert baseline_time < 1.0, f"Simple template baseline regression: {baseline_time:.2f}s"
    
    @pytest.mark.performance
    def test_complex_template_baseline(self):
        """Baseline performance test for complex templates"""
        def color_func(level):
            return {"A": "red", "B": "green", "C": "blue"}[level]
        
        def style_func(level):
            return "bold" if level == "A" else "normal"
        
        def condition_func(count):
            return count > 10
        
        formatter = DynamicFormatter(
            "{{#color_func@style_func;[;level;]}} {{message}} {{?condition_func;Count: ;count}} {{Duration: ;duration;s}}",
            functions={"color_func": color_func, "style_func": style_func, "condition_func": condition_func}
        )
        
        start_time = time.time()
        
        for i in range(1000):
            result = formatter.format(
                level="A" if i % 3 == 0 else "B" if i % 3 == 1 else "C",
                message=f"Complex message {i}",
                count=i,
                duration=i * 0.1
            )
        
        complex_time = time.time() - start_time
        
        # Record baseline for future regression testing
        assert complex_time < 2.0, f"Complex template baseline regression: {complex_time:.2f}s"
    
    @pytest.mark.performance
    def test_positional_args_performance_parity(self):
        """Test that positional args perform similarly to keyword args"""
        keyword_formatter = DynamicFormatter("{{Error: ;message}} {{Code: ;code}}")
        positional_formatter = DynamicFormatter("{{Error: ;}} {{Code: ;}}")
        
        # Test keyword performance
        start_time = time.time()
        for i in range(5000):
            result = keyword_formatter.format(message=f"Error {i}", code=i)
        keyword_time = time.time() - start_time
        
        # Test positional performance
        start_time = time.time()
        for i in range(5000):
            result = positional_formatter.format(f"Error {i}", i)
        positional_time = time.time() - start_time
        
        # Positional should not be significantly slower than keyword
        performance_ratio = positional_time / keyword_time
        assert performance_ratio < 1.5, f"Positional args too slow compared to keyword: {performance_ratio:.2f}x"


class TestMemoryLeakDetection:
    """Tests to detect memory leaks"""
    
    @pytest.mark.performance
    def test_formatter_creation_leak(self):
        """Test for memory leaks in formatter creation"""
        def create_and_use_formatter():
            formatter = DynamicFormatter("{{#red@bold;Test: ;field}}")
            return formatter.format(field="test")
        
        gc.collect()
        initial_memory = self._get_memory_usage()
        
        # Create and dispose many formatters
        for _ in range(1000):
            result = create_and_use_formatter()
        
        gc.collect()
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Should not accumulate significant memory
        assert memory_increase < 20, f"Potential memory leak in formatter creation: {memory_increase:.2f}MB"
    
    @pytest.mark.performance
    def test_function_registry_leak(self):
        """Test for memory leaks in function registries"""
        def create_formatter_with_functions():
            functions = {f"func{i}": lambda x, i=i: f"result{i}" for i in range(100)}
            formatter = DynamicFormatter("{{#func50;Test: ;field}}", functions=functions)
            return formatter.format(field="test")
        
        gc.collect()
        initial_memory = self._get_memory_usage()
        
        for _ in range(100):
            result = create_formatter_with_functions()
        
        gc.collect()
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Should not accumulate significant memory
        assert memory_increase < 30, f"Potential memory leak in function registries: {memory_increase:.2f}MB"
    
    def _get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback - return 0 if can't measure
            return 0.0
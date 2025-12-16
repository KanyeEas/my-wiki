# ArenaAllocator Optimization Testing Guide

This document describes how to compile and run the test suites associated with the ArenaAllocator optimization (Reset functionality and Thread-local pooling).

## 1. Test Locations

*   **Unit Tests**: `libarkbase/tests/arena_allocator_test.cpp`
    *   Tests: `ArenaAllocatorTest.ResetTest`, `ArenaAllocatorTest.ResetMultiArenaTest`
*   **Integration Tests**: `runtime/tests/class_linker_test.cpp`
    *   Tests: `ClassLinkerTest.ThreadLocalAllocatorReuse`

## 2. Compilation

The tests are split into two compilation targets: `arkbase_tests` (for base library tests) and `arkruntime_interpreter_test` (for runtime integration tests).

### Compile Unit Tests
```bash
cmake --build build --target arkbase_tests
```

### Compile Integration Tests
```bash
cmake --build build --target arkruntime_interpreter_test
```

> **Note**: Ensure your build directory is configured (e.g., `build`).

## 3. Running Tests

The compiled test binaries are located in `build/bin-gtests/`. Use `--gtest_filter` to run specific test cases.

### Run ArenaAllocator Unit Tests
To verify the `Reset()` functionality:

```bash
./build/bin-gtests/arkbase_tests --gtest_filter="ArenaAllocatorTest.Reset*"
```

**Expected Output:**
```
[ RUN      ] ArenaAllocatorTest.ResetTest
[       OK ] ArenaAllocatorTest.ResetTest (1 ms)
[ RUN      ] ArenaAllocatorTest.ResetMultiArenaTest
[       OK ] ArenaAllocatorTest.ResetMultiArenaTest (1 ms)
```

### Run ClassLinker Integration Tests
To verify the thread-local allocator pooling and reuse:

```bash
./build/bin-gtests/arkruntime_interpreter_test --gtest_filter="ClassLinkerTest.ThreadLocalAllocatorReuse"
```

**Expected Output:**
```
[ RUN      ] ClassLinkerTest.ThreadLocalAllocatorReuse
[       OK ] ClassLinkerTest.ThreadLocalAllocatorReuse (7 ms)
```

## 4. Troubleshooting

*   **Build Failures**: If you modify `arena_allocator.h` or `.cpp`, you must rebuild **both** targets to ensure changes propagate to the runtime tests.
*   **Target Not Found**: If `arkruntime_interpreter_test` is not found, verify that you are compiling for the correct architecture/platform configuration in your `build` directory.

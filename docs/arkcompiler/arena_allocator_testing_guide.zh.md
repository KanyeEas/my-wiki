# ArenaAllocator 优化测试指南

本文档描述了如何编译和运行与 ArenaAllocator 优化（Reset 功能和线程本地池）相关的测试套件。

## 1. 测试位置

*   **单元测试**: `libarkbase/tests/arena_allocator_test.cpp`
    *   测试用例: `ArenaAllocatorTest.ResetTest`, `ArenaAllocatorTest.ResetMultiArenaTest`
*   **集成测试**: `runtime/tests/class_linker_test.cpp`
    *   测试用例: `ClassLinkerTest.ThreadLocalAllocatorReuse`

## 2. 编译

测试分为两个编译目标：`arkbase_tests`（用于基础库测试）和 `arkruntime_interpreter_test`（用于运行时集成测试）。

### 编译单元测试
```bash
cmake --build build --target arkbase_tests
```

### 编译集成测试
```bash
cmake --build build --target arkruntime_interpreter_test
```

> **注意**: 请确保您的构建目录已配置好（例如 `build`）。

## 3. 运行测试

编译后的测试二进制文件位于 `build/bin-gtests/`。使用 `--gtest_filter` 来运行特定的测试用例。

### 运行 ArenaAllocator 单元测试
验证 `Reset()` 功能：

```bash
./build/bin-gtests/arkbase_tests --gtest_filter="ArenaAllocatorTest.Reset*"
```

**预期输出:**
```
[ RUN      ] ArenaAllocatorTest.ResetTest
[       OK ] ArenaAllocatorTest.ResetTest (1 ms)
[ RUN      ] ArenaAllocatorTest.ResetMultiArenaTest
[       OK ] ArenaAllocatorTest.ResetMultiArenaTest (1 ms)
```

### 运行 ClassLinker 集成测试
验证线程本地分配器池化和重用：

```bash
./build/bin-gtests/arkruntime_interpreter_test --gtest_filter="ClassLinkerTest.ThreadLocalAllocatorReuse"
```

**预期输出:**
```
[ RUN      ] ClassLinkerTest.ThreadLocalAllocatorReuse
[       OK ] ClassLinkerTest.ThreadLocalAllocatorReuse (7 ms)
```

## 4. 故障排除

*   **构建失败**: 如果您修改了 `arena_allocator.h` 或 `.cpp`，必须重建 **两个** 目标，以确保更改传播到运行时测试中。
*   **未找到目标**: 如果未找到 `arkruntime_interpreter_test`，请验证您是否在 `build` 目录中为正确的架构/平台配置进行了编译。

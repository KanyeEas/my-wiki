---
title: ArkCompiler 编译指南
order: 20
---
# ArkCompiler LLVM 解释器构建指南

本文整理 `static_core` 当前 CMake/SDK 构建系统中，构建支持 LLVM 解释器 runtime 产物时常见的两类命令：

1. 直接用 CMake 构建 Linux x86_64 Host 产物。
2. 用 `scripts/sdk/build_sdk.sh` 构建 OHOS Arm64 Device 产物和 Linux Host 工具。

分析依据为当前仓库源码，主要入口包括：

- `CMakeLists.txt`
- `cmake/Definitions.cmake`
- `libllvmbackend/cmake/LLVM.cmake`
- `cmake/HostTools.cmake`
- `runtime/options.yaml`
- `runtime/interpreter/interpreter_impl.cpp`
- `runtime/CMakeLists.txt`
- `irtoc/backend/CMakeLists.txt`
- `plugins/ets/runtime/CMakeLists.txt`
- `scripts/sdk/build_sdk.sh`
- `scripts/sdk/build_sdk_lib`

## 1. 总结

### 命令 1：Host CMake 构建

原始命令：

```bash
sudo ../scripts/install-deps-ubuntu -i=llvm-prebuilts
cd build
cmake .. -DPANDA_LLVM_BACKEND=ON -DPANDA_LLVM_INTERPRETER=ON -DPANDA_LLVM_FASTPATH=ON -DLLVM_DIR=/path/to/llvm-15-prebuilts/lib/cmake/llvm/
ninja all
```

如果没有指定交叉编译 toolchain，这类 `cmake ..` 是按当前主机平台构建。常见开发环境是 Linux x86_64，因此它构建的是 Linux x86_64 Host 产物，而不是 OHOS/Arm64 Device 产物。

当前仓库还有一个重要限制：Linux x86_64 非交叉构建不支持显式打开 `PANDA_LLVM_FASTPATH=ON`。`cmake/Definitions.cmake` 中对 `PANDA_TARGET_AMD64 AND NOT CMAKE_CROSSCOMPILING AND NOT HOST_TOOLS` 的情况会直接报错：

```text
PANDA_LLVM_FASTPATH is not supported for x86_64
```

所以这条命令在当前源码下需要调整，至少不要在 x86_64 Host 构建中显式传 `-DPANDA_LLVM_FASTPATH=ON`。

### 命令 2：SDK 构建

原始命令：

```bash
cd static_core/scripts/sdk
./build_sdk.sh build-sdk --build_type=Release --ohos_arm64 --ets_std_lib --linux_tools
```

这条命令会创建独立的 SDK 构建目录，默认输出到：

```text
static_core/scripts/sdk/build-sdk/sdk
```

它会构建两类内容：

- `--ohos_arm64`：OHOS/aarch64 Device 侧 runtime 和相关库。
- `--linux_tools`：Linux x86_64 Host 上运行的工具链工具，例如 `es2panda`、`ark_link`、`ark_disasm`、`verifier`、Host 版 `ark/ark_aot`。

它不依赖命令 1 已经编译出的 build 目录。两者只是都依赖同一套 LLVM prebuilts。

## 2. LLVM Backend 相关 CMake 选项

`PANDA_LLVM_BACKEND=ON` 是总开关。打开后，CMake 会按目标平台和用户显式参数决定以下能力：

- `PANDA_LLVM_INTERPRETER`：LLVM irtoc interpreter。默认会打开。
- `PANDA_LLVM_AOT`：LLVM AOT compiler。默认会打开。
- `PANDA_LLVM_FASTPATH`：LLVM fastpath 对象。Arm64 和交叉构建中默认会打开；Linux x86_64 非交叉构建中默认关闭，且显式打开会报错。
- `PANDA_LLVM_IRTOC`：内部标记。只要 LLVM interpreter 或 LLVM fastpath 打开，就需要生成 LLVM irtoc 对象。
- `PANDA_BUILD_LLVM_BACKEND`：内部标记。决定是否编译 `libllvmbackend`。

对应源码逻辑在 `cmake/Definitions.cmake`：

```cmake
option(PANDA_LLVM_BACKEND "Enable LLVM backend for Ark compiler" OFF)

if (PANDA_LLVM_BACKEND)
    if (NOT DEFINED PANDA_LLVM_INTERPRETER)
        set(PANDA_LLVM_INTERPRETER ON)
    endif()
    if (PANDA_TARGET_AMD64 AND NOT CMAKE_CROSSCOMPILING AND NOT HOST_TOOLS)
        if (NOT DEFINED PANDA_LLVM_FASTPATH)
            set(PANDA_LLVM_FASTPATH OFF)
        elseif(PANDA_LLVM_FASTPATH)
            message(FATAL_ERROR "PANDA_LLVM_FASTPATH is not supported for x86_64")
        endif()
    else()
        if (NOT DEFINED PANDA_LLVM_FASTPATH)
            set(PANDA_LLVM_FASTPATH ON)
        endif()
    endif()
    if (NOT DEFINED PANDA_LLVM_AOT)
        set(PANDA_LLVM_AOT ON)
    endif()
endif()
```

## 3. LLVM prebuilts

安装命令：

```bash
cd /path/to/runtime_core/static_core
sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts
```

该依赖会安装 Ark 修改版 LLVM 15 prebuilts。当前安装脚本会准备的常用路径包括：

```text
/opt/llvm-15-release-x86_64
/opt/llvm-15-debug-x86_64
/opt/llvm-15-release-aarch64
/opt/llvm-15-debug-aarch64
/opt/llvm-15-release-ohos
```

SDK 脚本中还预留了 FastVerify 路径变量，例如 `/opt/llvm-15-release-aarch64-fastverify` 和 `/opt/llvm-15-release-ohos-fastverify`。如果使用 `--build_type=FastVerify`，需要确认这些目录实际存在，或者通过 `--llvm_prebuilts_*_fastverify=...` 参数覆盖。

仓库 CMake 文档和 SDK 脚本主要使用 `LLVM_TARGET_PATH`，例如：

```bash
-DLLVM_TARGET_PATH=/opt/llvm-15-release-x86_64
```

`libllvmbackend/cmake/LLVM.cmake` 中实际通过以下方式找 LLVM：

```cmake
find_package(LLVM 15 REQUIRED CONFIG NO_DEFAULT_PATH CMAKE_FIND_ROOT_PATH_BOTH PATHS ${LLVM_TARGET_PATH})
```

因此，直接传 `LLVM_DIR=/path/to/lib/cmake/llvm` 有时也可能被 CMake 接受，但它不是当前仓库 README 和 SDK 脚本采用的标准写法。建议优先使用 `LLVM_TARGET_PATH`。

交叉编译时需要两套 LLVM：

- `LLVM_TARGET_PATH`：目标平台 LLVM，例如 OHOS/aarch64 的 `/opt/llvm-15-release-ohos`。
- `LLVM_HOST_PATH`：Host 工具构建使用的 LLVM，例如 `/opt/llvm-15-release-x86_64`。

## 4. 推荐的 Linux x86_64 Host 构建命令

用于在 Linux x86_64 Host 上构建带 LLVM interpreter/LLVM AOT 的 Ark runtime 和工具：

```bash
cd /path/to/runtime_core/static_core

sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts

cmake -S . -B build-llvm-host \
  -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain/host_clang_14.cmake \
  -DPANDA_LLVM_BACKEND=ON \
  -DPANDA_LLVM_FASTPATH=OFF \
  -DLLVM_TARGET_PATH=/opt/llvm-15-release-x86_64

ninja -C build-llvm-host all
```

如果只关心核心执行和 AOT 工具，可以用更小的目标集合：

```bash
ninja -C build-llvm-host ark ark_aot arkruntime llvmbackend
```

典型产物：

```text
build-llvm-host/bin/ark
build-llvm-host/bin/ark_aot
build-llvm-host/lib/libarkruntime.so
build-llvm-host/lib/libllvmbackend.so
build-llvm-host/lib/libLLVM-15.so
```

注意：如果在 Linux x86_64 Host 构建中传了 `-DPANDA_LLVM_FASTPATH=ON`，当前仓库会 CMake 配置失败。

## 5. 推荐的 OHOS Arm64 Device SDK 构建命令

用于构建设备侧 OHOS/aarch64 runtime，并同时构建 Linux Host 工具：

```bash
cd /path/to/runtime_core/static_core

sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts

cd scripts/sdk
./build_sdk.sh build-sdk --build_type=Release --ohos_arm64 --ets_std_lib --linux_tools
```

默认输出目录：

```text
static_core/scripts/sdk/build-sdk/sdk
```

### `--ohos_arm64` 做了什么

`scripts/sdk/build_sdk_lib` 中的 `ohos_arm64()` 会配置一个交叉编译 build：

```text
static_core/scripts/sdk/build-sdk/ohos_arm64
```

关键 CMake 参数：

```bash
-DCMAKE_TOOLCHAIN_FILE=cmake/toolchain/cross-ohos-musl-aarch64.cmake
-DTOOLCHAIN_SYSROOT=$OHOS_SDK_NATIVE/sysroot
-DTOOLCHAIN_CLANG_ROOT=$OHOS_SDK_NATIVE/llvm
-DPANDA_ETS_INTEROP_JS=ON
-DPANDA_LLVM_BACKEND=ON
-DLLVM_TARGET_PATH=/opt/llvm-15-release-ohos
-DLLVM_HOST_PATH=/opt/llvm-15-release-x86_64
```

目标平台由 toolchain 文件设置为：

```cmake
CMAKE_SYSTEM_NAME      = OHOS
CMAKE_SYSTEM_PROCESSOR = aarch64
PANDA_TRIPLET          = aarch64-linux-ohos
```

构建目标包括：

```text
ark
ark_aot
arkruntime
arkassembler
ets_interop_js_napi
e2p_test_plugin
ani_helpers
aspt_converter
dependency_analyzer
```

拷贝到 SDK 的关键设备侧产物包括：

```text
sdk/ohos_arm64/bin/ark
sdk/ohos_arm64/bin/ark_aot
sdk/ohos_arm64/lib/libarkruntime.so
sdk/ohos_arm64/lib/libarkcompiler.so
sdk/ohos_arm64/lib/libllvmbackend.so
sdk/ohos_arm64/lib/libLLVM-15.so
```

完整拷贝清单见：

```text
scripts/sdk/ohos_arm64.txt
```

### `--linux_tools` 做了什么

`linux_tools()` 会配置一个 Linux x86_64 Host build：

```text
static_core/scripts/sdk/build-sdk/linux_host_tools
```

关键 CMake 参数：

```bash
-DCMAKE_TOOLCHAIN_FILE=cmake/toolchain/host_clang_14.cmake
-DPANDA_CROSS_AARCH64_TOOLCHAIN_FILE=cmake/toolchain/cross-ohos-musl-aarch64.cmake
-DTOOLCHAIN_SYSROOT=$OHOS_SDK_NATIVE/sysroot
-DTOOLCHAIN_CLANG_ROOT=$OHOS_SDK_NATIVE/llvm
-DPANDA_ETS_INTEROP_JS=ON
-DPANDA_LLVM_BACKEND=ON
-DLLVM_TARGET_PATH=/opt/llvm-15-release-x86_64
-DLLVM_HOST_PATH=/opt/llvm-15-release-x86_64
```

构建目标包括：

```text
ark
ark_aot
ets_interop_js_napi
ark_disasm
ark_link
es2panda
etssdk
e2p_test_plugin
verifier
ani_helpers
aspt_converter
dependency_analyzer
```

拷贝到 SDK 的关键 Host 工具包括：

```text
sdk/linux_host_tools/bin/ark
sdk/linux_host_tools/bin/ark_aot
sdk/linux_host_tools/bin/ark_disasm
sdk/linux_host_tools/bin/ark_link
sdk/linux_host_tools/bin/es2panda
sdk/linux_host_tools/bin/verifier
sdk/linux_host_tools/lib/libllvmbackend.so
sdk/linux_host_tools/lib/libLLVM-15.so
```

完整拷贝清单见：

```text
scripts/sdk/linux_host_tools.txt
```

### `--ets_std_lib` 做了什么

该选项不会打开 LLVM，也不会决定目标平台。它只是把 ETS 标准库源码目录复制到 SDK：

```text
plugins/ets/stdlib/std
plugins/ets/stdlib/arkruntime
```

另外，构建过程中如果生成了 `etsstdlib.abc`，`copy_abc_files()` 会把它复制到：

```text
sdk/ets/etsstdlib.abc
```

## 6. SDK 构建中的 Host Tools 递归构建

交叉编译 OHOS Arm64 时，目标产物不能直接在 Host 上执行。但构建过程需要运行一些 Host 工具来生成代码，例如 irtoc 相关对象。

因此 `cmake/HostTools.cmake` 会在交叉编译 build 内部创建一个独立的 Host tools 子构建：

```text
static_core/scripts/sdk/build-sdk/ohos_arm64/host-tools-build
```

它会用 `LLVM_HOST_PATH` 查找 Host 侧 LLVM：

```bash
-DLLVM_TARGET_PATH=${LLVM_HOST_PATH}
```

并生成目标构建需要的对象，例如：

```text
irtoc_fastpath.o
irtoc_fastpath_llvm.o
irtoc_interpreter.o
irtoc_interpreter_llvm.o
```

这和 `--linux_tools` 的 SDK Host 工具构建不是同一个目录，也不是同一个用途：

- `ohos_arm64/host-tools-build`：交叉编译内部使用，服务于 OHOS Arm64 目标构建。
- `linux_host_tools`：SDK 对外交付的 Linux Host 工具。

## 7. LLVM 解释器如何生效

运行时默认选项在 `runtime/options.yaml`：

```yaml
- name: interpreter-type
  type: std::string
  default: llvm
  possible_values: [cpp, irtoc, llvm]
```

如果构建中定义了 `PANDA_LLVM_INTERPRETER`，运行时选择 `--interpreter-type=llvm` 时会进入：

```cpp
ExecuteImplFast_LLVM(...)
ExecuteImplFastEH_LLVM(...)
```

如果没有定义 `PANDA_LLVM_INTERPRETER`，默认 `llvm` 会降级到 `irtoc`。如果没有 `PANDA_WITH_IRTOC`，还会继续降级到 `cpp`。

建议 benchmark 或定位问题时显式传入：

```bash
--interpreter-type=llvm
```

避免误以为默认值一定命中了 LLVM interpreter。

## 8. 部署 OHOS Arm64 产物

SDK 构建完成后，设备侧产物在：

```text
static_core/scripts/sdk/build-sdk/sdk/ohos_arm64
```

常用拷贝内容：

```text
sdk/ohos_arm64/bin/ark
sdk/ohos_arm64/bin/ark_aot
sdk/ohos_arm64/lib/
sdk/ets/etsstdlib.abc
```

运行时需要确保设备侧能找到动态库，尤其是：

```text
libarkruntime.so
libarkcompiler.so
libllvmbackend.so
libLLVM-15.so
```

如果手动部署到设备目录，通常需要同步设置 `LD_LIBRARY_PATH` 到对应 `lib` 目录。

## 9. 常见误区

### 误区 1：命令 2 依赖命令 1 的 build 输出

不依赖。`build_sdk.sh` 会自己创建 `ohos_arm64` 和 `linux_host_tools` build 目录。它只依赖 LLVM prebuilts、OHOS SDK native、源码和第三方依赖。

### 误区 2：`--ohos_arm64` 是 Linux Arm64

不是。`--ohos_arm64` 使用 `cross-ohos-musl-aarch64.cmake`，目标系统是 OHOS，目标架构是 aarch64。

如果需要 Linux/aarch64 工具，应使用：

```bash
--linux_arm64_tools
```

### 误区 3：Host x86_64 构建可以打开 LLVM fastpath

当前仓库不支持。x86_64 Host 上要么不要传 `PANDA_LLVM_FASTPATH`，让 CMake 默认关闭；要么显式传：

```bash
-DPANDA_LLVM_FASTPATH=OFF
```

### 误区 4：交叉编译只需要一套 LLVM

如果开启完整 LLVM backend 功能，交叉编译需要两套路径：

```bash
-DLLVM_TARGET_PATH=/opt/llvm-15-release-ohos
-DLLVM_HOST_PATH=/opt/llvm-15-release-x86_64
```

SDK 脚本已经自动传入这两个参数。

### 误区 5：`LLVM_DIR` 是推荐参数

当前仓库推荐使用 `LLVM_TARGET_PATH`。`LLVM_DIR` 可能可以工作，但不符合 README 和 SDK 脚本里的主路径约定。

## 10. 最小决策表

| 目标 | 推荐命令 | 运行位置 | 主要输出 |
|---|---|---|---|
| Linux x86_64 Host runtime + tools | CMake Host 构建 | Host | `build/bin`、`build/lib` |
| OHOS Arm64 Device runtime | `build_sdk.sh --ohos_arm64` | Device | `sdk/ohos_arm64` |
| Linux x86_64 Host SDK tools | `build_sdk.sh --linux_tools` | Host | `sdk/linux_host_tools` |
| Linux Arm64 tools | `build_sdk.sh --linux_arm64_tools` | Linux/aarch64 或 QEMU 场景 | `sdk/linux_arm64_host_tools` |

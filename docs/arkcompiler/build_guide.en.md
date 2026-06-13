---
title: ArkCompiler Build Guide
order: 20
---
# ArkCompiler LLVM Interpreter Build Guide

This document summarizes how the current `static_core` CMake and SDK build system handles runtime artifacts with LLVM interpreter support.

It focuses on two common command patterns:

1. Building Linux x86_64 host artifacts directly with CMake.
2. Building OHOS Arm64 device artifacts and Linux host tools with `scripts/sdk/build_sdk.sh`.

The analysis is based on the current repository sources, mainly:

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

## 1. Summary

### Command 1: Host CMake Build

Original command:

```bash
sudo ../scripts/install-deps-ubuntu -i=llvm-prebuilts
cd build
cmake .. -DPANDA_LLVM_BACKEND=ON -DPANDA_LLVM_INTERPRETER=ON -DPANDA_LLVM_FASTPATH=ON -DLLVM_DIR=/path/to/llvm-15-prebuilts/lib/cmake/llvm/
ninja all
```

Without a cross-compilation toolchain, `cmake ..` builds for the current host platform. On a typical development machine, this means Linux x86_64 host artifacts, not OHOS/Arm64 device artifacts.

There is also an important current-source restriction: Linux x86_64 non-cross builds do not support explicitly enabling `PANDA_LLVM_FASTPATH=ON`. For `PANDA_TARGET_AMD64 AND NOT CMAKE_CROSSCOMPILING AND NOT HOST_TOOLS`, `cmake/Definitions.cmake` fails configuration with:

```text
PANDA_LLVM_FASTPATH is not supported for x86_64
```

So this command must be adjusted for the current repository. At minimum, do not pass `-DPANDA_LLVM_FASTPATH=ON` for a Linux x86_64 host build.

### Command 2: SDK Build

Original command:

```bash
cd static_core/scripts/sdk
./build_sdk.sh build-sdk --build_type=Release --ohos_arm64 --ets_std_lib --linux_tools
```

Here `build-sdk` is the SDK build destination name, not a subcommand. By default, the final SDK is written to:

```text
static_core/scripts/sdk/build-sdk/sdk
```

This command builds two kinds of artifacts:

- `--ohos_arm64`: OHOS/aarch64 device runtime and related libraries.
- `--linux_tools`: Linux x86_64 host tools, such as `es2panda`, `ark_link`, `ark_disasm`, `verifier`, and host versions of `ark` and `ark_aot`.

It does not depend on the build directory produced by Command 1. Both command flows depend on the same LLVM prebuilts, but they create separate CMake build trees.

## 2. LLVM Backend CMake Options

`PANDA_LLVM_BACKEND=ON` is the top-level switch. Once enabled, CMake derives or accepts the following feature flags depending on target platform and explicit user arguments:

- `PANDA_LLVM_INTERPRETER`: LLVM irtoc interpreter. Enabled by default.
- `PANDA_LLVM_AOT`: LLVM AOT compiler. Enabled by default.
- `PANDA_LLVM_FASTPATH`: LLVM fastpath objects. Enabled by default for Arm64 and cross builds, but disabled by default for Linux x86_64 non-cross builds. Explicitly enabling it for Linux x86_64 host builds is an error.
- `PANDA_LLVM_IRTOC`: Internal flag. Set when LLVM interpreter or LLVM fastpath generation is needed.
- `PANDA_BUILD_LLVM_BACKEND`: Internal flag. Decides whether `libllvmbackend` should be built.

The corresponding logic is in `cmake/Definitions.cmake`:

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

## 3. LLVM Prebuilts

Install the Ark-modified LLVM 15 prebuilts:

```bash
cd /path/to/runtime_core/static_core
sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts
```

The dependency installs Ark-modified LLVM 15 prebuilts. Common paths prepared by the current installer include:

```text
/opt/llvm-15-release-x86_64
/opt/llvm-15-debug-x86_64
/opt/llvm-15-release-aarch64
/opt/llvm-15-debug-aarch64
/opt/llvm-15-release-ohos
```

The SDK script also has default variables for FastVerify paths, such as `/opt/llvm-15-release-aarch64-fastverify` and `/opt/llvm-15-release-ohos-fastverify`. If using `--build_type=FastVerify`, make sure those directories exist or override them with the corresponding `--llvm_prebuilts_*_fastverify=...` options.

The repository README and SDK scripts primarily use `LLVM_TARGET_PATH`, for example:

```bash
-DLLVM_TARGET_PATH=/opt/llvm-15-release-x86_64
```

`libllvmbackend/cmake/LLVM.cmake` finds LLVM with:

```cmake
find_package(LLVM 15 REQUIRED CONFIG NO_DEFAULT_PATH CMAKE_FIND_ROOT_PATH_BOTH PATHS ${LLVM_TARGET_PATH})
```

Passing `LLVM_DIR=/path/to/lib/cmake/llvm` may work in some configurations, but it is not the main convention used by this repository. Prefer `LLVM_TARGET_PATH`.

Cross builds need two LLVM paths:

- `LLVM_TARGET_PATH`: target-platform LLVM, for example `/opt/llvm-15-release-ohos` for OHOS/aarch64.
- `LLVM_HOST_PATH`: host LLVM used by host tools, for example `/opt/llvm-15-release-x86_64`.

## 4. Recommended Linux x86_64 Host Build

Use this when you need Linux x86_64 host `ark`, `ark_aot`, runtime libraries, and LLVM backend support:

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

If you only need the core runtime and AOT tool, build a smaller target set:

```bash
ninja -C build-llvm-host ark ark_aot arkruntime llvmbackend
```

Typical artifacts:

```text
build-llvm-host/bin/ark
build-llvm-host/bin/ark_aot
build-llvm-host/lib/libarkruntime.so
build-llvm-host/lib/libllvmbackend.so
build-llvm-host/lib/libLLVM-15.so
```

Do not pass `-DPANDA_LLVM_FASTPATH=ON` for a Linux x86_64 host build in the current repository.

## 5. Recommended OHOS Arm64 Device SDK Build

Use this to build OHOS/aarch64 device runtime artifacts and Linux host tools:

```bash
cd /path/to/runtime_core/static_core

sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts

cd scripts/sdk
./build_sdk.sh build-sdk --build_type=Release --ohos_arm64 --ets_std_lib --linux_tools
```

Default output directory:

```text
static_core/scripts/sdk/build-sdk/sdk
```

### What `--ohos_arm64` Builds

`ohos_arm64()` in `scripts/sdk/build_sdk_lib` configures a cross build:

```text
static_core/scripts/sdk/build-sdk/ohos_arm64
```

Key CMake arguments:

```bash
-DCMAKE_TOOLCHAIN_FILE=cmake/toolchain/cross-ohos-musl-aarch64.cmake
-DTOOLCHAIN_SYSROOT=$OHOS_SDK_NATIVE/sysroot
-DTOOLCHAIN_CLANG_ROOT=$OHOS_SDK_NATIVE/llvm
-DPANDA_ETS_INTEROP_JS=ON
-DPANDA_LLVM_BACKEND=ON
-DLLVM_TARGET_PATH=/opt/llvm-15-release-ohos
-DLLVM_HOST_PATH=/opt/llvm-15-release-x86_64
```

The toolchain file sets:

```cmake
CMAKE_SYSTEM_NAME      = OHOS
CMAKE_SYSTEM_PROCESSOR = aarch64
PANDA_TRIPLET          = aarch64-linux-ohos
```

Build targets include:

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

Key device artifacts copied into the SDK:

```text
sdk/ohos_arm64/bin/ark
sdk/ohos_arm64/bin/ark_aot
sdk/ohos_arm64/lib/libarkruntime.so
sdk/ohos_arm64/lib/libarkcompiler.so
sdk/ohos_arm64/lib/libllvmbackend.so
sdk/ohos_arm64/lib/libLLVM-15.so
```

Full copy list:

```text
scripts/sdk/ohos_arm64.txt
```

### What `--linux_tools` Builds

`linux_tools()` configures a Linux x86_64 host build:

```text
static_core/scripts/sdk/build-sdk/linux_host_tools
```

Key CMake arguments:

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

Build targets include:

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

Key host tools copied into the SDK:

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

Full copy list:

```text
scripts/sdk/linux_host_tools.txt
```

### What `--ets_std_lib` Does

This option does not enable LLVM and does not select a target platform. It only copies ETS standard library source directories into the SDK:

```text
plugins/ets/stdlib/std
plugins/ets/stdlib/arkruntime
```

If `etsstdlib.abc` is generated during the build, `copy_abc_files()` copies it to:

```text
sdk/ets/etsstdlib.abc
```

## 6. Host Tools Inside the SDK Cross Build

When cross-compiling OHOS Arm64 artifacts, target binaries cannot run on the Linux host. However, the build still needs host-executable tools to generate code, especially irtoc objects.

For this reason, `cmake/HostTools.cmake` creates an internal host-tools build inside the OHOS Arm64 build tree:

```text
static_core/scripts/sdk/build-sdk/ohos_arm64/host-tools-build
```

It uses `LLVM_HOST_PATH` as its LLVM target path:

```bash
-DLLVM_TARGET_PATH=${LLVM_HOST_PATH}
```

It produces generated objects required by the target build, such as:

```text
irtoc_fastpath.o
irtoc_fastpath_llvm.o
irtoc_interpreter.o
irtoc_interpreter_llvm.o
```

This internal host-tools build is not the same as the SDK `--linux_tools` build:

- `ohos_arm64/host-tools-build`: internal build-time tools used by the OHOS Arm64 cross build.
- `linux_host_tools`: delivered SDK tools for Linux x86_64 hosts.

## 7. How the LLVM Interpreter Is Selected

The runtime default is declared in `runtime/options.yaml`:

```yaml
- name: interpreter-type
  type: std::string
  default: llvm
  possible_values: [cpp, irtoc, llvm]
```

When `PANDA_LLVM_INTERPRETER` is defined, `--interpreter-type=llvm` enters:

```cpp
ExecuteImplFast_LLVM(...)
ExecuteImplFastEH_LLVM(...)
```

If `PANDA_LLVM_INTERPRETER` is not defined, the default `llvm` mode is downgraded to `irtoc`. If `PANDA_WITH_IRTOC` is not defined either, it is further downgraded to `cpp`.

For benchmarks and debugging, pass the interpreter explicitly:

```bash
--interpreter-type=llvm
```

This avoids assuming that the default always reaches the LLVM interpreter.

## 8. Deploying OHOS Arm64 Artifacts

After the SDK build, device-side artifacts are under:

```text
static_core/scripts/sdk/build-sdk/sdk/ohos_arm64
```

Common files to deploy:

```text
sdk/ohos_arm64/bin/ark
sdk/ohos_arm64/bin/ark_aot
sdk/ohos_arm64/lib/
sdk/ets/etsstdlib.abc
```

Make sure the device runtime can find the shared libraries, especially:

```text
libarkruntime.so
libarkcompiler.so
libllvmbackend.so
libLLVM-15.so
```

If deploying manually, set `LD_LIBRARY_PATH` to the deployed `lib` directory.

## 9. Common Misunderstandings

### Misunderstanding 1: Command 2 depends on Command 1 output

It does not. `build_sdk.sh` creates its own `ohos_arm64` and `linux_host_tools` build directories. It depends on LLVM prebuilts, OHOS SDK native, source files, and third-party dependencies.

### Misunderstanding 2: `--ohos_arm64` means Linux Arm64

It does not. `--ohos_arm64` uses `cross-ohos-musl-aarch64.cmake`; the target OS is OHOS and the target architecture is aarch64.

For Linux/aarch64 tools, use:

```bash
--linux_arm64_tools
```

### Misunderstanding 3: LLVM fastpath can be enabled for host x86_64 builds

Not in the current repository. For Linux x86_64 host builds, either omit `PANDA_LLVM_FASTPATH` and let CMake disable it by default, or pass:

```bash
-DPANDA_LLVM_FASTPATH=OFF
```

### Misunderstanding 4: Cross builds need only one LLVM path

With full LLVM backend functionality enabled, cross builds need both:

```bash
-DLLVM_TARGET_PATH=/opt/llvm-15-release-ohos
-DLLVM_HOST_PATH=/opt/llvm-15-release-x86_64
```

The SDK script passes both automatically.

### Misunderstanding 5: `LLVM_DIR` is the recommended parameter

The current repository convention is `LLVM_TARGET_PATH`. `LLVM_DIR` may work, but it is not the primary path convention used by the README and SDK scripts.

## 10. Minimal Decision Table

| Goal | Recommended command | Runs on | Main output |
|---|---|---|---|
| Linux x86_64 host runtime and tools | Host CMake build | Host | `build/bin`, `build/lib` |
| OHOS Arm64 device runtime | `build_sdk.sh --ohos_arm64` | Device | `sdk/ohos_arm64` |
| Linux x86_64 host SDK tools | `build_sdk.sh --linux_tools` | Host | `sdk/linux_host_tools` |
| Linux Arm64 tools | `build_sdk.sh --linux_arm64_tools` | Linux/aarch64 or QEMU scenarios | `sdk/linux_arm64_host_tools` |

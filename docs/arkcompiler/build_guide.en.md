# ArkCompiler Build Guide

This document consolidates the CMake build commands and Device LLVM build steps for ArkCompiler.

## 1. Environment Preparation

Ensure all necessary dependencies are installed before building.

```bash
cd static_core/tools
ln -s ../../../arkcompiler_ets_frontend/ets2panda es2panda

cd ..
sudo ./scripts/install-deps-ubuntu -i=dev -i=test
sudo apt install gdb
./scripts/install-third-party --force-clone
```

## 2. CMake Build (Host)

### Release Build

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=./cmake/toolchain/host_clang_default.cmake -GNinja .
cmake --build build
```

### Debug Build

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_TOOLCHAIN_FILE=./cmake/toolchain/host_clang_default.cmake -GNinja .
cmake --build build
```

## 3. LLVM Device Build (OHOS ARM64)

### Install Dependencies

```bash
sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts
```

### Build SDK

```bash
cd /home/fanzewei/code/fzw_arkc_0805/arkcompiler_runtime_core/static_core/scripts/sdk
./build_sdk.sh build-sdk --build_type=Release --ohos_arm64 --ets_std_lib --linux_tools
```

### Deploy Artifacts

Copy the compiled binaries and libraries to the target directory:

```bash
# Copy binaries
cp ./ohos_arm64/bin/ark /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out/
cp ./ohos_arm64/bin/ark_aot /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out/

# Copy libraries
cp -r ./ohos_arm64/lib /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out

# Copy stdlib abc file
cp ./sdk/ets/etsstdlib.abc /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out
```

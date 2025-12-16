# ArkCompiler 编译指南

本文档汇总了 ArkCompiler 的 CMake 编译命令以及 Device LLVM 的构建步骤。

## 1. 编译环境准备

在开始编译之前，请确保已安装所有必要的依赖项。

```bash
cd static_core/tools
ln -s ../../../arkcompiler_ets_frontend/ets2panda es2panda

cd ..
sudo ./scripts/install-deps-ubuntu -i=dev -i=test
sudo apt install gdb
./scripts/install-third-party --force-clone
```

## 2. CMake 编译 (Host)

### Release 版本

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=./cmake/toolchain/host_clang_default.cmake -GNinja .
cmake --build build
```

### Debug 版本

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_TOOLCHAIN_FILE=./cmake/toolchain/host_clang_default.cmake -GNinja .
cmake --build build
```

## 3. LLVM Device 编译 (OHOS ARM64)

### 安装依赖

```bash
sudo ./scripts/install-deps-ubuntu -i=llvm-prebuilts
```

### 构建 SDK

```bash
cd /home/fanzewei/code/fzw_arkc_0805/arkcompiler_runtime_core/static_core/scripts/sdk
./build_sdk.sh build-sdk --build_type=Release --ohos_arm64 --ets_std_lib --linux_tools
```

### 部署产物

将编译生成的二进制文件和库文件复制到指定目录：

```bash
# 复制二进制文件
cp ./ohos_arm64/bin/ark /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out/
cp ./ohos_arm64/bin/ark_aot /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out/

# 复制库文件
cp -r ./ohos_arm64/lib /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out

# 复制标准库 abc 文件
cp ./sdk/ets/etsstdlib.abc /home/fanzewei/code/fzw_arkc_0805/0821_llvm_out
```

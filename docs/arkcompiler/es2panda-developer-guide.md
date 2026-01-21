# es2panda Developer Guide

本文档汇总并补充 `es2panda` 在编译 ArkTS (`.ets`) 时常见配置与实践，重点覆盖：声明依赖（`.d.ets`）、`arktsconfig.json`、标准库使用、以及导入路径解析的关键规则。

---

## 1. 编译包含声明依赖（`.d.ets`）

当代码依赖第三方声明（`.d.ets`）或拆分模块时，有两种主要方式让编译器解析依赖。

### 方法 A：使用 `arktsconfig.json`（推荐）

建议在真实工程或复杂依赖中使用 `arktsconfig.json`，通过 `compilerOptions.paths` 显式映射模块路径。

**命令：**
```bash
./build/bin/es2panda --arktsconfig path/to/arktsconfig.json source_file.ets
```

**配置结构：**
- 必须包含标准库路径 `std` 与 `escompat`，否则基础类型（如 `string`、`Object`、`console`）无法解析。
- 可选添加 `api` 与 `arkts`，用于引入 SDK API 与 ArkTS 扩展接口（与构建时默认配置保持一致）。

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "std": ["/path/to/arkcompiler/runtime_core/static_core/plugins/ets/stdlib/std"],
      "escompat": ["/path/to/arkcompiler/runtime_core/static_core/plugins/ets/stdlib/escompat"],
      "api": ["/path/to/arkcompiler/runtime_core/static_core/plugins/ets/sdk/api"],
      "arkts": ["/path/to/arkcompiler/runtime_core/static_core/plugins/ets/sdk/arkts"],
      "dependency": ["./path/to/your/lib.d.ets"]
    }
  }
}
```

**依赖元信息（可选）：`compilerOptions.dependencies`**

`dependencies` 可为某些导入路径标注语言类型与声明文件位置。若未指定，语言由后缀推断，`hasDecl` 默认为 `true`。

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "std": [".../stdlib/std"],
      "escompat": [".../stdlib/escompat"]
    },
    "dependencies": {
      "dynamic_js_import_tests": { "language": "js" },
      "path/to/ets/dynamic_import_tests": {
        "language": "js",
        "path": "path/to/ets/declaration"
      }
    }
  }
}
```

### 方法 B：相对路径引用（简单快速）

用于小型验证或临时测试，可直接把 `.d.ets` 放在同目录或相对目录中，通过相对路径导入。

**结构示例：**
```
project/
  ├── Main.ets
  └── Lib.d.ets
```

**使用方式：**
```ts
// Main.ets
import { foo } from "./Lib";   // 可省略扩展名
// 或
import { foo } from "./Lib.d"; // 常见于测试用例
```

**命令：**
```bash
./build/bin/es2panda project/Main.ets
```

> 说明：导入路径可以是相对或绝对路径；可带或不带扩展名。也可指向包目录（含 `index.ets`/`index.ts`）或包模块路径。

---

## 2. 编写合法的 `.d.ets` 声明文件

**顶层导出**应使用 `declare`，例如：

```ts
export declare function foo(): void;
export declare class Bar {
    public static id(): string;
}
```

**在 `export declare namespace` 内部**，成员可以直接 `export function` / `export class`，不需要再加 `declare`：

```ts
export declare namespace MixedNamespace {
    export const constantValue: number;
    export function someFunction(): void;
    export interface SomeInterface {
        id: number;
    }
    export class SomeClass {
        prop: string;
    }
}
```

> 建议：若未使用 `declare`，可能触发语义错误或类型检查失败。为减少歧义，尽量在顶层使用 `export declare`。

---

## 3. 标准库与隐式导入

### 高精度计时（`Chrono.nanoNow()`）

推荐从包路径导入：

```ts
import { Chrono } from "std/time";

function main() {
    let t: long = Chrono.nanoNow();
    console.log(t);
}
```

**API 细节：**
- **Package**: `std.time`
- **Class**: `Chrono`（`final`）
- **Method**: `public static native nanoNow(): long;`

### 隐式标准库导入

编译器会为每个模块隐式导入一部分核心标准库包（例如 `std/core`、`std/math`），因此 `console` 等符号可以直接使用。该行为由内部默认导入文件实现，常规项目无需显式配置。

---

## 4. 导入风格：包导入 vs 文件导入

| 导入方式 | 示例 | 行为 | 建议 |
| :--- | :--- | :--- | :--- |
| **包导入** | `import { Chrono } from "std/time";` | 按包路径聚合导出，稳定可靠 | **推荐** |
| **文件导入** | `import { Chrono } from "std/time/Chrono";` | 直接指向物理文件，容易因文件移动而失效 | 不推荐 |

> 结论：优先使用包路径（如 `std/time`），除非有明确理由必须绑定具体文件。

---

## 5. `arktsconfig.json` 速查与常用模板

### 最小可用模板

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "std": ["../lib/stdlib/std"],
      "escompat": ["../lib/stdlib/escompat"]
    }
  }
}
```

### SDK 示例（含 `files`）

```json
{
  "compilerOptions": {
    "baseUrl": "../../",
    "paths": {
      "std": ["ets/stdlib/std"],
      "escompat": ["ets/stdlib/escompat"]
    },
    "outDir": "../cache"
  },
  "files": [
    "./api/@ohos.buffer.ets",
    "./arkts/@arkts.math.Decimal.ets"
  ]
}
```

> 参考位置：`plugins/ets/stdlib/stdconfig.json` 与 `plugins/ets/sdk/arktsconfig.json`。

### 构建时生成的默认配置

构建系统会生成 `arktsconfig.json`，其内容通常包含 `std`、`escompat`、`api`、`arkts` 等路径。可用于核对路径设置是否一致。

---

## 6. 补充：`import type` 与值导入

ArkTS 支持 `import type` 只导入类型：

```ts
import type { A } from "./types";
import { AImpl } from "./impl";
```

- `import type` 仅引入类型，不引入值；
- 普通 `import` 同时引入类型与运行时值。

---

## 7. 常见排错提示

- **基础类型/console 未解析**：多半是 `std` / `escompat` 映射缺失。
- **依赖 JS 模块解析失败**：考虑在 `dependencies` 中声明 `language` 或 `path`。
- **声明文件编译失败**：检查顶层是否正确使用 `export declare`。


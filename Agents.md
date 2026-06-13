# AI Agent Wiki Maintenance Protocol (Agents.md)

This document is a Standard Operating Procedure (SOP) guide designed for AI Coding Assistants (e.g., Antigravity, Claude, ChatGPT, Cursor). It instructs how to properly add, edit, restructure, and automatically deploy wiki articles in this repository.

---

## 📂 Project Structure Overview

```text
my-wiki/
├── docs/                     # Source Markdown files
│   ├── index.zh.md           # Chinese landing page (default locale)
│   ├── index.en.md           # English landing page
│   ├── <category_name>/      # A category directory (e.g. arkcompiler, leetcode)
│   │   ├── category.yml      # Directory metadata (title, translation, sort order)
│   │   ├── article1.zh.md    # Chinese version of article1
│   │   └── article1.en.md    # English version of article1
├── .github/workflows/
│   └── publish.yml           # GitHub Actions deploy workflow
├── generate_nav.py           # Python script to auto-generate mkdocs.yml navigation
└── mkdocs.yml                # MkDocs configuration (auto-updated by script)
```

---

## 📝 Rules for Adding or Editing Documents

### 1. File Naming & Multi-language Mapping
We use `mkdocs-static-i18n` with the `suffix` structure for translation.
*   **Chinese/Default Version**: Use `filename.zh.md` (or simply `filename.md`).
*   **English Version**: Use `filename.en.md`.
*   Both language files must share the exact same base name `filename` to be grouped under the same logical navigation item.

### 2. Front Matter Specifications
Every Markdown file **MUST** include a YAML Front Matter block at the very top. It specifies the display title and sorting order:

```yaml
---
title: Arena 分配器测试指南             # Navigation title for this language
title_en: Arena Allocator Testing Guide # (Optional) English translation fallback (if en.md does not exist)
order: 10                               # Sort order (smaller numbers appear first)
---
# Actual Heading 1
...
```

*   **order**: Specify an integer value (e.g., `10`, `20`, `30`). This defines the relative sorting position within the parent directory.
*   If no `title` is declared in Front Matter, the script fallback-extracts the first `# H1` tag in the document.

### 3. Adding a New Directory (Category)
When creating a new subfolder under `docs/`, you **MUST** create a `category.yml` inside it:
```yaml
title: 编译器 (ArkCompiler)              # Chinese title for this category folder in nav
title_en: ArkCompiler                  # English translation for this folder in nav
order: 1                               # Sort order of this category in the main tabs
```
*   If `category.yml` is missing, the script defaults to the directory name (capitalized).

---

## 🤖 Steps to Execute After Modifications

When you (the AI Assistant) have finished creating or modifying markdown files/folders, execute the following steps sequentially:

### Step 1: Regenerate Navigation
Run the Python script in the repository root to scan the filesystem and update `mkdocs.yml`:
```bash
python3 generate_nav.py
```
*   This will automatically update the `nav:` block and the `plugins.i18n.nav_translations.en` mapping in `mkdocs.yml`.

### Step 2: Local Verification (Optional but Recommended)
Build the MkDocs site locally to ensure there are no formatting, YAML structure, or plugin errors:
```bash
python3 -m mkdocs build
```
*   Ensure that the build succeeds without error.

### Step 3: Git Commit and Push
Finally, stage all changes (including the updated `mkdocs.yml` and `category.yml` files, if any) and push to GitHub:
```bash
git add .
git commit -m "docs: add/update articles via AI Agent"
git push origin main
```
*   *Note*: The GitHub Action (`.github/workflows/publish.yml`) is configured to run `python generate_nav.py` automatically before compilation. However, committing the updated `mkdocs.yml` keeps your local working tree clean and in-sync.

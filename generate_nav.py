#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import yaml

# ==============================================================================
# PyYAML 处理自定义标记 (如 !!python/name:...) 的兼容逻辑
# ==============================================================================
class PyNameTag:
    """透传存储和还原 !!python/name: 标签的对象"""
    def __init__(self, suffix):
        self.suffix = suffix
    def __repr__(self):
        return f"PyNameTag({self.suffix})"

def python_name_constructor(loader, tag_suffix, node):
    return PyNameTag(tag_suffix)

def python_name_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:python/name:' + data.suffix, '')

# 注册 Loader 和 Dumper
yaml.SafeLoader.add_multi_constructor('tag:yaml.org,2002:python/name:', python_name_constructor)
yaml.SafeDumper.add_representer(PyNameTag, python_name_representer)

# ==============================================================================
# 解析与扫描逻辑
# ==============================================================================
def parse_front_matter(file_path):
    """解析 Markdown 头部的 Front Matter (YAML)"""
    title = None
    title_en = None
    order = 999
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 正则匹配最头部的 --- ... ---
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm_text = match.group(1)
                fm = yaml.safe_load(fm_text)
                if fm:
                    title = fm.get('title')
                    title_en = fm.get('title_en')
                    order = fm.get('order', 999)
            
            # 如果 Front Matter 中没有定义 title，提取第一个 # 标题
            if not title:
                body = content[match.end():] if match else content
                h1_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
                if h1_match:
                    title = h1_match.group(1).strip()
    except Exception as e:
        print(f"[Warning] Failed to parse front matter of {file_path}: {e}")
        
    return title, title_en, order


def get_category_meta(dir_path):
    """读取子目录中的 category.yml 配置"""
    category_file = os.path.join(dir_path, 'category.yml')
    # 默认值：文件夹名首字母大写
    default_title = os.path.basename(dir_path).replace('_', ' ').capitalize()
    title = default_title
    title_en = None
    order = 999
    
    if os.path.exists(category_file):
        try:
            with open(category_file, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)
                if meta:
                    title = meta.get('title', title)
                    title_en = meta.get('title_en')
                    order = meta.get('order', 999)
        except Exception as e:
            print(f"[Warning] Failed to parse category.yml at {dir_path}: {e}")
            
    return title, title_en, order


def scan_directory(dir_path, base_docs_dir):
    """
    递归扫描 docs 目录
    返回:
      - nav_items: 列表，含元组 (order, nav_node)
      - translations: dict, 存放中文到英文的标题翻译映射
    """
    items = []
    translations = {}
    
    # 扫描该目录下的项
    entries = sorted(os.listdir(dir_path))
    
    md_groups = {}
    subdirs = []
    
    for entry in entries:
        full_path = os.path.join(dir_path, entry)
        
        # 1. 递归处理子目录 (忽略以点开头的隐藏目录)
        if os.path.isdir(full_path):
            if not entry.startswith('.'):
                subdirs.append(full_path)
                
        # 2. 聚合 Markdown 文件（如 build.zh.md / build.en.md -> build.md）
        elif entry.endswith('.md'):
            # 排除各目录下的 index.md 首页文件（首页固定处理，子目录暂时也不作为 nav 节点）
            if entry.startswith('index.'):
                continue
                
            base_name = entry
            for suffix in ['.zh.md', '.en.md', '.md']:
                if entry.endswith(suffix):
                    base_name = entry[:-len(suffix)]
                    break
            
            if base_name not in md_groups:
                md_groups[base_name] = {}
                
            if entry.endswith('.zh.md'):
                md_groups[base_name]['zh'] = entry
            elif entry.endswith('.en.md'):
                md_groups[base_name]['en'] = entry
            elif entry.endswith('.md'):
                md_groups[base_name]['default'] = entry

    # 处理聚合后的 Markdown 文档
    for base_name, files in md_groups.items():
        # 换算相对于 docs 目录的相对路径
        rel_dir = os.path.relpath(dir_path, base_docs_dir)
        if rel_dir == '.':
            rel_dir = ''
            
        logical_rel_path = os.path.join(rel_dir, f"{base_name}.md").replace('\\', '/')
        
        zh_file = files.get('zh') or files.get('default')
        en_file = files.get('en')
        
        zh_full_path = os.path.join(dir_path, zh_file) if zh_file else None
        en_full_path = os.path.join(dir_path, en_file) if en_file else None
        
        # 解析元数据
        title_zh, title_zh_en, order_zh = parse_front_matter(zh_full_path) if zh_full_path else (None, None, 999)
        title_en, _, order_en = parse_front_matter(en_full_path) if en_full_path else (None, None, 999)
        
        # 组合最终值
        final_title_zh = title_zh or title_en or base_name.replace('_', ' ').capitalize()
        # 英文标题：优先使用 en.md 中的 title，其次使用 zh.md 中声明的 title_en，最后使用 zh.md 本身 title
        final_title_en = title_en or title_zh_en or title_zh or base_name.replace('_', ' ').capitalize()
        final_order = min(order_zh, order_en)
        
        # 记录翻译
        if final_title_en and final_title_en != final_title_zh:
            translations[final_title_zh] = final_title_en
            
        items.append((final_order, {final_title_zh: logical_rel_path}))

    # 处理子目录
    for subdir in subdirs:
        sub_title_zh, sub_title_en, sub_order = get_category_meta(subdir)
        sub_items, sub_translations = scan_directory(subdir, base_docs_dir)
        
        # 合并子目录中产出的翻译
        translations.update(sub_translations)
        if sub_title_en:
            translations[sub_title_zh] = sub_title_en
            
        if sub_items:
            # 根据 order 对子目录内条目排序
            sub_items.sort(key=lambda x: x[0])
            sorted_sub_nav = [x[1] for x in sub_items]
            
            items.append((sub_order, {sub_title_zh: sorted_sub_nav}))
            
    return items, translations


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(script_dir, 'docs')
    mkdocs_file = os.path.join(script_dir, 'mkdocs.yml')
    
    print("Scanning docs folder for navigation metadata...")
    items, translations = scan_directory(docs_dir, docs_dir)
    
    # 按照 order 排序顶层目录和文件
    items.sort(key=lambda x: x[0])
    
    # 组装最终 nav 结构
    final_nav = [{"Home": "index.md"}]
    for order, item in items:
        final_nav.append(item)
        
    print(f"Generated nav structure: {final_nav}")
    print(f"Generated i18n translations: {translations}")
    
    # 读取并修改 mkdocs.yml
    if not os.path.exists(mkdocs_file):
        print(f"[Error] {mkdocs_file} does not exist.")
        return
        
    with open(mkdocs_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    # 覆写 nav
    config['nav'] = final_nav
    
    # 覆写 i18n 中的 nav_translations
    i18n_plugin = None
    if 'plugins' in config:
        for idx, plugin in enumerate(config['plugins']):
            if isinstance(plugin, dict) and 'i18n' in plugin:
                i18n_plugin = plugin['i18n']
                break
            elif plugin == 'i18n':
                i18n_plugin = {}
                config['plugins'][idx] = {'i18n': i18n_plugin}
                break
                
    if i18n_plugin is not None:
        # 清除可能残留的旧全局 nav_translations 键
        i18n_plugin.pop('nav_translations', None)
        
        # 寻找到 languages 列表中 locale == 'en' 的项并更新其 nav_translations
        if 'languages' in i18n_plugin and isinstance(i18n_plugin['languages'], list):
            en_lang_config = None
            for lang in i18n_plugin['languages']:
                if isinstance(lang, dict) and lang.get('locale') == 'en':
                    en_lang_config = lang
                    break
            
            if en_lang_config is not None:
                en_lang_config['nav_translations'] = {}
                en_lang_config['nav_translations']['Home'] = 'Home'
                for zh_name, en_name in translations.items():
                    en_lang_config['nav_translations'][zh_name] = en_name
            else:
                print("[Warning] Could not find 'en' locale config in 'languages'.")
        else:
            print("[Warning] 'languages' block is missing or not a list in mkdocs.yml.")
    else:
        print("[Warning] Could not find 'i18n' plugin in mkdocs.yml. Translations won't be applied.")

    # 回写到 mkdocs.yml
    with open(mkdocs_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
    print("Successfully updated mkdocs.yml!")

if __name__ == '__main__':
    main()

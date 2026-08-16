#!/usr/bin/env python3
"""SDD (Spec-Driven Development) Lifecycle & Cascading Synchronization Engine.

Commands:
  status   - View current active feature progress, task states & document health
  new      - Initialize a new PRD feature from templates
  sync     - Cascade and propagate mid-iteration changes across spec -> plan -> tasks -> eval
  archive  - Archive completed iteration, update ARCHIVE_INDEX.md, and reset context
"""

import argparse
import datetime
import os
import re
import shutil
import sys
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPECS_DIR = os.path.join(WORKSPACE_ROOT, "specs")
TEMPLATES_DIR = os.path.join(SPECS_DIR, "templates")
ARCHIVE_DIR = os.path.join(SPECS_DIR, "archive")
INDEX_FILE = os.path.join(SPECS_DIR, "ARCHIVE_INDEX.md")

SDD_FILES = ["spec.md", "plan.md", "tasks.md", "eval.md", "learnings.md"]


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Parse YAML frontmatter from a markdown string."""
    data = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            for line in yaml_block.strip().split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().split("#")[0].strip().strip('"').strip("'")
                    data[k] = v
    return data


def get_active_feature_info() -> Optional[Dict[str, str]]:
    """Retrieve info about currently active feature in specs/."""
    spec_path = os.path.join(SPECS_DIR, "spec.md")
    if not os.path.exists(spec_path):
        return None
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()
    fm = parse_frontmatter(content)
    # Extract title from H1 if not in frontmatter
    if "title" not in fm:
        m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if m:
            fm["title"] = m.group(1).strip()
    return fm


def cmd_status(args: argparse.Namespace) -> int:
    """Check status of active feature."""
    print("=" * 65)
    print("📋 SDD (Spec-Driven Development) 活跃工作区状态")
    print("=" * 65)

    feat_info = get_active_feature_info()
    if not feat_info:
        print("[状态] 当前无活跃中的 PRD 特性开发（specs/ 干净）。")
        print("💡 提示：运行 `python tools/sdd.py new <FEAT_ID> <名称>` 启动新特性。")
        if os.path.exists(INDEX_FILE):
            print(f"\n📂 历史已归档特性见索引: {INDEX_FILE}")
        return 0

    spec_id = feat_info.get("specId", "未知 ID")
    title = feat_info.get("title", "未命名特性")
    status = feat_info.get("status", "未知")
    version = feat_info.get("version", "0.1")

    print(f"🎯 当前特性: {spec_id} - {title}")
    print(f"📌 当前版本: v{version} | 状态: {status}")
    print("-" * 65)

    # Check existence and stats of 5 SDD files
    print("📄 规范文档状态清单:")
    for fname in SDD_FILES:
        fpath = os.path.join(SPECS_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                c = f.read()
            lines = len(c.splitlines())
            fm = parse_frontmatter(c)
            doc_status = fm.get("status", "已创建")
            print(f"  ✅ specs/{fname:<14} [{doc_status:<6}] ({lines} 行)")
        else:
            print(f"  ❌ specs/{fname:<14} [缺失]")

    # Check tasks progress
    tasks_path = os.path.join(SPECS_DIR, "tasks.md")
    if os.path.exists(tasks_path):
        with open(tasks_path, "r", encoding="utf-8") as f:
            tc = f.read()
        done_tasks = len(re.findall(r"\[x\]|✅", tc, re.IGNORECASE))
        pending_tasks = len(re.findall(r"\[ \]", tc))
        total_tasks = done_tasks + pending_tasks
        if total_tasks > 0:
            pct = int((done_tasks / total_tasks) * 100)
            print(f"\n🚀 任务执行进度: {done_tasks}/{total_tasks} 完成 ({pct}%)")

    # Check eval verdict
    eval_path = os.path.join(SPECS_DIR, "eval.md")
    if os.path.exists(eval_path):
        with open(eval_path, "r", encoding="utf-8") as f:
            ec = f.read()
        if "【通过】" in ec or "status: 已确认" in ec:
            print("🏆 评测验收结论: ✅ 【通过】 (可执行 `python tools/sdd.py archive` 归档)")
        else:
            print("⏳ 评测验收结论: 待完成评测回填")

    print("=" * 65)
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    """Initialize a new PRD feature in specs/."""
    feat_id = args.feat_id.strip()
    feat_name = args.name.strip()
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # Check if active unarchived work exists
    if get_active_feature_info() and not args.force:
        print(f"[警告] 当前 specs/ 中已有活跃特性未归档！")
        print("建议先运行 `python tools/sdd.py archive` 归档当前工作，或使用 `--force` 强制覆盖。")
        return 1

    print(f"🚀 初始化新 PRD 特性: [{feat_id}] {feat_name}")

    if not os.path.exists(TEMPLATES_DIR):
        print(f"[错误] 模板目录不存在: {TEMPLATES_DIR}")
        return 1

    os.makedirs(SPECS_DIR, exist_ok=True)

    template_mapping = {
        "spec.template.md": "spec.md",
        "plan.template.md": "plan.md",
        "tasks.template.md": "tasks.md",
        "eval.template.md": "eval.md",
        "learnings.template.md": "learnings.md",
    }

    for tname, target_name in template_mapping.items():
        tpath = os.path.join(TEMPLATES_DIR, tname)
        target_path = os.path.join(SPECS_DIR, target_name)
        if not os.path.exists(tpath):
            print(f"[跳过] 模板文件不存在: {tpath}")
            continue
        with open(tpath, "r", encoding="utf-8") as f:
            content = f.read()

        # Variable replacement
        content = content.replace("<PROJECT>", feat_id)
        content = content.replace("<项目名称>", feat_name)
        content = content.replace("<YYYY-MM-DD>", today_str)
        content = content.replace("SPEC-<组名>-001", f"SPEC-{feat_id}")
        content = content.replace("TASKS-<组名>-001", f"TASKS-{feat_id}")
        content = content.replace("EVAL-<组名>-001", f"EVAL-{feat_id}")
        content = content.replace("LEARNINGS-<组名>-001", f"LEARNINGS-{feat_id}")

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  📝 生成: specs/{target_name}")

    print(f"\n🎉 成功初始化特性 [{feat_id}] {feat_name} 的 5 份 SDD 规范文档！")
    print("下一步操作:")
    print("  1. 由 Coding Agent 或人工完善 specs/spec.md (消歧、US验收标准)");
    print("  2. 人工评审确认后推进 plan.md 与 eval.md；");
    print("  3. 若开发中有变更，随时运行 `python tools/sdd.py sync` 级联同步。")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Cascade and propagate mid-iteration changes across all SDD documents."""
    desc = args.desc.strip()
    author = args.author or "Agent/Human"
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    impact = [s.strip().lower() for s in (args.impact or "spec,plan,tasks,eval").split(",")]

    print("=" * 65)
    print(f"🔄 执行全流程文档级联同步: \"{desc}\"")
    print("=" * 65)

    feat_info = get_active_feature_info()
    if not feat_info:
        print("[错误] 未找到活跃特性，无法同步变更。")
        return 1

    log_entry = f"| **{today_str}** | 变更调优 | {desc} | {author} |\n"

    # 1. Update spec.md change record
    if "spec" in impact:
        spec_path = os.path.join(SPECS_DIR, "spec.md")
        if os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                c = f.read()
            if "## 9. 变更记录" in c:
                c = c.strip() + f"\n{log_entry}"
            elif "## 变更记录" in c:
                c = c.strip() + f"\n{log_entry}"
            else:
                c = c.strip() + f"\n\n## 9. 变更记录\n| 版本 | 变更类型 | 变更内容说明 | 评审人 |\n| :--- | :--- | :--- | :--- |\n{log_entry}"
            with open(spec_path, "w", encoding="utf-8") as f:
                f.write(c)
            print("  ✅ [spec.md] 已记录需求变更与影响面")

    # 2. Update plan.md change record
    if "plan" in impact:
        plan_path = os.path.join(SPECS_DIR, "plan.md")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                c = f.read()
            if "## 8. 变更记录" in c:
                c = c.strip() + f"\n{log_entry}"
            elif "## 变更记录" in c:
                c = c.strip() + f"\n{log_entry}"
            else:
                c = c.strip() + f"\n\n## 8. 变更记录\n| 版本 | 变更类型 | 变更内容说明 | 评审人 |\n| :--- | :--- | :--- | :--- |\n{log_entry}"
            with open(plan_path, "w", encoding="utf-8") as f:
                f.write(c)
            print("  ✅ [plan.md] 已同步架构设计调整与约束变更")

    # 3. Update tasks.md
    if "tasks" in impact:
        tasks_path = os.path.join(SPECS_DIR, "tasks.md")
        if os.path.exists(tasks_path):
            with open(tasks_path, "r", encoding="utf-8") as f:
                c = f.read()
            # Append change note
            if "## 变更记录" not in c:
                c = c.strip() + f"\n\n## 变更记录\n| 日期 | 变更说明 | 责任人 |\n| :--- | :--- | :--- |\n| **{today_str}** | {desc} | {author} |\n"
            else:
                c = c.strip() + f"\n| **{today_str}** | {desc} | {author} |\n"
            with open(tasks_path, "w", encoding="utf-8") as f:
                f.write(c)
            print("  ✅ [tasks.md] 已关联任务依赖与执行备注")

    # 4. Update eval.md
    if "eval" in impact:
        eval_path = os.path.join(SPECS_DIR, "eval.md")
        if os.path.exists(eval_path):
            with open(eval_path, "r", encoding="utf-8") as f:
                c = f.read()
            if "## 变更记录" not in c:
                c = c.strip() + f"\n\n## 变更记录\n| 日期 | 变更说明 | 责任人 |\n| :--- | :--- | :--- |\n| **{today_str}** | {desc} | {author} |\n"
            else:
                c = c.strip() + f"\n| **{today_str}** | {desc} | {author} |\n"
            with open(eval_path, "w", encoding="utf-8") as f:
                f.write(c)
            print("  ✅ [eval.md] 已同步测试用例与验收考量")

    print("-" * 65)
    print("🎯 全流程文档级联更新完毕！")
    print("💡 建议：Agent 接下来请根据变更同步修改代码及 verify 校验命令。")
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    """Archive current completed SDD iteration and reset context."""
    print("=" * 65)
    print("📦 SDD 特性迭代自动归档与上下文隔离引擎")
    print("=" * 65)

    feat_info = get_active_feature_info()
    if not feat_info:
        print("[错误] 未在 specs/ 中检测到活跃特性，无需归档。")
        return 1

    spec_id = feat_info.get("specId", "FEAT-UNKNOWN").replace("SPEC-", "FEAT-")
    title = feat_info.get("title", "unnamed_feature")
    today_str = datetime.date.today().strftime("%Y%m%d")

    # Sanitize folder name
    safe_name = re.sub(r"[^\w\-_]", "_", title).strip("_")
    archive_folder_name = f"{spec_id}_{safe_name}"
    target_archive_dir = os.path.join(ARCHIVE_DIR, archive_folder_name)

    # Check eval.md for completion verification
    eval_path = os.path.join(SPECS_DIR, "eval.md")
    verdict = "已完成归档"
    if os.path.exists(eval_path):
        with open(eval_path, "r", encoding="utf-8") as f:
            ec = f.read()
        if "通过" in ec:
            verdict = "✅ 通过"
        elif "有条件通过" in ec:
            verdict = "⚠️ 有条件通过"

    print(f"📁 目标归档路径: specs/archive/{archive_folder_name}/")
    print(f"📊 评测判定结论: {verdict}")

    os.makedirs(target_archive_dir, exist_ok=True)

    # 1. Move all SDD files to archive
    archived_files = []
    for fname in SDD_FILES:
        src = os.path.join(SPECS_DIR, fname)
        if os.path.exists(src):
            dst = os.path.join(target_archive_dir, fname)
            shutil.move(src, dst)
            archived_files.append(fname)
            print(f"  📦 归档: specs/{fname} -> specs/archive/{archive_folder_name}/{fname}")

    # 2. Extract key learnings from learnings.md
    learnings_summary = "完成高保真还原与组件交付。"
    archived_learnings = os.path.join(target_archive_dir, "learnings.md")
    if os.path.exists(archived_learnings):
        with open(archived_learnings, "r", encoding="utf-8") as f:
            lc = f.read()
        learnings_items = re.findall(r"###\s+📌\s+\[(L-\d+)\]\s+(.+)", lc)
        if learnings_items:
            learnings_summary = "；".join([f"{code} {title}" for code, title in learnings_items])

    # 3. Update ARCHIVE_INDEX.md
    index_header = """# 📚 全局已归档特性与历史认知索引 (ARCHIVE_INDEX)

> 本文件由 `tools/sdd.py archive` 自动维护。记录所有已完成交付的 PRD 特性、判定结论与沉淀经验，供后续新 PRD 开发时作为全局上下文参考。

| 特性编号 | 特性名称 | 归档日期 | 验收结论 | 核心认知与沉淀经验 (Learnings) | 归档归属 |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(index_header)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        existing_index = f.read()

    new_index_entry = f"| **{spec_id}** | {title} | {datetime.date.today().strftime('%Y-%m-%d')} | {verdict} | {learnings_summary} | [`{archive_folder_name}/`](file:///Users/feng.liu/workspace/specs/archive/{archive_folder_name}) |\n"

    # Avoid duplicate index entries
    if spec_id not in existing_index:
        with open(INDEX_FILE, "a", encoding="utf-8") as f:
            f.write(new_index_entry)
        print(f"  📝 已追加更新全局特性索引: specs/ARCHIVE_INDEX.md")
    else:
        print(f"  ℹ️ 全局特性索引已有记录: {spec_id}")

    print("-" * 65)
    print(f"🎉 特性 [{spec_id}] 成功归档！")
    print(f"✨ 当前 `specs/` 活跃开发目录已自动清空重置，上下文干净无污染。")
    print(f"💡 准备下一个功能时，请运行: `python tools/sdd.py new <FEAT_ID> <名称>`")
    print("=" * 65)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="SDD (Spec-Driven Development) Lifecycle & Cascading Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: status
    parser_status = subparsers.add_parser("status", help="Check active feature status")
    parser_status.set_defaults(func=cmd_status)

    # Subcommand: new
    parser_new = subparsers.add_parser("new", help="Initialize new PRD feature from templates")
    parser_new.add_argument("feat_id", help="Feature identifier, e.g. FEAT-002")
    parser_new.add_argument("name", help="Feature name/title")
    parser_new.add_argument("-f", "--force", action="store_true", help="Force overwrite active specs")
    parser_new.set_defaults(func=cmd_new)

    # Subcommand: sync
    parser_sync = subparsers.add_parser("sync", help="Cascade mid-iteration change across all SDD documents")
    parser_sync.add_argument("--desc", required=True, help="Description of the change")
    parser_sync.add_argument("--impact", default="spec,plan,tasks,eval", help="Impacted documents (comma-separated)")
    parser_sync.add_argument("--author", default="Agent/Human", help="Author of change")
    parser_sync.set_defaults(func=cmd_sync)

    # Subcommand: archive
    parser_archive = subparsers.add_parser("archive", help="Archive completed iteration & reset specs")
    parser_archive.add_argument("-f", "--force", action="store_true", help="Force archive without check")
    parser_archive.set_defaults(func=cmd_archive)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

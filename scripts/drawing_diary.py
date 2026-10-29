#!/usr/bin/env python3
"""Local diary bookkeeping. No network access or publishing."""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def entries(root):
    found = [(p.parent, read(p)) for p in (root / "entries").glob("*/*/entry.json")]
    return sorted(found, key=lambda row: row[1]["number"])


def inside(folder, relative):
    candidate = (folder / relative).resolve()
    if not candidate.is_relative_to(folder.resolve()):
        raise ValueError("记录中的文件路径必须在指定目录内")
    return candidate


def lesson_file(root, entry):
    relative = Path(entry["lesson_path"])
    expected = Path("lessons") / entry["stage"] / f"{entry['number']:03d}-{entry['slug']}.md"
    if relative != expected:
        raise ValueError("教案路径应为lessons/阶段/编号-题目.md")
    return inside(root / "lessons", relative.relative_to("lessons"))


def create_next(root):
    rows = entries(root)
    pending = [(p, e) for p, e in rows if e["practice"]["status"] != "completed"]
    if pending:
        print("继续未完成作品：" + str(lesson_file(root, pending[0][1])))
        return
    project = read(root / "config/project.json")
    stage_id = project["current_stage"]
    stages = read(root / "config/stages.json")
    stage = next(s for s in stages if s["id"] == stage_id)
    tools = read(root / "config/tools" / (project["current_tools"] + ".json"))
    curriculum = read(root / "curriculum" / (stage_id + ".json"))
    used = {e["slug"] for _, e in rows if e["stage"] == stage_id}
    lesson = next((l for l in curriculum if l["slug"] not in used), None)
    if lesson is None:
        raise ValueError("当前题目已用完：先做阶段复盘，再补题；不自动升级或重复编号")
    colors = lesson["colors"]
    if set(colors) - set(tools["markers"]["colors"]):
        raise ValueError("课程色号不在当前工具中，先调整课程")
    if len(colors) > stage["lesson_limits"]["marker_colors_max"]:
        raise ValueError("色数超出当前阶段设置")
    number = max((e["number"] for _, e in rows), default=0) + 1
    lesson_relative = f"lessons/{stage_id}/{number:03d}-{lesson['slug']}.md"
    target = lesson_file(root, {"lesson_path": lesson_relative, "stage": stage_id,
                                "number": number, "slug": lesson["slug"]})
    if target.exists():
        raise ValueError("教案文件已存在，不覆盖")
    folder = root / "entries" / stage_id / f"{number:03d}-{lesson['slug']}"
    folder.mkdir(parents=True, exist_ok=False)
    for sub in ("reference", "practice", "publication"):
        (folder / sub).mkdir()
    write(folder / "tools.snapshot.json", tools)
    write(folder / "stage.snapshot.json", stage)
    write(folder / "entry.json", {
        "number": number, "slug": lesson["slug"], "title": lesson["title"], "stage": stage_id,
        "tools_profile": tools["id"], "goal": lesson["goal"], "marker_colors": colors,
        "lesson_path": lesson_relative,
        "target_minutes": project["daily_minutes"], "lesson_status": "draft", "references": [],
        "practice": {"status": "pending", "completed_on": None, "actual_minutes": None,
                     "photos": [], "liked": None, "improve": None},
        "publication": {"status": "draft", "url": None, "published_at": None, "metrics": []}
    })
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"# {number:03d} {lesson['title']}\n\n教案状态：待完善，尚无参考图和真实作品。\n\n"
        f"目标：{lesson['goal']}。计划{project['daily_minutes']}分钟。\n\n"
        f"候选色号：{' / '.join(colors)}，以实物试色为准。\n\n"
        "由每日一画skill在本页补齐：参考图、所需纸笔、造型大小、一个基础点、分步画法、"
        "色号对应区域、留白时机、一个常见问题、检查点与来源。正文完整后再标记ready并加入阶段学习目录。\n",
        encoding="utf-8")
    print("已建待完善教案：" + str(target))


def find_entry(root, name):
    matches = [(p, e) for p, e in entries(root) if p.name == name]
    if len(matches) != 1:
        raise ValueError("作品编号不存在或不唯一")
    return matches[0]


def copy_private_photo(folder, filename):
    source = Path(filename).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".heic"}:
        raise ValueError("照片应为现有的JPG、PNG、WebP或HEIC文件")
    dest = folder / "practice/private" / ("finished" + source.suffix.lower())
    if dest.exists():
        raise ValueError("同名照片已存在，不覆盖")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return {"path": dest.relative_to(folder).as_posix(), "visibility": "private", "origin": "user_practice"}


def add_photo(root, args):
    folder, entry = find_entry(root, args.entry)
    entry["practice"]["photos"].append(copy_private_photo(folder, args.photo))
    write(folder / "entry.json", entry)
    print("已补存成品照，原完成状态与用时保持不变：" + str(folder))


def record(root, args):
    matches = [(p, e) for p, e in entries(root) if p.name == args.entry]
    if len(matches) != 1:
        raise ValueError("作品编号不存在或不唯一")
    folder, entry = matches[0]
    completed_on = dt.date.fromisoformat(args.date) if args.date else None
    if completed_on is not None and completed_on > dt.date.today():
        raise ValueError("完成日期不能在未来")
    if args.minutes is not None and args.minutes <= 0:
        raise ValueError("实际用时必须为正数；未知时省略--minutes")
    practice = entry["practice"]
    if practice["status"] == "completed":
        raise ValueError("这幅已有完成记录；更正时请检查并直接编辑entry.json，避免覆盖历史")
    photos = []
    if args.photo:
        photos = [copy_private_photo(folder, args.photo)]
    practice.update(status="completed", completed_on=completed_on.isoformat() if completed_on else None,
                    actual_minutes=args.minutes, photos=practice["photos"] + photos, liked=args.liked, improve=args.improve)
    write(folder / "entry.json", entry)
    print("已记录真实练习；照片原件默认私有，未发布：" + str(folder))


def validate(root):
    project = read(root / "config/project.json")
    stages = read(root / "config/stages.json")
    assert project["current_stage"] in {s["id"] for s in stages}, "当前阶段不存在"
    current_tools = read(root / "config/tools" / (project["current_tools"] + ".json"))
    for stage in stages:
        if stage["tools_profile"]:
            assert (root / "config/tools" / (stage["tools_profile"] + ".json")).is_file(), "阶段工具不存在"
    for path in (root / "curriculum").glob("*.json"):
        stage = next(s for s in stages if s["id"] == path.stem)
        tools = read(root / "config/tools" / ((stage["tools_profile"] or current_tools["id"]) + ".json"))
        for lesson in read(path):
            assert re.fullmatch(r"[a-z0-9-]+", lesson["slug"]), "题目slug不合法"
            assert not set(lesson["colors"]) - set(tools["markers"]["colors"]), "课程色号错误"
    numbers = set()
    for folder, e in entries(root):
        assert e["number"] not in numbers, "重复编号"
        numbers.add(e["number"])
        assert folder.name == f"{e['number']:03d}-{e['slug']}", "编号与目录不一致"
        tools = read(folder / "tools.snapshot.json")
        stage = read(folder / "stage.snapshot.json")
        assert tools["id"] == e["tools_profile"], "工具快照不匹配"
        assert stage["id"] == e["stage"], "阶段快照不匹配"
        assert not set(e["marker_colors"]) - set(tools["markers"]["colors"]), "作品色号错误"
        assert len(e["marker_colors"]) <= stage["lesson_limits"]["marker_colors_max"], "色数超限"
        assert e["lesson_status"] in {"draft", "ready"}, "未知教案状态"
        assert lesson_file(root, e).is_file(), "缺教案"
        for ref in e["references"]:
            assert inside(folder, ref["path"]).is_file(), "参考文件不存在"
            assert ref["origin"] in {"ai_generated", "user_created", "external_link"}, "缺参考来源"
        p = e["practice"]
        assert p["status"] in {"pending", "completed"}, "未知练习状态"
        if p["status"] == "pending":
            assert p["completed_on"] is None and p["actual_minutes"] is None, "未完成却已有完成信息"
        elif p["completed_on"] is not None:
            assert dt.date.fromisoformat(p["completed_on"]) <= dt.date.today(), "日期在未来"
        assert p["actual_minutes"] is None or p["actual_minutes"] > 0, "无效用时"
        for photo in p["photos"]:
            assert photo["origin"] == "user_practice", "实拍来源错误"
            target = inside(folder, photo["path"])
            if photo["visibility"] == "private":
                assert target.is_relative_to((folder / "practice/private").resolve()), "私有照片位置错误"
                # Git intentionally excludes originals; public clones need not contain them.
            else:
                assert photo["visibility"] == "public" and target.is_file(), "公开实拍文件不存在"
    print(f"校验通过：{len(numbers)}幅作品；当前工具{len(current_tools['markers']['colors'])}色")


def index(root):
    lines = ["# 作品索引", "", "学习入口：[入门版练习](../lessons/beginner/README.md)。这里记录教案与实际练习进度，二者分开。", "",
             "| 编号 | 作品 | 阶段 | 教案 | 练习 | 实际用时 |", "| --- | --- | --- | --- | --- | --- |"]
    for folder, e in entries(root):
        p = e["practice"]
        label = "已完成" if p["status"] == "completed" else "待手绘"
        minutes = "未记录（可省略）" if p["actual_minutes"] is None else f"{p['actual_minutes']:g}分钟"
        link = Path(os.path.relpath(lesson_file(root, e), root / "entries")).as_posix()
        title = e["title"].replace("|", "\\|")
        stage_label = "入门版练习" if e["stage"] == "beginner" else e["stage"]
        lesson_label = "可跟画" if e["lesson_status"] == "ready" else "待完善"
        lines.append(f"| {e['number']:03d} | [{title}]({link}) | {stage_label} | {lesson_label} | {label} | {minutes} |")
    target = root / "entries/INDEX.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("status", "next", "index", "validate"):
        subs.add_parser(command)
    r = subs.add_parser("record")
    r.add_argument("entry")
    r.add_argument("--date", default=None, help="可选：真实完成日期 YYYY-MM-DD；未知留空")
    r.add_argument("--minutes", type=float, default=None)
    r.add_argument("--photo")
    r.add_argument("--liked")
    r.add_argument("--improve")
    photo_parser = subs.add_parser("add-photo", help="日后补存成品照，不改变完成记录")
    photo_parser.add_argument("entry")
    photo_parser.add_argument("--photo", required=True)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    try:
        if args.command == "status":
            for folder, e in entries(root):
                print(f"{folder.name} | 教案{e['lesson_status']} | 练习{e['practice']['status']} | 发布{e['publication']['status']}")
        elif args.command == "next":
            create_next(root)
        elif args.command == "record":
            record(root, args)
        elif args.command == "add-photo":
            add_photo(root, args)
        elif args.command == "index":
            index(root)
        else:
            validate(root)
    except (ValueError, AssertionError, KeyError, OSError, StopIteration) as exc:
        parser.exit(1, f"未完成：{exc}\n")


if __name__ == "__main__":
    main()

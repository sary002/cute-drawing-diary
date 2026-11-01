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


TEACHING_MODES = {"guided", "supported", "independent"}


def learning_context(root, style_id=None):
    catalog = read(root / "config/styles.json")
    style_id = style_id or catalog["default_style_id"]
    style = next((s for s in catalog["styles"] if s["id"] == style_id), None)
    if style is None:
        raise ValueError("风格尚未正式收录，请先预览并确认收录")
    progress = read(root / "config/learning-progress.json")
    if style_id not in progress["styles"]:
        raise ValueError("所选风格缺少独立学习进度，请先初始化")
    state = progress["styles"][style_id]
    stage = next((s for s in read(root / "config/stages.json") if s["id"] == state["current_stage"]), None)
    if stage is None:
        raise ValueError("所选风格的学习阶段不存在")
    if state["teaching_mode"] not in TEACHING_MODES:
        raise ValueError("未知教学方式")
    return style, state, stage, progress


def stage_completed(root, style_id, stage_id):
    return sum(e.get("style_id") == style_id and e["stage"] == stage_id
               and e["practice"]["status"] == "completed" for _, e in entries(root))


def review_target(state, stage):
    reviews = [r for r in state["reviews"] if r["stage"] == stage["id"]]
    return reviews[-1]["next_review_at"] if reviews else stage["review_after_completed_entries"]


def status(root, style_id=None):
    selected = [style_id] if style_id else [s["id"] for s in read(root / "config/styles.json")["styles"]]
    for selected_id in selected:
        style, state, stage, _ = learning_context(root, selected_id)
        completed = stage_completed(root, style["id"], stage["id"])
        print(f"{style['id']} {style['name']} | {stage['level']} {stage['name']} | "
              f"教学{state['teaching_mode']} | 当前阶段真实完成{completed}幅")
        if completed >= review_target(state, stage):
            print("已到复盘点：结合实际练习评估，不按张数自动晋级")
        for folder, e in entries(root):
            if e.get("style_id") == style["id"]:
                print(f"{folder.name} | 阶段{e['stage']} | 教案{e['lesson_status']} | "
                      f"练习{e['practice']['status']} | 发布{e['publication']['status']}")
    if style_id is None:
        for folder, e in entries(root):
            if not e.get("style_id"):
                print(f"{folder.name} | 历史风格未分类 | 教案{e['lesson_status']} | 练习{e['practice']['status']}")


def review(root, args):
    style, state, stage, progress = learning_context(root, args.style)
    completed = stage_completed(root, style["id"], stage["id"])
    evidence = args.evidence.strip()
    if not evidence:
        raise ValueError("复盘需提供简短的实际绘画依据")
    if not completed:
        raise ValueError("当前风格阶段尚无实际完成记录，不能据AI示意复盘晋级")
    stages = read(root / "config/stages.json")
    position = next(i for i, s in enumerate(stages) if s["id"] == stage["id"])
    if args.decision == "advance" and position == len(stages) - 1:
        raise ValueError("D4为自主创作阶段，可继续创作或巩固，无默认更高阶段")
    state["reviews"].append({"stage": stage["id"], "completed_count": completed,
                             "decision": args.decision, "evidence": evidence,
                             "next_review_at": completed + 2})
    if args.decision == "advance":
        state["current_stage"] = stages[position + 1]["id"]
    write(root / "config/learning-progress.json", progress)
    print(f"已保存{style['id']}复盘：{args.decision}；当前阶段{state['current_stage']}；未改写旧作")


def create_next(root, style_id=None, new=False, teaching_mode=None):
    style, state, stage, _ = learning_context(root, style_id)
    stage_id = stage["id"]
    rows = entries(root)
    pending = [(p, e) for p, e in rows if e.get("style_id") == style["id"]
               and e["stage"] == stage_id and e["practice"]["status"] != "completed"]
    if pending and not new:
        print("继续未完成作品：" + str(lesson_file(root, pending[0][1])))
        return
    project = read(root / "config/project.json")
    tools = read(root / "config/tools" / (project["current_tools"] + ".json"))
    curriculum_path = style["curriculum_paths"].get(stage_id)
    if not curriculum_path:
        raise ValueError("该风格当前阶段尚无题库，请按独立风格备课，不沿用其他风格题目")
    curriculum = read(inside(root, curriculum_path))
    used = {e["slug"] for _, e in rows if e["stage"] == stage_id and e.get("style_id") == style["id"]}
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
        "style_id": style["id"], "teaching_mode": teaching_mode or state["teaching_mode"],
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
        f"风格：{style['id']} {style['name']}；等级：{stage['level']}；"
        f"教学方式：{teaching_mode or state['teaching_mode']}。\n\n"
        f"目标：{lesson['goal']}。单次预算{project['daily_minutes']}分钟，整幅时间待备课估计，可分次。\n\n"
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
    assert [s["level"] for s in stages] == ["D1", "D2", "D3", "D4"], "共同阶段顺序错误"
    stage_ids = {s["id"] for s in stages}
    catalog = read(root / "config/styles.json")
    style_ids = [s["id"] for s in catalog["styles"]]
    assert len(set(style_ids)) == len(style_ids), "重复风格编号"
    assert catalog["default_style_id"] in style_ids, "默认风格不存在"
    assert project["default_style_id"] == catalog["default_style_id"], "默认风格配置不一致"
    progress = read(root / "config/learning-progress.json")
    assert set(progress["styles"]) == set(style_ids), "风格与独立进度不匹配"
    current_tools = read(root / "config/tools" / (project["current_tools"] + ".json"))
    for stage in stages:
        if stage["tools_profile"]:
            assert (root / "config/tools" / (stage["tools_profile"] + ".json")).is_file(), "阶段工具不存在"
    curriculum_owners = set()
    for style in catalog["styles"]:
        assert re.fullmatch(r"S\d{3,}", style["id"]), "风格编号不合法"
        assert inside(root, style["profile_path"]).is_file(), "缺风格档案"
        _, state, _, _ = learning_context(root, style["id"])
        for item in state["reviews"]:
            assert item["stage"] in stage_ids, "复盘阶段不存在"
            assert item["decision"] in {"advance", "practice", "stay"} and item["evidence"].strip(), "复盘缺依据"
            assert 0 < item["completed_count"] <= stage_completed(root, style["id"], item["stage"]), "复盘完成数错误"
            assert item["next_review_at"] > item["completed_count"], "复盘检查点错误"
        for stage_id, relative in style["curriculum_paths"].items():
            assert stage_id in stage_ids, "题库阶段不存在"
            path = inside(root, relative)
            assert path.is_relative_to((root / "curriculum").resolve()), "题库路径错误"
            assert path not in curriculum_owners, "不同风格或阶段不得共享同一题库文件"
            curriculum_owners.add(path)
            slugs = set()
            stage = next(s for s in stages if s["id"] == stage_id)
            for lesson in read(path):
                assert re.fullmatch(r"[a-z0-9-]+", lesson["slug"]), "题目slug不合法"
                assert lesson["slug"] not in slugs, "题库内题目重复"
                slugs.add(lesson["slug"])
                assert not set(lesson["colors"]) - set(current_tools["markers"]["colors"]), "课程色号错误"
                assert len(lesson["colors"]) <= stage["lesson_limits"]["marker_colors_max"], "课程色数超限"
    numbers = set()
    for folder, e in entries(root):
        assert e["number"] not in numbers, "重复编号"
        numbers.add(e["number"])
        assert "style_id" not in e or e["style_id"] in style_ids, "作品风格不存在"
        assert e["stage"] in stage_ids, "作品阶段不存在"
        assert e.get("teaching_mode", "guided") in TEACHING_MODES, "作品教学方式错误"
        assert folder.name == f"{e['number']:03d}-{e['slug']}", "编号与目录不一致"
        tools = read(folder / "tools.snapshot.json")
        stage = read(folder / "stage.snapshot.json")
        assert tools["id"] == e["tools_profile"], "工具快照不匹配"
        assert stage["id"] == e["stage"], "阶段快照不匹配"
        assert not set(e["marker_colors"]) - set(tools["markers"]["colors"]), "作品色号错误"
        assert len(e["marker_colors"]) <= stage["lesson_limits"]["marker_colors_max"], "色数超限"
        assert e["lesson_status"] in {"draft", "ready"}, "未知教案状态"
        if e.get("color_review", {}).get("status") == "requires_revision":
            assert e["lesson_status"] == "draft", "配色待校正的教案不得标ready"
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
    lines = ["# 作品索引", "", "学习入口：[每日一练总目录](../lessons/README.md)。这里记录教案与实际练习进度，二者分开；素材编号用于选课，内部编号保留旧链接。", "",
             "| 素材编号 | 内部编号 | 作品 | 风格 | 等级 | 教案 | 练习 | 实际用时 |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    stages = {s["id"]: s for s in read(root / "config/stages.json")}
    for folder, e in sorted(entries(root), key=lambda row: (row[1].get("style_id", ""), row[1].get("course_slot", row[1]["number"]))):
        p = e["practice"]
        label = "已完成" if p["status"] == "completed" else "待手绘"
        minutes = "未记录（可省略）" if p["actual_minutes"] is None else f"{p['actual_minutes']:g}分钟"
        link = Path(os.path.relpath(lesson_file(root, e), root / "entries")).as_posix()
        title = e["title"].replace("|", "\\|")
        stage_label = stages[e["stage"]]["level"]
        lesson_label = ("配色待校正" if e.get("color_review", {}).get("status") == "requires_revision"
                        else "可学习" if e["lesson_status"] == "ready" else "待完善")
        lines.append(f"| {e.get('material_id', '未分配')} | {e['number']:03d} | [{title}]({link}) | {e.get('style_id', '未分类')} | {stage_label} | {lesson_label} | {label} | {minutes} |")
    target = root / "entries/INDEX.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("index", "validate"):
        subs.add_parser(command)
    status_parser = subs.add_parser("status")
    status_parser.add_argument("--style")
    next_parser = subs.add_parser("next")
    next_parser.add_argument("--style")
    next_parser.add_argument("--new", action="store_true", help="明确换题，保留旧作未完成状态")
    next_parser.add_argument("--teaching-mode", choices=sorted(TEACHING_MODES), help="仅指定本次新教案的帮助程度")
    review_parser = subs.add_parser("review")
    review_parser.add_argument("--style")
    review_parser.add_argument("--decision", choices=("advance", "practice", "stay"), required=True)
    review_parser.add_argument("--evidence", required=True, help="只写实际绘画依据，不写私人信息")
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
            status(root, args.style)
        elif args.command == "next":
            create_next(root, args.style, args.new, args.teaching_mode)
        elif args.command == "review":
            review(root, args)
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

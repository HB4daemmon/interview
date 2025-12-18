# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import textwrap
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

NBFORMAT = 4
NBFORMAT_MINOR = 5


def _cell_id() -> str:
    return uuid.uuid4().hex[:8]


def _lines(text: str) -> List[str]:
    text = textwrap.dedent(text).lstrip("\n")
    if not text:
        return []
    if not text.endswith("\n"):
        text += "\n"
    return [line + "\n" for line in text.splitlines()]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "id": _cell_id(), "metadata": {}, "source": _lines(text)}


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "id": _cell_id(),
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _lines(src),
    }


def nb(cells: List[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.8"},
        },
        "nbformat": NBFORMAT,
        "nbformat_minor": NBFORMAT_MINOR,
    }


def write_nb(path: Path, notebook: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


COMMON_NOTE = "> 约定：Python 3.8；示例尽量只用标准库；代码块可直接运行（第三方依赖会做可选降级）。"

ARTIFACTS_SETUP = """\\
from pathlib import Path

ART = Path('_nb_artifacts')
ART.mkdir(exist_ok=True)
print('artifacts dir:', ART.resolve())
"""


@dataclass(frozen=True)
class Point:
    title: str
    detail_md: str
    demo: Optional[str] = None


@dataclass(frozen=True)
class Topic:
    no: str
    filename: str
    title_zh: str
    title_en: str
    overview: str
    prerequisites: List[str]
    checklist: List[str]
    points: List[Point]
    pitfalls: List[str]
    mini_case_title: str
    mini_case_md: str
    mini_case_code: str
    self_check: List[str]
    exercises: List[str]


def build(topic: Topic) -> dict:
    prereq = "\n".join([f"- {x}" for x in (topic.prerequisites or [])]) or "- 无"
    checklist = "\n".join([f"- [ ] {x}" for x in (topic.checklist or [])]) or "- [ ] 无"
    toc = "\n".join([f"- {i+1}. {p.title}" for i, p in enumerate(topic.points)])
    pitfalls = "\n".join([f"- {x}" for x in (topic.pitfalls or [])]) or "- 无"

    cells: List[dict] = [
        md(
            f"""\\
            # {topic.no}. {topic.title_zh}（{topic.title_en}）

            {topic.overview.strip()}

            {COMMON_NOTE}
            """
        ),
        md(f"## 前置知识\n\n{prereq}\n"),
        md(f"## 知识点地图\n\n{toc}\n"),
        md(f"## 自检清单（学完打勾）\n\n{checklist}\n"),
        code(ARTIFACTS_SETUP),
    ]

    for i, p in enumerate(topic.points, start=1):
        cells.append(md(f"## 知识点 {i}：{p.title}\n\n{p.detail_md.strip()}\n"))
        if p.demo:
            cells.append(code(p.demo))

    cells.append(md(f"## 常见坑\n\n{pitfalls}\n"))

    cells.append(md(f"## 综合小案例：{topic.mini_case_title}\n\n{topic.mini_case_md.strip()}\n"))
    if topic.mini_case_code.strip():
        cells.append(code(topic.mini_case_code))

    cells.append(md("## 自测题（不写代码也能回答）\n\n" + "\n".join([f"- {q}" for q in topic.self_check]) + "\n"))
    cells.append(md("## 练习题（建议写代码）\n\n" + "\n".join([f"- {q}" for q in topic.exercises]) + "\n"))

    return nb(cells)


def write_readme(notebooks_dir: Path) -> None:
    items = sorted([p.name for p in notebooks_dir.glob("*.ipynb")])
    lines = [
        "# Python 基础教学 Notebooks\n\n",
        "目录：`notebooks/`\n\n",
        "打开方式：\n",
        "- `jupyter notebook` 或 `jupyter lab`\n",
        "- 建议在项目根目录启动，然后按编号顺序打开学习\n\n",
        "说明：\n",
        "- 部分 Notebook 会在项目根目录创建 `./_nb_artifacts/` 存放示例产生的临时文件（模块/文件/日志等）\n",
        "- 部分篇章含可选依赖：`websockets`、MySQL 驱动（`mysql-connector-python` 或 `pymysql`）、`pika`、`pymongo`、`flask`、`fastapi`、`numpy`、`pandas`、`scikit-learn`、`torch`\n\n",
        "顺序：\n",
    ]
    for name in items:
        lines.append(f"- `{name}`\n")
    (notebooks_dir / "README.md").write_text("".join(lines), encoding="utf-8")


def validate_notebooks(notebooks_dir: Path) -> None:
    for p in notebooks_dir.glob("*.ipynb"):
        json.loads(p.read_text(encoding="utf-8"))

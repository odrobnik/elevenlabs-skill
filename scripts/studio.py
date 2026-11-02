#!/usr/bin/env python3
"""
ElevenLabs Studio (projects / chapters) API wrapper.

Reference: https://elevenlabs.io/docs/api-reference/studio/add-project

Usage (CLI):
    studio.py list
    studio.py get <project_id>
    studio.py create --name "Contract Law English" --content content.json [options]
    studio.py bookforge-content <book_dir> -o content.json
    studio.py update-content <project_id> --content content.json
    studio.py edit <project_id> --name ... --title ... --author ...
    studio.py convert <project_id>
    studio.py delete <project_id>
    studio.py chapters <project_id>
    studio.py chapter <project_id> <chapter_id>
    studio.py add-chapter <project_id> --name "Unit 14"
    studio.py update-chapter <project_id> <chapter_id> [--name N] [--content chapter.json]
    studio.py delete-chapter <project_id> <chapter_id>
    studio.py convert-chapter <project_id> <chapter_id>
    studio.py snapshots <project_id>
    studio.py download <project_id> -o out.zip [--snapshot ID] [--stream]

Content JSON (create / update-content) is a list of chapters:
    [{"name": "Unit 1", "blocks": [{"sub_type": "h1", "nodes": [
        {"type": "tts_node", "voice_id": "...", "text": "..."}]}]}]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io") + "/v1/studio"

QUALITY_PRESETS = ["standard", "high", "ultra", "ultra_lossless"]


def _headers() -> dict[str, str]:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError("ELEVENLABS_API_KEY not set")
    return {"xi-api-key": key}


def _request(method: str, path: str, *, stream: bool = False, **kwargs: Any) -> requests.Response:
    resp = requests.request(
        method, BASE_URL + path, headers=_headers(), timeout=kwargs.pop("timeout", 300), stream=stream, **kwargs
    )
    if resp.status_code != 200:
        detail: Any = resp.text
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        raise RuntimeError(f"ElevenLabs API error {resp.status_code}: {detail}")
    return resp


# --- Projects -----------------------------------------------------------------

def list_projects() -> list[dict]:
    return _request("GET", "/projects").json()["projects"]


def get_project(project_id: str) -> dict:
    return _request("GET", f"/projects/{project_id}").json()  # fields at top level, unlike create/edit


def create_project(
    name: str,
    content: list[dict] | None = None,
    document: Path | None = None,
    from_url: str | None = None,
    pronunciation_dictionaries: list[dict] | None = None,
    voice_settings: list[dict] | None = None,
    **fields: Any,
) -> dict:
    """POST /v1/studio/projects (multipart). `fields` are the scalar form fields
    (default_model_id, quality_preset, title, author, language, ...); None values are dropped."""
    data: list[tuple[str, str]] = [("name", name)]
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, bool):
            v = "true" if v else "false"
        if isinstance(v, (list, tuple)):
            data.extend((k, str(i)) for i in v)  # repeated fields (genres)
        else:
            data.append((k, str(v)))
    if content is not None:
        data.append(("from_content_json", json.dumps(content, ensure_ascii=False)))
    if from_url:
        data.append(("from_url", from_url))
    for loc in pronunciation_dictionaries or []:
        data.append(("pronunciation_dictionary_locators", json.dumps(loc)))
    for vs in voice_settings or []:
        data.append(("voice_settings", json.dumps(vs)))

    files = None
    if document:
        files = {"from_document": (document.name, open(document, "rb"))}
    try:
        return _request("POST", "/projects", data=data, files=files).json()["project"]
    finally:
        if files:
            files["from_document"][1].close()


def update_content(project_id: str, content: list[dict], auto_convert: bool = False) -> dict:
    data = [("from_content_json", json.dumps(content, ensure_ascii=False)),
            ("auto_convert", "true" if auto_convert else "false")]
    return _request("POST", f"/projects/{project_id}/content", data=data).json()["project"]


def edit_project(project_id: str, **body: Any) -> dict:
    body = {k: v for k, v in body.items() if v is not None}
    return _request("POST", f"/projects/{project_id}", json=body).json()["project"]


def convert_project(project_id: str) -> dict:
    return _request("POST", f"/projects/{project_id}/convert").json()


def delete_project(project_id: str) -> dict:
    return _request("DELETE", f"/projects/{project_id}").json()


def wait_for_conversion(project_id: str, poll: float = 15.0, timeout: float = 6 * 3600) -> dict:
    start = time.time()
    while True:
        p = get_project(project_id)
        if p["state"] == "default":
            return p
        if time.time() - start > timeout:
            raise TimeoutError(f"Project still '{p['state']}' after {timeout:.0f}s")
        print(f"  state={p['state']} ...", file=sys.stderr)
        time.sleep(poll)


# --- Chapters -----------------------------------------------------------------

def list_chapters(project_id: str) -> list[dict]:
    return _request("GET", f"/projects/{project_id}/chapters").json()["chapters"]


def get_chapter(project_id: str, chapter_id: str) -> dict:
    return _request("GET", f"/projects/{project_id}/chapters/{chapter_id}").json()


def add_chapter(project_id: str, name: str, from_url: str | None = None) -> dict:
    body: dict[str, Any] = {"name": name}
    if from_url:
        body["from_url"] = from_url
    return _request("POST", f"/projects/{project_id}/chapters", json=body).json()["chapter"]


def update_chapter(project_id: str, chapter_id: str, name: str | None = None, content: dict | None = None) -> dict:
    body = {k: v for k, v in {"name": name, "content": content}.items() if v is not None}
    return _request("POST", f"/projects/{project_id}/chapters/{chapter_id}", json=body).json()["chapter"]


def delete_chapter(project_id: str, chapter_id: str) -> dict:
    return _request("DELETE", f"/projects/{project_id}/chapters/{chapter_id}").json()


def convert_chapter(project_id: str, chapter_id: str) -> dict:
    return _request("POST", f"/projects/{project_id}/chapters/{chapter_id}/convert").json()


# --- Snapshots / downloads ----------------------------------------------------

def list_snapshots(project_id: str) -> list[dict]:
    return _request("GET", f"/projects/{project_id}/snapshots").json()["snapshots"]


def download_snapshot(project_id: str, snapshot_id: str, out: Path, archive: bool = True) -> None:
    """archive=True: zip of the project's audio (one file per chapter); False: streamed single audio."""
    if archive:
        resp = _request("POST", f"/projects/{project_id}/snapshots/{snapshot_id}/archive", stream=True)
    else:
        resp = _request("POST", f"/projects/{project_id}/snapshots/{snapshot_id}/stream",
                        stream=True, json={"convert_to_mpeg": False})
    with open(out, "wb") as f:
        for chunk in resp.iter_content(1 << 20):
            f.write(chunk)


# --- Bookforge books -> Studio content ----------------------------------------

def bookforge_content(book_dir: Path, units: list[int] | None = None) -> list[dict]:
    """Build Studio chapters from a bookforge book's chunk plans.

    Reads audio/takes/unit-NN/plan.json (written by `bookforge synth`, also with --dry), whose
    chunks carry the exact spoken text and voice, in order. One Studio chapter per unit
    (unit-00 is the narrated front matter); one block per paragraph, one tts_node per block with
    that chunk's voice. A unit's "Unit N. Title." line becomes h1, a part's title h2. The
    credits and bookforge's pauses between chunks are not part of the content.
    """
    takes = book_dir / "audio" / "takes"
    chapters = []
    for udir in sorted(takes.glob("unit-*")):
        if not udir.name[5:].isdigit() or udir.name == "unit-99":  # unit-99: store credits
            continue
        n = int(udir.name[5:])
        if units and n not in units:
            continue
        plan_path = udir / "plan.json"
        if not plan_path.exists():
            raise FileNotFoundError(f"{plan_path} missing: run `bookforge synth --dry` in the book first")
        chunks = sorted(json.loads(plan_path.read_text()), key=lambda c: c["index"])
        blocks = []
        for c in chunks:
            paras = [t.strip() for t in c["text"].split("\n\n") if t.strip()]
            for i, text in enumerate(paras):
                sub = "p"
                if c["role"] == "intro" and n > 0 and i == len(paras) - 1 and len(paras) > 1:
                    sub = "h1"
                elif i == 0 and c.get("chapter") and c["role"] == "body" and text.rstrip(".") == c["chapter"]:
                    sub = "h2"
                blocks.append({"sub_type": sub,
                               "nodes": [{"type": "tts_node", "voice_id": c["voice"], "text": text}]})
        chapters.append({"name": chunks[0].get("chapter") or udir.name, "blocks": blocks})
    return chapters


# --- CLI ----------------------------------------------------------------------

def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text())


def main() -> None:
    ap = argparse.ArgumentParser(description="ElevenLabs Studio projects", formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    for c in ("get", "convert", "delete", "chapters", "snapshots"):
        sub.add_parser(c).add_argument("project_id")

    p = sub.add_parser("create")
    p.add_argument("--name", required=True)
    src = p.add_mutually_exclusive_group()
    src.add_argument("--content", help="content JSON file (chapters/blocks/nodes)")
    src.add_argument("--document", help=".epub/.pdf/.txt to import")
    src.add_argument("--url", help="URL to import")
    src.add_argument("--bookforge", metavar="BOOK_DIR", help="build content from a bookforge book's takes")
    p.add_argument("--units", type=int, nargs="*", help="with --bookforge: only these units")
    p.add_argument("--title-voice", dest="default_title_voice_id")
    p.add_argument("--paragraph-voice", dest="default_paragraph_voice_id")
    p.add_argument("--model", dest="default_model_id")
    p.add_argument("--quality", dest="quality_preset", choices=QUALITY_PRESETS)
    p.add_argument("--title")
    p.add_argument("--author")
    p.add_argument("--description")
    p.add_argument("--language")
    p.add_argument("--genre", dest="genres", action="append")
    p.add_argument("--target-audience", dest="target_audience", choices=["children", "young adult", "adult", "all ages"])
    p.add_argument("--content-type", dest="content_type")
    p.add_argument("--isbn", dest="isbn_number")
    p.add_argument("--fiction", choices=["fiction", "non-fiction"])
    p.add_argument("--source-type", dest="source_type", choices=["blank", "book", "article", "genfm", "video", "screenplay"])
    p.add_argument("--volume-normalization", dest="volume_normalization", action="store_true", default=None)
    p.add_argument("--normalize", dest="apply_text_normalization", choices=["auto", "on", "apply_english", "off"])
    p.add_argument("--pronunciation-dict", action="append", metavar="ID:VERSION")
    p.add_argument("--voice-setting", action="append", metavar="JSON",
                   help='per-voice override, e.g. \'{"voice_id":"..","stability":0.5,"similarity_boost":0.75,"speed":1.0}\'')
    p.add_argument("--auto-convert", dest="auto_convert", action="store_true", default=None)
    p.add_argument("--callback-url", dest="callback_url")

    p = sub.add_parser("bookforge-content", help="write Studio content JSON from a bookforge book")
    p.add_argument("book_dir")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--units", type=int, nargs="*")

    p = sub.add_parser("update-content")
    p.add_argument("project_id")
    p.add_argument("--content", required=True)
    p.add_argument("--auto-convert", action="store_true")

    p = sub.add_parser("edit")
    p.add_argument("project_id")
    p.add_argument("--name"); p.add_argument("--title-voice"); p.add_argument("--paragraph-voice")
    p.add_argument("--title"); p.add_argument("--author"); p.add_argument("--isbn")
    p.add_argument("--volume-normalization", action="store_true", default=None)

    p = sub.add_parser("chapter")
    p.add_argument("project_id"); p.add_argument("chapter_id")
    p = sub.add_parser("add-chapter")
    p.add_argument("project_id"); p.add_argument("--name", required=True); p.add_argument("--url")
    p = sub.add_parser("update-chapter")
    p.add_argument("project_id"); p.add_argument("chapter_id")
    p.add_argument("--name"); p.add_argument("--content", help='JSON file: {"blocks": [...]}')
    for c in ("delete-chapter", "convert-chapter"):
        q = sub.add_parser(c); q.add_argument("project_id"); q.add_argument("chapter_id")

    p = sub.add_parser("download")
    p.add_argument("project_id")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--snapshot", help="snapshot id (default: newest)")
    p.add_argument("--stream", action="store_true", help="single streamed audio instead of a zip archive")

    p = sub.add_parser("wait")
    p.add_argument("project_id")

    a = ap.parse_args()
    try:
        if a.cmd == "list":
            for pr in list_projects():
                print(f"{pr['project_id']}  {pr['state']:<10} {pr['name']}")
        elif a.cmd == "get":
            _print(get_project(a.project_id))
        elif a.cmd == "create":
            content = None
            if a.content:
                content = _load_json(a.content)
            elif a.bookforge:
                content = bookforge_content(Path(a.bookforge), a.units)
            dicts = []
            for d in a.pronunciation_dict or []:
                did, ver = d.split(":", 1)
                dicts.append({"pronunciation_dictionary_id": did, "version_id": ver})
            skip = {"cmd", "name", "content", "document", "url", "bookforge", "units", "pronunciation_dict", "voice_setting"}
            fields = {k: v for k, v in vars(a).items() if k not in skip}
            _print(create_project(
                a.name, content=content, document=Path(a.document) if a.document else None, from_url=a.url,
                pronunciation_dictionaries=dicts, voice_settings=[json.loads(v) for v in a.voice_setting or []], **fields))
        elif a.cmd == "bookforge-content":
            from _pathguard import safe_output_path
            out = safe_output_path(a.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            ch = bookforge_content(Path(a.book_dir), a.units)
            out.write_text(json.dumps(ch, ensure_ascii=False, indent=1))
            chars = sum(len(n["text"]) for c in ch for b in c["blocks"] for n in b["nodes"])
            print(f"{out}: {len(ch)} chapters, {chars} characters", file=sys.stderr)
        elif a.cmd == "update-content":
            _print(update_content(a.project_id, _load_json(a.content), a.auto_convert))
        elif a.cmd == "edit":
            cur = get_project(a.project_id)
            _print(edit_project(
                a.project_id,
                name=a.name or cur["name"],
                default_title_voice_id=a.title_voice or cur["default_title_voice_id"],
                default_paragraph_voice_id=a.paragraph_voice or cur["default_paragraph_voice_id"],
                title=a.title, author=a.author, isbn_number=a.isbn, volume_normalization=a.volume_normalization))
        elif a.cmd == "convert":
            _print(convert_project(a.project_id))
        elif a.cmd == "wait":
            _print(wait_for_conversion(a.project_id))
        elif a.cmd == "delete":
            _print(delete_project(a.project_id))
        elif a.cmd == "chapters":
            for c in list_chapters(a.project_id):
                st = c.get("statistics") or {}
                print(f"{c['chapter_id']}  {c['state']:<10} {c['name']}  "
                      f"(converted {st.get('characters_converted', '?')} / unconverted {st.get('characters_unconverted', '?')} chars)")
        elif a.cmd == "chapter":
            _print(get_chapter(a.project_id, a.chapter_id))
        elif a.cmd == "add-chapter":
            _print(add_chapter(a.project_id, a.name, a.url))
        elif a.cmd == "update-chapter":
            _print(update_chapter(a.project_id, a.chapter_id, a.name, _load_json(a.content) if a.content else None))
        elif a.cmd == "delete-chapter":
            _print(delete_chapter(a.project_id, a.chapter_id))
        elif a.cmd == "convert-chapter":
            _print(convert_chapter(a.project_id, a.chapter_id))
        elif a.cmd == "snapshots":
            for s in list_snapshots(a.project_id):
                print(f"{s['project_snapshot_id']}  {s['created_at_unix']}  {s['name']}")
        elif a.cmd == "download":
            from _pathguard import safe_output_path
            out = safe_output_path(a.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            sid = a.snapshot
            if not sid:
                snaps = sorted(list_snapshots(a.project_id), key=lambda s: s["created_at_unix"])
                if not snaps:
                    raise RuntimeError("No snapshots yet: convert the project first")
                sid = snaps[-1]["project_snapshot_id"]
            download_snapshot(a.project_id, sid, out, archive=not a.stream)
            print(f"Downloaded: {out}", file=sys.stderr)
    except BrokenPipeError:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

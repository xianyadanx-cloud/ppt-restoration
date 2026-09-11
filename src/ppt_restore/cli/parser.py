import argparse


def _parser():
    p = argparse.ArgumentParser(prog="pptrestore")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    probe = sub.add_parser("render-probe")
    probe.add_argument("--output-dir", required=True)
    probe.add_argument(
        "--renderer", choices=("powerpoint", "libreoffice"), default="libreoffice"
    )
    nxt = sub.add_parser("next")
    nxt.add_argument("case_dir")
    blueprint = sub.add_parser("blueprint")
    blueprint.add_argument("case_dir")
    fonts = sub.add_parser("font-candidates")
    fonts.add_argument("text")
    fonts.add_argument("--size-pt", type=float, required=True)
    fonts.add_argument("--width-pt", type=float, required=True)
    fonts.add_argument("--weight", type=int, default=400)
    patch = sub.add_parser("revise")
    patch.add_argument("case_dir")
    patch.add_argument("patch")
    patch.add_argument("--output", required=True)
    rev = sub.add_parser("review")
    rev.add_argument("case_dir")
    rev.add_argument("--block", required=True)
    rev.add_argument("--pptx")
    rev.add_argument(
        "--renderer",
        choices=("auto", "powerpoint", "wps", "libreoffice"),
        default="auto",
    )
    rev.add_argument("--wps-pdf")
    c = sub.add_parser("canonicalize")
    c.add_argument("input")
    c.add_argument("--case-dir", required=True)
    c.add_argument("--page-index", type=int, default=0)
    c.add_argument(
        "--primary-renderer", choices=("powerpoint", "wps"), default="powerpoint"
    )
    prep = sub.add_parser("prepare")
    prep.add_argument("input")
    prep.add_argument("--case-dir", required=True)
    prep.add_argument("--page-index", type=int, default=0)
    prep.add_argument(
        "--primary-renderer", choices=("powerpoint", "wps"), default="powerpoint"
    )
    prep.add_argument("--ocr", choices=("none", "auto"), default="auto")
    i = sub.add_parser("ingest")
    i.add_argument("case_dir")
    i.add_argument("scene_proposed")
    i.add_argument(
        "--content-audit",
        "--audit",
        dest="content_audit",
        default=None,
        help="host multimodal pass-2 content audit JSON",
    )
    i.add_argument(
        "--allow-missing-audit",
        action="store_true",
        help="explicit unaudited v2 mode; records a warning and skips pass-2 audit",
    )
    b = sub.add_parser("build")
    b.add_argument("case_dir")
    b.add_argument("--output", required=True)
    b.add_argument("--blocks", nargs="*")
    b.add_argument(
        "--render-strategy",
        choices=("hybrid_editable", "strict_native"),
        default="hybrid_editable",
    )
    r = sub.add_parser("render")
    r.add_argument("pptx")
    r.add_argument(
        "--renderer",
        choices=("auto", "powerpoint", "wps", "libreoffice"),
        default="auto",
    )
    r.add_argument("--output-dir", default=None)
    r.add_argument("--wps-pdf")
    v = sub.add_parser("verify")
    v.add_argument("case_dir")
    v.add_argument("pptx")
    v.add_argument(
        "--renderer",
        choices=("auto", "powerpoint", "wps", "libreoffice"),
        default="auto",
    )
    v.add_argument("--wps-pdf")
    o = sub.add_parser("optimize")
    o.add_argument("case_dir")
    o.add_argument("--block", required=True)
    o.add_argument(
        "--renderer", choices=("auto", "powerpoint", "libreoffice"), default="auto"
    )
    o.add_argument("--max-rounds", type=int, default=5)
    o.add_argument("--max-candidates", type=int, default=32)
    bi = sub.add_parser("block-init")
    bi.add_argument("case_dir")
    bi.add_argument("blueprint")
    bs = sub.add_parser("block-status")
    bs.add_argument("case_dir")
    ba = sub.add_parser("block-approve")
    ba.add_argument("case_dir")
    ba.add_argument("block_id")
    ba.add_argument("--review-report", required=True)
    ba.add_argument("--user-confirmed", action="store_true")
    pl = sub.add_parser("pipeline")
    pl.add_argument("input")
    pl.add_argument("--output", required=True)
    pl.add_argument("--case-dir")
    pl.add_argument("--page-index", type=int, default=0)
    pl.add_argument(
        "--primary-renderer", choices=("powerpoint", "wps"), default="powerpoint"
    )
    pl.add_argument(
        "--renderer",
        choices=("auto", "powerpoint", "wps", "libreoffice"),
        default="auto",
    )
    pl.add_argument("--wps-pdf")
    pl.add_argument("--ocr", choices=("none", "auto"), default="none")
    pl.add_argument("--blocks", nargs="*")
    pl.add_argument(
        "--render-strategy",
        choices=("hybrid_editable", "strict_native"),
        default="hybrid_editable",
    )
    pl.add_argument(
        "--allow-missing-audit",
        action="store_true",
        help="explicit unaudited v2 mode for an existing v2 scene",
    )
    return p

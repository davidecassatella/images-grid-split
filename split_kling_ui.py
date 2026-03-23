#!/usr/bin/env python3
"""
Images Grid Split — interfaccia grafica (tkinter).

Avviabile direttamente:
  python split_kling_ui.py

Oppure tramite il CLI unificato:
  python split_kling.py ui
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# ── directory del bundle/progetto e home utente ────────────────────────────────
import sys as _sys

# PyInstaller (frozen) imposta sys._MEIPASS con il path delle risorse estratte.
# In tutti gli altri casi (sviluppo, bundled manuale) si usa la directory del file.
if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
    _HERE = Path(_sys._MEIPASS)
else:
    _HERE = Path(__file__).resolve().parent

# Quando l'app è bundled i path input/output di default puntano a ~/Documents
# così l'app non scrive mai dentro il bundle (che potrebbe essere read-only).
_is_bundled = getattr(_sys, "frozen", False) or "Contents/Resources" in str(_HERE)
_DEFAULT_BASE = Path.home() / "Documents" if _is_bundled else _HERE


# ── split logic (senza side-effect di stampa) ──────────────────────────────────


def _do_split_2x2(image_path: Path, output_dir: Path) -> None:
    with Image.open(image_path) as img:
        w, h = img.size
        hw, hh = w // 2, h // 2
        for label, box in [
            ("01_top_left", (0, 0, hw, hh)),
            ("02_top_right", (hw, 0, w, hh)),
            ("03_bottom_left", (0, hh, hw, h)),
            ("04_bottom_right", (hw, hh, w, h)),
        ]:
            img.crop(box).save(output_dir / f"{image_path.stem}_{label}.png")


def _do_split_3x3(image_path: Path, output_dir: Path) -> None:
    with Image.open(image_path) as img:
        w, h = img.size
        cw, ch = w // 3, h // 3
        idx = 1
        for row in range(3):
            for col in range(3):
                left = col * cw
                top = row * ch
                right = w if col == 2 else (col + 1) * cw
                bottom = h if row == 2 else (row + 1) * ch
                img.crop((left, top, right, bottom)).save(
                    output_dir / f"{image_path.stem}_shot_{idx:02d}.png"
                )
                idx += 1


# ── palette dark ───────────────────────────────────────────────────────────────
BG = "#161618"
CARD = "#1e1e20"
CARD2 = "#28282a"
FIELD = "#111113"
BORDER = "#323234"
BORDER2 = "#48484a"
GREEN = "#30d158"
GREEN_H = "#25a244"
BLUE = "#0a84ff"
BLUE_H = "#006edc"
FG = "#f5f5f7"
FG2 = "#8e8e93"
FG3 = "#48484a"
LOG_OK = "#30d158"
LOG_ERR = "#ff453a"
LOG_SUM = "#ffd60a"

_SF = "SF Pro Rounded" if sys.platform == "darwin" else "Helvetica"
_SF2 = "SF Pro Text" if sys.platform == "darwin" else "Helvetica"
_MONO = "Menlo" if sys.platform == "darwin" else "Consolas"

F_TITLE = (_SF, 20, "bold")
F_H2 = (_SF, 13, "bold")
F_SM = (_SF2, 11)
F_TINY = (_SF2, 10)
F_MONO = (_MONO, 11)

P = 22
P2 = 16
P3 = 10
P4 = 6


def _rrect(canvas, x0, y0, x1, y1, r, fill, outline, width=1, tag=""):
    """Draw a filled rounded rectangle on a Canvas."""
    d = 2 * r
    kw = dict(fill=fill, outline=fill)
    canvas.create_arc(x0, y0, x0 + d, y0 + d, start=90, extent=90, tags=tag, **kw)
    canvas.create_arc(x1 - d, y0, x1, y0 + d, start=0, extent=90, tags=tag, **kw)
    canvas.create_arc(x0, y1 - d, x0 + d, y1, start=180, extent=90, tags=tag, **kw)
    canvas.create_arc(x1 - d, y1 - d, x1, y1, start=270, extent=90, tags=tag, **kw)
    canvas.create_rectangle(x0 + r, y0, x1 - r, y1, tags=tag, **kw)
    canvas.create_rectangle(x0, y0 + r, x1, y1 - r, tags=tag, **kw)
    if outline != fill and width:
        ow = dict(style="arc", outline=outline, width=width)
        lw = dict(fill=outline, width=width)
        canvas.create_arc(x0, y0, x0 + d, y0 + d, start=90, extent=90, tags=tag, **ow)
        canvas.create_arc(x1 - d, y0, x1, y0 + d, start=0, extent=90, tags=tag, **ow)
        canvas.create_arc(x0, y1 - d, x0 + d, y1, start=180, extent=90, tags=tag, **ow)
        canvas.create_arc(x1 - d, y1 - d, x1, y1, start=270, extent=90, tags=tag, **ow)
        canvas.create_line(x0 + r, y0, x1 - r, y0, tags=tag, **lw)
        canvas.create_line(x0 + r, y1, x1 - r, y1, tags=tag, **lw)
        canvas.create_line(x0, y0 + r, x0, y1 - r, tags=tag, **lw)
        canvas.create_line(x1, y0 + r, x1, y1 - r, tags=tag, **lw)


class _RoundedBtn(tk.Canvas):
    """Full-width button with smooth Canvas-rendered rounded corners."""

    def __init__(
        self,
        parent,
        text,
        command,
        *,
        bg=GREEN,
        hover=GREEN_H,
        fg=FG,
        disabled_bg="#3a3a3c",
        height=46,
        radius=12,
        font=None,
        **kw,
    ):
        super().__init__(
            parent,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=parent["bg"],
            cursor="hand2",
            **kw,
        )
        self._text, self._command = text, command
        self._bg_n, self._bg_h, self._bg_d = bg, hover, disabled_bg
        self._fg, self._radius = fg, radius
        self._font = font or (_SF, 13, "bold")
        self._enabled = True
        self._hov = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._set_hov(True))
        self.bind("<Leave>", lambda e: self._set_hov(False))

    def configure(self, **kw):
        changed = False
        if "text" in kw:
            self._text = kw.pop("text")
            changed = True
        if "state" in kw:
            self._enabled = kw.pop("state") != "disabled"
            super().configure(cursor="hand2" if self._enabled else "arrow")
            changed = True
        if kw:
            super().configure(**kw)
        if changed:
            self.after_idle(self._draw)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        bg = (
            self._bg_d
            if not self._enabled
            else (self._bg_h if self._hov else self._bg_n)
        )
        _rrect(self, 0, 0, w, h, self._radius, bg, bg)
        c = FG2 if not self._enabled else self._fg
        self.create_text(w // 2, h // 2, text=self._text, fill=c, font=self._font)

    def _click(self, _):
        if self._enabled:
            self._command()

    def _set_hov(self, v):
        self._hov = v
        self._draw()


class _ModeCard(tk.Canvas):
    """Selectable card showing a PIL grid preview + label."""

    def __init__(self, parent, mode, var, on_change, *, preview, height=120, **kw):
        super().__init__(
            parent,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=parent["bg"],
            cursor="hand2",
            **kw,
        )
        self._mode, self._var = mode, var
        self._on_change = on_change
        self._preview = preview
        self._hov = False
        self._sub = "4 frame" if mode == "2x2" else "9 frame"
        self._r = 14
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._set_hov(True))
        self.bind("<Leave>", lambda e: self._set_hov(False))

    def refresh(self):
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        active = self._var.get() == self._mode
        if active:
            bg, border, bw = CARD2, GREEN, 2
        elif self._hov:
            bg, border, bw = CARD2, BORDER2, 1
        else:
            bg, border, bw = CARD, BORDER, 1
        _rrect(self, 0, 0, w, h, self._r, bg, border, bw)
        if self._preview:
            self.create_image(w // 2, h // 2 - 10, image=self._preview, anchor="center")
        fg_lbl = FG if active else FG2
        fg_sub = GREEN if active else FG3
        self.create_text(
            w // 2, h - 26, text=self._mode, fill=fg_lbl, font=(_SF, 14, "bold")
        )
        self.create_text(w // 2, h - 11, text=self._sub, fill=fg_sub, font=(_SF2, 10))

    def _click(self, _):
        self._var.set(self._mode)
        self._on_change(self._mode)
        self._draw()

    def _set_hov(self, v):
        self._hov = v
        self._draw()


class _SegBtn(tk.Canvas):
    """One segment of a segmented pill control."""

    def __init__(
        self,
        parent,
        label,
        value,
        var,
        on_change,
        *,
        active_bg=BLUE,
        height=34,
        radius=9,
        **kw,
    ):
        super().__init__(
            parent,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=parent["bg"],
            cursor="hand2",
            **kw,
        )
        self._label, self._value = label, value
        self._var, self._on_change = var, on_change
        self._active_bg = active_bg
        self._r = radius
        self._hov = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._set_hov(True))
        self.bind("<Leave>", lambda e: self._set_hov(False))

    def refresh(self):
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        active = self._var.get() == self._value
        if active:
            bg, border, bw, fg = self._active_bg, self._active_bg, 0, FG
        elif self._hov:
            bg, border, bw, fg = CARD2, BORDER2, 1, FG
        else:
            bg, border, bw, fg = CARD, BORDER, 1, FG2
        _rrect(self, 0, 0, w, h, self._r, bg, border, bw)
        self.create_text(w // 2, h // 2, text=self._label, fill=fg, font=F_SM)

    def _click(self, _):
        self._var.set(self._value)
        self._on_change(self._value)
        self._draw()

    def _set_hov(self, v):
        self._hov = v
        self._draw()


def _grid_preview(rows: int, cols: int, px: int = 56) -> ImageTk.PhotoImage:
    """Mini PIL grid preview for mode cards."""
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gap = max(3, px // 16)
    cell_w = (px - gap * (cols + 1)) // cols
    cell_h = (px - gap * (rows + 1)) // rows
    palette = [(48, 209, 88, 230), (10, 132, 255, 230)]
    cr = max(2, px // 22)
    for r in range(rows):
        for c in range(cols):
            x0 = gap + c * (cell_w + gap)
            y0 = gap + r * (cell_h + gap)
            d.rounded_rectangle(
                [(x0, y0), (x0 + cell_w, y0 + cell_h)],
                radius=cr,
                fill=palette[(r * cols + c) % 2],
            )
    return ImageTk.PhotoImage(img)


def _field_row(parent, label, var, browse_cmd, bg=CARD):
    """Labeled entry row with browse button. Returns (frame, entry)."""
    row = tk.Frame(parent, bg=bg)
    tk.Label(row, text=label, font=F_TINY, fg=FG2, bg=bg, width=7, anchor="w").pack(
        side="left", padx=(0, P4)
    )
    ent = tk.Entry(
        row,
        textvariable=var,
        font=F_SM,
        bg=FIELD,
        fg=FG,
        insertbackground=FG,
        relief="flat",
        bd=6,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=BLUE,
    )
    ent.pack(side="left", fill="x", expand=True, padx=(0, P4))
    tk.Button(
        row,
        text="…",
        command=browse_cmd,
        font=(_SF2, 12),
        bg=CARD2,
        fg=FG2,
        activebackground=BORDER2,
        activeforeground=FG,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=10,
        pady=3,
    ).pack(side="left")
    return row, ent


def _section_lbl(parent, text, bg=BG):
    return tk.Label(
        parent, text=text.upper(), font=(_SF2, 10), fg=FG3, bg=bg, anchor="w"
    )


def _hsep(parent, bg=BG):
    return tk.Frame(parent, height=1, bg=BORDER)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Images Grid Split")
        self.resizable(False, False)
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "g.Horizontal.TProgressbar",
            troughcolor=CARD,
            background=GREEN,
            bordercolor=CARD,
            lightcolor=GREEN,
            darkcolor=GREEN,
        )

        self.mode_var = tk.StringVar(value="2x2")
        self.source_var = tk.StringVar(value="folder")
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self._processing = False

        self._load_icon()
        self._build()
        self._on_mode_change()
        self._on_source_change()

    # ── icona ──────────────────────────────────────────────────────────────────

    def _load_icon(self) -> None:
        path = _HERE / "assets" / "icon.png"
        self._icon_hdr = self._icon_win = None
        if not path.exists():
            return
        try:
            self._icon_hdr = ImageTk.PhotoImage(
                Image.open(path).resize((56, 56), Image.LANCZOS)
            )
            large = ImageTk.PhotoImage(
                Image.open(path).resize((256, 256), Image.LANCZOS)
            )
            self._icon_win = large
            self.iconphoto(True, large)
        except Exception:
            pass

    # ── UI construction ────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = tk.Frame(self, bg=BG, padx=P, pady=P)
        root.pack(fill="both", expand=True)

        # HEADER
        hdr = tk.Frame(root, bg=BG)
        hdr.pack(fill="x", pady=(0, P3))
        if self._icon_hdr:
            tk.Label(hdr, image=self._icon_hdr, bg=BG).pack(side="left", padx=(0, P2))
        tb = tk.Frame(hdr, bg=BG)
        tb.pack(side="left", fill="y", pady=2)
        tk.Label(tb, text="Images Grid Split", font=F_TITLE, fg=FG, bg=BG).pack(
            anchor="w"
        )
        tk.Label(
            tb,
            text="Dividi griglie 2×2 o 3×3 in frame separati",
            font=F_SM,
            fg=FG2,
            bg=BG,
        ).pack(anchor="w", pady=(2, 0))

        _hsep(root).pack(fill="x", pady=(0, P2 + 2))

        # MODALITÀ
        _section_lbl(root, "Modalità").pack(anchor="w", pady=(0, P4))
        mode_row = tk.Frame(root, bg=BG)
        mode_row.pack(fill="x", pady=(0, P2))
        self._mode_cards: dict[str, _ModeCard] = {}
        for m in ("2x2", "3x3"):
            preview = _grid_preview(int(m[0]), int(m[2]))
            card = _ModeCard(
                mode_row,
                m,
                self.mode_var,
                self._set_mode,
                preview=preview,
                height=118,
                width=1,
            )
            card.pack(
                side="left", fill="x", expand=True, padx=(0, P3) if m == "2x2" else 0
            )
            self._mode_cards[m] = card

        # SORGENTE
        _section_lbl(root, "Sorgente").pack(anchor="w", pady=(0, P4))
        seg_row = tk.Frame(root, bg=BG)
        seg_row.pack(fill="x", pady=(0, P2))
        self._seg_btns: dict[str, _SegBtn] = {}
        for val, lbl in (
            ("folder", "📁  Cartella intera"),
            ("file", "🖼  File singolo"),
        ):
            sb = _SegBtn(
                seg_row,
                lbl,
                val,
                self.source_var,
                self._set_source,
                active_bg=BLUE,
                height=36,
            )
            sb.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, P4) if val == "folder" else 0,
            )
            self._seg_btns[val] = sb

        # PERCORSI
        _section_lbl(root, "Percorsi").pack(anchor="w", pady=(0, P4))
        paths_border = tk.Frame(root, bg=BORDER, padx=1, pady=1)
        paths_border.pack(fill="x", pady=(0, P2))
        paths_inner = tk.Frame(paths_border, bg=CARD, padx=P2, pady=P2)
        paths_inner.pack(fill="both")

        # Variable area: shows input_row OR file_row
        self._var_area = tk.Frame(paths_inner, bg=CARD)
        self._var_area.pack(fill="x")
        self._input_row, self._input_entry = _field_row(
            self._var_area, "Input", self.input_var, self._browse_input
        )
        self._file_row, self._file_entry = _field_row(
            self._var_area, "File", self.file_var, self._browse_file
        )

        tk.Frame(paths_inner, bg=BORDER, height=1).pack(fill="x", pady=P4)
        out_row, _ = _field_row(
            paths_inner, "Output", self.output_var, self._browse_output
        )
        out_row.pack(fill="x")

        # CTA
        self._process_btn = _RoundedBtn(
            root,
            "▶   Elabora",
            self._on_process,
            bg=GREEN,
            hover=GREEN_H,
            height=46,
        )
        self._process_btn.pack(fill="x", pady=(P3, P4))

        # PROGRESS
        prog_wrap = tk.Frame(root, bg=BG)
        prog_wrap.pack(fill="x", pady=(0, P2))
        prog_wrap.columnconfigure(0, weight=1)
        self._progress = ttk.Progressbar(
            prog_wrap, style="g.Horizontal.TProgressbar", mode="determinate"
        )
        self._progress.grid(row=0, column=0, sticky="ew")
        self._progress_lbl = tk.Label(
            prog_wrap, text="", font=F_TINY, fg=FG2, bg=BG, width=16, anchor="e"
        )
        self._progress_lbl.grid(row=0, column=1, sticky="e", padx=(P4, 0))

        _hsep(root).pack(fill="x", pady=(0, P4))

        # LOG
        log_hdr = tk.Frame(root, bg=BG)
        log_hdr.pack(fill="x", pady=(0, P4))
        tk.Label(log_hdr, text="Attività", font=F_H2, fg=FG, bg=BG).pack(side="left")
        for txt, cmd in (
            ("📂  Output", self._open_output),
            ("Pulisci", self._clear_log),
        ):
            tk.Button(
                log_hdr,
                text=txt,
                command=cmd,
                font=F_TINY,
                bg=CARD2,
                fg=FG2,
                activebackground=BORDER2,
                activeforeground=FG,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=10,
                pady=4,
            ).pack(side="right", padx=(P4, 0))

        log_card_border = tk.Frame(root, bg=BORDER, padx=1, pady=1)
        log_card_border.pack(fill="x", pady=(0, 4))
        log_card = tk.Frame(log_card_border, bg=FIELD)
        log_card.pack(fill="both")
        sb = tk.Scrollbar(log_card, bg=CARD, troughcolor=FIELD, activebackground=CARD2)
        sb.pack(side="right", fill="y")
        self._log_text = tk.Text(
            log_card,
            height=9,
            width=1,
            state="disabled",
            font=F_MONO,
            bg=FIELD,
            fg=FG,
            insertbackground=FG,
            yscrollcommand=sb.set,
            relief="flat",
            borderwidth=10,
            wrap="none",
            selectbackground=BLUE,
        )
        self._log_text.pack(side="left", fill="both", expand=True)
        sb.config(command=self._log_text.yview)

        self._log_text.tag_config("ok", foreground=LOG_OK)
        self._log_text.tag_config("err", foreground=LOG_ERR)
        self._log_text.tag_config("sum", foreground=LOG_SUM)
        self._log_text.tag_config("dim", foreground=FG2)

    # ── state callbacks ────────────────────────────────────────────────────────

    def _set_mode(self, mode: str) -> None:
        self.mode_var.set(mode)
        self._on_mode_change()
        self._refresh_mode_btns()

    def _set_source(self, src: str) -> None:
        self.source_var.set(src)
        self._on_source_change()
        self._refresh_src_btns()

    def _refresh_mode_btns(self) -> None:
        for card in self._mode_cards.values():
            card.refresh()

    def _refresh_src_btns(self) -> None:
        for sb in self._seg_btns.values():
            sb.refresh()

    def _on_mode_change(self) -> None:
        m = self.mode_var.get()
        self.input_var.set(str(_DEFAULT_BASE / f"input_grids_{m}"))
        self.output_var.set(str(_DEFAULT_BASE / f"output_frames_{m}"))

    def _on_source_change(self) -> None:
        is_file = self.source_var.get() == "file"
        self._input_row.pack_forget()
        self._file_row.pack_forget()
        if is_file:
            self._file_row.pack(fill="x")
        else:
            self._input_row.pack(fill="x")

    # ── browse callbacks ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_initialdir(raw: str) -> str:
        """Restituisce la prima cartella esistente risalendo dal percorso dato."""
        p = Path(raw).expanduser().resolve() if raw.strip() else Path.cwd()
        # se è un file, usa il suo genitore
        if p.is_file():
            p = p.parent
        # risali finché troviamo una dir esistente
        for candidate in [p, *p.parents]:
            if candidate.is_dir():
                return str(candidate)
        return str(Path.cwd())

    def _browse_input(self) -> None:
        path = filedialog.askdirectory(
            title="Scegli cartella di input",
            initialdir=self._resolve_initialdir(self.input_var.get()),
        )
        if path:
            self.input_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(
            title="Scegli cartella di output",
            initialdir=self._resolve_initialdir(self.output_var.get()),
        )
        if path:
            self.output_var.set(path)

    def _browse_file(self) -> None:
        initial = self.file_var.get() or self.input_var.get()
        path = filedialog.askopenfilename(
            title="Scegli un'immagine",
            initialdir=self._resolve_initialdir(initial),
            filetypes=[
                ("Immagini", "*.png *.jpg *.jpeg *.webp"),
                ("Tutti i file", "*.*"),
            ],
        )
        if path:
            self.file_var.set(path)
            m = self.mode_var.get()
            self.output_var.set(str(Path(path).parent / f"output_frames_{m}"))

    # ── processing ─────────────────────────────────────────────────────────────

    def _on_process(self) -> None:
        if self._processing:
            return
        self._validate_and_run()

    def _validate_and_run(self) -> None:
        mode = self.mode_var.get()
        output_dir = Path(self.output_var.get().strip())
        is_file_mode = self.source_var.get() == "file"

        if is_file_mode:
            single = Path(self.file_var.get().strip())
            if not single.is_file():
                messagebox.showerror("Errore", f"File non trovato:\n{single}")
                return
            files = [single]
        else:
            input_dir = Path(self.input_var.get().strip())
            if not input_dir.is_dir():
                messagebox.showerror("Errore", f"Cartella non trovata:\n{input_dir}")
                return
            files = sorted(
                p
                for p in input_dir.iterdir()
                if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
            )
            if not files:
                messagebox.showwarning(
                    "Avviso", f"Nessuna immagine trovata in:\n{input_dir}"
                )
                return

        try:
            from PIL import Image as _  # noqa: F401 — verify Pillow available
        except ImportError as exc:
            messagebox.showerror("Import error", f"Pillow non trovato:\n{exc}")
            return

        split_fn = _do_split_2x2 if mode == "2x2" else _do_split_3x3
        frames_each = 4 if mode == "2x2" else 9

        self._processing = True
        self._process_btn.configure(state="disabled", text="Elaborazione…")
        self._progress.configure(value=0, maximum=len(files))
        self._progress_lbl.configure(text="")
        self._clear_log()

        def worker() -> None:
            output_dir.mkdir(parents=True, exist_ok=True)
            n_ok = n_err = 0
            for i, f in enumerate(files, 1):
                try:
                    split_fn(f, output_dir)
                    n_ok += 1
                    self._log_tagged(f"✓  {f.name}  →  {frames_each} frame\n", "ok")
                except Exception as exc:
                    n_err += 1
                    self._log_tagged(f"✗  {f.name}: {exc}\n", "err")
                self.after(0, lambda v=i: self._set_progress(v, len(files)))
            self.after(
                0,
                lambda: self._done(n_ok, n_err, n_ok * frames_each, output_dir),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _set_progress(self, done: int, total: int) -> None:
        self._progress.configure(value=done)
        pct = int(done / total * 100) if total else 0
        self._progress_lbl.configure(text=f"{done} / {total}  ({pct} %)")

    def _done(self, n_ok: int, n_err: int, n_frames: int, output_dir: Path) -> None:
        self._processing = False
        self._process_btn.configure(state="normal", text="▶   Elabora")
        summary = (
            f"\n── Completato: {n_ok} immagini · {n_frames} frame · {n_err} errori ──\n"
        )
        self._log_tagged(summary, "sum")
        if n_err == 0:
            messagebox.showinfo(
                "Fatto!",
                f"Elaborate: {n_ok} immagini\n"
                f"Frame generati: {n_frames}\n\n"
                f"Output: {output_dir.resolve()}",
            )
        else:
            messagebox.showwarning(
                "Completato con errori",
                f"Elaborate: {n_ok}  |  Errori: {n_err}\n"
                f"Frame generati: {n_frames}\n\n"
                f"Output: {output_dir.resolve()}",
            )

    # ── log helpers ────────────────────────────────────────────────────────────

    def _log_tagged(self, msg: str, tag: str = "") -> None:
        """Thread-safe: schedule log append from any thread."""
        self.after(0, lambda m=msg, t=tag: self._append_log(m, t))

    def _append_log(self, msg: str, tag: str = "") -> None:
        self._log_text.configure(state="normal")
        if tag:
            self._log_text.insert(tk.END, msg, tag)
        else:
            self._log_text.insert(tk.END, msg)
        self._log_text.see(tk.END)
        self._log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", tk.END)
        self._log_text.configure(state="disabled")

    # ── utilities ──────────────────────────────────────────────────────────────

    def _open_output(self) -> None:
        out = Path(self.output_var.get().strip()).resolve()
        if not out.exists():
            messagebox.showwarning("Avviso", f"Cartella non trovata:\n{out}")
            return
        if sys.platform == "darwin":
            subprocess.run(["open", str(out)], check=False)
        elif sys.platform == "win32":
            os.startfile(str(out))
        else:
            subprocess.run(["xdg-open", str(out)], check=False)


# ── entry points ───────────────────────────────────────────────────────────────


def launch() -> None:
    """Chiamato da split_kling.py quando si usa il sottocomando 'ui'."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    launch()

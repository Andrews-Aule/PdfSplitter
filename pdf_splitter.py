#!/usr/bin/env python3
"""PDF Splitter — split a PDF into parts of a chosen maximum size."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, GLib, Gio, Gdk

import os
import base64
import subprocess
import threading
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "input_label":       "Input PDF file",
        "output_label":      "Destination folder",
        "size_label":        "Maximum size per file",
        "browse":            "Browse…",
        "placeholder_pdf":   "No file selected…",
        "placeholder_out":   "Same folder as PDF…",
        "cancel":            "Cancel",
        "split":             "Split PDF",
        "waiting":           "Waiting…",
        "starting":          "Starting…",
        "page_of":           "Page {current} of {total}",
        "done":              "Done!",
        "cancelled":         "Cancelled",
        "cancelling":        "Cancelling…",
        "created_files":     "Created {n} file(s) in the destination folder.",
        "cancelled_msg":     "Operation cancelled.",
        "error_title":       "Error",
        "err_no_file":       "Please select a PDF file first.",
        "err_file_missing":  "The selected PDF file does not exist.",
        "err_no_dir":        "The destination folder does not exist.",
        "err_no_pages":      "Cannot read page count from the PDF.",
        "select_pdf_title":  "Select PDF",
        "select_pdf_filter": "PDF files",
        "select_dir_title":  "Select destination folder",
    },
    "it": {
        "input_label":       "File PDF di input",
        "output_label":      "Cartella di destinazione",
        "size_label":        "Dimensione massima per file",
        "browse":            "Sfoglia…",
        "placeholder_pdf":   "Nessun file selezionato…",
        "placeholder_out":   "Stessa cartella del PDF…",
        "cancel":            "Annulla",
        "split":             "Dividi PDF",
        "waiting":           "In attesa…",
        "starting":          "Avvio…",
        "page_of":           "Pagina {current} di {total}",
        "done":              "Completato!",
        "cancelled":         "Annullato",
        "cancelling":        "Annullamento in corso…",
        "created_files":     "Creati {n} file nella cartella di destinazione.",
        "cancelled_msg":     "Operazione annullata.",
        "error_title":       "Errore",
        "err_no_file":       "Seleziona prima un file PDF.",
        "err_file_missing":  "Il file PDF selezionato non esiste.",
        "err_no_dir":        "La cartella di destinazione non esiste.",
        "err_no_pages":      "Impossibile leggere il numero di pagine.",
        "select_pdf_title":  "Seleziona PDF",
        "select_pdf_filter": "File PDF",
        "select_dir_title":  "Seleziona cartella di destinazione",
    },
}

LANG_LABELS = {"en": "English", "it": "Italiano"}
LANG_KEYS   = list(LANG_LABELS.keys())   # ["en", "it"]


# ---------------------------------------------------------------------------
# Icon — embedded as base64 so the standalone binary carries it with itself
# ---------------------------------------------------------------------------

_ICON_B64 = (
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjgg"
    "MTI4IiB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCI+CiAgPCEtLSBMZWZ0IG91dHB1dCBkb2N1bWVu"
    "dCAtLT4KICA8cmVjdCB4PSI2IiB5PSIzOCIgd2lkdGg9IjQyIiBoZWlnaHQ9IjU0IiByeD0iNSIg"
    "cnk9IjUiIGZpbGw9IiM1YjliZDUiIC8+CiAgPHJlY3QgeD0iNiIgeT0iMzgiIHdpZHRoPSI0MiIg"
    "aGVpZ2h0PSI1NCIgcng9IjUiIHJ5PSI1IiBmaWxsPSJub25lIiBzdHJva2U9IiMzYTdhYmYiIHN0"
    "cm9rZS13aWR0aD0iMiIvPgogIDxwb2x5Z29uIHBvaW50cz0iMzMsMzggNDgsMzggNDgsNTMiIGZp"
    "bGw9IiMzYTdhYmYiLz4KICA8bGluZSB4MT0iMTMiIHkxPSI2MCIgeDI9IjQxIiB5Mj0iNjAiIHN0"
    "cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CiAg"
    "PGxpbmUgeDE9IjEzIiB5MT0iNzAiIHgyPSI0MSIgeTI9IjcwIiBzdHJva2U9IndoaXRlIiBzdHJv"
    "a2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgogIDxsaW5lIHgxPSIxMyIgeTE9"
    "IjgwIiB4Mj0iMzAiIHkyPSI4MCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJv"
    "a2UtbGluZWNhcD0icm91bmQiLz4KCiAgPCEtLSBSaWdodCBvdXRwdXQgZG9jdW1lbnQgLS0+CiAg"
    "PHJlY3QgeD0iODAiIHk9IjM4IiB3aWR0aD0iNDIiIGhlaWdodD0iNTQiIHJ4PSI1IiByeT0iNSIg"
    "ZmlsbD0iIzViOWJkNSIgLz4KICA8cmVjdCB4PSI4MCIgeT0iMzgiIHdpZHRoPSI0MiIgaGVpZ2h0"
    "PSI1NCIgcng9IjUiIHJ5PSI1IiBmaWxsPSJub25lIiBzdHJva2U9IiMzYTdhYmYiIHN0cm9rZS13"
    "aWR0aD0iMiIvPgogIDxwb2x5Z29uIHBvaW50cz0iMTA3LDM4IDEyMiwzOCAxMjIsNTMiIGZpbGw9"
    "IiMzYTdhYmYiLz4KICA8bGluZSB4MT0iODciIHkxPSI2MCIgeDI9IjExNSIgeTI9IjYwIiBzdHJv"
    "a2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgogIDxs"
    "aW5lIHgxPSI4NyIgeTE9IjcwIiB4Mj0iMTE1IiB5Mj0iNzAiIHN0cm9rZT0id2hpdGUiIHN0cm9r"
    "ZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CiAgPGxpbmUgeDE9Ijg3IiB5MT0i"
    "ODAiIHgyPSIxMDQiIHkyPSI4MCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJv"
    "a2UtbGluZWNhcD0icm91bmQiLz4KCiAgPCEtLSBDZW50ZXIgUERGIHNvdXJjZSBkb2N1bWVudCAt"
    "LT4KICA8cmVjdCB4PSIzMCIgeT0iMTQiIHdpZHRoPSI2OCIgaGVpZ2h0PSI4NiIgcng9IjYiIHJ5"
    "PSI2IiBmaWxsPSIjZThmMGZiIiAvPgogIDxyZWN0IHg9IjMwIiB5PSIxNCIgd2lkdGg9IjY4IiBo"
    "ZWlnaHQ9Ijg2IiByeD0iNiIgcnk9IjYiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzNhN2FiZiIgc3Ry"
    "b2tlLXdpZHRoPSIyLjUiLz4KICA8cG9seWdvbiBwb2ludHM9Ijc3LDE0IDk4LDE0IDk4LDM1IiBm"
    "aWxsPSIjYzBkNGYwIi8+CiAgPGxpbmUgeDE9Ijc3IiB5MT0iMTQiIHgyPSI3NyIgeTI9IjM1IiAg"
    "c3Ryb2tlPSIjM2E3YWJmIiBzdHJva2Utd2lkdGg9IjEuNSIvPgogIDxsaW5lIHgxPSI3NyIgeTE9"
    "IjM1IiB4Mj0iOTgiIHkyPSIzNSIgc3Ryb2tlPSIjM2E3YWJmIiBzdHJva2Utd2lkdGg9IjEuNSIv"
    "PgoKICA8IS0tIFBERiBsYWJlbCAtLT4KICA8cmVjdCB4PSIzNiIgeT0iNDIiIHdpZHRoPSI0MCIg"
    "aGVpZ2h0PSIxOCIgcng9IjMiIGZpbGw9IiNlMDVjNWMiLz4KICA8dGV4dCB4PSI1NiIgeT0iNTUi"
    "IGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iYm9sZCIgZm9udC1zaXplPSIx"
    "MSIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPlBERjwvdGV4dD4KCiAgPCEtLSBM"
    "aW5lcyBvbiBzb3VyY2UgZG9jIC0tPgogIDxsaW5lIHgxPSIzOCIgeTE9IjcyIiB4Mj0iOTAiIHky"
    "PSI3MiIgc3Ryb2tlPSIjYWFjM2U4IiBzdHJva2Utd2lkdGg9IjIuNSIgc3Ryb2tlLWxpbmVjYXA9"
    "InJvdW5kIi8+CiAgPGxpbmUgeDE9IjM4IiB5MT0iODEiIHgyPSI5MCIgeTI9IjgxIiBzdHJva2U9"
    "IiNhYWMzZTgiIHN0cm9rZS13aWR0aD0iMi41IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KICA8"
    "bGluZSB4MT0iMzgiIHkxPSI5MCIgeDI9IjcwIiB5Mj0iOTAiIHN0cm9rZT0iI2FhYzNlOCIgc3Ry"
    "b2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgoKICA8IS0tIFNwbGl0IGFy"
    "cm93cyAtLT4KICA8bGluZSB4MT0iMjkiIHkxPSIxMTAiIHgyPSIxNiIgeTI9Ijk1IiBzdHJva2U9"
    "IiNlMDVjNWMiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CiAgPHBv"
    "bHlnb24gcG9pbnRzPSIxNiw5NSAxMCwxMDAgMjIsMTAzIiBmaWxsPSIjZTA1YzVjIi8+CgogIDxs"
    "aW5lIHgxPSI5OSIgeTE9IjExMCIgeDI9IjExMiIgeTI9Ijk1IiBzdHJva2U9IiNlMDVjNWMiIHN0"
    "cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CiAgPHBvbHlnb24gcG9pbnRz"
    "PSIxMTIsOTUgMTE4LDEwMCAxMDYsMTAzIiBmaWxsPSIjZTA1YzVjIi8+Cjwvc3ZnPgo="
)

_ICON_NAME = "pdf-splitter"


def _bundle_path(relative: str) -> Path:
    """Return the path to a file bundled inside the PyInstaller binary, or the
    source-tree path when running as a plain script."""
    import sys
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative


def _install_icon() -> None:
    svg_dir = Path.home() / ".local/share/icons/hicolor/scalable/apps"
    svg_dir.mkdir(parents=True, exist_ok=True)
    svg_path = svg_dir / f"{_ICON_NAME}.svg"
    if not svg_path.exists():
        svg_path.write_bytes(base64.b64decode(_ICON_B64))

    # Install PNG sizes bundled with the binary
    for size in (16, 32, 48, 64, 128, 256, 512):
        src = _bundle_path(f"icons/pdf-splitter-{size}.png")
        if src.exists():
            dst_dir = Path.home() / f".local/share/icons/hicolor/{size}x{size}/apps"
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f"{_ICON_NAME}.png"
            if not dst.exists():
                import shutil
                shutil.copy2(src, dst)

    # Refresh icon cache
    subprocess.run(
        ["gtk-update-icon-cache", "-f", "-t",
         str(Path.home() / ".local/share/icons/hicolor")],
        capture_output=True,
    )

    display = Gdk.Display.get_default()
    if display:
        theme = Gtk.IconTheme.get_for_display(display)
        search_path = str(Path.home() / ".local/share/icons")
        if search_path not in theme.get_search_path():
            theme.add_search_path(search_path)


# ---------------------------------------------------------------------------
# PDF helpers (ghostscript)
# ---------------------------------------------------------------------------

def gs_page_count(pdf_path: str) -> int:
    result = subprocess.run(
        ["gs", "-q", "-dNODISPLAY", "-dNOSAFER",
         "-c", f"({pdf_path}) (r) file runpdfbegin pdfpagecount = quit"],
        capture_output=True, text=True,
    )
    return int(result.stdout.strip())


def gs_extract_pages(pdf_path: str, first: int, last: int, out_path: str) -> None:
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dNOSAFER",
         "-sDEVICE=pdfwrite",
         f"-dFirstPage={first}", f"-dLastPage={last}",
         f"-sOutputFile={out_path}", pdf_path],
        capture_output=True,
    )


def split_pdf(pdf_path, out_dir, max_bytes, progress_cb, cancelled_flag, lang="en"):
    total = gs_page_count(pdf_path)
    if total == 0:
        raise ValueError(STRINGS[lang]["err_no_pages"])

    stem = Path(pdf_path).stem
    outputs, part, start = [], 1, 1

    with tempfile.TemporaryDirectory() as tmp:
        while start <= total:
            if cancelled_flag.is_set():
                return outputs

            lo, hi, best_end = start, total, start
            while lo <= hi:
                mid = (lo + hi) // 2
                probe = os.path.join(tmp, "probe.pdf")
                gs_extract_pages(pdf_path, start, mid, probe)
                size = os.path.getsize(probe)
                if size <= max_bytes:
                    best_end = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
                if mid == start and size > max_bytes:
                    best_end = start
                    break

            out_path = os.path.join(out_dir, f"{stem}_part{part:03d}.pdf")
            gs_extract_pages(pdf_path, start, best_end, out_path)
            outputs.append(out_path)
            progress_cb(best_end, total)
            start = best_end + 1
            part += 1

    return outputs


# ---------------------------------------------------------------------------
# GTK4 Application
# ---------------------------------------------------------------------------

class PdfSplitterApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="com.example.pdf-splitter",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        _install_icon()
        win = MainWindow(application=self)
        win.present()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(title="PDF Splitter", **kwargs)
        self.set_default_size(520, 460)
        self.set_resizable(False)
        self.set_icon_name(_ICON_NAME)

        self._lang = "en"
        self._pdf_path = None
        self._out_dir = None
        self._cancel_flag = threading.Event()

        self._build_ui()
        self._apply_lang()

    # ------------------------------------------------------------------
    def _t(self, key: str) -> str:
        return STRINGS[self._lang][key]

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        # Header bar
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="PDF Splitter"))

        # Language selector in header bar
        self._lang_combo = Gtk.DropDown.new_from_strings(
            [LANG_LABELS[k] for k in LANG_KEYS]
        )
        self._lang_combo.set_selected(LANG_KEYS.index(self._lang))
        self._lang_combo.connect("notify::selected", self._on_lang_changed)
        header.pack_end(self._lang_combo)
        self.set_titlebar(header)

        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=24, margin_bottom=24,
            margin_start=28, margin_end=28,
        )
        root.append(content)

        # --- Input file ---
        self._lbl_input = self._section_label("")
        content.append(self._lbl_input)
        row_in = Gtk.Box(spacing=8)
        self._entry_pdf = Gtk.Entry(hexpand=True, editable=False)
        self._btn_browse_pdf = Gtk.Button()
        self._btn_browse_pdf.connect("clicked", self._on_choose_pdf)
        row_in.append(self._entry_pdf)
        row_in.append(self._btn_browse_pdf)
        content.append(row_in)

        # --- Output directory ---
        self._lbl_output = self._section_label("")
        content.append(self._lbl_output)
        row_out = Gtk.Box(spacing=8)
        self._entry_out = Gtk.Entry(hexpand=True, editable=False)
        self._btn_browse_out = Gtk.Button()
        self._btn_browse_out.connect("clicked", self._on_choose_out)
        row_out.append(self._entry_out)
        row_out.append(self._btn_browse_out)
        content.append(row_out)

        # --- Size limit ---
        self._lbl_size = self._section_label("")
        content.append(self._lbl_size)
        row_size = Gtk.Box(spacing=8)
        self._spin = Gtk.SpinButton()
        self._spin.set_adjustment(
            Gtk.Adjustment(value=5, lower=0.1, upper=9999,
                           step_increment=0.5, page_increment=5, page_size=0))
        self._spin.set_digits(1)
        self._spin.set_hexpand(True)
        self._unit_combo = Gtk.DropDown.new_from_strings(["MB", "KB"])
        self._unit_combo.set_selected(0)
        row_size.append(self._spin)
        row_size.append(self._unit_combo)
        content.append(row_size)

        # --- Progress ---
        self._progress = Gtk.ProgressBar(show_text=True)
        content.append(self._progress)

        # --- Status ---
        self._status = Gtk.Label(label="", wrap=True, max_width_chars=55, xalign=0)
        self._status.add_css_class("dim-label")
        content.append(self._status)

        # --- Buttons ---
        btn_row = Gtk.Box(spacing=12, halign=Gtk.Align.END)
        self._btn_cancel = Gtk.Button()
        self._btn_cancel.set_sensitive(False)
        self._btn_cancel.connect("clicked", self._on_cancel)
        self._btn_split = Gtk.Button()
        self._btn_split.add_css_class("suggested-action")
        self._btn_split.connect("clicked", self._on_split)
        btn_row.append(self._btn_cancel)
        btn_row.append(self._btn_split)
        content.append(btn_row)

    # ------------------------------------------------------------------
    def _section_label(self, text: str) -> Gtk.Label:
        lbl = Gtk.Label(use_markup=True, xalign=0)
        lbl.set_label(f"<b>{text}</b>")
        return lbl

    def _apply_lang(self):
        t = self._t
        self._lbl_input.set_label(f"<b>{t('input_label')}</b>")
        self._lbl_output.set_label(f"<b>{t('output_label')}</b>")
        self._lbl_size.set_label(f"<b>{t('size_label')}</b>")
        self._entry_pdf.set_placeholder_text(t("placeholder_pdf"))
        self._entry_out.set_placeholder_text(t("placeholder_out"))
        self._btn_browse_pdf.set_label(t("browse"))
        self._btn_browse_out.set_label(t("browse"))
        self._btn_cancel.set_label(t("cancel"))
        self._btn_split.set_label(t("split"))
        # Keep progress text in sync if idle
        if not self._cancel_flag.is_set() and not self._btn_split.get_sensitive() is False:
            self._progress.set_text(t("waiting"))

    # ------------------------------------------------------------------
    def _on_lang_changed(self, combo, _param):
        self._lang = LANG_KEYS[combo.get_selected()]
        self._apply_lang()

    # ------------------------------------------------------------------
    def _on_choose_pdf(self, _btn):
        dlg = Gtk.FileDialog()
        dlg.set_title(self._t("select_pdf_title"))
        f = Gtk.FileFilter()
        f.set_name(self._t("select_pdf_filter"))
        f.add_pattern("*.pdf")
        f.add_pattern("*.PDF")
        store = Gio.ListStore.new(Gtk.FileFilter)
        store.append(f)
        dlg.set_filters(store)
        dlg.set_default_filter(f)
        dlg.open(self, None, self._pdf_chosen_cb)

    def _pdf_chosen_cb(self, dlg, result):
        try:
            gfile = dlg.open_finish(result)
        except Exception:
            return
        self._pdf_path = gfile.get_path()
        self._entry_pdf.set_text(self._pdf_path)

    # ------------------------------------------------------------------
    def _on_choose_out(self, _btn):
        dlg = Gtk.FileDialog()
        dlg.set_title(self._t("select_dir_title"))
        dlg.select_folder(self, None, self._out_chosen_cb)

    def _out_chosen_cb(self, dlg, result):
        try:
            gfile = dlg.select_folder_finish(result)
        except Exception:
            return
        self._out_dir = gfile.get_path()
        self._entry_out.set_text(self._out_dir)

    # ------------------------------------------------------------------
    def _on_cancel(self, _btn):
        self._cancel_flag.set()
        self._status.set_text(self._t("cancelling"))

    # ------------------------------------------------------------------
    def _on_split(self, _btn):
        t = self._t
        if not self._pdf_path:
            self._show_error(t("err_no_file"))
            return
        if not os.path.isfile(self._pdf_path):
            self._show_error(t("err_file_missing"))
            return
        out_dir = self._out_dir or str(Path(self._pdf_path).parent)
        if not os.path.isdir(out_dir):
            self._show_error(t("err_no_dir"))
            return

        size_val = self._spin.get_value()
        unit = self._unit_combo.get_selected()  # 0=MB, 1=KB
        max_bytes = int(size_val * (1024 * 1024 if unit == 0 else 1024))

        self._cancel_flag.clear()
        self._set_working(True)
        self._progress.set_fraction(0)
        self._progress.set_text(t("starting"))
        self._status.set_text("")

        threading.Thread(
            target=self._worker,
            args=(self._pdf_path, out_dir, max_bytes, self._lang),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    def _worker(self, pdf_path, out_dir, max_bytes, lang):
        try:
            outputs = split_pdf(
                pdf_path, out_dir, max_bytes,
                progress_cb=self._progress_cb,
                cancelled_flag=self._cancel_flag,
                lang=lang,
            )
            GLib.idle_add(self._on_done, outputs)
        except Exception as exc:
            GLib.idle_add(self._on_error, str(exc))

    def _progress_cb(self, current, total):
        frac = current / total
        text = self._t("page_of").format(current=current, total=total)
        GLib.idle_add(self._progress.set_fraction, frac)
        GLib.idle_add(self._progress.set_text, text)

    # ------------------------------------------------------------------
    def _on_done(self, outputs):
        self._set_working(False)
        if self._cancel_flag.is_set():
            self._progress.set_text(self._t("cancelled"))
            self._status.set_text(self._t("cancelled_msg"))
        else:
            self._progress.set_fraction(1.0)
            self._progress.set_text(self._t("done"))
            self._status.set_text(self._t("created_files").format(n=len(outputs)))

    def _on_error(self, msg):
        self._set_working(False)
        self._progress.set_text(self._t("error_title"))
        self._show_error(msg)

    # ------------------------------------------------------------------
    def _set_working(self, working: bool):
        self._btn_split.set_sensitive(not working)
        self._btn_cancel.set_sensitive(working)
        self._lang_combo.set_sensitive(not working)

    def _show_error(self, msg: str):
        dlg = Gtk.AlertDialog()
        dlg.set_message(self._t("error_title"))
        dlg.set_detail(msg)
        dlg.show(self)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = PdfSplitterApp()
    app.run()

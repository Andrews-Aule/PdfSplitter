#!/usr/bin/env python3
"""PDF Splitter — divide un PDF in parti di dimensione massima scelta."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, GLib, Gio, GObject

import os
import subprocess
import threading
import tempfile
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# PDF helpers (uses ghostscript, always installed on Ubuntu)
# ---------------------------------------------------------------------------

def gs_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF using ghostscript."""
    result = subprocess.run(
        [
            "gs", "-q", "-dNODISPLAY", "-dNOSAFER",
            "-c", f"({pdf_path}) (r) file runpdfbegin pdfpagecount = quit",
        ],
        capture_output=True, text=True,
    )
    return int(result.stdout.strip())


def gs_extract_pages(pdf_path: str, first: int, last: int, out_path: str) -> None:
    """Extract pages [first, last] (1-based) from pdf_path into out_path."""
    subprocess.run(
        [
            "gs", "-q", "-dNOPAUSE", "-dBATCH", "-dNOSAFER",
            "-sDEVICE=pdfwrite",
            f"-dFirstPage={first}",
            f"-dLastPage={last}",
            f"-sOutputFile={out_path}",
            pdf_path,
        ],
        capture_output=True,
    )


def split_pdf(
    pdf_path: str,
    out_dir: str,
    max_bytes: int,
    progress_cb,        # callable(current_page, total_pages)
    cancelled_flag,     # threading.Event
) -> list[str]:
    """
    Split pdf_path into chunks each ≤ max_bytes.
    Returns list of output file paths.
    """
    total = gs_page_count(pdf_path)
    if total == 0:
        raise ValueError("Impossibile leggere il numero di pagine.")

    stem = Path(pdf_path).stem
    outputs = []
    part = 1
    start = 1

    with tempfile.TemporaryDirectory() as tmp:
        while start <= total:
            if cancelled_flag.is_set():
                return outputs

            # Binary search: find the maximum 'end' such that
            # pages [start..end] fit within max_bytes.
            lo, hi = start, total
            best_end = start  # at minimum extract 1 page

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

                # Always make progress (single page may exceed limit — keep it)
                if mid == start and size > max_bytes:
                    best_end = start
                    break

            out_name = f"{stem}_parte{part:03d}.pdf"
            out_path = os.path.join(out_dir, out_name)
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
            application_id="com.example.pdfsplitter",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        win = MainWindow(application=self)
        win.present()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(title="PDF Splitter", **kwargs)
        self.set_default_size(520, 420)
        self.set_resizable(False)

        self._pdf_path = None
        self._out_dir = None
        self._cancel_flag = threading.Event()

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        # Header bar style via CSS
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="PDF Splitter"))
        self.set_titlebar(header)

        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=24,
            margin_bottom=24,
            margin_start=28,
            margin_end=28,
        )
        root.append(content)

        # --- Input file ---
        content.append(self._section_label("File PDF di input"))
        row_in = Gtk.Box(spacing=8)
        self._entry_pdf = Gtk.Entry(hexpand=True, editable=False,
                                    placeholder_text="Nessun file selezionato…")
        btn_choose_pdf = Gtk.Button(label="Sfoglia…")
        btn_choose_pdf.connect("clicked", self._on_choose_pdf)
        row_in.append(self._entry_pdf)
        row_in.append(btn_choose_pdf)
        content.append(row_in)

        # --- Output directory ---
        content.append(self._section_label("Cartella di destinazione"))
        row_out = Gtk.Box(spacing=8)
        self._entry_out = Gtk.Entry(hexpand=True, editable=False,
                                     placeholder_text="Stessa cartella del PDF…")
        btn_choose_out = Gtk.Button(label="Sfoglia…")
        btn_choose_out.connect("clicked", self._on_choose_out)
        row_out.append(self._entry_out)
        row_out.append(btn_choose_out)
        content.append(row_out)

        # --- Size limit ---
        content.append(self._section_label("Dimensione massima per file"))
        row_size = Gtk.Box(spacing=8)

        self._spin = Gtk.SpinButton()
        self._spin.set_adjustment(
            Gtk.Adjustment(value=5, lower=0.1, upper=9999, step_increment=0.5,
                           page_increment=5, page_size=0))
        self._spin.set_digits(1)
        self._spin.set_hexpand(True)

        self._unit_combo = Gtk.DropDown.new_from_strings(["MB", "KB"])
        self._unit_combo.set_selected(0)

        row_size.append(self._spin)
        row_size.append(self._unit_combo)
        content.append(row_size)

        # --- Progress ---
        self._progress = Gtk.ProgressBar(show_text=True)
        self._progress.set_text("In attesa…")
        content.append(self._progress)

        # --- Status label ---
        self._status = Gtk.Label(label="", wrap=True, max_width_chars=55,
                                  xalign=0)
        self._status.add_css_class("dim-label")
        content.append(self._status)

        # --- Buttons ---
        btn_row = Gtk.Box(spacing=12, halign=Gtk.Align.END)
        self._btn_cancel = Gtk.Button(label="Annulla")
        self._btn_cancel.set_sensitive(False)
        self._btn_cancel.connect("clicked", self._on_cancel)

        self._btn_split = Gtk.Button(label="Dividi PDF")
        self._btn_split.add_css_class("suggested-action")
        self._btn_split.connect("clicked", self._on_split)

        btn_row.append(self._btn_cancel)
        btn_row.append(self._btn_split)
        content.append(btn_row)

    # ------------------------------------------------------------------
    def _section_label(self, text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=f"<b>{text}</b>", use_markup=True, xalign=0)
        return lbl

    # ------------------------------------------------------------------
    def _on_choose_pdf(self, _btn):
        dlg = Gtk.FileDialog()
        dlg.set_title("Seleziona PDF")
        f = Gtk.FileFilter()
        f.set_name("File PDF")
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
        dlg.set_title("Seleziona cartella di destinazione")
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
        self._status.set_text("Annullamento in corso…")

    # ------------------------------------------------------------------
    def _on_split(self, _btn):
        if not self._pdf_path:
            self._show_error("Seleziona prima un file PDF.")
            return
        if not os.path.isfile(self._pdf_path):
            self._show_error("Il file PDF selezionato non esiste.")
            return

        out_dir = self._out_dir or str(Path(self._pdf_path).parent)
        if not os.path.isdir(out_dir):
            self._show_error("La cartella di destinazione non esiste.")
            return

        size_val = self._spin.get_value()
        unit = self._unit_combo.get_selected()  # 0=MB, 1=KB
        max_bytes = int(size_val * (1024 * 1024 if unit == 0 else 1024))

        self._cancel_flag.clear()
        self._set_working(True)
        self._progress.set_fraction(0)
        self._progress.set_text("Avvio…")
        self._status.set_text("")

        thread = threading.Thread(
            target=self._worker,
            args=(self._pdf_path, out_dir, max_bytes),
            daemon=True,
        )
        thread.start()

    # ------------------------------------------------------------------
    def _worker(self, pdf_path, out_dir, max_bytes):
        try:
            outputs = split_pdf(
                pdf_path, out_dir, max_bytes,
                progress_cb=self._progress_cb,
                cancelled_flag=self._cancel_flag,
            )
            GLib.idle_add(self._on_done, outputs)
        except Exception as exc:
            GLib.idle_add(self._on_error, str(exc))

    def _progress_cb(self, current, total):
        frac = current / total
        text = f"Pagina {current} di {total}"
        GLib.idle_add(self._progress.set_fraction, frac)
        GLib.idle_add(self._progress.set_text, text)

    # ------------------------------------------------------------------
    def _on_done(self, outputs):
        self._set_working(False)
        if self._cancel_flag.is_set():
            self._progress.set_text("Annullato")
            self._status.set_text("Operazione annullata.")
        else:
            self._progress.set_fraction(1.0)
            self._progress.set_text("Completato!")
            self._status.set_text(
                f"Creati {len(outputs)} file nella cartella di destinazione."
            )

    def _on_error(self, msg):
        self._set_working(False)
        self._progress.set_text("Errore")
        self._show_error(msg)

    # ------------------------------------------------------------------
    def _set_working(self, working: bool):
        self._btn_split.set_sensitive(not working)
        self._btn_cancel.set_sensitive(working)

    def _show_error(self, msg: str):
        dlg = Gtk.AlertDialog()
        dlg.set_message("Errore")
        dlg.set_detail(msg)
        dlg.show(self)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = PdfSplitterApp()
    app.run()

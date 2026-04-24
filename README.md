# PDF Splitter

Desktop app for Ubuntu that splits a PDF file into multiple files of a chosen maximum size.

## Requirements

- Ubuntu (or any Linux distro with GNOME)
- Python 3 with `python3-gi` (GTK4) — installed by default on Ubuntu
- Ghostscript — installed by default on Ubuntu
- Inkscape — required only to build the binary
- PyInstaller — required only to build the binary

To verify the runtime dependencies:
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 ok')"
gs --version
```

## Run directly (no build needed)

```bash
python3 pdf_splitter.py
```

## Build the standalone binary

```bash
# Install PyInstaller (only needed once)
curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --user --break-system-packages
python3 -m pip install --user --break-system-packages pyinstaller

# Build
python3 -m PyInstaller --onefile --windowed --name "pdf-splitter" --add-data "assets/icons:icons" pdf_splitter.py
```

The binary is created at `dist/pdf-splitter`.

## Add to the GNOME application menu (required for the icon to appear)

```bash
cp pdf_splitter.desktop ~/.local/share/applications/com.example.pdf-splitter.desktop
update-desktop-database ~/.local/share/applications/
```

> **Important:** always launch the app from the GNOME overview (Super key → search "PDF Splitter")
> or with `gio launch ~/.local/share/applications/com.example.pdf-splitter.desktop`.
> Running the binary directly from the terminal bypasses the `.desktop` file and GNOME
> will not show the icon in the taskbar.

## Usage

1. **Input PDF file** — select the PDF to split
2. **Destination folder** — where to save the output files (default: same folder as the PDF)
3. **Maximum size** — set the limit in MB or KB
4. Click **Split PDF**

Output files are named `filename_part001.pdf`, `filename_part002.pdf`, etc.

## How it works

For each part it uses a binary search to find the maximum number of pages that fits within the chosen size limit, maximising pages per file without exceeding the threshold. PDF manipulation is handled by Ghostscript.

## Files

| File | Description |
|------|-------------|
| `pdf_splitter.py` | Main application source |
| `pdf_splitter.svg` | Icon source (SVG) |
| `pdf_splitter.desktop` | Shortcut for the GNOME application menu |
| `assets/icons/` | Pre-rendered PNG icons (bundled into the binary) |

---

# PDF Splitter _(Italiano)_

App desktop per Ubuntu che divide un file PDF in più file di dimensione massima scelta.

## Requisiti

- Ubuntu (o qualsiasi distro Linux con GNOME)
- Python 3 con `python3-gi` (GTK4) — installato di default su Ubuntu
- Ghostscript — installato di default su Ubuntu
- Inkscape — necessario solo per compilare il binario
- PyInstaller — necessario solo per compilare il binario

Per verificare le dipendenze runtime:
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 ok')"
gs --version
```

## Avvio diretto (senza compilazione)

```bash
python3 pdf_splitter.py
```

## Compilare il binario standalone

```bash
# Installa PyInstaller (solo la prima volta)
curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --user --break-system-packages
python3 -m pip install --user --break-system-packages pyinstaller

# Compila
python3 -m PyInstaller --onefile --windowed --name "pdf-splitter" --add-data "assets/icons:icons" pdf_splitter.py
```

Il binario viene creato in `dist/pdf-splitter`.

## Aggiunta al menu applicazioni GNOME (necessario per vedere l'icona)

```bash
cp pdf_splitter.desktop ~/.local/share/applications/com.example.pdf-splitter.desktop
update-desktop-database ~/.local/share/applications/
```

> **Importante:** avviare sempre l'app dall'overview di GNOME (tasto Super → cerca "PDF Splitter")
> oppure con `gio launch ~/.local/share/applications/com.example.pdf-splitter.desktop`.
> Avviando il binario direttamente dal terminale, GNOME non collega la finestra al file
> `.desktop` e non mostra l'icona nella taskbar.

## Utilizzo

1. **File PDF di input** — seleziona il PDF da dividere
2. **Cartella di destinazione** — dove salvare i file in output (default: stessa cartella del PDF)
3. **Dimensione massima** — imposta il limite in MB o KB
4. Clicca **Split PDF**

I file in output vengono nominati `nomefile_part001.pdf`, `nomefile_part002.pdf`, ecc.

## Come funziona

Per ogni parte usa una ricerca binaria per trovare il numero massimo di pagine che rientra nel limite di dimensione scelto, massimizzando le pagine per file senza superare la soglia. La manipolazione del PDF avviene tramite Ghostscript.

## File

| File | Descrizione |
|------|-------------|
| `pdf_splitter.py` | Sorgente principale dell'applicazione |
| `pdf_splitter.svg` | Sorgente dell'icona (SVG) |
| `pdf_splitter.desktop` | Collegamento per il menu applicazioni GNOME |
| `assets/icons/` | Icone PNG precompilate (incorporate nel binario) |

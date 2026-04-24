# PDF Splitter

App desktop per Ubuntu che divide un file PDF in più file di dimensione massima scelta.

## Requisiti

- Ubuntu (o qualsiasi distro Linux con GNOME)
- Python 3 con `python3-gi` (GTK4) — installato di default su Ubuntu
- Ghostscript — installato di default su Ubuntu

Per verificare:
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 ok')"
gs --version
```

## Avvio

```bash
python3 pdf_splitter.py
```

### Aggiunta al menu applicazioni GNOME

```bash
cp pdf_splitter.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

Dopo questo passaggio l'app appare cercando "PDF Splitter" nell'overview di GNOME.

## Utilizzo

1. **File PDF di input** — seleziona il PDF da dividere
2. **Cartella di destinazione** — dove salvare i file in output (default: stessa cartella del PDF)
3. **Dimensione massima** — imposta il limite in MB o KB
4. Clicca **Dividi PDF**

I file in output vengono nominati `nomefile_parte001.pdf`, `nomefile_parte002.pdf`, ecc.

## Come funziona

Per ogni parte usa una ricerca binaria per trovare il numero massimo di pagine che rientra nel limite di dimensione scelto, massimizzando le pagine per file senza superare la soglia. La manipolazione del PDF avviene tramite Ghostscript.

## File

| File | Descrizione |
|------|-------------|
| `pdf_splitter.py` | Sorgente principale dell'applicazione |
| `pdf_splitter.desktop` | Collegamento per il menu applicazioni GNOME |

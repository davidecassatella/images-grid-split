# Images Grid Split

Script Python per dividere immagini grid in frame separati.  
Funziona bene per storyboard, frame sequence e immagini da preparare per Kling.

---

## Download (macOS — nessun Python richiesto)

1. Vai su **[Releases](https://github.com/davidecassatella/images-grid-split/releases)**
2. Scarica `Images.Grid.Split_v1.0.dmg`
3. Aprilo e trascina l'app in `/Applications`
4. Doppio clic per avviarla

### Primo avvio — avviso di sicurezza macOS

macOS blocca le app non firmate con un Apple Developer ID. È normale.  
Per aprirla la prima volta hai due opzioni:

**Opzione A — clic destro (più veloce)**

1. Clicca **Fine** sul messaggio di avviso
2. Vai in `/Applications`, trova `Images Grid Split.app`
3. **Clic destro** sull'app → **Apri**
4. Nella nuova finestra clicca **Apri**

**Opzione B — Impostazioni di Sistema**

1. **Apple menu** → Impostazioni di Sistema → **Privacy e sicurezza**
2. Scorri fino a trovare _"Images Grid Split è stata bloccata…"_
3. Clicca **Apri comunque**

Dopo la prima volta l'app si avvia normalmente con doppio clic.

---

## File

| File                | Descrizione                                      |
| ------------------- | ------------------------------------------------ |
| `split_kling.py`    | **CLI unificato** — punto di ingresso principale |
| `split_kling_ui.py` | **Interfaccia grafica** (tkinter)                |
| `split_2x2.py`      | Logica splitting 2×2 (4 frame)                   |
| `split_3x3.py`      | Logica splitting 3×3 (9 frame)                   |

---

## Requisiti

- macOS, Linux o Windows
- Python 3.10+
- Pillow, rich (vedere `requirements.txt`)

---

## Installazione

```bash
# 0. (macOS) Assicurati che tkinter sia disponibile per Python 3.14+
brew install python-tk@3.14

# 1. Crea e attiva un virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 2. Installa le dipendenze
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Utilizzo

### Interfaccia grafica

**Opzione A — App macOS (doppio clic, nessun terminale)**

Esegui una volta sola per creare il bundle `.app`:

```bash
bash make_app.sh
```

Poi apri `Images Grid Split.app` dal Finder con doppio clic, oppure trascinala nel Dock.

> Se macOS chiede conferma la prima volta ("app da sviluppatore non identificato"), fai clic destro → Apri.

**Opzione B — da terminale**

```bash
source .venv/bin/activate
python split_kling.py ui
# oppure direttamente:
python split_kling_ui.py
```

La GUI permette di:

- scegliere la modalità **2×2** o **3×3**
- selezionare una **cartella intera** o un **file singolo**
- scegliere le cartelle di input/output con il file browser
- seguire l'avanzamento con una barra di progresso
- visualizzare il log colorato con il risultato di ogni immagine
- aprire la cartella di output con un click

### CLI unificato

```bash
# Sintassi generale
python split_kling.py [2x2|3x3|ui] [opzioni]

# Elabora tutte le immagini in input_grids_2x2/ → output_frames_2x2/
python split_kling.py 2x2

# Cartella personalizzata
python split_kling.py 3x3 -i mia_cartella -o mio_output

# File singolo
python split_kling.py 2x2 -f immagine.png -o output

# Aiuto
python split_kling.py --help
python split_kling.py 2x2 --help
```

### Script diretti (uso legacy)

```bash
python split_2x2.py [-i INPUT] [-o OUTPUT]
python split_3x3.py [-i INPUT] [-o OUTPUT]
```

---

## Struttura cartelle

```
split-kling/
├── split_kling.py          ← CLI unificato (usa questo)
├── split_kling_ui.py       ← GUI tkinter
├── split_2x2.py
├── split_3x3.py
├── requirements.txt
├── input_grids_2x2/        ← metti qui le grid 2×2
├── output_frames_2x2/      ← frame 2×2 generati
├── input_grids_3x3/        ← metti qui le grid 3×3
└── output_frames_3x3/      ← frame 3×3 generati
```

├── README.md
├── input_grids/
├── output_frames/
├── input_grids_3x3/
└── output_frames_3x3/
Uso script 2x2

Di default usa:

input: input_grids

output: output_frames

Esecuzione con cartelle di default
python split_2x2.py
Esecuzione con cartelle personalizzate
python split_2x2.py --input mie_grid --output frame_kling

oppure:

python split_2x2.py -i mie_grid -o frame_kling
Output generato

Per un file chiamato:

scena01.png

otterrai:

scena01_01_top_left.png
scena01_02_top_right.png
scena01_03_bottom_left.png
scena01_04_bottom_right.png

Ordine:

01_top_left 02_top_right
03_bottom_left 04_bottom_right
Uso script 3x3

Di default usa:

input: input_grids_3x3

output: output_frames_3x3

Esecuzione con cartelle di default
python split_3x3.py
Esecuzione con cartelle personalizzate
python split_3x3.py --input mie_grid_3x3 --output frame_kling_3x3

oppure:

python split_3x3.py -i mie_grid_3x3 -o frame_kling_3x3
Output generato

Per un file chiamato:

storyboard.png

otterrai:

storyboard_shot_01.png
storyboard_shot_02.png
storyboard_shot_03.png
storyboard_shot_04.png
storyboard_shot_05.png
storyboard_shot_06.png
storyboard_shot_07.png
storyboard_shot_08.png
storyboard_shot_09.png

Ordine:

shot_01 shot_02 shot_03
shot_04 shot_05 shot_06
shot_07 shot_08 shot_09
Note importanti

Gli script dividono l'immagine in celle uguali.

Quindi funzionano bene se:

la grid è regolare

non ci sono bordi spessi tra i pannelli

non ci sono spazi bianchi grandi

i pannelli occupano tutta l'immagine

Se l'immagine ha separatori, padding o bordi, il crop potrebbe includerli.

Formati supportati

.png

.jpg

.jpeg

.webp

Esempio workflow veloce
2x2

Metti le immagini dentro input_grids

Esegui:

python split_2x2.py

Trova i file separati dentro output_frames

3x3

Metti le immagini dentro input_grids_3x3

Esegui:

python split_3x3.py

Trova i file separati dentro output_frames_3x3

Riattivare il virtual environment in futuro

Ogni volta che riapri il terminale:

macOS / Linux
cd kling_splitter
source .venv/bin/activate
Windows
cd kling_splitter
.venv\Scripts\activate
Uscire dal virtual environment
deactivate

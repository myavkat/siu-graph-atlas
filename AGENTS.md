# AGENTS.md

Guidance for coding agents that work in this repository.

## Layout

| Path | Contents |
|---|---|
| `data/` | OpenAlex corpus snapshot, `siu_papers_2020_2026.csv`, 2,630 papers from 2020 to 2026. |
| `src/` | Analysis code. Python scripts and configuration files go here. |
| `report/` | IEEEtran journal report, two columns. |
| `report/main.tex` | Report entry point. Holds the preamble and imports the section files. |
| `report/sections/` | One file per section: `abstract.tex`, `introduction.tex`, `methodology.tex`, `results.tex`, `discussion.tex`, `conclusion.tex`. |
| `report/references.bib` | BibTeX database for the report. |
| `report/assets/` | Figures and tables for the report. |
| `presentation/` | Metropolis beamer presentation, 16:9. |
| `presentation/main.tex` | Slide entry point. |
| `presentation/assets/` | Figures for the slides. |

## Build

Build from the folder that holds the file, never from the repository root.

```sh
cd report && latexmk -pdf main.tex
cd presentation && latexmk -xelatex main.tex
```

The presentation needs XeLaTeX. The metropolis theme loads Fira Sans through
`fontspec`. pdfLaTeX gives a warning and falls back to Computer Modern, so do not
change the engine.

Both builds must finish with 0 errors and 0 warnings. `latexmk -C` in the same
folder removes the build intermediates.

## Editing rules

- Write report text in `report/sections/<section>.tex`. Do not grow `main.tex` with body text.
- Put figures in `report/assets/` or `presentation/assets/`. Both entry points set the graphics path, so `\includegraphics{name}` is enough.
- Cite with `\cite` and keys from `report/references.bib`. `main.tex` holds one `\nocite` line that keeps the bibliography compiling while the sections are empty. Remove it once the text cites OpenAlex normally.
- Add Python dependencies and usage notes next to the code in `src/`.
- Use the ASCII hyphen `-` in prose. Do not use en dashes or em dashes.
- Do not add IEEE Xplore records, publisher PDFs, or other third-party files. The corpus in `data/` comes from OpenAlex and is CC0.

## Data

- Snapshot date: 2026-11-12. Source: OpenAlex conference source `S4363607818`.
- License: OpenAlex data is CC0. Cite Priem, Piwowar, and Orr (2022) when the data is used.

## Before a commit

- Run both build commands above.
- Run `git status` and confirm that no build intermediates appear. `main.pdf` is a build output, decide per release whether it is committed.

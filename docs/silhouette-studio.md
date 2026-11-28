# Opening the cut files in Silhouette Studio

How to get the leather cut files onto the Silhouette Cameo 4 Plus, and what had to be fixed for them to open correctly. Worked out and tested on 2026-11-28 with Silhouette Studio 5.0.402 on macOS 27.2.

When the user says "import it on the app" (or "open it in Silhouette"), it means: open the right `latest-cutting-machine-*.dxf` file in Silhouette Studio, as in [Opening a file](#opening-a-file) below, then ask the user to check it.

## Which file to open

The ready-to-cut files are the four `latest-cutting-machine-*` pointers in `dxf/`, one per mat. Their section in [`../dxf/README.md`](../dxf/README.md) says what each one is a copy of.

| Mat loaded | Files to open (one cut each) |
| --- | --- |
| 14" × 15" | `latest-cutting-machine-14x15-mat1.dxf`, then `latest-cutting-machine-14x15-mat2.dxf` |
| 12" × 24" | `latest-cutting-machine-12x24-mat1.dxf`, then `latest-cutting-machine-12x24-mat2.dxf` |

`12x24-mat2` fits within 12" × 9.2", so it also cuts on a 14" × 15" mat.

## Opening the app

- The app is `/Applications/Silhouette Studio.app`.
- It's free (Basic Edition). DXF opens in Basic; SVG would need the paid Designer Edition.
- Silhouette says the Cameo 4 Plus needs Studio 4.3.370 or newer, and that most DXF problems are fixed by updating Studio.

## Opening a file

From the terminal (this is what Claude runs). It starts Studio if it's closed, and opens the file in a new tab:

```sh
open -a "Silhouette Studio" "/Users/jayrcastro/Repositories/personal-projects/boxing/dxf/latest-cutting-machine-14x15-mat1.dxf"
```

By hand: **File → Open** in Studio, pick the DXF.

Claude can't see Studio's screen from a terminal session, so after opening a file, ask the user for a screenshot with everything selected (⌘A) and check it against [Checking the file](#checking-the-file).

## One-time setting: Import "As is"

**Silhouette Studio → Preferences (⌘,) → Import → set the open option to "As is".** This is already set on this Mac.

| Option | What it does to our DXFs |
| --- | --- |
| **As is** | Keeps the true size and position. **Use this.** |
| Centered | True size, but moves the design to the middle of the page, so the layout on the mat is lost |
| Fit to page | Shrinks the design to fit inside the page margins and centres it. 14x15 mat 1 opened at 12.326" × 13.209" instead of 13.991" × 14.956", about 88%. Leather cut like this would be too small to sew. |

Silhouette's own note: DXF "does not retain size information" on import. That's why this setting matters, and why the size must be checked after every open.

## Checking the file

Press ⌘A in Studio. The toolbar shows **W**, **H**, **X** and **Y**, and the selection shows size labels.

| File | W × H | X, Y |
| --- | --- | --- |
| `latest-cutting-machine-14x15-mat1.dxf` | 13.991 × 14.956 in | 0.000, 0.000 |
| `latest-cutting-machine-14x15-mat2.dxf` | 13.734 × 11.271 in | 0.000, 0.000 |
| `latest-cutting-machine-12x24-mat1.dxf` | 11.159 × 21.972 in | 0.000, 0.000 |
| `latest-cutting-machine-12x24-mat2.dxf` | 11.991 × 9.157 in | 0.000, 0.000 |

These sizes are for the current files. If the files are rebuilt, read the new sizes from the output of `scripts/leather_cut.py layout` or `studio-top`.

Also check:

- Every piece and hole is there, with smooth curves (the pieces of each mat are listed in [`../dxf/README.md`](../dxf/README.md)).
- All pieces are inside the **red line** (the cutting area). On 14x15 mat 1 there's only about 1 mm to spare top to bottom.
- In **Page Setup**, the machine is the Cameo 4 Plus and the mat size matches the mat loaded.

If the size is wrong, fix the Import setting and reopen. Don't just type the right W into the toolbar: that fixes the size but not the position.

## How the DXFs are adjusted for Studio

Two things in the DXF itself, both done by `scripts/leather_cut.py`:

1. **Units: inches.** The files are in inches (`$INSUNITS` = 1). With "As is", Studio reads them at the right size.
2. **The design sits below y = 0.** DXF counts y upward from the bottom, but Studio counts y downward from the top of the page (Studio y = −DXF y). A design drawn from y = 0 upward opens entirely **above** the mat; the first test showed Y −14.956. So every mat file is moved straight down until its top-left corner is at (0, 0), and the design runs down to negative y. It then opens on the mat, top-left at the page's top-left. Shapes, sizes and layout don't change.

`layout` writes the mat files already moved (named `... mat <n> of <m> - studio top.dxf`). To move any other DXF the same way:

```sh
uv run --with ezdxf --with matplotlib --with shapely python scripts/leather_cut.py studio-top "dxf/<file>.dxf" "dxf/<new name>.dxf"
```

What else the file needs (from Silhouette's DXF support notes):

- Only these entity types are supported: Arc, Circle, Ellipse, Line, polyline ("DWPolyline" on Silhouette's page), Spline and Text. Our files use only SPLINE and LWPOLYLINE, and both open fine.
- No groups or compound paths. Each outline and each hole is its own closed line, which is what we have.
- The files are DXF 2018 (AC1032), and Studio 5 opens them. Silhouette suggests R13 for Illustrator exports; if a future file won't open, try writing an older version.

## Sending to the machine

1. In the **Send** tab, choose the Cameo 4 Plus. Bluetooth works: turn it on on the Mac and press the Bluetooth button on the Cameo. USB is safer for the tight 14x15 mat 1, because a dropped connection stops the cut partway.
2. Set the material and blade for the leather. The machine takes material up to 3 mm thick.
3. Cut the holes before the outlines (cut order), so a piece doesn't shift once it's cut free.
4. Do a paper test first, especially for 14x15 mat 1.

Silhouette lists macOS 13–15 for the Cameo 4 Plus; this Mac is on 27.2, which is newer than the list. If the machine doesn't connect, that may be why.

## Bluetooth won't connect

**Status (2026-11-28): not solved yet.** Sending over Bluetooth didn't work on the first try. Use USB to cut until it does. The steps below come from Silhouette's support pages and haven't been confirmed on this Mac yet. When something works, record it here.

What the Mac showed (`system_profiler SPBluetoothDataType`):

- `CAMEO 4 PLUS-375252C` appeared **twice**: connected over Bluetooth Low Energy (BLE, probably Studio's own link), and as a saved, not-connected pairing listed as a "Desktop Computer".
- The second one looks like a pairing made in System Settings. Silhouette's fix is to connect only from inside Studio.

Steps, in order:

1. **Forget the old pairing.** System Settings → Bluetooth → ⓘ next to `CAMEO 4 PLUS-375252C` → **Forget This Device**. Forget both if there are two.
2. **Allow Studio to use Bluetooth.** System Settings → Privacy & Security → Bluetooth → turn on **Silhouette Studio**.
3. **Restart both.** Quit Studio (⌘Q) and switch the Cameo off and on. Check that the Cameo's Bluetooth button is lit.
4. **Connect from Studio.** **Send** tab → the small machine icon at the bottom → pick the **CAMEO 4 PLUS** marked "Available" next to the Bluetooth symbol.
5. **Update the firmware over USB.** Plug in the USB cable; if Studio offers **Update Now**, accept it, then try Bluetooth again.
6. **Still nothing?** macOS 27.2 isn't on Silhouette's list, and some Mac users report never getting Bluetooth to work. Contact Silhouette support.

To check what the Mac sees from the terminal:

```sh
system_profiler SPBluetoothDataType | grep -A3 -i cameo
```

## Sources

- [Silhouette: Importing and Exporting Troubleshooting](https://silhouetteamerica.freshdesk.com/support/solutions/articles/35000276938-importing-and-exporting-troubleshooting) (DXF limits, size on import)
- [Silhouette: Bluetooth-compatible machines](https://silhouetteamerica.freshdesk.com/support/solutions/articles/35000206350)
- [USCutter: Cameo 4 Plus specs](https://www.uscutter.com/15in-Silhouette-Came-4-PLUS-Craft-Cutter) (14.6" × 15" cutting area on a mat, 3 mm thickness)
- [Silhouette: Can't connect via USB but can via Bluetooth](https://silhouetteamerica.freshdesk.com/support/solutions/articles/35000213489-can-t-connect-via-usb-but-can-connect-via-bluetooth) (clearing the pairing)
- [Silhouette School: Cameo 4 Bluetooth setup](https://silhouetteschoolblog.com/2019/09/silhouette-cameo-4-bluetooth-set-up.html)
- [Sure Cuts A Lot forum: Cameo 4 Bluetooth](https://forum.surecutsalot.com/viewtopic.php?p=199747) (a Mac user who never got Bluetooth working)

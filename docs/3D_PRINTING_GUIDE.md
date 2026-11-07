# 3D Printing & Modular Screwless Enclosure Assembly Guide

This guide provides complete instructions for 3D printing and assembling the **modular, tool-less, screwless snap-fit enclosure** for the **LED Flight Information Display**, featuring **zero-binding drop-in display fit**, **dead-flush outer mating seam**, and **swappable display feet**.

---

## 1. Overview & Mechanical Revisions (Revision 3.1)

### What Was Fixed in This Revision:
1. **Dead-Flush Outer Seam & Zero-Squeeze Slip-Fit Alignment**:
   - **Root Cause of Squeezing**: In previous builds, the male collar tongue on the front bezel had an undersized inset ($1.2\text{ mm}$), placing its outer wall at $y=1.2\text{ mm}$. Because the rear chassis outer walls are $3.2\text{ mm}$ thick, the collar collided directly with the solid chassis wall ($1.8\text{ mm}$ interference on all four sides), forcing users to forcefully squeeze the plastic inward to get the halves to mate, which created an uneven, non-flush edge.
   - **Calibrated Tongue Inset & Clearance**: The male tongue boundary is now placed at $x \in [3.60, 166.40]\text{ mm}$ and $y \in [3.60, 86.40]\text{ mm}$. This provides an exact **$0.40\text{ mm}$ slip-fit clearance** on every side relative to the chassis cavity ($3.20\text{ mm}$ to $166.80\text{ mm}$ / $86.80\text{ mm}$).
   - **45° Self-Centering Lead-In Chamfer**: Added a continuous $1.5\text{ mm}$ high, $0.8\text{ mm}$ bevel chamfer at the tip of the male tongue. When mating, the chamfer automatically self-locates into the chassis opening without any manual squeezing or pinching.
   - **Softened Locking Detents**: Refined locking detent protrusion to $0.45\text{ mm}$ with gentle $25^\circ$ lead-in ramps matching the recessed female grooves on the chassis inner walls.
   - **Dead-Flush Outer Rim**: Both front bezel and rear chassis share identical outer perimeter dimensions (**$170.0\text{ mm} \times 90.0\text{ mm}$**) at the parting seam plane ($Z_0 = 18.0\text{ mm}$), ensuring an ultra-smooth, continuous transition with zero overhang or lip.

2. **Generous Zero-Binding Display Pocket ($163.6 \times 83.6 \times 15.5\text{ mm}$)**:
   - The front bezel internal pocket has been expanded to **$163.6\text{ mm (Width)} \times 83.6\text{ mm (Height)} \times 15.5\text{ mm (Depth)}$**.
   - Accommodates actual measured **$14.0\text{ mm}$ thick displays** with a generous **$+1.5\text{ mm}$ depth headroom** ($+1.8\text{ mm}$ clearance on width and height), ensuring the panel drops in completely flat with zero binding against the front retention shelf.
   - **100% Unobstructed 90° Square Corners**: Completely removed the internal corner gussets that previously obstructed the square corners of the display.

3. **Unobstructed Rear Chassis Opening ($164.6\text{ mm} \times 84.6\text{ mm}$)**:
   - Completely eliminated the corner clamping ribs and corner posts that previously blocked the display from seating and caused it to sit on top of the rim.
   - The entire front opening of the rear chassis is wider and taller than the display, completely preventing any collision or binding.

4. **Unbreakable Perimeter Interlocking Collar (No More Snapping Tabs)**:
   - Replaced fragile isolated vertical cantilever tabs with a **continuous reinforced perimeter tongue ($1.8\text{ mm}$ thick)** extending from the front bezel into the rear chassis.
   - 4x integrated wide detent locking beads ($18.0\text{ mm}$ wide, $0.45\text{ mm}$ protrusion, $25^\circ$ lead-in ramps) lock with an audible click into matching recessed grooves on the inner chassis walls.
   - Two external **coin pry slots** on the bottom seam allow opening the case in seconds by simply twisting a coin, guitar pick, or fingernail without any stress on layer lines.

5. **Modular Swappable Display Feet (Tool-Less Sliding T-Rail System)**:
   - Two low-profile sliding T-rails ($2.8\text{ mm}$ height) on the chassis bottom allow sliding swappable feet on and off with zero screws.
   - Three pre-modeled angle variants:
     * **10° Foot (`modular_foot_10deg.stl`)**: Standard eye-level desktop and monitor shelf viewing angle.
     * **15° Foot (`modular_foot_15deg.stl`)**: Steeper tilt for low coffee tables, standing desks, or bedside nightstands.
     * **0° Stand Foot (`modular_foot_0deg.stl`)**: 90° vertical upright stand for shelving, display cabinets, or cockpit consoles.
     * **Detached Flat Profile**: With feet removed, the chassis has a clean, low-profile base that sits flat on desks or mounts against walls!
   - **Universal Foot Symmetry**: Symmetrical along X, so the user prints the **same model twice (2x)** for Left and Right.
   - **Anti-Tip Stabilizer Heel**: Runner skis ($26\text{ mm}$ wide $\times 65\text{ mm}$ long) extend **$15\text{ mm}$ behind the rear chassis**, completely preventing the unit from tipping backward when pressed.

6. **Deep Cable Cavity ($50.3\text{ mm}$)**:
   - Total body depth is **$71.5\text{ mm}$** (rear depth: $53.5\text{ mm}$, front bezel: $18.0\text{ mm}$).
   - Abundant headroom ($>13\text{ mm}$ clearance) for vertical molex power connectors and folded ribbon cables, plus $41.8\text{ mm}$ open lateral bays on either side of the Raspberry Pi.

7. **Dual-Mode Visualization Rest: Quad Corner Support Ledges ($Z = 19.5\text{ mm}$)**:
   - Four dedicated horizontal corner support ledges ($16.0 \times 16.0\text{ mm}$ envelope) built directly into the rear chassis top opening.
   - Provides a solid **$11.0\text{ mm} \times 11.0\text{ mm}$ planar bearing area under each corner of the matrix** ($484\text{ mm}^2$ total solid support).
   - Recessed $1.5\text{ mm}$ below the mating rim ($Z = 19.5\text{ mm}$): When testing or if the front frame is not installed (or does not fit 100%), the display drops $1.5\text{ mm}$ into the chassis opening, resting flat and level on the corner ledges. The outer chassis walls act as a locator collar, preventing the display from sliding off and keeping it safely at the top of the case for visualization.
   - **Support-Free Printability**: Corner support columns extend continuously down to the backplate ($Z = 68.3\text{ mm}$) with $0^\circ$ vertical walls, printing 100% support-free when the chassis is printed with its backplate flat on the bed.
   - **Front Tongue Corner Relief**: The front bezel tongue features $17.5\text{ mm}$ corner reliefs ($1.5\text{ mm}$ clearance from the shelves), completely preventing any collision when snapping the front frame on.

---

## 2. Included 3D Model Files (`models/`)

| File Name | Description | Build Plate Orientation | Supports |
| :--- | :--- | :--- | :--- |
| [`display_front_bezel.stl`](file:///Volumes/ssd/Documents/github/led_flight_info/models/display_front_bezel.stl) | Front frame with unobstructed $163.6 \times 83.6\text{ mm}$ pocket and reinforced perimeter interlocking collar. | **Face-down on build plate** ($z=0$ on bed). | **None (0%)** |
| [`rear_chassis_enclosure.stl`](file:///Volumes/ssd/Documents/github/led_flight_info/models/rear_chassis_enclosure.stl) | Deep rear case with clear $164.6 \times 84.6\text{ mm}$ opening, bottom T-rails, Pi 4 snap-mounts, and fused louvers. | **Backplate face-down on build plate** ($z=70$ on bed). | Minimal tree supports. |
| [`modular_foot_10deg.stl`](file:///Volumes/ssd/Documents/github/led_flight_info/models/modular_foot_10deg.stl) | **10° Viewing Angle Foot** with sliding T-channel and anti-tip heel. (Universal: **Print 2x**). | **Flat side face on build plate** ($x=\pm 13$ on bed). | **None (0%)** |
| [`modular_foot_15deg.stl`](file:///Volumes/ssd/Documents/github/led_flight_info/models/modular_foot_15deg.stl) | **15° Low-Surface Tilt Foot** with sliding T-channel and anti-tip heel. (Universal: **Print 2x**). | **Flat side face on build plate** ($x=\pm 13$ on bed). | **None (0%)** |
| [`modular_foot_0deg.stl`](file:///Volumes/ssd/Documents/github/led_flight_info/models/modular_foot_0deg.stl) | **0° Upright Stand Foot** with sliding T-channel and anti-tip heel. (Universal: **Print 2x**). | **Flat side face on build plate** ($x=\pm 13$ on bed). | **None (0%)** |
| [`complete_enclosure_assembly.stl`](file:///Volumes/ssd/Documents/github/led_flight_info/models/complete_enclosure_assembly.stl) | Complete assembled reference model showing bezel, chassis, and 10° feet installed. | CAD reference / slicer preview. | N/A |

---

## 3. Recommended Slicer Settings

Compatible with **Bambu Studio**, **PrusaSlicer**, **OrcaSlicer**, **Creality Print**, and **UltiMaker Cura**.

| Slicer Parameter | Recommended Value | Notes |
| :--- | :--- | :--- |
| **Material** | **PETG** or **PLA+** | PETG is recommended for natural spring flexibility on the interlocking collar and heat resistance ($\approx 75^\circ\text{C}$). High-temp PLA+ also works great. |
| **Layer Height** | **0.20 mm** | Ensures smooth sliding action on the T-rails and crisp locking detents. |
| **Perimeters / Walls** | **4 perimeters** (1.6 mm wall thickness) | Critical for rigid T-rails and durable perimeter collar. |
| **Top & Bottom Layers** | **5 top / 5 bottom layers** (1.0 mm) | Gives watertight solid faces and smooth outer finish. |
| **Infill Density** | **20% to 25%** | **Gyroid** or **Grid** pattern. |
| **Foot Print Orientation** | Print on flat side face | Zero supports required; T-channel prints horizontally with optimal layer lines. |
| **Bed Adhesion** | Textured PEI sheet | Clean bed with isopropyl alcohol for maximum adhesion. |

---

## 4. Hardware Bill of Materials (BOM)

| Qty | Item | Specification | Usage |
| :--- | :--- | :--- | :--- |
| **0** | Screws | None needed! | 100% tool-less snap-fit and slide-rail design. |
| **1** | 64×32 P2.5 RGB LED Matrix | $160 \times 80 \times 13\text{ mm}$ (HUB75) | Display panel. |
| **1** | Raspberry Pi 4 Model B | 2GB / 4GB / 8GB | Computer running LED Flight Info. |
| **1** | RGB Matrix Adapter Board | Direct GPIO HAT / Adapter | Drives HUB75 matrix from Pi GPIO. |
| **1** | 16-pin HUB75 Ribbon Cable | Standard $\approx 10 - 15\text{ cm}$ length | Connects adapter to matrix DATA IN. |
| **1** | 5V 4A DC Power Supply | Barrel Jack or USB-C | Powers the Pi and LED Matrix. |
| **2** | Modular Display Feet | 10°, 15°, or 0° (Printed) | Slide onto bottom chassis T-rails. |
| **4** | Adhesive Rubber Pads (Optional) | $\varnothing 8\text{ mm} - 12\text{ mm}$ silicone pads | Stick onto the bottom runner feet. |

---

## 5. Step-by-Step Tool-Less Assembly Instructions

```
[ FRONT BEZEL ]  <---  [ 64x32 MATRIX ]  <---  [ CABLE CAVITY ]  <---  [ PI 4 + ADAPTER ]  <---  [ REAR CHASSIS ]
                                                                                                    |
                                                                                           [ MODULAR FEET (2x) ]
                                                                                           (Slide into T-Rails)
```

### Step 1: Drop the Matrix Panel into the Front Bezel
1. Place the **Front Bezel** face-down on a soft cloth.
2. Drop the **64×32 RGB LED Matrix Panel** directly into the internal retention pocket:
   - Ensure the white arrow on the matrix back PCB points horizontally from **IN** to **OUT**.
   - With the enlarged $163.6 \times 83.6\text{ mm}$ pocket and clear square corners, the matrix drops in **effortlessly and sits completely flat** against the front $2.8\text{ mm}$ retention shelf.

### Step 2: Snap the Raspberry Pi 4 into the Rear Chassis
1. Place the **Rear Chassis** on your desk with the interior facing up.
2. Align the Pi's 4 mounting holes over the 4 standoff pedestals with the $\varnothing 2.4\text{ mm}$ locator pins (micro-SD card facing the left access slot).
3. Press down gently until the flexible snap hooks on the top and bottom edges click over the PCB edges.

### Step 3: Install Adapter Board & Route Cables
1. Press the **RGB Matrix Adapter Board** down onto the Pi's GPIO header.
2. Plug the 16-pin ribbon cable between the adapter board and the matrix **DATA IN** socket.
3. Connect the 4-pin 5V power cable to the adapter's vertical molex power connector and the matrix power socket.
4. Route the main 5V power wire through the rear cable pass-through port.
   - *Note*: The deep $51.5\text{ mm}$ cavity easily clears the vertical molex connector and ribbon cable loop. Excess wire slack tucks into the side bays beside the Pi.

### Step 4: Snap the Enclosure Together
1. Align the Front Bezel's continuous collar with the Rear Chassis opening.
2. Press together firmly until the **locking detent beads click into the inner grooves**.
3. The display is firmly sandwiched and retained with zero play and zero screws!

### Step 5: Slide on the Modular Display Feet
1. Select your preferred angle foot (10°, 15°, or 0° upright).
2. Align the foot's female T-slot channel with the male T-rail on the bottom of the chassis.
3. Slide the foot backward from the front until it hits the rear stop block and clicks into place.
4. Repeat for the second foot on the opposite side.
5. To change angles or remove for flat mounting: Simply slide the feet forward off the rails!

---

## 6. Re-generating or Customizing the Models

The parametric CAD generator is located at:
[`scripts/generate_3d_models.py`](file:///Volumes/ssd/Documents/github/led_flight_info/scripts/generate_3d_models.py)

To re-generate all STL files:
```bash
python scripts/generate_3d_models.py
```
All output meshes will be regenerated in `models/` with updated triangle geometry.

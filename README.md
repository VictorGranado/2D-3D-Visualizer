# Vector Visualizer (2D / 3D) — Unit 1 Project

A small Python GUI tool to help visualize **Unit 1 vector concepts** like:
- points and position vectors
- vector components (x, y, z)
- vector addition (head-to-tail using tails)
- scalar multiplication (scaling)
- direction and magnitude (arrow length)

I made this because I sometimes understand the math but struggle to **picture** what the vectors are doing.

## Features
- 2D and 3D plotting mode
- Plot multiple **points** (e.g. `(1,2)` or `(1,2,3)`)
- Plot **vectors** as arrows from the origin or from any tail point  
  - `<vx,vy>`  
  - `<vx,vy>@(tx,ty)`  
  - `<vx,vy,vz>@(tx,ty,tz)`
- Optional curve/surface plotting (used as geometric context - a little buggy still) 

## Screenshots
Add your screenshots here after you save them into `screenshots/`.

Example:
- `screenshots/demo_2d.png`
- `screenshots/demo_3d.png`

## Install
Make sure you have Python 3.11+.

```bash
pip install -r requirements.txt


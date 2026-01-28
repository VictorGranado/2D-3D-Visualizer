import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import sympy as sp

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


# --------------------------
# Helpers: parsing & plotting
# --------------------------

def _safe_sympy_expr(expr_str: str, symbols: dict):
    """
    Parse a math expression using sympy with a limited namespace.
    Examples:
      "sin(x)", "x**2 + 3", "sqrt(x**2 + y**2)"
    """
    expr_str = expr_str.strip()
    if not expr_str:
        raise ValueError("Empty expression.")

    # allow common functions/constants
    local_dict = {
        **symbols,
        "pi": sp.pi,
        "e": sp.E,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "sqrt": sp.sqrt,
        "abs": sp.Abs,
        "ln": sp.log,
        "log": sp.log,
        "exp": sp.exp,
    }

    # sympify is generally safer than eval; still treat as untrusted input.
    expr = sp.sympify(expr_str, locals=local_dict)
    return sp.simplify(expr)


def parse_points(text: str, dims: int):
    """
    Input examples:
      2D: (1,2); (0,0); (-3,4)
      3D: (1,2,3); (0,0,0)
    """
    pts = []
    s = text.strip()
    if not s:
        return pts

    parts = [p.strip() for p in s.split(";") if p.strip()]
    for p in parts:
        if not (p.startswith("(") and p.endswith(")")):
            raise ValueError(f"Point must be like (a,b) or (a,b,c). Got: {p}")
        inner = p[1:-1].strip()
        nums = [n.strip() for n in inner.split(",")]
        if len(nums) != dims:
            raise ValueError(f"Point {p} must have {dims} numbers.")
        vals = [float(n) for n in nums]
        pts.append(vals)
    return np.array(pts, dtype=float)


def parse_vectors(text: str, dims: int):
    """
    Vectors are arrows. Format:
      2D: <vx,vy>; <vx,vy>@(tx,ty); <1,2>@(3,4)
      3D: <vx,vy,vz>; <1,2,3>@(0,0,0)

    Meaning:
      - <vx,vy> is a vector from origin
      - <vx,vy>@(tx,ty) is vector with tail at (tx,ty)
    """
    vecs = []
    s = text.strip()
    if not s:
        return vecs

    parts = [p.strip() for p in s.split(";") if p.strip()]
    for item in parts:
        if "@(" in item:
            vpart, tpart = item.split("@", 1)
            tail_str = tpart.strip()
        else:
            vpart, tail_str = item, None

        vpart = vpart.strip()
        if not (vpart.startswith("<") and vpart.endswith(">")):
            raise ValueError(f"Vector must be like <a,b> or <a,b,c>. Got: {vpart}")
        inner = vpart[1:-1].strip()
        nums = [n.strip() for n in inner.split(",")]
        if len(nums) != dims:
            raise ValueError(f"Vector {vpart} must have {dims} numbers.")
        v = np.array([float(n) for n in nums], dtype=float)

        if tail_str:
            if not (tail_str.startswith("(") and tail_str.endswith(")")):
                raise ValueError(f"Tail must be like @(x,y) or @(x,y,z). Got: @{tail_str}")
            inner_t = tail_str[1:-1].strip()
            tnums = [n.strip() for n in inner_t.split(",")]
            if len(tnums) != dims:
                raise ValueError(f"Tail {tail_str} must have {dims} numbers.")
            tail = np.array([float(n) for n in tnums], dtype=float)
        else:
            tail = np.zeros(dims, dtype=float)

        vecs.append((tail, v))
    return vecs


# --------------------------
# GUI App
# --------------------------

class VectorVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SDL - 1 | Mini Vector Visualizer (2D/3D)")
        self.geometry("1100x700")

        self.mode = tk.StringVar(value="2D")

        # Controls frame
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        # Plot frame
        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Mode selector
        ttk.Label(left, text="Mode").pack(anchor="w")
        mode_box = ttk.Combobox(left, textvariable=self.mode, values=["2D", "3D"], state="readonly", width=6)
        mode_box.pack(anchor="w", pady=(0, 10))
        mode_box.bind("<<ComboboxSelected>>", lambda e: self._reset_axes())

        # Range controls
        ttk.Label(left, text="Plot Range").pack(anchor="w")
        range_row = ttk.Frame(left)
        range_row.pack(anchor="w", pady=(0, 10))

        self.range_min = tk.StringVar(value="-5")
        self.range_max = tk.StringVar(value="5")
        ttk.Entry(range_row, textvariable=self.range_min, width=6).pack(side=tk.LEFT)
        ttk.Label(range_row, text=" to ").pack(side=tk.LEFT)
        ttk.Entry(range_row, textvariable=self.range_max, width=6).pack(side=tk.LEFT)

        # Points input
        ttk.Label(left, text="Points (separate with ;)").pack(anchor="w")
        self.points_text = tk.Text(left, height=4, width=35)
        self.points_text.pack(anchor="w", pady=(0, 10))
        self.points_text.insert("1.0", "(1,2); (0,0); (-3,4)")

        # Vectors input
        ttk.Label(left, text="Vectors (separate with ;)").pack(anchor="w")
        ttk.Label(left, text="Format: <vx,vy> or <vx,vy>@(tx,ty)\n3D: <vx,vy,vz>@(tx,ty,tz)", foreground="#444").pack(anchor="w")
        self.vectors_text = tk.Text(left, height=5, width=35)
        self.vectors_text.pack(anchor="w", pady=(0, 10))
        self.vectors_text.insert("1.0", "<2,1>; <-1,2>@(1,1)")

        # Equation input
        ttk.Label(left, text="Equation (optional)").pack(anchor="w")
        ttk.Label(left, text="2D: y = f(x)  (or just f(x))\n3D: z = f(x,y) (or just f(x,y))", foreground="#444").pack(anchor="w")
        self.eq_var = tk.StringVar(value="x**2")
        ttk.Entry(left, textvariable=self.eq_var, width=35).pack(anchor="w", pady=(0, 10))

        # Buttons
        btn_row = ttk.Frame(left)
        btn_row.pack(anchor="w", pady=(5, 10))

        ttk.Button(btn_row, text="Render", command=self.render).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Clear", command=self.clear_plot).pack(side=tk.LEFT, padx=8)

        # Status
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(left, textvariable=self.status, foreground="#005").pack(anchor="w", pady=(10, 0))

        # Matplotlib figure/canvas
        self.fig = Figure(figsize=(7.5, 6), dpi=100)
        self.ax = None
        self._reset_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, right)
        toolbar.update()

    def _reset_axes(self):
        self.fig.clear()
        if self.mode.get() == "3D":
            self.ax = self.fig.add_subplot(111, projection="3d")
        else:
            self.ax = self.fig.add_subplot(111)
        self.ax.set_title(f"Vector Visualizer ({self.mode.get()})")
        self.ax.grid(True)
        self.canvas_draw_safe()

    def canvas_draw_safe(self):
        try:
            self.canvas.draw()
        except Exception:
            pass

    def clear_plot(self):
        self._reset_axes()
        self.status.set("Cleared.")

    def render(self):
        try:
            mode = self.mode.get()
            dims = 3 if mode == "3D" else 2

            rmin = float(self.range_min.get())
            rmax = float(self.range_max.get())
            if rmin >= rmax:
                raise ValueError("Range min must be less than range max.")

            # Clear & set axes
            self._reset_axes()

            # --- Points ---
            pts = parse_points(self.points_text.get("1.0", "end").strip(), dims)
            if pts.size:
                if dims == 2:
                    self.ax.scatter(pts[:, 0], pts[:, 1], s=35)
                    for i, (x, y) in enumerate(pts):
                        self.ax.text(x, y, f"P{i}", fontsize=9)
                else:
                    self.ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=35)
                    for i, (x, y, z) in enumerate(pts):
                        self.ax.text(x, y, z, f"P{i}", fontsize=9)

            # --- Vectors ---
            vecs = parse_vectors(self.vectors_text.get("1.0", "end").strip(), dims)
            for idx, (tail, v) in enumerate(vecs):
                if dims == 2:
                    self.ax.quiver(
                        tail[0], tail[1], v[0], v[1],
                        angles="xy", scale_units="xy", scale=1
                    )
                    self.ax.text(tail[0] + v[0], tail[1] + v[1], f"v{idx}", fontsize=9)
                else:
                    self.ax.quiver(
                        tail[0], tail[1], tail[2],
                        v[0], v[1], v[2],
                        length=1.0, normalize=False
                    )
                    self.ax.text(tail[0] + v[0], tail[1] + v[1], tail[2] + v[2], f"v{idx}", fontsize=9)

            # --- Equation ---
            eq_str = self.eq_var.get().strip()
            if eq_str:
                eq_str = eq_str.replace("y=", "").replace("z=", "").strip()

                if dims == 2:
                    x = sp.Symbol("x", real=True)
                    expr = _safe_sympy_expr(eq_str, {"x": x})
                    f = sp.lambdify(x, expr, "numpy")

                    xs = np.linspace(rmin, rmax, 600)
                    ys = f(xs)
                    self.ax.plot(xs, ys, linewidth=2)

                else:
                    x, y = sp.Symbol("x", real=True), sp.Symbol("y", real=True)
                    expr = _safe_sympy_expr(eq_str, {"x": x, "y": y})
                    f = sp.lambdify((x, y), expr, "numpy")

                    n = 80
                    xs = np.linspace(rmin, rmax, n)
                    ys = np.linspace(rmin, rmax, n)
                    X, Y = np.meshgrid(xs, ys)
                    Z = f(X, Y)
                    self.ax.plot_surface(X, Y, Z, alpha=0.6, rstride=1, cstride=1, linewidth=0)

            # --- Axis formatting ---
            if dims == 2:
                self.ax.set_xlim(rmin, rmax)
                self.ax.set_ylim(rmin, rmax)
                self.ax.set_aspect("equal", adjustable="box")
                self.ax.set_xlabel("x")
                self.ax.set_ylabel("y")
            else:
                self.ax.set_xlim(rmin, rmax)
                self.ax.set_ylim(rmin, rmax)
                self.ax.set_zlabel("z")
                self.ax.set_xlabel("x")
                self.ax.set_ylabel("y")

            self.status.set("Rendered.")
            self.canvas.draw()

        except Exception as e:
            self.status.set("Error.")
            messagebox.showerror("Render error", str(e))


if __name__ == "__main__":
    app = VectorVisualizerApp()
    app.mainloop()

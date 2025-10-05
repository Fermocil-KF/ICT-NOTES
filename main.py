"""
Browser-safe calculator for PyScript / Pyodide.

Expects HTML IDs:
- expression
- calc-btn
- output
"""
from js import document  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
import ast

def _eval_node(node):
    # Handle Expression root
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    # Binary operations
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Pow):
            return left ** right
        raise ValueError("Unsupported operator")

    # Unary operations
    if isinstance(node, ast.UnaryOp):
        val = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.USub):
            return -val
        raise ValueError("Unsupported unary operator")

    # Numeric constants (py3.8+: Constant, older: Num)
    if isinstance(node, ast.Constant):  # Python 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only int/float constants allowed")
    if isinstance(node, ast.Num):  # older AST node
        return node.n

    raise ValueError(f"Unsupported expression type: {type(node).__name__}")

def safe_eval(expr: str):
    """Parse and safely evaluate numeric arithmetic expressions."""
    parsed = ast.parse(expr, mode="eval")
    return _eval_node(parsed)

def calculate_expression(evt=None):
    """Evaluate expression from #expression and write to #output."""
    input_el = document.getElementById("expression")
    output_el = document.getElementById("output")
    if input_el is None or output_el is None:
        return

    expr = (input_el.value or "").strip()
    if not expr:
        output_el.innerText = "Please enter an expression."
        output_el.style.color = "red"
        return

    try:
        result = safe_eval(expr)
        # Normalize display of integers vs floats
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        output_el.innerHTML = f"Result: {result}<br>Type: {type(result).__name__}"
        output_el.style.color = "green"
    except Exception as e:
        output_el.innerText = f"Error: {e}"
        output_el.style.color = "red"

def _on_key(ev):
    if getattr(ev, "key", "") == "Enter":
        calculate_expression(ev)

# Keep proxy references to prevent garbage collection
_PROXIES = []

def setup(_evt=None):
    """Attach event listeners after DOM is ready."""
    btn = document.getElementById("calc-btn")
    if btn is not None:
        btn_proxy = create_proxy(calculate_expression)
        _PROXIES.append(btn_proxy)
        btn.addEventListener("click", btn_proxy)

    inp = document.getElementById("expression")
    if inp is not None:
        key_proxy = create_proxy(_on_key)
        _PROXIES.append(key_proxy)
        inp.addEventListener("keydown", key_proxy)

# If DOM not ready yet, wait for DOMContentLoaded; otherwise run setup now.
if getattr(document, "readyState", "") == "loading":
    dom_proxy = create_proxy(setup)
    _PROXIES.append(dom_proxy)
    document.addEventListener("DOMContentLoaded", dom_proxy)
else:
    setup()
from langchain_core.tools import tool
import ast
import operator
import math

# Safe math evaluator
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg
}

def eval_expr(expr):
    """Safe mathematical evaluation."""
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): # number constant
            return node.value
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return _SAFE_OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return _SAFE_OPERATORS[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(node)
    return _eval(ast.parse(expr, mode='eval').body)

@tool
def calculate_math(expression: str) -> str:
    """
    Evaluates a mathematical expression safely. 
    Use this for capital gains, percentages, or basic arithmetic.
    Example: '1000 * 0.15' or '(500 + 200) / 2'
    """
    try:
        result = eval_expr(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"

"""
Adapted from https://github.com/huggingface/smolagents/blob/main/src/smolagents/local_python_executor.py
"""


def evaluate_python_code(
    code: str,
    static_tools: dict,
    custom_tools: dict,
    state: dict,
    authorized_imports: list,
    max_print_outputs_length: int = 1000,
):
    """
    Evaluate Python code in a safe environment.

    Args:
        code (str): The Python code to evaluate.
        static_tools (dict): A dictionary of static tools to pass to the code.
        custom_tools (dict): A dictionary of custom tools to pass to the code.
        state (dict): A dictionary of state to pass to the code.
        authorized_imports (list): A list of authorized imports.
        max_print_outputs_length (int): The maximum length of print outputs.

    Returns:
        str: The output of the code.
        bool: Whether the output is a final answer.
    """
    # Imports
    import sys
    import io
    import contextlib

    # Redirect stdout
    stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Redirect stderr
    stderr = sys.stderr
    sys.stderr = io.StringIO()

    # Redirect print
    @contextlib.contextmanager
    def stdout_redirector(stream):
        sys.stdout = stream
        yield
        sys.stdout = stdout

    # Redirect print
    @contextlib.contextmanager
    def stderr_redirector(stream):
        sys.stderr = stream
        yield
        sys.stderr = stderr

    # Initialize
    output = ""
    is_final_answer = False

    # Execute code
    try:
        with stdout_redirector(sys.stdout), stderr_redirector(sys.stderr):
            exec(
                code,
                {
                    **static_tools,
                    **custom_tools,
                    **state,
                },
            )
    except Exception as e:
        output = str(e)
    else:
        output = sys.stdout.getvalue() + sys.stderr.getvalue()

    # Check if the output is a final answer
    if len(output) <= max_print_outputs_length:
        is_final_answer = True

    # Reset stdout
    sys.stdout = stdout

    # Reset stderr
    sys.stderr = stderr

    return output, is_final_answer


class PythonInterpreter:
    def __init__(self):
        pass

    def __call__(self):
        output, is_final_answer = evaluate_python_code(
            code_action,
            static_tools=self.static_tools,
            custom_tools=self.custom_tools,
            state=self.state,
            authorized_imports=self.authorized_imports,
            max_print_outputs_length=self.max_print_outputs_length,
        )

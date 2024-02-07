import sys
from io import StringIO


def helper_assert_and_print(expected_output: str, i: int, mock_stdout: StringIO) -> None:
    """
    Helper function to assert and print managers in tests.

    Args:
        expected_output (str): The expected managers string.
        i (int): The iteration count.
        mock_stdout (StringIO): The mocked stdout buffer.

    """
    # Check the buffer content after each switch
    buffer_lines = mock_stdout.getvalue().split('\r')
    if len(buffer_lines) > 1:
        # Get the last line; the first one is empty due to the split on \r
        actual_output = buffer_lines[-1]
        if expected_output.startswith('\r'):
            expected_output = expected_output[1:]
        assert actual_output == expected_output, f"\nExpected: {expected_output}\nActual:   {actual_output}"

    # Print the buffer content after each update for inspection
    # Using sys.__stdout__ to avoid the patch
    sys.__stdout__.write(f"After update {i + 1}:\n{mock_stdout.getvalue()}\n")
    sys.__stdout__.flush()

from typing import Iterable


def average(numbers: Iterable[float]) -> float:
    """Compute and return the average of a sequence of numbers.

    Args:
        numbers: An iterable of numeric values.

    Returns:
        The arithmetic mean of the provided numbers.

    Raises:
        ValueError: If the input iterable is empty.
    """
    numbers_list = list(numbers)
    if not numbers_list:
        raise ValueError("Cannot compute average of an empty list")
    return sum(numbers_list) / len(numbers_list)

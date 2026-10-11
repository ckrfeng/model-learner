"""Public hand-written reference solutions; controlled tests, no agent output."""

import bisect
import re
import statistics


def clamp(value, lower, upper):
    if lower > upper:
        raise ValueError
    return min(upper, max(lower, value))


def duration_seconds(text):
    match = re.fullmatch(r"([0-9]+)([smh])", text.strip())
    if match is None:
        raise ValueError
    return int(match[1]) * {"s": 1, "m": 60, "h": 3600}[match[2]]


def ceil_div(n, d):
    return -(-n // d)


def first_index(values, target):
    position = bisect.bisect_left(values, target)
    return position if position < len(values) and values[position] == target else -1


def interval_length(intervals):
    if any(start > end for start, end in intervals):
        raise ValueError
    total, boundary = 0, None
    for start, end in sorted(intervals):
        total += (
            max(0, end - max(start, boundary)) if boundary is not None else end - start
        )
        boundary = end if boundary is None else max(boundary, end)
    return total


def hex_integer(text):
    text = text.strip()
    if re.fullmatch(r"[+-]?(?:0[xX])?[0-9a-fA-F]+", text) is None:
        raise ValueError
    return int(text, 16)


def median(values):
    if not values:
        raise ValueError
    return statistics.median(values)


def edit_distance(a, b):
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (char_a != char_b),
                )
            )
        previous = current
    return previous[-1]


def components(n, edges):
    if n < 0:
        raise ValueError
    parents = list(range(n))

    def find(vertex):
        while parents[vertex] != vertex:
            vertex = parents[vertex]
        return vertex

    for a, b in edges:
        if not 0 <= a < n or not 0 <= b < n:
            raise ValueError
        parents[find(a)] = find(b)
    return len({find(vertex) for vertex in range(n)})


def unique_window(text):
    previous, start, best = {}, 0, 0
    for i, char in enumerate(text):
        start = max(start, previous.get(char, -1) + 1)
        previous[char] = i
        best = max(best, i - start + 1)
    return best


def rpn(tokens):
    stack = []
    for token in tokens:
        if token in ("+", "-", "*", "/"):
            if len(stack) < 2:
                raise ValueError
            b, a = stack.pop(), stack.pop()
            if token == "+":
                value = a + b
            elif token == "-":
                value = a - b
            elif token == "*":
                value = a * b
            else:
                value = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
            stack.append(value)
        else:
            if re.fullmatch(r"[+-]?[0-9]+", token) is None:
                raise ValueError
            stack.append(int(token))
    if len(stack) != 1:
        raise ValueError
    return stack[0]


def balanced_span(text):
    stack, best = [-1], 0
    for i, char in enumerate(text):
        if char == "(":
            stack.append(i)
        elif char == ")":
            stack.pop()
            if stack:
                best = max(best, i - stack[-1])
            else:
                stack.append(i)
        else:
            raise ValueError
    return best

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code for breaking ties in the heuristic solutions.

Author: Gertjan van den Burg
Copyright (c) 2018 - The Alan Turing Institute
License: See the LICENSE file.
Date: 2018-10-30

"""

from common.parser import parse_file
from common.utils import pairwise


def break_ties_two(data, A, B):
    """
    Break ties between dialects A and B.

    """
    if A.delimiter == B.delimiter and A.escapechar == B.escapechar:
        if A.quotechar == "" or B.quotechar == "":
            d_no = A if A.quotechar == "" else B
            d_yes = B if d_no == A else A

            X = parse_file(data, dialect=d_no)
            Y = parse_file(data, dialect=d_yes)

            if X == Y:
                # quotechar has no effect
                return d_no
            else:
                # quotechar has an effect
                return d_yes
    elif A.quotechar == B.quotechar and A.escapechar == B.escapechar:
        if sorted([A.delimiter, B.delimiter]) == sorted([",", " "]):
            # Artifact due to type detection (comma as radix point)
            if A.delimiter == ",":
                return A
            else:
                return B
        elif A.delimiter == "-" or B.delimiter == "-":
            # Artifact due to type detection (dash as minus sign)
            if A.delimiter == "-":
                return B
            else:
                return A
    elif A.delimiter == B.delimiter and A.quotechar == B.quotechar:
        Dnone, Descape = (A, B) if A.escapechar == "" else (B, A)

        X = parse_file(data, Dnone)
        Y = parse_file(data, Descape)

        # double check shape. Usually if the shape differs the pattern score
        # should have caught it, but if by a freakish occurance it hasn't then
        # we can't break this tie (for now)
        if len(X) != len(Y):
            return None
        for x, y in zip(X, Y):
            if len(x) != len(y):
                return None

        cells_escaped = []
        cells_unescaped = []
        for x, y in zip(X, Y):
            for u, v in zip(x, y):
                if u != v:
                    cells_unescaped.append(u)
                    cells_escaped.append(v)

        # We will break the ties in the following ways:
        #
        # If the escapechar precedes the quotechar an even number of times
        # within each offending cell, then we think it is a functional escape
        # and the escaped version is the correct dialect. Note that if an odd
        # number of escaped quotechars would occur, then the shape of the file
        # will be different if it is ignored. Only if it occurs an even number
        # of times within the cell can we get the same shape.
        for u in cells_unescaped:
            count = 0
            for a, b in pairwise(u):
                if a != Descape.escapechar:
                    continue
                if a == Descape.escapechar and b == Descape.quotechar:
                    count += 1
            if count > 0 and count % 2 == 0:
                return Descape
            else:
                return Dnone
    return None


def break_ties_three(data, A, B, C):
    # NOTE: We have only observed one tie for each case during development, so
    # this may need to be improved in the future.
    equal_delim = A.delimiter == B.delimiter == C.delimiter
    equal_escape = A.escapechar == B.escapechar == C.escapechar

    if equal_delim and equal_escape:
        # difference is *only* in quotechar
        dialects = [A, B, C]

        # TODO: shouldn't hardcode single/double quotes here.
        # try with type-only on: 
        # github/test_set/files/6367b9c5338b9a035a221cfffd928e92.csv
        d_none = next((d for d in dialects if d.quotechar == ""), None)
        d_single = next((d for d in dialects if d.quotechar == "'"), None)
        d_double = next((d for d in dialects if d.quotechar == '"'), None)

        # Added to fix above todo note, doesn't affect test results.
        if any((d is None for d in [d_none, d_single, d_double])):
            return None

        r_none = parse_file(data, d_none)
        r_single = parse_file(data, d_single)
        r_double = parse_file(data, d_double)

        if len(r_none) != len(r_single) or len(r_none) != len(r_double):
            return None

        if r_none == r_single:
            return break_ties_two(data, d_none, d_double)
        elif r_none == r_double:
            return break_ties_two(data, d_none, d_single)
    elif equal_delim:
        # difference is in quotechar *and* escapechar

        # NOTE: The reasoning here is as follows. If we are in this situation,
        # then there is both a potential escapechar and there are quotechars,
        # but the pattern score is the same and the type score can't make a
        # difference because no cells become clean if we interpret the
        # quote/escape correctly. This implies that the quote and escape do
        # have a function. Thus, we find the dialects that have a quote and
        # defer to break_ties_two.

        dialects = [A, B, C]
        with_quote = [d for d in dialects if d.quotechar != ""]

        if len(with_quote) != 2:
            return None

        return break_ties_two(data, with_quote[0], with_quote[1])

    return None


def break_ties_four(data, dialects):
    # NOTE: We have only observed one case during development where this
    # function was needed. It may need to be revisited in the future if other
    # examples are found.

    equal_delim = len(set([d.delimiter for d in dialects])) == 1
    if not equal_delim:
        return None

    # First, identify dialects that result in the same parsing result.
    equal_dialects = []
    for a, b in pairwise(dialects):
        X = parse_file(data, a)
        Y = parse_file(data, b)
        if X == Y:
            equal_dialects.append((a, b))

    # Try to break the ties in these pairs
    new_dialects = set()
    visited = set()
    for A, B in equal_dialects:
        ans = break_ties_two(data, A, B)
        if not ans is None:
            new_dialects.add(ans)
        visited.add(A)
        visited.add(B)
    for d in dialects:
        if not d in visited:
            new_dialects.add(d)

    dialects = list(new_dialects)

    # Defer to other functions if the number of dialects was reduced
    if len(dialects) == 2:
        return break_ties_two(data, *dialects)
    elif len(dialects) == 3:
        return break_ties_three(data, *dialects)

    return None


def break_ties(data, dialects):
    if len(dialects) == 2:
        return break_ties_two(data, dialects[0], dialects[1])
    elif len(dialects) == 3:
        return break_ties_three(data, dialects[0], dialects[1], dialects[2])
    elif len(dialects) == 4:
        return break_ties_four(data, dialects)
    return None

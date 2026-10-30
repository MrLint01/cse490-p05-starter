"""Four small helpers. One of them is wrong. test_utils.py will tell you which."""


def slugify(text):
    """'Hello, World!' -> 'hello-world': lowercase, words joined by single dashes,
    everything that is not a letter or digit dropped."""
    words = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    return "-".join(words)


def clamp(x, lo, hi):
    """x pinned into [lo, hi]: clamp(15, 0, 10) -> 10, clamp(-3, 0, 10) -> 0."""
    return max(lo, min(x, hi))


def median(nums):
    """The middle value of a non-empty list. For an even count, the mean of the
    two middle values: median([1, 2, 3, 4]) -> 2.5."""
    s = sorted(nums)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def is_palindrome(text):
    """True when the letters and digits read the same backwards, ignoring case,
    spaces and punctuation: 'A man, a plan, a canal: Panama' -> True."""
    core = [c.lower() for c in text if c.isalnum()]
    return core == core[::-1]

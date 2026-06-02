# 🍅 Tomato Standard Library

This document describes the built-in functions currently available in the Tomato interpreter.

## Quick summary

- Lists: `list`, `len`, `push`, `pop`, `get`, `set`
- Type/conversion: `type`, `str`, `num`

## Function reference

### `list(a, b, c, ...) -> list`

Creates a new list from its arguments.

Example:

```tomato
assign values = list(1, 2, 3);
print values;
```

---

### `len(value) -> number`

Returns the number of items in a list or characters in a string.

Example:

```tomato
assign values = [1, 2, 3];
print len(values);   // 3
print len("tomato"); // 6
```

---

### `push(listValue, item) -> list`

Appends `item` to `listValue` and returns the same list.

Example:

```tomato
assign values = [1, 2];
call push(values, 3);
print values; // [1, 2, 3]
```

---

### `pop(listValue) -> any`

Removes and returns the last item in a list.

Example:

```tomato
assign values = [1, 2, 3];
print pop(values); // 3
print values;      // [1, 2]
```

Notes:

- Errors when called on an empty list.

---

### `get(listValue, index) -> any`

Returns the list item at `index`.

Example:

```tomato
assign values = [10, 20, 30];
print get(values, 1); // 20
```

Notes:

- `index` is converted to a number.
- Errors when out of range.

---

### `set(listValue, index, item) -> list`

Sets `listValue[index] = item` and returns the list.

Example:

```tomato
assign values = [10, 20, 30];
call set(values, 0, 99);
print values; // [99, 20, 30]
```

Notes:

- `index` is converted to a number.
- Errors when out of range.

---

### `type(value) -> string`

Returns one of:

- `"null"`
- `"boolean"`
- `"number"`
- `"string"`
- `"list"`
- `"function"`
- `"builtin"`

Example:

```tomato
assign values = [1, 2, 3];
print type(values); // list
```

---

### `str(value) -> string`

Converts a value to string using Tomato conversion rules.

Notable behavior:

- number → alphabet form (`1 -> "a"`, `27 -> "aa"`)
- boolean → `"true"` or `"false"`
- null → `"null"`

Example:

```tomato
print str(27); // aa
```

---

### `num(value) -> number`

Converts a value to number using Tomato conversion rules.

Notable behavior:

- string alphabet form → number (`"aa" -> 27`)
- boolean → `1` or `0`
- null → `0`

Example:

```tomato
print num("zz");
```

## Full example

See `parser/examples/lists.tomato` for a runnable standard-library demo.

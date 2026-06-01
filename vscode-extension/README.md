# Tomato Language Support

Syntax highlighting support for the cursed **Tomato** programming language in Visual Studio Code.

Parser and interpreter implementations available at <https://github.com/magentapenugin/tomato>.

## Features

- `.tomato` file recognition
- Highlighting for Tomato keywords (`assign`, `print`, `input`, `where`, `loop`, `function`, etc.)
- Number, string, boolean, and null token highlighting
- Function declaration/call highlighting
- Bracket, quote, and comment configuration

## Example

```tomato
input "Enter your name: " into name;
assign values = [1, 2, 3];
call push(values, 4);
print "Hello", name, values;
```

## Release Notes

See [CHANGELOG.md](./CHANGELOG.md).

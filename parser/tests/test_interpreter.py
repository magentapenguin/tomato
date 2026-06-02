import io
import unittest

from parser.interpreter import interpret_source


class TomatoInterpreterTests(unittest.TestCase):
    def test_print_and_assignment(self) -> None:
        source = """
var x;
assign x = (5 + 3) * 2;
print x;
"""
        output = io.StringIO()
        interpret_source(source, output=output)

        self.assertEqual(output.getvalue(), "16.0\n")

    def test_number_assignment(self) -> None:
        source = """assign 4 = 10;
        print 4;"""
        output = io.StringIO()
        interpret_source(source, output=output)
        self.assertEqual(output.getvalue(), "10.0\n")

    def test_cursed_string_number_conversion(self) -> None:
        source = """
assign x = "a" + 1;
print x;
assign y = "aa" - 1;
print y;
"""
        output = io.StringIO()
        interpret_source(source, output=output)

        self.assertEqual(output.getvalue(), "aa\n26.0\n")

    def test_function_call_and_return(self) -> None:
        source = """
function add(a, b) {
  return a + b;
}
assign result = add(3, 4);
print result;
"""
        output = io.StringIO()
        interpret_source(source, output=output)

        self.assertEqual(output.getvalue(), "7.0\n")

    def test_input_statement(self) -> None:
        source = """
input "Enter your name: " into name;
print name;
"""
        output = io.StringIO()
        prompts: list[str] = []

        def fake_input(prompt: str) -> str:
            prompts.append(prompt)
            return "tomato"

        interpret_source(source, output=output, input_provider=fake_input)

        self.assertEqual(prompts, ["Enter your name: "])
        self.assertEqual(output.getvalue(), "tomato\n")

    def test_standard_library_list_helpers(self) -> None:
        source = """
assign values = [1, 2];
call push(values, 3);
print len(values);
print get(values, 1);
call set(values, 0, 99);
print pop(values);
print type(values);
print values;
"""
        output = io.StringIO()
        interpret_source(source, output=output)

        self.assertEqual(output.getvalue(), "3\n2\n3\nlist\n[99, 2]\n")

    def test_unset_cursed_number_assignment(self) -> None:
        source = """
assign 4 = 10;
print 4;
unset 4;
print 4;
"""
        output = io.StringIO()
        interpret_source(source, output=output)

        self.assertEqual(output.getvalue(), "10.0\n4\n")

    def test_unset_identifier(self) -> None:
        source = """
assign x = 7;
print x;
unset x;
assign x = 9;
print x;
"""
        output = io.StringIO()
        interpret_source(source, output=output)

        self.assertEqual(output.getvalue(), "7\n9\n")


if __name__ == "__main__":
    unittest.main()

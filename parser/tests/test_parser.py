import unittest

from parser.tomato_parser import parse_source


class TomatoParserTests(unittest.TestCase):
    def test_assign_to_anything(self) -> None:
        tree = parse_source("assign 5 = 10;")
        stmt = tree["body"][0]

        self.assertEqual(stmt["type"], "AssignStatement")
        self.assertEqual(stmt["target"]["type"], "NumberLiteral")
        self.assertEqual(stmt["target"]["value"], 5)
        self.assertEqual(stmt["value"]["value"], 10)
    
    def test_emoji_in_variable_names(self) -> None:
        tree = parse_source("var 🍅; assign 🍅 = 42;")
        decl_stmt = tree["body"][0]
        assign_stmt = tree["body"][1]

        self.assertEqual(decl_stmt["type"], "VarDeclaration")
        self.assertEqual(decl_stmt["name"], "🍅")

        self.assertEqual(assign_stmt["type"], "AssignStatement")
        self.assertEqual(assign_stmt["target"]["type"], "Identifier")
        self.assertEqual(assign_stmt["target"]["name"], "🍅")
        self.assertEqual(assign_stmt["value"]["type"], "NumberLiteral")
        self.assertEqual(assign_stmt["value"]["value"], 42)

    def test_function_and_call(self) -> None:
        source = """
function add(a, b) {
  return a + b;
}
call add(1, 2);
"""
        tree = parse_source(source)

        fn_stmt = tree["body"][0]
        call_stmt = tree["body"][1]

        self.assertEqual(fn_stmt["type"], "FunctionDeclaration")
        self.assertEqual(fn_stmt["name"], "add")
        self.assertEqual(fn_stmt["params"], ["a", "b"])

        self.assertEqual(call_stmt["type"], "CallStatement")
        self.assertEqual(call_stmt["call"]["callee"], "add")
        self.assertEqual(len(call_stmt["call"]["args"]), 2)

    def test_input_and_list_syntax(self) -> None:
        source = """
input "Name? " into name;
assign a = [1, 2, 3];
assign b = list(4, 5);
"""
        tree = parse_source(source)

        input_stmt = tree["body"][0]
        list_literal_stmt = tree["body"][1]
        list_keyword_stmt = tree["body"][2]

        self.assertEqual(input_stmt["type"], "InputStatement")
        self.assertEqual(input_stmt["name"], "name")

        self.assertEqual(list_literal_stmt["type"], "AssignStatement")
        self.assertEqual(list_literal_stmt["value"]["type"], "ListLiteral")
        self.assertEqual(len(list_literal_stmt["value"]["elements"]), 3)

        self.assertEqual(list_keyword_stmt["type"], "AssignStatement")
        self.assertEqual(list_keyword_stmt["value"]["type"], "ListLiteral")
        self.assertEqual(len(list_keyword_stmt["value"]["elements"]), 2)


if __name__ == "__main__":
    unittest.main()

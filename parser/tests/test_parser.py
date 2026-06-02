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

    def test_function_declaration_to_anything(self) -> None:
        tree = parse_source("function 5(a, b) { return a + b; }")
        stmt = tree["body"][0]

        self.assertEqual(stmt["type"], "FunctionDeclaration")
        self.assertEqual(stmt["name"], "5")
        self.assertEqual(stmt["params"], ["a", "b"])

    def test_export_and_import_alias_syntax(self) -> None:
        source = """
export function add(a, b) { return a + b; }
import "utils.tomato" as stuff;
    call stuff.add(1, 2);
"""
        tree = parse_source(source)
        export_stmt = tree["body"][0]
        import_stmt = tree["body"][1]
        call_stmt = tree["body"][2]

        self.assertEqual(export_stmt["type"], "ExportStatement")
        self.assertEqual(export_stmt["statement"]["type"], "FunctionDeclaration")
        self.assertEqual(export_stmt["statement"]["name"], "add")

        self.assertEqual(import_stmt["type"], "ImportStatement")
        self.assertEqual(import_stmt["path"], "utils.tomato")
        self.assertEqual(import_stmt["alias"], "stuff")

        self.assertEqual(call_stmt["type"], "CallStatement")
        self.assertEqual(call_stmt["call"]["callee"], "stuff.add")

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

    def test_unset_syntax(self) -> None:
        source = """
assign 4 = 10;
unset 4;
var x;
unset x;
"""
        tree = parse_source(source)

        self.assertEqual(tree["body"][1]["type"], "UnsetStatement")
        self.assertEqual(tree["body"][1]["target"]["type"], "NumberLiteral")
        self.assertEqual(tree["body"][3]["type"], "UnsetStatement")
        self.assertEqual(tree["body"][3]["target"]["type"], "Identifier")


if __name__ == "__main__":
    unittest.main()

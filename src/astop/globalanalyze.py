
import ast

class GlobalAnalyzeVisitor(ast.NodeVisitor):
    def visit(self, node):
        super(GlobalAnalyzeVisitor, self).visit(node)
        self.generic_visit(node)
        # self.analyze(node)

    def visit_Module(self, mod):
        print 'Module', ast.dump(mod)

    def visit_FunctionDef(self, func):
        print 'Function', ast.dump(func)

    def visit_ClassDef(self, cls):
        print 'Class', ast.dump(cls)

    def analyze(self, node):
        print 'analyzing', ast.dump(node)


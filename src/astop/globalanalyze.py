
import ast
import namescope

# class GlobalAnalyzeVisitor(ast.NodeVisitor):
#     def __init__(self):
#         super(GlobalAnalyzeVisitor, self).__init__()
#         self.currentScope = namescope.builtinsNameScope
#
#     def visit(self, node):
#         if isinstance(node, ast.Module):
#             self.currentScope = namescope.newGlobalNameScope()
#         elif isinstance(node, ast.ClassDef):
#             self.currentScope = namescope.NameScope(self.currentScope)
#         elif isinstance(node, ast.FunctionDef):
#             self.currentScope = namescope.NameScope(self.currentScope)
#
#         super(GlobalAnalyzeVisitor, self).visit(node)
#
#         if isinstance(node, ast.Module):
#             self.currentScope = self.currentScope.parent
#         elif isinstance(node, ast.ClassDef):
#             self.currentScope = self.currentScope.parent
#         elif isinstance(node, ast.FunctionDef):
#             self.currentScope = self.currentScope.parent
#
#     def visit_Module(self, mod):
#         print 'Module',  self.currentScope.names
#
#     def visit_FunctionDef(self, func):
#         print 'Function', ast.dump(func)
#
#     def visit_ClassDef(self, cls):
#         print 'Class', ast.dump(cls)
#
#     def analyze(self, node):
#         print 'analyzing', ast.dump(node)
#

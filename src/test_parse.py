
source = """

a = u'abc'


"""

import ast
mod = ast.parse(source, '<string>')
print `mod.body[0].value.s`
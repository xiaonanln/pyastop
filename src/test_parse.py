
source = """

quality += 1

"""

import ast
mod = ast.parse(source, '<string>')
print `mod.body[0].target.ctx`
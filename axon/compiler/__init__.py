# AXON Compiler — Front-end pipeline + IR generation
# Source → Tokens → AST → Type-Checked AST → AXON IR

from .lexer import Lexer
from .parser import Parser
from .type_checker import TypeChecker
from .ir_generator import IRGenerator
from .ir_nodes import IRProgram

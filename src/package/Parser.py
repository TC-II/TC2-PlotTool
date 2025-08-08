import sympy as sym
from sympy import Symbol, S, oo
import re

s = sym.symbols('s')

def safe_sympify(txt):
    # Insert a '*' between a number and a letter (e.g., "2s" -> "2*s")
    txt = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', txt)
    return sym.sympify(txt)

#Puntaje asignado a la complejidad para la simplificación de sympy
def determinar_complejidad(expr):
    DIV = Symbol('/')
    count = sym.count_ops(expr, visual=True).subs(DIV, 100000) #penalizo fuertemente las divisiones
    count = count.replace(Symbol, type(S.One)) #A todo lo demás le doy un 1
    return count

class ExprParser():
    def __init__(self, txt='', expr = None, *args):
      self.symEx = None
      self.fractionEx = None
      self.txt = ''
      if txt != '':
        self.setTxt(txt)
      if expr != None:
        self.setExpression(expr)

    def applyFactor(self, factor):
      symEx = symEx * factor
      # self.simplify()

    def setTxt(self, txt):
      self.txt = txt
      self.symEx = sym.parsing.sympy_parser.parse_expr(txt, transformations = 'all')
      self.simplify()

    def setExpression(self, expr):
      self.symEx = expr
      self.simplify()

    def simplify(self):
      self.symEx = sym.cancel(self.symEx) # sym.simplify(self.symEx, ratio=oo, measure=determinar_complejidad)
      self.fractionEx = sym.fraction(self.symEx)

    def transform(self, transformation):
      self.symEx = self.symEx.subs(s, transformation)
      self.simplify()

    def getND(self):
      N = sym.Poly(self.fractionEx[0].evalf()).all_coeffs() if (s in self.fractionEx[0].free_symbols) else [self.fractionEx[0].evalf()]
      D = sym.Poly(self.fractionEx[1].evalf()).all_coeffs() if (s in self.fractionEx[1].free_symbols) else [self.fractionEx[1].evalf()]
      return N, D

    def getLatex(self, txt=None):
      if not txt:
        return sym.latex(safe_sympify(self.txt))
      else:
        return sym.latex(safe_sympify(txt))
      
    def getSympyfied(self, txt=None):
      if not txt:
        return safe_sympify(self.txt)
      else:
        return safe_sympify(txt)
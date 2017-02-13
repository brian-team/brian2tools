from brian2.parsing.rendering import NodeRenderer

class LEMSRenderer(NodeRenderer):
    expression_ops = NodeRenderer.expression_ops.copy()
    expression_ops.update({
          # BinOp
          'Pow': '^',
          # ??? 'Mod': '%', 
          # Compare
          'Lt': '.lt.',
          'LtE': '.le.',
          'Gt': '.gt.',
          'GtE': '.ge.',
          'Eq': '.eq.',
          'NotEq': '.ne.',
          # Unary ops
          'Not': '.not.',
          # Bool ops
          'And': '.and.',
          'Or': '.or.'
          })

    # all function names supported by LEMS (from jLEMS Parser)
    lems_functions = ('sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
                      'exp', 'sqrt', 'ceil', 'sum', 'factorial', 'abs',
                      'product', 'ln', 'log', 'random' 'H')

    # functions supported by LEMS and Brian2 but with different names:
    brian2lems_func = {'log': 'ln',
                       'log10': 'log',
                       'rand': 'random',
                       'sign': 'H'}

    def render_func(self, node):
        if node.id in self.lems_functions:
            return node.id
        elif node.id in self.brian2lems_func:
            return self.brian2lems_func[node.id]
        else:
            raise ValueError("Function {} not supported".format(node.id))

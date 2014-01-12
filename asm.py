import tokenize, StringIO, token, parser, symbol, compiler, ast, astpp, sys
#s = "var = 1 + 2 + 3\nvar2 = var - 4\nif var2 == 2:\n\tvar3 = True"
#s = "20 - 4 >= 2 + 9 + 10"
#s = "1 and 2 and 0 or 4"

s = sys.argv[1]
#print s

labels = {
    "and":  0,
    "or":   0,
}

AND = """
clc
adc #0
beq and_{0}
pla
jmp and_2_{0}
and_{0}:
tsx
inx
txs
and_2_{0}:
"""

OR = """
clc
adc #0
bne or_{0}
pla
jmp or_2_{0}
or_{0}:
tsx
inx
txs
or_2_{0}:
"""

class ASTPrinter(ast.NodeVisitor):
    def __init__(self):
        self.op = "null"
        super(ASTPrinter, self).__init__()

    def generic_visit(self, node):
        print node
        super(ASTPrinter, self).generic_visit(node)


    def _do_op(self, op, n):
        if op == "lda":
            print "lda %s" % n

        elif op == "add":
            print "adc %s" % n
        elif op == "sub":
            print "sec\nsbc %s" % n

        elif op == "gt":
            print "sbc %s" % n
        elif op == "gte":
            print "sec\nsbc %s" % n

        elif op == "and":
            # A and B = 0 if A or B is 0 else B
            # 1 and 2 = 2
            # 0 and 2 = 0
            # 1 and 0 = 0
            # A is the value in the accumulator and B is the value on top of
            # the stack.
            print AND.format(labels["and"])
            labels["and"] += 1
        elif op == "or":
            # A or B = 0 if A and B is 0 else A
            # 1 or 2 = 1
            # 0 or 2 = 2
            # 1 or 0 = 1
            # A is the value in the accumulator and B is the value on top of
            # the stack.
            print OR.format(labels["or"])
            labels["or"] += 1
        else:
            print op

    def _set_op(self, op):
        if type(op) == str:
            self.op = op

        elif type(op) == ast.Add:
            self.op = "add"
        elif type(op) == ast.Sub:
            self.op = "sub"

        elif type(op) == ast.Gt:
            self.op = "gt"
        elif type(op) == ast.GtE:
            self.op = "gte"

        elif type(op) == ast.And:
            self.op = "and"
        elif type(op) == ast.Or:
            self.op = "or"

        else:
            print op

    def visit_BinOp(self, node):
        self.op = "lda"
        super(ASTPrinter, self).visit(node.right)
        print "pha"

        self._set_op("lda")
        super(ASTPrinter, self).visit(node.left)

        self._set_op(node.op)
        print "tsx\ninx\ntxs"
        self._do_op(self.op, "$0100,X")

    def visit_BoolOp(self, node):
        """
            Resolve 'and' and 'or' expressions.
            each value is computing in reverse order and then combined.
        """

        #Load first value
        self.op = "lda"
        super(ASTPrinter, self).visit(node.values[-1])
        print "pha"

        for i in range(len(node.values)-2, -1, -1):
            #Compute the next value, leaving it in A
            self.op = "lda"
            super(ASTPrinter, self).visit(node.values[i])

            #Combine the two values and store on the stack
            self._set_op(node.op)
            self._do_op(self.op, "STACK")

            #Don't need to store if it's the last one
            if i > 0:
                print "pha"

    def visit_Num(self, node):
        self._do_op(self.op, "#%s" % node.n)

    def visit_Name(self, node):
        self._do_op(self.op, node.id)

    def visit_Assign(self, node):
        super(ASTPrinter, self).visit(node.value)
        print "sta %s" % node.targets[0].id

    def visit_If(self, node):
        print node
        print dir(node)
        print node.test
        print node.body
        print node.orelse


    def visit_Compare(self, node):
        # Compute right branch and store it on the stack
        self.op = "lda"
        super(ASTPrinter, self).visit(node.comparators[0])
        print "pha"

        #print "tsx"
        #self._set_op(node.ops[0])

        #Compute left branch
        self.op = "lda"
        super(ASTPrinter, self).visit(node.left)

        #Do op
        print "tsx\ninx"
        self._set_op(node.ops[0])
        self._do_op(self.op, "$0100,X")

        #STUFF HERE
       
        print node
        print dir(node)
        #print node.left.n
        print node.ops
        #print node.comparators[0].n
        print node.comparators[0]

print s
ap = ASTPrinter()
t = ast.parse(s)
ap.visit(t)

#print astpp.dump(t)
print astpp.dump(t, False)

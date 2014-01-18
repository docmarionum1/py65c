import tokenize, StringIO, token, parser, symbol, compiler, ast, astpp, sys
#s = "var = 1 + 2 + 3\nvar2 = var - 4\nif var2 == 2:\n\tvar3 = True"
#s = "20 - 4 >= 2 + 9 + 10"
#s = "1 and 2 and 0 or 4"

s = sys.argv[1]

try:
    with open(sys.argv[1], 'r') as f:
        s = f.read()
except:
    s = sys.argv[1]
#print s

labels = {
    "and":      0,
    "or":       0,
    "if":       0,
    "while":    0,
    "gt":       0,
    "gte":      0,
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

GT = """
clc
sbc {0}
lda #0
bcc end_gt_{1}
adc #0
end_gt_{1}:
"""

GTE = """
sec
sbc {0}
lda #0
bcc end_gte_{1}
adc #0
end_gte_{1}:
"""


class ASTPrinter(ast.NodeVisitor):
    def __init__(self, debug=False):
        self.op = "null"
        self.heap = {"True": 1, "False": 0}
        self.heap_pointer = 0x200
        self.debug = debug
        super(ASTPrinter, self).__init__()

    def generic_visit(self, node):
        print node
        super(ASTPrinter, self).generic_visit(node)

    def visit(self, node):
        if self.debug:
            print "node:", node
            print "dir(node):", dir(node)
            for a in ["test", "body", "orelse", "targets", "value", "ops", "comparators"]:
                if hasattr(node, a):
                    print "%s:" % a, getattr(node, a)

        super(ASTPrinter, self).visit(node)

    def _do_op(self, op, n):
        if op == "lda":
            print "lda %s" % n
        elif op == "sta":
            print "sta %s" % n

        elif op == "add":
            print "clc\nadc %s" % n
        elif op == "sub":
            print "sec\nsbc %s" % n

        elif op == "gt":
            print GT.format(n, labels["gt"])
            labels["gt"] += 1
        elif op == "gte":
            print GTE.format(n, labels["gte"])
            labels["gte"] += 1

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

    def _addr(self, name):
        if name not in self.heap:
            self.heap[name] = self.heap_pointer
            self.heap_pointer += 1

        return "$%s" % hex(self.heap[name])[2:]

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
        if node.id == "True":
            v = "#1"
        elif node.id == "False":
            v = "#0"
        else:
            v = self._addr(node.id)

        self._do_op(self.op, v)

    def visit_Assign(self, node):
        self._set_op("lda")
        super(ASTPrinter, self).visit(node.value)
        self._set_op("sta")
        super(ASTPrinter, self).visit(node.targets[0])

    def visit_If(self, node):
        self._set_op("lda")
        super(ASTPrinter, self).visit(node.test)
        label = "if_not_%s" % labels["if"]
        label_2 = "end_if_%s" % labels["if"]
        labels["if"] += 1
        print "clc\nadc #0\nbeq %s" % label

        for n in node.body:
            super(ASTPrinter, self).visit(n)

        if node.orelse:
            print "jmp %s\n%s:" % (label_2, label)

            for n in node.orelse:
                super(ASTPrinter, self).visit(n)
            print "%s:" % label_2

    def visit_While(self, node):
        print "while_{0}:".format(labels["while"])
        self._set_op("lda")
        super(ASTPrinter, self).visit(node.test)
        print "clc\nadc #0\nbeq end_while_{0}".format(labels["while"])

        for n in node.body:
            super(ASTPrinter, self).visit(n)

        print "jmp while_{0}\nend_while_{0}:".format(labels["while"])

        labels["while"] += 1


    def visit_Compare(self, node):
        # Compute right branch and store it on the stack
        self.op = "lda"
        super(ASTPrinter, self).visit(node.comparators[0])
        print "pha"

        #Compute left branch
        self.op = "lda"
        super(ASTPrinter, self).visit(node.left)

        #Do op
        print "tsx\ninx"
        self._set_op(node.ops[0])
        self._do_op(self.op, "$0100,X")

print s
ap = ASTPrinter(False)
t = ast.parse(s)
ap.visit(t)

#print astpp.dump(t)
print astpp.dump(t, False)

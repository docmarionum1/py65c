import tokenize, StringIO, token, parser, symbol, compiler, ast, astpp, sys, random, string

from py65asm.assembler import Assembler
from py65emu.mmu import MMU
from symbols import SymbolTable

labels = {
    "and":      0,
    "or":       0,
    "if":       0,
    "while":    0,
    "gt":       0,
    "gte":      0,
    "lt":       0,
    "lte":      0,
    "mult":     0
}

AND = """
clc
adc #0
beq and_{1}
lda {0}
and_{1}:
"""

OR = """
clc
adc #0
bne or_{1}
lda {0}
or_{1}:
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

LT = """
sec
sbc {0}
clc
bpl end_lt_{1}
sec
end_lt_{1}:
lda #0
adc #0
"""

LTE = """
clc
sbc {0}
clc
bpl end_lte_{1}
sec
end_lte_{1}:
lda #0
adc #0
"""

MULT = """
tay
beq mult_zero_{1}
lda #0
clc
mult_{1}:
adc {0}
dey
bne mult_{1}
beq mult_not_zero_{1}
mult_zero_{1}:
lda #0
mult_not_zero_{1}
"""



class Compiler(ast.NodeVisitor):
    def __init__(self, mmu=None, debug=False):
        """
            mmu used for allocating memory to variables.  The MMU should
            be representative of the target device.
        """
        self.op = "null"
        self.debug = debug
        self.output = []
        self.output_end = []

        if mmu:
            self.mmu = mmu
        else:
            self.mmu = MMU([(0, 0x1000)])

        self.symbol_table = SymbolTable()
        self.symbol_table.put('True', {'addr': None, 'value': True})
        self.symbol_table.put('False', {'addr': None, 'value': False})

        super(Compiler, self).__init__()

    def generic_visit(self, node):
        #print node
        super(Compiler, self).generic_visit(node)

    def visit(self, node):
        if self.debug:
            print "node:", node
            print "dir(node):", dir(node)
            for a in ["test", "body", "orelse", "targets", "value", "ops", "comparators", "ctx", "elts"]:
                if hasattr(node, a):
                    print "%s:" % a, getattr(node, a)

        super(Compiler, self).visit(node)

    def _do_op(self, op, n):
        if op == "lda":
            self.output.append("lda %s" % n)
        elif op == "sta":
            self.output.append("sta %s" % n)

        elif op == "add":
            self.output.append("clc\nadc %s" % n)
        elif op == "sub":
            self.output.append("sec\nsbc %s" % n)

        elif op == "mult":
            self.output.append(MULT.format(n, labels["mult"]))
            labels["mult"] += 1

        elif op == "gt":
            self.output.append(GT.format(n, labels["gt"]))
            labels["gt"] += 1
        elif op == "gte":
            self.output.append(GTE.format(n, labels["gte"]))
            labels["gte"] += 1

        elif op == "lt":
            self.output.append(LT.format(n, labels["lt"]))
            labels["lt"] += 1
        elif op == "lte":
            self.output.append(LTE.format(n, labels["lte"]))
            labels["lte"] += 1

        elif op == "and":
            # A and B = 0 if A or B is 0 else B
            # 1 and 2 = 2
            # 0 and 2 = 0
            # 1 and 0 = 0
            # A is the value in the accumulator and B is the value on top of
            # the stack.
            self.output.append(AND.format(n, labels["and"]))
            labels["and"] += 1
        elif op == "or":
            # A or B = 0 if A and B is 0 else A
            # 1 or 2 = 1
            # 0 or 2 = 2
            # 1 or 0 = 1
            # A is the value in the accumulator and B is the value on top of
            # the stack.
            self.output.append(OR.format(n, labels["or"]))
            labels["or"] += 1
        else: #debug
            print op

    def _set_op(self, op):
        if type(op) == str:
            self.op = op

        elif type(op) == ast.Add:
            self.op = "add"
        elif type(op) == ast.Sub:
            self.op = "sub"

        elif type(op) == ast.Mult:
            self.op = "mult"

        elif type(op) == ast.Gt:
            self.op = "gt"
        elif type(op) == ast.GtE:
            self.op = "gte"

        elif type(op) == ast.Lt:
            self.op = "lt"
        elif type(op) == ast.LtE:
            self.op = "lte"

        elif type(op) == ast.And:
            self.op = "and"
        elif type(op) == ast.Or:
            self.op = "or"

        else:
            print op

        return self.op

    def _malloc(self, size=1, location="zero_page"):
        if location == "zero_page":
            start = 0x0
        elif location == "stack":
            start = 0x100
        else:
            start = 0x200

        count = 0
        for i in range(start, 0x10000):
            try:
                if not self.mmu.read(i):
                    count += 1
                else:
                    count = 0
            except:
                count = 0

            if count == size:
                for j in range(i - count + 1, i - count + size + 1):
                    self.mmu.write(j, 1)
                return i - count + 1

        raise Exception("Out of memory")


    def _free(self, location, size=1):
        if type(location) == int:
            for i in range(size):
                self.mmu.write(location+i, 0)

    def _freeVar(self, name, size=1):
        a = self.symbol_table.getAddr(name)
        if type(location) == int:
            self._free(a, size)

    def _addr(self, name=None, location="heap"):
        if not name:
            name = self._id()
        if not self.symbol_table.getLocal(name):
            if self.symbol_table.scopeIsGlobal():
                a = self._malloc(location=location)
            else:
                a = '$01%0*x,X' % (2, 3+self.symbol_table.numNonGlobalVars())


            self.symbol_table.put(name, {'addr': a})

        return self.symbol_table.getAddr(name)

    def _id(self, size=32, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def visit_BinOp(self, node):
        self._set_op("lda")
        super(Compiler, self).visit(node.right)
        a = self._addr(name=str(hash(node)), location="zero_page")
        self._do_op("sta", a)

        self._set_op("lda")
        super(Compiler, self).visit(node.left)

        self._set_op(node.op)
        self._do_op(self.op, a)
        self._free(a)

    def visit_BoolOp(self, node):
        """
            Resolve 'and' and 'or' expressions.
            each value is computing in reverse order and then combined.
        """

        #Load first value
        self.op = "lda"
        super(Compiler, self).visit(node.values[-1])
        a = self._addr(name=str(hash(node)), location="zero_page")
        self._do_op("sta", a)

        for i in range(len(node.values)-2, -1, -1):
            #Compute the next value, leaving it in A
            self.op = "lda"
            super(Compiler, self).visit(node.values[i])

            #Combine the two values and store on the stack
            self._set_op(node.op)
            self._do_op(self.op, a)

            #Don't need to store if it's the last one
            if i > 0:
                #self.output.append("pha")
                self._do_op("sta", a)

        self._free(a)

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

    def visit_List(self, node):
        a = self._malloc(len(node.elts), location="heap")
        for i in range(len(node.elts)):
            self._set_op("lda")
            super(Compiler, self).visit(node.elts[i])
            self.output.append("sta ${0}".format(hex(a + i)[2:]))
        return a, len(node.elts)

    def visit_Subscript(self, node):
        self.output.append("pha")
        self._set_op("lda")
        super(Compiler, self).visit(node.slice)
        self.output.append("tay")
        self.output.append("pla")

        if type(node.ctx) == ast.Load:
            self.output.append("lda ({0}),y".format(self._addr(node.value.id)))
        elif type(node.ctx) == ast.Store:
            self.output.append("sta ({0}),y".format(self._addr(node.value.id)))
            

    def visit_Assign(self, node):
        if type(node.value) == ast.List:
            a = self._malloc(2)
            h, l = super(Compiler, self).visit(node.value)
            self._do_op("lda", "#{0}".format(h & 0xff))
            self._do_op("sta", a)
            self._do_op("lda", "#{0}".format(h >> 8))
            self._do_op("sta", a + 1)
            self.symbol_table.put(node.targets[0].id, {'addr': a, 'list_addr': h, 'len': l})
        else:
            self._set_op("lda")
            super(Compiler, self).visit(node.value)
            self._set_op("sta")
            super(Compiler, self).visit(node.targets[0])

    def visit_If(self, node):
        self._set_op("lda")
        super(Compiler, self).visit(node.test)
        label = "if_not_%s" % labels["if"]
        label_2 = "end_if_%s" % labels["if"]
        labels["if"] += 1
        self.output.append("clc\nadc #0\nbeq %s" % label)

        for n in node.body:
            super(Compiler, self).visit(n)

        if node.orelse:
            self.output.append("jmp %s\n%s:" % (label_2, label))

            for n in node.orelse:
                super(Compiler, self).visit(n)
            self.output.append("%s:" % label_2)
        else:
            self.output.append("%s:" % label)

    def visit_While(self, node):
        self.output.append("while_{0}:".format(labels["while"]))
        self._set_op("lda")
        super(Compiler, self).visit(node.test)
        self.output.append("clc\nadc #0\nbne while_body_{0}\njmp end_while_{0}\nwhile_body_{0}:".format(labels["while"]))

        for n in node.body:
            super(Compiler, self).visit(n)

        self.output.append("jmp while_{0}\nend_while_{0}:".format(labels["while"]))

        labels["while"] += 1


    def visit_Compare(self, node):
        # Compute right branch and store it on the stack
        self.op = "lda"
        super(Compiler, self).visit(node.comparators[0])
        a = self._addr(name=str(hash(node)), location="zero_page")
        self._do_op("sta", a)

        #Compute left branch
        self.op = "lda"
        super(Compiler, self).visit(node.left)

        #Do op
        self._set_op(node.ops[0])
        self._do_op(self.op, a)
        self._free(a)

    def visit_FunctionDef(self, node):
        # Create a placeholder for the function definition in the outer scope.
        self.symbol_table.put(node.name, {"PROCESSING": True})

        # Create new scope for function
        self.symbol_table.push()

        # Process the arguments to create local variables for them and store defaults.
        args_dict = {}
        args_list = []
        for i in range(len(node.args.args)):
            arg = {'i': i, 'name': node.args.args[i].id}

            if (len(node.args.args) - i) <= len(node.args.defaults):
                arg['default'] = node.args.defaults[i + len(node.args.defaults) - len(node.args.args)]
            else:
                arg['default'] = None

            args_dict[node.args.args[i].id] = arg
            args_list.append(arg)

            #register stack location on symtable
            self._addr(node.args.args[i].id)


        # Process the function body and store the output at the end.
        temp = self.output
        self.output = self.output_end

        self.output.append(node.name + ":")
        self.output.append("tsx")
        for n in node.body:
            super(Compiler, self).visit(n)

        self.output = temp

        # Update the function definition
        num_locals = self.symbol_table.numLocalVars() - len(args_list)
        self.symbol_table.set(node.name, 
            {'addr': node.name, 'args': [args_list, args_dict], 'num_locals': num_locals})

        #Check for Recursive Calls
        while True:
            try:
                i = self.output_end.index("RECURSION_%s" % node.name)
                temp = self.output
                self.output = []
                super(Compiler, self).visit(self.output_end[i+1])
                self.output_end = self.output_end[:i] + self.output + self.output_end[i+2:]
                self.output = temp
            except:
                break

        # Resolve Return Addresses
        a = self._addr("return_value")
        for i in range(len(self.output_end)):
            self.output_end[i] = self.output_end[i].replace('return_value', a)


        self.symbol_table.pop()
        

    def visit_Return(self, node):
        super(Compiler, self).visit(node.value)
        self.output.append("sta %s" % "return_value")
        self.output.append("rts")

    def visit_Call(self, node):
        #Check if this is a recursive call
        if "PROCESSING" in self.symbol_table.get(node.func.id):
            #Put a placeholder for the call.
            self.output.append("RECURSION_%s" % node.func.id)
            self.output.append(node)

            #Allocate space for locals in the call arguments
            temp = self.output
            self.output = []
            for i in range(len(node.args)):
                super(Compiler, self).visit(node.args[i])
            self.output = temp
            return

        #Allocate space for return value and local variables
        for i in range(self.symbol_table.get(node.func.id)['num_locals'] + 1):
            self.output.append("pha")

        #Push args onto stack
        keywords = dict([(i.arg, i.value) for i in node.keywords])
        defaults = self.symbol_table.get(node.func.id)['args']

        for i in range(len(defaults[0]) - 1, -1, -1):
            if i < len(node.args):
                super(Compiler, self).visit(node.args[i])
            elif defaults[0][i]['name'] in keywords:
                super(Compiler, self).visit(keywords[defaults[0][i]['name']])
            else:
                super(Compiler, self).visit(defaults[0][i]['default'])
                
            self.output.append("pha")

        #Call function
        self.output.append("jsr %s" % node.func.id)

        #Pull off all arguments and the return value
        self.output.append("tsx")
        for i in range(len(defaults[0])+self.symbol_table.get(node.func.id)['num_locals']):
            self.output.append("inx")
        self.output.append("txs")
        self.output.append("pla")
        self.output.append("tsx")



def compile(inp, debug=True, org=0x1000):
    print inp, type(inp)
    if type(inp) == file:
        s = inp.read()
    elif type(inp) == str:
        try:
            with open(inp, 'r') as f:
                s = f.read()
        except:
            s = inp

    c = Compiler(debug=debug)
    t = ast.parse(s)
    c.visit(t)

    if debug:
        print s
        print astpp.dump(t, False)

    asm = "\n".join(c.output) + "\nbrk\n" + "\n".join(c.output_end)
    print "**********\n", asm
    a = Assembler(org=org)
    bin = a.assemble(asm)
    return bin


if __name__ == "__main__":
    compile(sys.argv[1])

class scope:
    def __init__(self, subscope):
        self.subscope = subscope
        self.curscope = {}
        self.localVarLoc = 0

    def get(self, var):
        if var in self.curscope:
            return self.curscope[var]
        else:
            if self.subscope:
                v = self.subscope.get(var)
                if v:
                    return v

    def getLocal(self, var):
        if var in self.curscope:
            return self.curscope[var]

    def set(self, var, value):
        if var in self.curscope:
            self.curscope[var] = value
            return True
        else:
            if self.subscope:
                return self.subscope.set(var, value)
            else:
                return False
    
    def put(self, var, val):
        self.curscope[var] = val

    def delete(self, var):
        del self.curscope[var]

    def pop(self):
        return self.subscope

    def numNonGlobalVars(self):
        if self.subscope:
            return len(self.curscope) + self.subscope.numNonGlobalVars()
        else:
            return 0

    def numLocalVars(self):
        return len(self.curscope)


#Push new scope
#   curscope = scope(curscope)
#get value, go down scopes if necessary
#   v = curscope.get(var)
#put new value in current scope
#   curscope.put(var, val)
#pop off old scope
#   curscope = curscope.pop()

class SymbolTable:
    def __init__(self):
        """
            mmu - the mmu representing the memory layout of the target device.
            used for allocating memory to variables.
        """
        self.scope = scope(None)

    def get(self, name):
        return self.scope.get(name)

    def getAddr(self, name):
        return self.scope.get(name)['addr']
    
    def set(self, name, value):
        self.scope.set(name, value)

    def put(self, name, value):
        self.scope.put(name, value)

    def delete(self, name):
        self.scope.delete(name)

    def push(self):
        self.scope = scope(self.scope)
    
    def pop(self):
        self.scope = self.scope.pop()

    def scopeIsGlobal(self):
        return self.scope.subscope == None

    def getLocal(self, name):
        return self.scope.getLocal(name)

    def numNonGlobalVars(self):
        return self.scope.numNonGlobalVars()

    def numLocalVars(self):
        return self.scope.numLocalVars()

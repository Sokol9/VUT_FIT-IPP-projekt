#!usr/bin/python3
"""
//implementation of interpret.py from task no.2 from IPP
//autor: Jakub Sokolik (xsokol14)
//13.4.2021
"""

import xml.etree.ElementTree as ET
from operator import attrgetter
import argparse
import sys
import re


ERR_ARGS = 10 #programs args
ERR_OPENRFILE = 11 #error during opennig file for read
ERR_OPENWFILE = 12 #error during opennig file for write
ERR_XMLFORM = 31 #error xml format
ERR_XMLSTRUCT = 32 #error xml struct of IPPcode21
ERR_SEM = 52 #semantic error like undefine label or try redefine var
ERR_OPTYPE = 53 #error invalid type of operands
ERR_UNEXVAR = 54 #error work with undefine variable
ERR_FRAME = 55 #error work with undefine frame
ERR_MISSVAL = 56 #error missing value in var, frame, data_stack...
ERR_WVAL = 57 #error wrong value of operands
ERR_STR = 58 #error wrong work with string


class controller:
    def __init__(self, input, labels):
        self.input = input
        self.labels =  labels

        self.gf = {}
        self.tf = None
        self.frame_stack = []

        #only symbol args
        self.data_stack = []

        self.call_stack = []

        self.inst_cnt = 0
        self.max_vars_cnt = 0
        self.hot_inst = {}

    def stats(self, inst, code):
        #code 1 is for var stat
        #code 2 is for inst stat
        #code 3 is for both stat (1+2)
        name = inst.getName()
        order = inst.getOrder()
        if (code >= 2):
            if (name != 'LABEL' and name != 'BREAK' and name != 'DPRINT'):
                self.inst_cnt += 1
                if (order in self.hot_inst.keys()):
                    self.hot_inst[order] = self.hot_inst[order] + 1
                else:
                    self.hot_inst[order] = 1
            code -= 2

        if (code == 1):
            if (name != 'DEFVAR'):
                #najviac premennych bude vzdy po pridani
                cnt = len(self.gf)

                if (self.frame_stack is not None):
                    for frame in self.frame_stack:
                        cnt += len(frame)

                if (self.tf is not None):
                    cnt += len(self.tf)

                if (cnt > self.max_vars_cnt):
                    self.max_vars_cnt = cnt

    def getStats(self):
        hot = None
        val = 0
        for order in self.hot_inst.keys():

            if (self.hot_inst[order] > val):
                val = self.hot_inst[order]
                hot = order
            elif(self.hot_inst[order] > val):
                if hot is None:
                    hot = order
                if (order < hot):
                    hot = order
        return self.inst_cnt, self.max_vars_cnt, hot

    def getVar(self, arg):
        frame, name = parseVar(arg)
        if (frame == 'GF'):
            if (name not in self.gf.keys()):
                error("Try to acces to undefined variable in GF")
                sys.exit(ERR_UNEXVAR)
            return self.gf[name]

        elif (frame == 'TF'):
            if (self.tf is None):
                error("TF is not defined")
                sys.exit(ERR_FRAME)
            if (name not in self.tf.keys()):
                error("Try to acces to undefined variable in TF")
                sys.exit(ERR_UNEXVAR)
            return self.tf[name]

        elif (frame == "LF"):
            if (len(self.frame_stack) == 0):
                error("LF is not defined")
                sys.exit(ERR_FRAME)
            if (name not in self.frame_stack[-1].keys()):
                error("Try to acces to undefined variable in LF")
                sys.exit(ERR_UNEXVAR)
            return self.frame_stack[-1][name]


    #funkcia vrati typ a hodnotu argumentu,
    #ak ide o premennu, tak ju dereferencuje
    def getAll(self, arg):
        type = arg.getType()
        if (type == 'var'):
            #dereferencia premennej
            type, val = self.getVar(arg).getAll()
        else:
            #hodnota argumentu
            val = arg.getValue()
        if type == None:
            error("Work with unset variable")
            sys.exit(ERR_MISSVAL)
        return type, val

    #praca s ramcami, volanie funkcii
    def move(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isSym()

        var = self.getVar(inst.getArg1())

        type, val = self.getAll(inst.getArg2())

        var.set(type, val)

    def createFrame(self, inst):
        self.tf = {}

    def pushFrame(self, inst):
        if (self.tf == None):
            error("Can't push TF, because is undefined")
            sys.exit(ERR_FRAME)
        self.frame_stack.append(self.tf)
        self.tf = None

    def popFrame(self, inst):
        if (len(self.frame_stack) == 0):
            error("LF is not defined")
            sys.exit(ERR_FRAME)
        self.tf = self.frame_stack.pop(-1)

    def defVar(self, inst):
        inst.getArg1().isVar()

        frame, name = parseVar(inst.getArg1())
        var = variable(None, None)
        if (frame == 'GF'):
            if (name in self.gf.keys()):
                error("Try redefine variable in GF")
                sys.exit(ERR_SEM)
            self.gf[name] = var

        elif (frame == 'TF'):
            if (self.tf is None):
                error("TF is not define")
                sys.exit(ERR_FRAME)
            if (name in self.tf.keys()):
                error("Try redefine variable in TF")
                sys.exit(ERR_SEM)
            self.tf[name] = var

        elif (frame == "LF"):
            if (len(self.frame_stack) == 0):
                error("LF is not defined")
                sys.exit(ERR_FRAME)

            lf = self.frame_stack[-1]

            if (name in lf.keys()):
                error("Try redefine variable in LF")
                sys.exit(ERR_SEM)
            lf[name] = var

    def call(self, inst, cnt):
        inst.getArg1().isLabel()

        self.call_stack.append(cnt)

    def ret(self, inst):
        if (len(self.call_stack) == 0):
            error("Can't call return when call_stack is empty")
            sys.exit(ERR_MISSVAL)

        return self.call_stack.pop(-1)

    #praca s datovym zasobnikom
    def pushs(self, inst):
        inst.getArg1().isSym();
        type, value = self.getAll(inst.getArg1())

        argum = arg(type, value)

        self.data_stack.append(argum)

    def pops(self, inst):
        inst.getArg1().isVar();
        if (len(self.data_stack) == 0):
            error("Invalid operation with stack, Stack is empty")
            sys.exit(ERR_MISSVAL)

        var = self.getVar(inst.getArg1())
        sym = self.data_stack.pop(-1)

        var.set(*sym.getAll())

    def clears(self, inst):
        self.data_stack = []

    #Aritmenticke, relacne, bool a konverz inst
    def arithmetic(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)
            iname = inst.getName()[:-1]

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())
            iname = inst.getName()

        if (type1 != type2):
            error("Invalid type of argument. aritmetic instructin need two same types")
            sys.exit(ERR_OPTYPE)

        if (type1 != 'int' and type1 != 'float' ):
            error("Invalid type of argument. aritmetic instructin need int or float")
            sys.exit(ERR_OPTYPE)


        if (iname == 'ADD'):
            var.set(type1, val1 + val2)
        elif (iname == 'SUB'):
            var.set(type1, val1 - val2)
        elif (iname == 'MUL'):
            var.set(type1, val1 * val2)
        elif (iname == 'IDIV'):
            if (val2 == 0):
                error("division by zero")
                sys.exit(ERR_WVAL)
            var.set(type1, val1 // val2)
        elif (iname == 'DIV'):
            if (type1 != 'float'):
                error("Invalid type of argument. Instructin DIV need float")
                sys.exit(ERR_OPTYPE)
            if (val2 == 0):
                error("division by zero")
                sys.exit(ERR_WVAL)
            var.set(type1, val1 / val2)

    def eq(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())


        #todo ask WHY nil jebnuty
        if (re.match(r'^(int|string|bool|nil|float)$', type1) is None):
            error("Invalid type of argument. Instructin need int, float, string, bool or nil")
            sys.exit(ERR_OPTYPE)
        if (re.match(r'^(int|string|bool|nil|float)$', type2) is None):
            error("Invalid type of argument. Instructin need int, float, string, bool or nil")
            sys.exit(ERR_OPTYPE)



        if (type1 !=  type2 ):
            if (type1 == 'nil' or type2 == 'nil'):
                var.set('bool', 'false')
                return
            error("Invalid type of argument. Instructin two equals types")
            sys.exit(ERR_OPTYPE)

        var.set('bool', 'true')

        if (val1 == val2):
            return

        var.set('bool', 'false')

    def lt(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())


        if (type1 !=  type2 ):
            error("Invalid type of argument. Instructin two equals types")
            sys.exit(ERR_OPTYPE)

        var.set('bool', 'true')

        if (re.match(r'^(int|string|bool|float)$', type1)):
            if (val1 < val2):
                return
        else:
            error("Invalid type of argument. Instructin need int, float, string or bool")
            sys.exit(ERR_OPTYPE)

        var.set('bool', 'false')

    def gt(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())

        if (type1 !=  type2 ):
            error("Invalid type of argument. Instructin two equals types")
            sys.exit(ERR_OPTYPE)

        var.set('bool', 'true')

        if (re.match(r'^(int|string|bool|float)$', type1)):
            if (val1 > val2):
                return
        else:
            error("Invalid type of argument. Instructin need int, float, string or bool")
            sys.exit(ERR_OPTYPE)

        var.set('bool', 'false')

    def And(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())


        if (type1 != 'bool' or type2 != 'bool'):
            error("Invalid type of argument. Instructin need two bools")
            sys.exit(ERR_OPTYPE)


        if (val1 == 'true' and val2 == 'true'):
            var.set(type1, 'true')
        else:
            var.set(type1, 'false')

    def Or(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())

        if (type1 != 'bool' or type2 != 'bool'):
            error("Invalid type of argument. Instructin need two bools")
            sys.exit(ERR_OPTYPE)


        if (val1 == 'true' or val2 == 'true'):
            var.set(type1, 'true')
        else:
            var.set(type1, 'false')

    def Not(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 1):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym = self.data_stack.pop(-1)

            sym.isSym()

            type, val = self.getAll(sym)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()

            type, val = self.getAll(inst.getArg2())

            var = self.getVar(inst.getArg1())


        if (type != 'bool'):
            error("Invalid type of argument. Instructin need two bools")
            sys.exit(ERR_OPTYPE)


        if (val == 'true'):
            var.set(type, 'false')
        else:
            var.set(type, 'true')

    def int2char(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 1):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym = self.data_stack.pop(-1)

            sym.isSym()

            type, val = self.getAll(sym)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()

            type, val = self.getAll(inst.getArg2())

            var = self.getVar(inst.getArg1())

        if (type != 'int'):
            error("Invalid type in instuction INT2CHAR")
            sys.exit(ERR_OPTYPE)

        try:
            var.set('string', chr(val))
        except:
            error("This int: " + str(val) + " can't convert to sring")
            exit(ERR_STR)

    def stri2int(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

            var = self.getVar(inst.getArg1())

        if (type1 != 'string' or type2 != 'int'):
            error("Invalid type in instuction stri2int")
            sys.exit(ERR_OPTYPE)

        if (len(val1) <= val2 or val2 < 0):
            error("index out of range")
            sys.exit(ERR_STR)

        var.set('int', ord(val1[val2]))

    def float2int(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 1):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym = self.data_stack.pop(-1)

            sym.isSym()

            type, val = self.getAll(sym1)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()

            type, val = self.getAll(inst.getArg2())

            var = self.getVar(inst.getArg1())

        if (type != 'float'):
            error("Invalid type for float2int")
            sys.exit(ERR_OPTYPE)

        var.set('int', int(val))

    def int2float(self, inst):
        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 1):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym = self.data_stack.pop(-1)

            sym.isSym()

            type, val = self.getAll(sym1)

            var = arg(None, None)
            self.data_stack.append(var)

        else:
            #clasic
            inst.getArg1().isVar()
            inst.getArg2().isSym()

            type, val = self.getAll(inst.getArg2())

            var = self.getVar(inst.getArg1())

        if (type != 'int'):
            error("Invalid type for float2int")
            sys.exit(ERR_OPTYPE)

        var.set('float', float(val))

    #praca in-out instuctions
    def read(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isType()
        var = self.getVar(inst.getArg1())


        readed_val = self.input.readline()

        if (len(readed_val) == 0):
            var.set('nil', 'nil')
            return

        type = inst.getArg2().getValue()
        if (type == 'int'):
            try:
                var.set(type, int(readed_val))
            except:
                var.set('nil', 'nil')
        elif (type == 'bool'):
            if (readed_val[-1] == '\n'):
                readed_val = readed_val.lower()[:-1]
            if (readed_val == 'true'):
                var.set(type, readed_val)
            else:
                var.set(type, 'false')
        elif (type == 'string'):
            if (readed_val[-1] == '\n'):
                readed_val = readed_val[:-1]
            #ask todo remove end of line
            var.set(type, readed_val)
        elif (type == 'float'):
            try:
                var.set(type, float.fromhex(readed_val))
            except:
                var.set('nil', 'nil')
        else:
            error("Invalid type. I can't read " + type)
            sys.exit(ERR_OPTYPE)

    def write(self, inst):
        inst.getArg1().isSym()

        type, val = self.getAll(inst.getArg1())


        if (type == 'nil'):
            print("",end = '')
        elif (type == 'float'):
            print(float.hex(val), end = '')
        else:
            print(val, end='')

    def concat(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isSym()
        inst.getArg3().isSym()

        var = self.getVar(inst.getArg1())
        type1, val1 = self.getAll(inst.getArg2())
        type2, val2 = self.getAll(inst.getArg3())

        if (type1 != 'string' or type2 !='string'):
            error("Invalid arg type")
            sys.exit(ERR_OPTYPE)

        var.set(type1, val1 + val2)

    def strlen(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isSym()

        type, val = self.getAll(inst.getArg2())
        var = self.getVar(inst.getArg1())

        if (type != 'string'):
            error("invalid arg type")
            sys.exit(ERR_OPTYPE)

        var.set('int', len(val))

    def getChar(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isSym()
        inst.getArg3().isSym()

        type1, val1 = self.getAll(inst.getArg2())
        type2, val2 = self.getAll(inst.getArg3())
        var = self.getVar(inst.getArg1())

        if (type1 != 'string' or type2 != 'int'):
            error("invalid arg type")
            sys.exit(ERR_OPTYPE)

        if (len(val1) <= val2 or val2 < 0):
            error("index out of range")
            sys.exit(ERR_STR)

        var.set('string', val1[val2])

    def setChar(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isSym()
        inst.getArg3().isSym()

        type1, val1 = self.getAll(inst.getArg1())
        type2, val2 = self.getAll(inst.getArg2())
        type3, val3 = self.getAll(inst.getArg3())
        var = self.getVar(inst.getArg1())

        if (type1 != 'string' or type2 != 'int' or type3 != 'string'):
            error("invalid arg type")
            sys.exit(ERR_OPTYPE)

        if (len(val1) <= val2 or len(val3) < 1 or val2 < 0):
            error("index out of range")
            sys.exit(ERR_STR)


        ls = list(val1)
        ls[val2] = val3[0]

        val1 = "".join(ls)

        var.setValue(val1)

    #praca s typmi
    def type(self, inst):
        inst.getArg1().isVar()
        inst.getArg2().isSym()

        type = inst.getArg2().getType()
        val = inst.getArg2().getValue()
        if (type == 'var'):
            var2 = self.getVar(inst.getArg2())
            type = var2.getType()
            val = var2.getValue()

        if (type == None):
            type = ""


        var = self.getVar(inst.getArg1())
        if (type == 'type'):
            var.set('type', 'string')
        else:
            var.set('type', type)

    #riadenie toku programu
    #todo co to kurva s tym nil v podmienenych skokoch?
    def jumpIfEQ(self, inst):
        inst.getArg1().isLabel()

        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

        else:
            #clasic
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

        if (inst.getArg1().getValue() not in self.labels.keys()):
            error("Invalid label")
            sys.exit(ERR_SEM)

        if (re.match(r'^(int|string|bool|nil|float)$', type1) is None):
            error("Invalid type of argument. Instructin need int, float, string, bool or nil")
            sys.exit(ERR_OPTYPE)
        if (re.match(r'^(int|string|bool|nil|float)$', type2) is None):
            error("Invalid type of argument. Instructin need int, float, string, bool or nil")
            sys.exit(ERR_OPTYPE)

        if (type1 != type2):
            if (type1 == 'nil' or type2 == 'nil'):
                return None
            error("Invalid type of argument. Instructin two equals types")
            sys.exit(ERR_OPTYPE)

        if (val1 != val2):
            return None

        return inst.getArg1().getValue()

    def jumpIfNEQ(self, inst):
        inst.getArg1().isLabel()

        if (inst.getName()[-1] == 'S'):
            #stack
            if (len(self.data_stack) < 2):
                error("Not enough item in data stack")
                sys.exit(ERR_MISSVAL)
            sym2 = self.data_stack.pop(-1)
            sym1 = self.data_stack.pop(-1)

            sym1.isSym()
            sym2.isSym()

            type1, val1 = self.getAll(sym1)
            type2, val2 = self.getAll(sym2)

        else:
            #clasic
            inst.getArg2().isSym()
            inst.getArg3().isSym()

            type1, val1 = self.getAll(inst.getArg2())
            type2, val2 = self.getAll(inst.getArg3())

        if (inst.getArg1().getValue() not in self.labels.keys()):
            error("Invalid label")
            sys.exit(ERR_SEM)

        if (re.match(r'^(int|string|bool|nil|float)$', type1) is None):
            error("Invalid type of argument. Instructin need int, string, bool or nil")
            sys.exit(ERR_OPTYPE)
        if (re.match(r'^(int|string|bool|nil|float)$', type2) is None):
            error("Invalid type of argument. Instructin need int, string, bool or nil")
            sys.exit(ERR_OPTYPE)

        if (type1 != type2):
            if (type1 == 'nil' or type2 == 'nil'):
                return inst.getArg1().getValue()
            error("Invalid type of argument. Instructin two equals types")
            sys.exit(ERR_OPTYPE)

        if (val1 != val2):
            return inst.getArg1().getValue()

        return None

    def exit(self, inst):
        inst.getArg1().isSym()

        type, val = self.getAll(inst.getArg1())

        if (type != 'int'):
            error("invalid arg type")
            sys.exit(ERR_OPTYPE)

        if (val < 0 or val > 49):
            error("invalid arg value")
            sys.exit(ERR_WVAL)

        sys.exit(val)

    def dprint(self, inst):
        inst.getArg1().isSym()
        type, val = self.getAll(inst.getArg1())

        if (type != 'string'):
            error("invalid arg type")
            sys.exit(ERR_OPTYPE)
        error(val)

    def brk(self, inst):
        print("\nInstruction: " + inst.getName() + ", order: " + str(inst.getOrder()))
        print("\nGF:")
        for i in self.gf.keys():
            print(i +": " + str(self.gf[i].getType()) + ", " + str(self.gf[i].getValue()))

        print("\nTF:")
        if self.tf is not None:
            for i in self.tf.keys():
                print(i +": " + str(self.tf[i].getType()) + ", " + str(self.tf[i].getValue()))
        else:
            print("uninicialized")

        print("\nact LF:")
        if len(self.frame_stack) > 0:
            fr = self.frame_stack[-1]
            for i in fr.keys():

                print(i +": " + str(fr[i].getType()) + ", " + str(fr[i].getValue()))
        else:
            print("uninicialized")

        if len(self.frame_stack) > 0:
            print ("\nFrame stack: " + str(len(self.frame_stack)) + " stacks")

        if len(self.data_stack) > 0:
            print ("\nData stack: " + str(len(self.data_stack)) + " items")


class variable:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def replace(self, var):
        self.type = var.getType()
        self.value = var.getValue()

    def getType(self):
        return self.type

    def getValue(self):
        return self.value

    def setType(self, type):
        self.type = type

    def setValue(self, value):
        self.value =  value

    def set(self, type, value):
        self.type = type
        self.value =  value

    def getAll(self):
        return self.type, self.value

class arg:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def getType(self):
        return self.type

    def getValue(self):
        return self.value

    def getAll(self):
        return self.type, self.value

    def isVar(self):
        if (self.type != 'var'):
            error("Invalid Arg, expected var")
            sys.exit(ERR_OPTYPE)

    def isSym(self):
        if (re.match( r'^(bool|nil|string|int|var|float)$', self.type) is None):
            error("Invalid type of operand, expected sym")
            sys.exit(ERR_OPTYPE)

    def isLabel(self):
        if (self.type != 'label'):
            error("Invalid type of operand, expected label")
            sys.exit(ERR_OPTYPE)

    def isType(self):
        if (self.type != 'type'):
            error("Invalid type of operand, expected type")
            sys.exit(ERR_OPTYPE)

    def set(self, type, value):
        self.type = type
        self.value =  value

class instuction:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.args = []

    def addArg(self, type, value):
        self.args.append(arg(type, value))

    def getName(self):
        return self.name

    def getOrder(self):
        return self.number

    def argsSize(self):
        return len(self.args)

    def getArg1(self):
        return self.args[0]

    def getArg2(self):
        return self.args[1]

    def getArg3(self):
        return self.args[2]

def error(str):
    sys.stderr.write(str + "\n")

def checkXML(root, instructions, labels):
    #check root tag
    if (root.tag != "program" or 'language' not in root.attrib.keys()):
        error("Invalid xml program tag")
        sys.exit(ERR_XMLSTRUCT)
    if (root.attrib['language'] != "IPPcode21"):
        error("Invalid xml program language")
        sys.exit(ERR_XMLSTRUCT)


    for child in root:
        if ("order" not in child.attrib.keys()):
            error("Somewhere is missing order atrib in instruction")
            sys.exit(ERR_XMLSTRUCT)
        try:
            int(child.get('order'))
        except:
            error("Somewhere in instruction is order atrib with wrong order value")
            sys.exit(ERR_XMLSTRUCT)

    #sort
    root[:] = sorted(root, key=lambda child: (child.tag,int(child.get('order'))))

    #chcek instructions tag and arg tags
    cnt = 0
    ord = None
    for child in root:

        if (child.tag != "instruction"):
            error("Invalid xml tag for instruction")
            sys.exit(ERR_XMLSTRUCT)

        if ( "opcode" not in child.attrib.keys() or len(child.attrib.keys()) != 2):
            error("Invalid xml instruction atribut")
            sys.exit(ERR_XMLSTRUCT)

        #instruction are sort by order, if order is same with previev instruction is err
        if (ord is not None):
            if (ord == int(child.attrib['order'])):
                error("Invalid xml instruction order")
                sys.exit(ERR_XMLSTRUCT)
        else:
            #inst are sorted there is enought to check first
            ord = int(child.attrib['order'])
            if (ord <= 0):
                error("Invalid xml instruction order")
                sys.exit(ERR_XMLSTRUCT)

        ord = int(child.attrib['order'])

        #make inst
        inst = instuction(child.attrib['opcode'].upper(), ord)
        instructions.append(inst)
        #if inst is label, add in list labels
        if (child.attrib['opcode'].upper() == "LABEL"):
            if (child[0].text in labels.keys()):
                error("Duplicate label")
                sys.exit(ERR_SEM)
            labels[child[0].text] = cnt

        #child sort args by tag
        child[:] = sorted(child, key=attrgetter("tag"))

        #check instructions args
        arg_cnt = 1
        for subelem in child:
            #there is not more then three args
            if (subelem.tag != "arg" + str(arg_cnt) or arg_cnt == 4):
                error("Invalid xml argument tag")
                sys.exit(ERR_XMLSTRUCT)

            if (len(subelem.attrib.keys()) != 1 or "type" not in subelem.attrib.keys()):
                error("Invalid xml instruction argument atrib")
                sys.exit(ERR_XMLSTRUCT)

            type = subelem.attrib["type"]
            val = subelem.text

            #check all possible types
            if (re.match(r'^(bool|nil|string|int|float|var|label|type)$', type) is None):
                error("Invalid xml argument type")
                sys.exit(ERR_XMLSTRUCT)

            #check validity of values
            if (type == 'bool'):
                if (re.match(r'^(true|false)$', val) is None):
                    error("Invalid xml argument value for bool")
                    sys.exit(ERR_XMLSTRUCT)
            elif (type == 'nil'):
                if (val != 'nil'):
                    error("Invalid xml argument value for nil")
                    sys.exit(ERR_XMLSTRUCT)
            elif (type == 'string'):
                if (val is None):
                    val = ""
                if (re.match(r'^(([^\\\#])|(\\[0-9]{3}))*$', val) is None):
                    error("Invalid xml argument value for string")
                    sys.exit(ERR_XMLSTRUCT)
                val = convertString(val)
            elif (type == 'int'):
                if (re.match(r'^(-){0,1}([0-9]*)$', val) is  None):
                    error("Invalid xml argument value for int")
                    sys.exit(ERR_XMLSTRUCT)
                val = int(val)
            elif (type == 'var'):
                if (re.match(r'^(GF|LF|TF)@([a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*)$', val) is  None):
                    error("Invalid xml argument value for var")
                    sys.exit(ERR_XMLSTRUCT)
            elif (type == 'label'):
                if (re.match(r'^([a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*)$', val) is  None):
                    error("Invalid xml argument value for label")
                    sys.exit(ERR_XMLSTRUCT)
            elif (type == 'type'):
                if (re.match(r'^(bool|nil|string|int|var|label|type|float)$', val) is None):
                    error("Invalid xml argument value for type")
                    sys.exit(ERR_XMLSTRUCT)
            elif ((type == 'float')):
                try:
                    val = float.fromhex(val)
                except:
                    error("Invalid xml argument value for float")
                    sys.exit(ERR_XMLSTRUCT)

            #in inst add arg
            inst.addArg(type, val)
            arg_cnt += 1

        cnt += 1
    return cnt

#function return frame and name of var
def parseVar(arg):
    if(arg.getType() != 'var'):
        error("Invalid type of operands")
        sys.exit(ERR_OPTYPE)

    match = re.match( r'^(GF|LF|TF)@(.*)$', arg.getValue())
    frame = match.group(1)
    name = match.group(2)
    return frame, name

#function convert sring. fuxkup \000
def convertString(string):
    for r in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&quot;', '\"'), ('&apos;', '\'')):
        string = string.replace(*r)

    for i in range(1000):
        if i < 10:
            patt = '00' + str(i)
        elif i < 100:
            patt = '0' + str(i)
        else:
            patt = str(i)
        string = string.replace('\\' + patt, chr(i))


    """
    match = re.match(r'.*\\([0-9]{3}).*', str)
    while(match is not None):
        print (match.group(1))
        print("-")
        str = str.replace('\\' + match.group(1), chr(int(match.group(1))))
        match = re.match(r'.*\\([0-9]{3}).*', str)
    """
    return string

def usage(err):
    print("\nUsage:")
    print("\t --help \t for help")
    print("\t --source=file \t set source file with xml code")
    print("\t --input=file \t set input file with xml code")
    print("\t --stati=file \t set file where will print statistic")
    print("\t    --insts \t will count executed instructions")
    print("\t    --hot \t will count most executed instruction")
    print("\t    --vars \t will count maximum deine variable in same time")
    sys.exit(err)
#################### MAIN ############################

############### parse ARGS
stati = {}
last_stat = None
code = 0
src = False
inp = False
for argi in sys.argv[1:]:
    if (argi == '--help'):
        usage(0)
    elif(re.search( '=', argi)):
        match = re.match(r'^--(.*)=(.*)$', argi)
        if (match.group(1) == 'source'):
            source = match.group(2)
            if (src):
                error("invalid argument --source")
                usage(ERR_ARGS)
            src = True

        elif (match.group(1) == 'input'):
            input = match.group(2)
            if (inp):
                error("invalid argument --input")
                usage(ERR_ARGS)
            inp = True

        elif (match.group(1) == 'stati'):
            stati[match.group(2)] = [0]
            last_stat = match.group(2)
    elif (argi == '--insts'):
        if (last_stat is None):
            error("invalid order of arguments")
            usage(ERR_ARGS)
        stati[last_stat].append("insts")
        if (stati[last_stat][0] < 2):
            stati[last_stat][0] += 2
        if (code < 2):
            code += 2
    elif (argi == '--hot'):
        if (last_stat is None):
            error("invalid order of arguments")
            usage(ERR_ARGS)
        stati[last_stat].append("hot")
        if (stati[last_stat][0] < 2):
            stati[last_stat][0] += 2
        if (code < 2):
            code += 2
    elif (argi == '--vars'):
        if (last_stat is None):
            error("invalid order of arguments")
            usage(ERR_ARGS)
        stati[last_stat].append("vars")
        if (stati[last_stat][0] < 1 or stati[last_stat][0] - 2 ==0):
            stati[last_stat][0] += 1
        if (code < 1 or code - 2 ==0):
            code += 1

if (not src and not inp):
    error("there must be at least one arg (source or input)")
    sys.exit(ERR_ARGS)
if (not src):
    source = sys.stdin
if (not inp):
    input = sys.stdin



################## LOAD XML
try:
    tree = ET.parse(source)
except:
    error("XML format Error")
    #ask 31 or 32
    sys.exit(ERR_XMLFORM)

root = tree.getroot()



#chceck xml and make instructions
instructions = []
labels = {}
cnt_inst = checkXML(root, instructions, labels)


controller = controller(input, labels)
cnt = 0
#switch for instruction
while (cnt < cnt_inst):
    inst = instructions[cnt]
    name = inst.getName()
    cnt_args = inst.argsSize()
    if (cnt_args == 0):
        if (name == 'CREATEFRAME'):
            controller.createFrame(inst)
        elif (name == 'PUSHFRAME'):
            controller.pushFrame(inst)
        elif (name == 'POPFRAME'):
            controller.popFrame(inst)
        elif (name == 'RETURN'):
            cnt = controller.ret(inst)
        elif (name == 'BREAK'):
            controller.brk(inst)
            break;
        elif (name == 'ADDS'):
            controller.arithmetic(inst)
        elif (name == 'SUBS'):
            controller.arithmetic(inst)
        elif (name == 'MULS'):
            controller.arithmetic(inst)
        elif (name == 'IDIVS'):
            controller.arithmetic(inst)
        elif (name == 'DIVS'):
            controller.arithmetic(inst)
        elif (name == 'INT2CHARS'):
            controller.int2char(inst)
        elif (name == 'STRI2INTS'):
            controller.stri2int(inst)
        elif (name == 'INT2FLOATS'):
            controller.int2float(inst)
        elif (name == 'FLOAT2INTS'):
            controller.float2int(inst)
        elif (name == 'EQS'):
            controller.eq(inst)
        elif (name == 'LTS'):
            controller.lt(inst)
        elif (name == 'GTS'):
            controller.gt(inst)
        elif (name == 'ANDS'):
            controller.And(inst)
        elif (name == 'ORS'):
            controller.Or(inst)
        elif (name == 'NOTS'):
            controller.Not(inst)
        elif (name == 'CLEARS'):
            controller.clears(inst)
        else:
            error("Invalid instruction")
            sys.exit(ERR_XMLSTRUCT)
    elif (cnt_args == 1):
        if (name == 'DEFVAR'):
            controller.defVar(inst)
        elif (name == 'LABEL'):
            pass
        elif (name == 'WRITE'):
            controller.write(inst)
        elif (name == 'JUMP'):
            inst.getArg1().isLabel()

            label = inst.getArg1().getValue()
            if (label not in labels.keys()):
                error("Invalid label")
                sys.exit(ERR_SEM)
            cnt = labels[label] - 1
        elif (name == 'PUSHS'):
            controller.pushs(inst)
        elif (name == 'POPS'):
            controller.pops(inst)
        elif (name == 'CALL'):
            controller.call(inst, cnt)
            label = inst.getArg1().getValue()
            if (label not in labels.keys()):
                error("Invalid label")
                sys.exit(ERR_SEM)
            cnt = labels[label] - 1
        elif (name == 'EXIT'):
            controller.exit(inst)
        elif (name == 'DPRINT'):
            controller.dprint(inst)
        elif (name == 'JUMPIFEQS'):
            label = controller.jumpIfEQ(inst)
            if (label is not None):
                cnt = labels[label]
        elif (name == 'JUMPIFNEQS'):
            label = controller.jumpIfNEQ(inst)
            if (label is not None):
                cnt = labels[label]
        else:
            error("Invalid instruction")
            sys.exit(ERR_XMLSTRUCT)
    elif (cnt_args == 2):
        if (name == 'MOVE'):
            controller.move(inst)
        elif (name == 'READ'):
            controller.read(inst)
        elif (name == 'INT2CHAR'):
            controller.int2char(inst)
        elif (name == 'INT2FLOAT'):
            controller.int2float(inst)
        elif (name == 'FLOAT2INT'):
            controller.float2int(inst)
        elif (name == 'NOT'):
            controller.Not(inst)
        elif (name == 'STRLEN'):
            controller.strlen(inst)
        elif (name == 'TYPE'):
            controller.type(inst)
        else:
            error("Invalid instruction")
            sys.exit(ERR_XMLSTRUCT)
    elif (cnt_args == 3):
        if (name == 'JUMPIFEQ'):
            label = controller.jumpIfEQ(inst)
            if (label is not None):
                cnt = labels[label]
        elif (name == 'JUMPIFNEQ'):
            label = controller.jumpIfNEQ(inst)
            if (label is not None):
                cnt = labels[label]
        elif (name == 'CONCAT'):
            controller.concat(inst)
        elif (name == 'ADD'):
            controller.arithmetic(inst)
        elif (name == 'SUB'):
            controller.arithmetic(inst)
        elif (name == 'MUL'):
            controller.arithmetic(inst)
        elif (name == 'IDIV'):
            controller.arithmetic(inst)
        elif (name == 'DIV'):
            controller.arithmetic(inst)
        elif (name == 'EQ'):
            controller.eq(inst)
        elif (name == 'LT'):
            controller.lt(inst)
        elif (name == 'GT'):
            controller.gt(inst)
        elif (name == 'AND'):
            controller.And(inst)
        elif (name == 'OR'):
            controller.Or(inst)
        elif (name == 'STRI2INT'):
            controller.stri2int(inst)
        elif (name == 'GETCHAR'):
            controller.getChar(inst)
        elif (name == 'SETCHAR'):
            controller.setChar(inst)
        else:
            error("Invalid instruction")
            sys.exit(ERR_XMLSTRUCT)
    else:
        error("Invalid count of arguments")
        sys.exit(ERR_XMLSTRUCT)
    if (code > 0):
        controller.stats(inst, code)
    cnt += 1


if (code > 0):
    insts, vars, hot = controller.getStats()
    for file in stati.keys():
        try:
            f = open(file, 'w')
        except:
            error("Error while i opening stati file")
            sys.exit(ERR_OPENWFILE)
        for i in stati[file][1:]:
            if(i == 'insts'):
                f.write(str(insts) + '\n')
            if(i == 'hot'):
                f.write(str(hot) + '\n')
            if(i == 'vars'):
                f.write(str(vars) + '\n')

sys.exit(0)

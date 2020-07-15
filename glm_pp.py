# usage for debugging with gdb:
# gdb -x gdb_prettyprinter.py bin/*your_executable*
# (gdb) break *linenumber*
# (gdb) run
# (gdb) print *name_of_the_variable*

import gdb.printing
import numpy

_type_letters = {
    "float": "",
    "double": "d",
    "int": "i",
    "bool": "b"
}

def _vec_info(v):
    length = v.type.template_argument(0)
    T = v.type.template_argument(1)
    letter = _type_letters.get(str(T), "t")
    V = v.address.cast(T.array(length-1).pointer()).dereference()
    items = list(float(V[i]) for i in range(length))
    return letter, length, items

class VecPrinter:
    def __init__(self, v):
        self.v = v

    def to_string(self):
        letter, length, items = _vec_info(self.v)
        with numpy.printoptions(precision=3, suppress=True):
            return "{}vec{}: {}".format(letter, length, str(numpy.array(items)))

    def children(self):
        length = self.v.type.template_argument(0)
        T = self.v.type.template_argument(1)
        p = self.v.address.cast(T.pointer())
        for i in range(length):
            yield '[{}]'.format(i), (p + i).dereference()

    def display_hint(self):
        return 'array'


class MatPrinter:
    def __init__(self, v):
        self.v = v

    def to_string(self):
        V = self.v["value"]
        columns = []
        for i in range(V.type.range()[1] + 1):
            letter, length, items = _vec_info(V[i])
            columns.append(items)
        with numpy.printoptions(precision=3, suppress=True):
            return "{}mat{}x{}: \n{}".format(
                letter, len(columns), length, str(numpy.matrix(columns)))

    def children(self):
        V = self.v["value"]
        for i in range(V.type.range()[1] + 1):
            v = V[i]
            length = v.type.template_argument(0)
            T = v.type.template_argument(1)
            p = v.address.cast(T.array(length-1).pointer())
            with numpy.printoptions(precision=3, suppress=True):
                yield '[{}]'.format(i), p.dereference()

    def display_hint(self):
        return 'array'


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("glm_pp")
    pp.add_printer("glm::vec", "^glm::vec<[^<>]*>$", VecPrinter)
    pp.add_printer("glm::mat", "^glm::mat<[^<>]*>$", MatPrinter)
    return pp

gdb.printing.register_pretty_printer(gdb.current_objfile(), build_pretty_printer())
print('glm pretty-printing enabled')

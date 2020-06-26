import sys
import xml.sax

from abc import ABC

class Measurable(ABC):

    def __init__(self, *args, **kwargs):
        self._counters = {}
        super().__init__(*args, **kwargs)

    def addCounter(self, counter):
        self._counters[counter.typeval] = counter
    
    def coverage(self, typeval):
        counter = self._counters.get(typeval)
        if counter is None:
            return None
        return counter.coverage()

    def coveragep(self, typeval):
        coverage = self.coverage(typeval)
        if coverage is None:
            return 'n/a'
        return '{:d}%'.format(int(coverage))

class Package(Measurable):

    def __init__(self, name):
        self._name = name
        super().__init__()

    def name(self):
        return self._name.replace('/', '.')


class Class(Measurable):

    def __init__(self, name, source):
        self._name = name
        self._source = source
        super().__init__()

    def name(self):
        return self._name.replace('/', '.')


class SourceFile(Measurable):

    def __init__(self, name):
        self._name = name
        super().__init__()

    def name(self):
        return self._name


class Method(Measurable):
    
    _primTypeMap = {
        'Z': 'boolean',
        'B': 'byte',
        'C': 'char',
        'S': 'short',
        'I': 'int',
        'J': 'long',
        'F': 'float',
        'D': 'double',
        'V': 'void'
    }

    def __init__(self, name, desc):
        self._name = name
        self._desc = desc
        super().__init__()

    def signature(self):
        #return ''.format(self._name, self._desc)
        return self.__convert()

    def __convert(self):
        parseArgs = False
        parseRet = False
        isFqc = False
        isArray = False
        fqcName = ''
        argTypes = []
        retType = ''
        for i, c in enumerate(self._desc):
            if c == '(':
                parseArgs = True
                parseRet = False
            elif c == ')':
                parseArgs = False
                parseRet = True
            elif c == '[':
                isArray = True
            elif c == ';':
                isFqc = False
                fqcName = fqcName.replace('/', '.')
                if isArray:
                    fqcName = fqcName + '[]'
                    isArray = False
                if parseRet:
                    retType = fqcName
                else:
                    argTypes.append(fqcName)
                fqcName = ''
            else:
                if isFqc:
                    fqcName += c
                elif c == 'L':
                    isFqc = True
                elif c in self._primTypeMap:
                    typeName = self._primTypeMap[c]
                    if isArray:
                        typeName = typeName + '[]'
                        isArray = False
                    if parseRet:
                        retType = typeName
                    else:
                        argTypes.append(typeName)
                else:
                    raise Exception('c[{}]={} in {}'.format(i, c, self._desc))
        return '{} {}({})'.format(retType, self._name, ';'.join(argTypes))

class Counter(object):

    def __init__(self, typeval, missed, covered):
        self._typeval = typeval
        self._missed = missed
        self._covered = covered

    @property
    def typeval(self):
        return self._typeval

    def coverage(self):
        covered = int(self._covered)
        missed = int(self._missed)
        return covered / (covered + missed) * 100.0


class JacocoXmlContentHandler(xml.sax.ContentHandler):

    _hdr = ('package', 'class', 'method', 'instruction', 'branch')

    def __init__(self, outfile):
        super().__init__()
        self._outfile = outfile
        self._package = None
        self._class = None
        self._sourceFile = None
        self._method = None

    def startDocument(self):
        #self._fp = open(self._outfile, 'w')
        self._fp = sys.stdout
        self.__print(self.__formatHeader())
        return super().startDocument()

    def endDocument(self):
        #self._fp.close()
        return super().endDocument()

    def startElement(self, name, attrs):
        if name == 'package':
            self.__startPackage(attrs)
        elif name == 'class':
            self.__startClass(attrs)
        elif name == 'method':
            self.__startMethod(attrs)
        elif name == 'sourcefile':
            self.__startSourceFile(attrs)
        elif name == 'counter':
            self.__startCounter(attrs)
        return super().startElement(name, attrs)

    def endElement(self, name):
        if name == 'package':
            self.__endPackage()
        elif name == 'class':
            self.__endClass()
        elif name == 'method':
            self.__endMethod()
        elif name == 'sourcefile':
            self.__endSourceFile()
        elif name == 'counter':
            self.__endCounter()
        return super().endElement(name)

    def __startPackage(self, attrs):
        self._package = Package(attrs.getValue('name'))

    def __startClass(self, attrs):
        self._class = Class(attrs.getValue('name'),
                        attrs.getValue('sourcefilename'))

    def __startMethod(self, attrs):
        self._method = Method(attrs.getValue('name'),
                        attrs.getValue('desc'))

    def __startSourceFile(self, attrs):
        self._method = SourceFile(attrs.getValue('name'))

    def __startCounter(self, attrs):
        counter = Counter(attrs.getValue('type'),
                    attrs.getValue('missed'),
                    attrs.getValue('covered'))
        if self.__isInPackage():
            if self.__isInClass():
                if self.__isInMethod():
                    self._method.addCounter(counter)
                else:
                    self._class.addCounter(counter)
            elif self.__isInSourceFile():
                self._sourceFile.addCounter(counter)
            else:
                self._package.addCounter(counter)

    def __endPackage(self):
        self._package = None

    def __endClass(self):
        self._class = None

    def __endMethod(self):
        self.__print('{package},{cls},{method},{instruction},{branch}'.format(
            package=self._package.name(),
            cls=self._class.name(),
            method=self._method.signature(),
            instruction=self._method.coveragep('INSTRUCTION'),
            branch=self._method.coveragep('BRANCH')))

        self._method = None

    def __endSourceFile(self):
        self._sourceFile = None

    def __endCounter(self):
        pass

    def __isInPackage(self):
        return self._package is not None

    def __isInClass(self):
        return self._class is not None

    def __isInMethod(self):
        return self._method is not None

    def __isInSourceFile(self):
        return self._sourceFile is not None

    @classmethod
    def __formatHeader(cls):
        return ','.join(cls._hdr)
    
    @classmethod
    def __coverage(cls, counter):
        if counter is None:
            return 'n/a'
        covered = int(counter['covered'])
        missed = int(counter['missed'])
        return '{:.1f}'.format(float(covered / (covered + missed) * 100))

    def __print(self, text):
        self._fp.write(text)
        self._fp.write('\n')


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'jacoco.xml'
    handler = JacocoXmlContentHandler(target)
    xml.sax.parse(target, handler)
        

if __name__ == '__main__':
    main()
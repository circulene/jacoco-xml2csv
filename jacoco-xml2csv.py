import sys
import xml.sax


class JacocoXmlContentHandler(xml.sax.ContentHandler):

    _hdr = ('package', 'class', 'method', 'instruction', 'branch')

    def __init__(self, outfile):
        super().__init__()
        self._outfile = outfile
        self._package = {}
        self._class = {}
        self._method = {}

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
        elif name == 'counter':
            self.__endCounter()
        return super().endElement(name)

    def __startPackage(self, attrs):
        self._package['name'] = attrs.getValue('name')

    def __startClass(self, attrs):
        self._class['name'] = attrs.getValue('name')

    def __startMethod(self, attrs):
        self._method['name'] = attrs.getValue('name')
        self._method['desc'] = attrs.getValue('desc')
        self._method['counters'] = {}

    def __startCounter(self, attrs):
        if self.__isInMethod():
            counterType = attrs.getValue('type')
            counter = {}
            counter['missed'] = attrs.getValue('missed')
            counter['covered'] = attrs.getValue('covered')
            self._method['counters'][counterType] = counter

    def __endPackage(self):
        self._package.clear()

    def __endClass(self):
        self._class.clear()

    def __endMethod(self):
        counters = self._method['counters']

        self.__print('{package},{cls},{method}({desc}),{instruction},{branch}'.format(
            package=self._package['name'],
            cls=self._class['name'],
            method=self._method['name'],
            desc=self._method['desc'],
            instruction=self.__coverage(counters.get('INSTRUCTION')),
            branch=self.__coverage(counters.get('BRANCH'))
            ))

        self._method.clear()

    def __endCounter(self):
        pass

    def __isInClass(self):
        return len(self._class.keys()) > 0
    
    def __isInMethod(self):
        return len(self._method.keys()) > 0

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
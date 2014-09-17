import os,re
HERE = os.path.dirname( __file__ )
TYPING = os.path.join( HERE, 'typing.csv' )
class Interpreter( object ):
    def __init__( self ):
        self.matchers = []
        self.load()
    def load( self ):
        for line in open(TYPING).read().splitlines():
            pattern,text = line.split('\t')
            matcher = re.compile( pattern, re.I|re.U|re.DOTALL )
            self.matchers.append( (matcher, text))
    def process( self, text ):
        for matcher,replacement in self.matchers:
            text= matcher.sub( replacement , text )
        return text

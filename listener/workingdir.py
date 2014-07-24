"""Creation of working directories for storing language models and training data"""
import os,shutil,tempfile,subprocess
from functools import wraps
def one_shot( func ):
    """Only calculate once for each instance"""
    key = '_' + func.__name__
    @wraps( func )
    def cached( self ):
        if not hasattr( self, key ):
            setattr( self, key, func(self))
        return getattr( self, key )
    return cached

def base_config_directory(appname='listener'):
    """Produce a reasonable working directory in which to store our files"""
    config_dir = os.environ.get('XDG_CONFIG_HOME',os.path.expanduser('~/.config'))
    if os.path.exists( config_dir ):
        config_dir = os.path.join( config_dir, appname )
    else:
        config_dir = os.path.expanduser( '~/.%s'%(appname) )
    return config_dir 
def base_cache_directory(appname='listener'):
    cache_dir = os.environ.get( 'XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
    cache_dir = os.path.join( cache_dir, appname )
    return cache_dir

class Context( object ):
    """Holds a dictation context from which we attempt to recognize"""
    def __init__( self, key, parent=None ):
        if not key.isalnum():
            raise ValueError( "Need an alpha-numeric name for the context" )
        self.key = key 
        if not os.path.exists( self.directory ):
            if not parent:
                self.initial_working_directory( )
            else:
                raise RuntimeError( """Don't have chained/parent contexts working yet""" )
    @property
    @one_shot
    def directory( self ):
        base = base_config_directory()
        return os.path.join( base, self.key )
    @property 
    @one_shot
    def language_model_directory( self ):
        return os.path.join( self.directory, 'lm' )
    @property 
    @one_shot
    def hmm_directory( self ):
        return os.path.join( self.directory, 'hmm' )
    @property 
    @one_shot
    def recording_directory( self ):
        return os.path.join( self.directory, 'recordings' )
    @property
    @one_shot
    def language_model_file( self ):
        return os.path.join( self.language_model_directory, 'language_model.dmp' )
    @property 
    @one_shot
    def dictionary_file( self ):
        return os.path.join( self.language_model_directory, 'dictionary.dict' )
    
    def initial_working_directory( self,  ):
        """Create an initial working directory by cloning the pocketsphinx default models"""
        if not os.path.exists( self.directory ):
            os.makedirs( self.directory, 0700 )
        if not os.path.exists( self.language_model_directory ):
            os.makedirs( self.language_model_directory, 0700 )
        # Pull down the language model...
        archive = self.download_hmm_archive()
        tempdir = tempfile.mkdtemp( prefix='listener-', suffix='-unpack' )
        subprocess.check_call( [
            'tar', '-zxf',
            archive,
        ], cwd=tempdir )
        # we expect either a HUB4 or WSJ model...
        HMMs = [
            os.path.join( tempdir, 'hub4wsj_sc_8k'),
        ]
        DMPs = [
            '/usr/share/pocketsphinx/model/lm/en_US/hub4.5000.DMP',
        ]
        DICTIONARY = [
            '/usr/share/pocketsphinx/model/lm/en_US/cmu07a.dic',
        ]
        found = False
        for (dmp,dic,hmm) in zip(DMPs,DICTIONARY,HMMs):
            if os.path.exists( dmp ):
                shutil.copy( 
                    dmp, 
                    self.language_model_file,
                )
                shutil.copy(
                    dic,
                    self.dictionary_file,
                )
                shutil.copytree( 
                    hmm,
                    self.hmm_directory,
                )
                found = True 
        if not found:
            raise RuntimeError( 
                """We appear to be missing the ubuntu/debian package pocketsphinx-hmm-en-hub4wsj""" 
            )
        if not os.path.exists( self.recording_directory ):
            os.mkdir( self.recording_directory )
        return self.directory

    def acoustic_adaptation( self ):
        """Run acoustic adaptation on recorded data-set
        
        TODO: Likely should be machine and sound-source dependent so that 
        users can switch between devices?
        """
        command = [
            'sphinx_fe',
                '-argfile', os.path.join( self.hmm_directory, 'feat.params'),
                '-samprate', '16000',
                '-c',os.path.join( self.hmm_directory,'arctic20.fileids'),
                '-di',self.hmm_directory,
                '-do',self.hmm_directory,
                '-ei','wav',
                '-eo','mfc',
                '-mswav','yes',
        ]
    
    def download_url( self, url, filename ):
        """Download given URL to a local filename in our cache directory 
        
        returns the full filename
        """
        filename = os.path.basename( filename )
        target = os.path.join( base_cache_directory(), filename )
        if not os.path.exists( target ):
            log.warn( 'Downloading from %s', url )
            import urllib
            urllib.urlretrieve( url, target )
        return target
        
    
    HMM_URL = 'https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4WSJ%20Acoustic%20Model/hub4wsj_sc_8k.tar.gz/download'
    def download_hmm_archive( self ):
        return self.download_url( self.HMM_URL, 'hub4_wsj_language_model.tar.gz' )
    

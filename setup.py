import distutils.ccompiler
import distutils.sysconfig
import glob
import os
import platform
import tempfile

from setuptools import setup, find_packages, Extension

def get_ijson_version():
    """Get version from code without fully importing it"""
    _globals = {}
    with open(os.path.join('ijson', 'version.py')) as f:
        code = f.read()
    exec(code, _globals)
    return _globals['__version__']

setupArgs = dict(
    name = 'ijson',
    version = get_ijson_version(),
    author = 'Rodrigo Tobar, Ivan Sagalaev',
    author_email = 'rtobar@icrar.org, maniac@softwaremaniacs.org',
    url = 'https://github.com/ICRAR/ijson',
    license = 'BSD',
    description = 'Iterative JSON parser with a standard Python iterator interface',
    long_description = open('README.rst').read(),

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages = find_packages(exclude=['test']),
)

# Check if the yajl library + headers are present
# We don't use compiler.has_function because it leaves a lot of files behind
# without properly cleaning up
def yajl_present():

    compiler = distutils.ccompiler.new_compiler(verbose=1)
    distutils.sysconfig.customize_compiler(compiler) # CC, CFLAGS, LDFLAGS, etc

    fname = tempfile.mktemp(".c", "yajl_version")
    try:
        with open(fname, "wt") as f:
            f.write('''
            #include <yajl/yajl_version.h>
            int main(int args, char **argv)
            {
            #if YAJL_MAJOR != 2
                fail to compile
            #else
                yajl_version();
            #endif
                return 0;
            }
            ''')

        try:
            objs = compiler.compile([fname])
            compiler.link_shared_lib(objs, 'a', libraries=["yajl"])
            return True
        finally:
            os.remove(compiler.library_filename('a', lib_type='shared'))
            for obj in objs:
                os.remove(obj)

    except:
        return False
    finally:
        if os.path.exists(fname):
            os.remove(fname)

# Conditional compilation of the yajl_c backend
if platform.python_implementation() == 'CPython':
    extra_sources = []
    extra_include_dirs = []
    libs = ['yajl']
    embed_yajl = os.environ.get('IJSON_EMBED_YAJL', None) == '1'
    if not embed_yajl:
        have_yajl = yajl_present()
    else:
        extra_sources = sorted(glob.glob(os.path.join('yajl', 'src', '*.c')))
        extra_sources.remove(os.path.join('yajl', 'src', 'yajl_version.c'))
        extra_include_dirs = ['yajl', os.path.join('yajl', 'src')]
        libs = []
    if embed_yajl or have_yajl:
        yajl_ext = Extension('ijson.backends._yajl2',
                             language='c',
                             sources=sorted(glob.glob('ijson/backends/yajl2_c/*.c')) + extra_sources,
                             include_dirs=['ijson/backends/yajl2_c'] + extra_include_dirs,
                             libraries=libs,
                             depends=glob.glob('ijson/backends/yajl2_c/*.h'))
        setupArgs['ext_modules'] = [yajl_ext]

setup(**setupArgs)

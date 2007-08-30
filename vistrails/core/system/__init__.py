############################################################################
##
## Copyright (C) 2006-2007 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
import os
import os.path
import sys
import platform
import popen2
from core.utils import unimplemented, VistrailsInternalError
import core.requirements

##############################################################################

systemType = platform.system()

if systemType in ['Windows', 'Microsoft']:
    from core.system.windows import guess_total_memory, temporary_directory, \
        list2cmdline, \
        home_directory, remote_copy_program, remote_shell_program, \
        graph_viz_dot_command_line, remove_graph_viz_temporaries, \
        link_or_copy,executable_is_in_path, executable_is_in_pythonpath, \
        TestWindows

elif systemType in ['Linux']:
    from core.system.linux import guess_total_memory, temporary_directory, \
        list2cmdline, \
        home_directory, remote_copy_program, remote_shell_program, \
        graph_viz_dot_command_line, remove_graph_viz_temporaries, \
        link_or_copy, XDestroyWindow, executable_is_in_path, \
        executable_is_in_pythonpath, TestLinux

elif systemType in ['Darwin']:
    from core.system.osx import guess_total_memory, temporary_directory, \
        list2cmdline, \
        home_directory, remote_copy_program, remote_shell_program, \
        graph_viz_dot_command_line, remove_graph_viz_temporaries, \
        link_or_copy, executable_is_in_path, executable_is_in_pythonpath, \
        TestMacOSX
else:
    print "Critical error"
    print "VisTrails could not detect your operating system."
    sys.exit(1)

def touch(file_name):
    """touch(file_name) -> None Equivalent to 'touch' in a shell. If
    file exists, updates modified time to current time. If not,
    creates a new 0-length file.
    
    """
    if os.path.isfile(file_name):
        os.utime(file_name, None)
    else:
        file(file_name, 'w')

##############################################################################

# Makes sure root directory is sensible.
if __name__ == '__main__':
    _thisDir = sys.argv[0]
else:
    _thisDir = sys.modules[__name__].__file__
_thisDir = os.path.split(_thisDir)[0]
__rootDir = os.path.realpath(_thisDir + '/../../') + '/'

__dataDir = os.path.realpath(__rootDir + 'data/') + '/'
__fileDir = os.path.realpath(__rootDir + '../examples/') + '/'

def set_vistrails_data_directory(d):
    """ set_vistrails_data_directory(d:str) -> None 
    Sets vistrails data directory taking into account environment variables

    """
    global __dataDir
    new_d = os.path.expanduser(d)
    new_d = os.path.expandvars(new_d)
    while new_d != d:
        d = new_d
        new_d = os.path.expandvars(d)
    __dataDir = os.path.realpath(d) + '/'

def set_vistrails_file_directory(d):
    """ set_vistrails_file_directory(d: str) -> None
    Sets vistrails file directory taking into accoun environment variables
    
    """
    global __fileDir
    new_d = os.path.expanduser(d)
    new_d = os.path.expandvars(new_d)
    while new_d != d:
        d = new_d
        new_d = os.path.expandvars(d)
    __fileDir = os.path.realpath(d) + '/'

def set_vistrails_root_directory(d):
    """ set_vistrails_root_directory(d:str) -> None 
    Sets vistrails root directory taking into account environment variables

    """

    global __rootDir
    new_d = os.path.expanduser(d)
    new_d = os.path.expandvars(new_d)
    while new_d != d:
        d = new_d
        new_d = os.path.expandvars(d)
    __rootDir = os.path.realpath(d) + '/'

def vistrails_root_directory():
    """ vistrails_root_directory() -> str
    Returns vistrails root directory

    """
    return __rootDir

def vistrails_file_directory():
    """ vistrails_directory() -> str 
    Returns vistrails examples directory

    """
    return __fileDir

def packages_directory():
    """ packages_directory() -> str 
    Returns vistrails packages directory

    """
    return vistrails_root_directory() + 'packages/'

def blank_vistrail_file():
    unimplemented()

def resource_directory():
    """ resource_directory() -> str 
    Returns vistrails gui resource directory

    """
    return vistrails_root_directory() + 'gui/resources/'

def default_options_file():
    """ default_options_file() -> str 
    Returns vistrails default options file

    """
    return home_directory() + "/.vistrailsrc"

def default_dot_vistrails():
    """ default_dot_vistrails() -> str 
    Returns VisTrails per-user directory.

    """
    return home_directory() + "/.vistrails"

def default_bookmarks_file():
    """ default_bookmarks_file() -> str
    Returns default Vistrails per-user bookmarks file

    """
    return default_dot_vistrails() + "/bookmarks.xml"

def default_connections_file():
    """ default_connections_file() -> str
    Returns default Vistrails per-user connections file

    """
    return default_dot_vistrails() + "/connections.xml"

def python_version():
   """python_version() -> (major, minor, micro, release, serial)
Returns python version info."""
   return sys.version_info

def vistrails_version():
   """vistrails_version() -> string - Returns the current VisTrails version."""
   # 0.1 was the Vis2005 version
   # 0.2 was the SIGMOD demo version
   # 0.3 was the plugin/vtk version
   # 0.4 is cleaned up version with new GUI
   return '0.4'

def vistrails_revision():
    """vistrails_revision() -> str 
    When run on a working copy, shows the current svn revision else
    shows the latest release revision

    """
    old_dir = os.getcwd()
    os.chdir(vistrails_root_directory())
    try:
        release = "606"
        if core.requirements.executable_file_exists('svn'):
            if systemType not in ['Windows', 'Microsoft']:
                process = popen2.Popen4("svn info")
                result = -1
                while result == -1:
                    result = process.poll()
                svn_output = process.fromchild
            else:
                #Popen4 does not seem to be present on Windows
                svn_output, input = popen2.popen4("svn info")
                result = 0
            lines = svn_output.readlines()
            if len(lines) > 5:
                revision_line = lines[4][:-1].split(' ')
                if result == 0:
                    if revision_line[0] == 'Revision:':
                        return revision_line[1]
        return release
    finally:
        os.chdir(old_dir)
        
def about_string():
   """about_string() -> string - Returns the about string for VisTrails."""
   return """VisTrails version %s.%s -- vistrails@sci.utah.edu

Copyright (c) 2006-2007 University of Utah. All rights reserved.
http://www.vistrails.org

THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY \
APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT \
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM AS IS WITHOUT \
WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT \
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR \
A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND \
PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE PROGRAM PROVE \
DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR \
CORRECTION. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO \
IN WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY \
MODIFY AND/OR REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE \
TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR \
CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE \
PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING \
RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A \
FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF \
SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH \
DAMAGES.""" % (vistrails_version(), vistrails_revision())

def untitled_locator():
    from core.db.locator import XMLFileLocator
    return XMLFileLocator(default_dot_vistrails() + '/untitled.xml')

def get_elementtree_library():
    try:
        import cElementTree as ElementTree
    except ImportError:
        # try python 2.5-style
        import xml.etree.cElementTree as ElementTree
    return ElementTree
    

################################################################################

import unittest
import os
import os.path

if __name__ == '__main__':
    unittest.main()

class TestSystem(unittest.TestCase):

    def test_vistrails_revision(self):
        _starting_dir = os.getcwd()
        try:
            r = vistrails_root_directory()
            os.chdir(r)
            v1 = vistrails_revision()
            try:
                os.chdir(r + '../')
                self.assertEquals(v1, vistrails_revision())
            except AssertionError:
                raise
            except:
                pass
            try:
                os.chdir(r + '../../')
                self.assertEquals(v1, vistrails_revision())
            except AssertionError:
                raise
            except:
                pass
        finally:
            os.chdir(_starting_dir)
            

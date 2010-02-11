############################################################################
##
## Copyright (C) 2006-2010 University of Utah. All rights reserved.
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

from core.modules.vistrails_module import Module, ModuleError
import core.modules
import core.modules.basic_modules
import core.modules.module_registry
import core.system
import gui.application
from PyQt4 import QtCore, QtGui

##############################################################################

class Dialog(Module):
    pass

class TextDialog(Dialog):

    def is_cacheable(self):
        return False

    def compute(self):
        if self.hasInputFromPort('title'):
            title = self.getInputFromPort('title')
        else:
            title = 'VisTrails Dialog'
        if self.hasInputFromPort('label'):
            label = self.getInputFromPort('label')
        else:
            label = ''
        if self.hasInputFromPort('default'):
            default = QtCore.QString(self.getInputFromPort('default'))
        else:
            default = QtCore.QString('')
            
        (result, ok) = QtGui.QInputDialog.getText(None, title, label,
                                                  QtGui.QLineEdit.Normal,
                                                  default)
        if not ok:
            raise ModuleError(self, "Canceled")
        self.setResult('result', str(result))

##############################################################################

def initialize(*args, **keywords):
    reg = core.modules.module_registry.get_module_registry()
    basic = core.modules.basic_modules
    reg.add_module(Dialog)
    reg.add_module(TextDialog)

    reg.add_input_port(TextDialog, "title", basic.String)
    reg.add_input_port(TextDialog, "label", basic.String)
    reg.add_input_port(TextDialog, "default", basic.String)
    reg.add_output_port(TextDialog, "result", basic.String)
    
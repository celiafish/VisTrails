###############################################################################
##
## Copyright (C) 2006-2011, University of Utah. 
## All rights reserved.
## Contact: contact@vistrails.org
##
## This file is part of VisTrails.
##
## "Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice, 
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright 
##    notice, this list of conditions and the following disclaimer in the 
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the University of Utah nor the names of its 
##    contributors may be used to endorse or promote products derived from 
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################

import pylab
import urllib

from vistrails.core.modules.basic_modules import CodeRunnerMixin
from vistrails.core.modules.vistrails_module import Module, NotCacheable

################################################################################

class MplProperties(Module):
    def compute(self, artist):
        pass

#base class for 2D plots
class MplPlot(NotCacheable, Module):
    pass

class MplSource(CodeRunnerMixin, MplPlot):
    """
    MplSource is a module similar to PythonSource. The user can enter
    Matplotlib code into this module. This will then get connected to
    MplFigure to draw the figure. Please note that, codes entered in
    this module should limit to subplot() scope only. Using
    Figure-level commands, e.g. figure() or show(), the result will be
    unknown
    
    """
    _input_ports = [('source', '(basic:String)')]

    def compute(self):
        """ compute() -> None
        """
        source = self.getInputFromPort('source')
        s = ('from pylab import *\n' +
             'from numpy import *\n' +
             urllib.unquote(source))

        self.run_code(s, use_input=True, use_output=True)

class MplFigure(Module):
    _input_ports = [("addPlot", "(MplPlot)"),
                    ("axesProperties", "(MplAxesProperties)"),
                    ("figureProperties", "(MplFigureProperties)"),
                    ("setLegend", "(MplLegend)")]

    _output_ports = [("file", "(basic:File)"),
                     ("self", "(MplFigure)")]

    def __init__(self):
        Module.__init__(self)
        self.figInstance = None

    def updateUpstream(self):
        if self.figInstance is None:
            self.figInstance = pylab.figure()
        pylab.hold(True)
        Module.updateUpstream(self)

    def compute(self):
        plots = self.getInputListFromPort("addPlot")

        if self.hasInputFromPort("figureProperties"):
            figure_props = self.getInputFromPort("figureProperties")
            figure_props.update_props(self.figInstance)
        if self.hasInputFromPort("axesProperties"):
            axes_props = self.getInputFromPort("axesProperties")
            axes_props.update_props(self.figInstance.gca())
        if self.hasInputFromPort("setLegend"):
            legend = self.getInputFromPort("setLegend")
            self.figInstance.gca().legend()

        #FIXME write file out if File port is attached!

        # if num_rows > 1 or num_cols > 1:
        #     # need to reconstruct plot...
        #     self.figInstance = pylab.figure()
        # else:
        #     self.figInstance = plots[0].figInstance

        # for plot in plots:
        #     p_axes = plot.get_fig().gca()
        #     print "DPI:", plot.get_fig().dpi
        #     for c in p_axes.collections:
        #         print "TRANSFORM:", c._transform
        #         print "DATALIM:", c.get_datalim(p_axes.transData)
        #         print "PREPARE POINTS:", c._prepare_points()

        # self.figInstance = pylab.figure()
        # axes = self.figInstance.gca()
        # x0 = None
        # x1 = None
        # y0 = None
        # y1 = None
        # dataLim = None
        # for plot in plots:
        #     p_axes = plot.get_fig().gca()
        #     dataLim = p_axes.dataLim.frozen()
        #     p_x0, p_x1 = p_axes.get_xlim()
        #     if x0 is None or p_x0 < x0:
        #         x0 = p_x0
        #     if x1 is None or p_x1 > x1:
        #         x1 = p_x1
        #     p_y0, p_y1 = p_axes.get_ylim()
        #     if y0 is None or p_y0 < y0:
        #         y0 = p_y0
        #     if y1 is None or p_y1 > y1:
        #         y1 = p_y1

        # print x0, x1, y0, y1
        # axes.set_xlim(x0, x1, emit=False, auto=None)
        # axes.set_ylim(y0, y1, emit=False, auto=None)

        # # axes.dataLim = dataLim
        # # axes.ignore_existing_data_limits = False
        # # axes.autoscale_view()

        # for plot in plots:
        #     p_axes = plot.get_fig().gca()
        #     # axes.lines.extend(p_axes.lines)
        #     for line in p_axes.lines:
        #         print "adding line!"
        #         line = copy.copy(line)
        #         line._transformSet = False
        #         axes.add_line(line)
        #     # axes.patches.extend(p_axes.patches)
        #     for patch in p_axes.patches:
        #         print "adding patch!"
        #         patch = copy.copy(patch)
        #         patch._transformSet = False
        #         axes.add_patch(patch)
        #     axes.texts.extend(p_axes.texts)
        #     # axes.tables.extend(p_axes.tables)
        #     for table in p_axes.tables:
        #         table = copy.copy(table)
        #         table._transformSet = False
        #         axes.add_table(table)
        #     # axes.artists.extend(p_axes.artists)
        #     for artist in p_axes.artists:
        #         artist = copy.copy(artist)
        #         artist._transformSet = False
        #         axes.add_artist(artist)
        #     axes.images.extend(p_axes.images)
        #     # axes.collections.extend(p_axes.collections)
        #     for collection in p_axes.collections:
        #         print "adding collection!"
        #         # print "collection:", collection.__class__.__name__
        #         # print "datalim:", p_axes.dataLim
        #         # transOffset = axes.transData
        #         collection = copy.copy(collection)
        #         # collection._transformSet = False
        #         # print dir(mtransforms)
        #         collection.set_transform(mtransforms.IdentityTransform())
        #         collection._transOffset = axes.transData
        #         # collection._transformSet = False
        #         collection._label = None
        #         collection._clippath = None
        #         axes.add_collection(collection)
        #         # collection.set_transform(mtransforms.IdentityTransform())
        #         # axes.collections.append(collection)
        #     # axes.containers.extend(p_axes.containers)
        # print "transFigure start:", self.figInstance.transFigure
        # # axes.dataLim = dataLim
        # # axes.ignore_existing_data_limits = False
        # # print "datalim after:", axes.dataLim


        # # print "DPI:", self.figInstance.dpi
        # # for c in axes.collections:
        # #     print "TRANSFORM:", c._transform
        # #     print "DATALIM:", c.get_datalim(p_axes.transData)
        # #     print "PREPARE POINTS:", c._prepare_points()


        self.setResult("self", self)

class MplContourSet(Module):
    pass

class MplQuadContourSet(MplContourSet):
    pass
        
_modules = [(MplProperties, {'abstract': True}),
            (MplPlot, {'abstract': True}), 
            (MplSource, {'configureWidgetType': \
                             ('vistrails.packages.matplotlib.widgets',
                              'MplSourceConfigurationWidget')}),
            MplFigure,
            MplContourSet,
            MplQuadContourSet]
